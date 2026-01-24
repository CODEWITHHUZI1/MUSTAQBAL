__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. INITIALIZATION & DATABASE
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")
API_KEY = st.secrets["GEMINI_API_KEY"]
SQL_DB_FILE = "advocate_ai_v5.db"

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

def db_save_message(email, case_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    res = c.fetchone()
    if res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", 
                  (res[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def db_load_history(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, content FROM history JOIN cases ON history.case_id = cases.id WHERE cases.email=? AND cases.case_name=? ORDER BY history.id ASC", (email, case_name))
    data = [{"role": r, "content": t} for r, t in c.fetchall()]
    conn.close()
    return data

init_sql_db()

# ==============================================================================
# 2. VOICE & EMAIL UTILITIES (ENGLISH ONLY TTS)
# ==============================================================================
def play_voice_js(english_text):
    """Voice Engine strictly for English output"""
    safe_text = english_text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; margin: 10px 0;">
        <span style="font-size: 0.8rem; font-weight: bold;">🔊 English Audio:</span>
        <button onclick="window.speechSynthesis.resume()">Play</button>
        <button onclick="window.speechSynthesis.pause()">Pause</button>
        <button onclick="window.speechSynthesis.cancel()">Stop</button>
    </div>
    <script>
        function speakNow() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            msg.lang = 'en-US';
            msg.rate = 1.0;
            window.speechSynthesis.speak(msg);
        }}
        speakNow();
    </script>
    """
    components.html(js_code, height=80)

# ==============================================================================
# 3. CHAMBERS
# ==============================================================================
def render_chambers():
    # Only the three target languages + English
    langs = {"Sindhi": "sd-PK", "Pashto": "ps-PK", "Balochi": "bal-PK", "English": "en-US"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Choose Language Script", list(langs.keys()))
        st.divider()
        
        st.subheader("📁 Case Management")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        active_case = st.selectbox("Active Case", cases if cases else ["General"])
        st.session_state.active_case = active_case

        with st.expander("Case Options"):
            new_c_name = st.text_input("New Case")
            if st.button("➕ Create"):
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (st.session_state.user_email, new_c_name, "2026-01-24"))
                conn.commit(); conn.close(); st.rerun()

    st.header(f"💼 Case: {active_case}")
    chat_container = st.container()
    
    # Quick Actions
    st.write("### Quick Actions")
    q1, q2, q3 = st.columns(3)
    quick_query = None
    if q1.button("🔍 Infer Context"): quick_query = "Infer legal context from our conversation."
    if q2.button("⚖️ Give Ruling"): quick_query = "Provide a legal ruling/opinion based on Pakistani law."
    if q3.button("📝 Summarize"): quick_query = "Summarize the case history."

    st.divider()
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Enter query...")

    history = db_load_history(st.session_state.user_email, active_case)
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"].split("|||")[0])

    final_query = voice_in or text_in or quick_query
    if final_query:
        db_save_message(st.session_state.user_email, active_case, "user", final_query)
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)
            
            # CORE SCRIPT TRANSLATION PROMPT
            prompt = f"""
            You are a Pakistani Law Expert.
            Translate your answer strictly into the {target_lang} native script.
            Provide the response in two parts separated by '|||'.
            Part 1: The response in {target_lang} script.
            Part 2: The exact same response translated into English for TTS.
            Example: [Native Script] ||| [English Translation]
            Query: {final_query}
            """
            
            response = llm.invoke(prompt).content
            db_save_message(st.session_state.user_email, active_case, "assistant", response)
            st.rerun() 
        except Exception as e: st.error(f"Error: {e}")

    if history and history[-1]["role"] == "assistant":
        if "|||" in history[-1]["content"]:
            english_part = history[-1]["content"].split("|||")[1]
            if st.session_state.get("last_spoken") != english_part:
                play_voice_js(english_part)
                st.session_state.last_spoken = english_part

# ==============================================================================
# 4. ABOUT & NAVIGATION
# ==============================================================================
def render_about():
    st.header("ℹ️ About Advocate AI")
    st.markdown("""
    **Advocate AI (Alpha Apex)** is a digital gateway designed to solve the justice gap in Pakistan.
    - **Problem:** Barriers of high cost, language complexity, and exclusion from the legal system.
    - **Value:** Real-time translation into Sindhi, Pashto, and Balochi scripts with English TTS analysis.
    """)
    team = [
        {"Name": "Saim Ahmed", "Role": "Lead Developer"},
        {"Name": "Huzaifa Khan", "Role": "Legal Strategist"}
    ]
    st.table(team)

if not st.session_state.get("logged_in"):
    st.title("⚖️ Alpha Apex Login")
    email = st.text_input("Email")
    if st.button("Login"):
        st.session_state.logged_in = True; st.session_state.user_email = email; st.rerun()
else:
    page = st.sidebar.radio("Nav", ["Chambers", "Library", "About"])
    if page == "Chambers": render_chambers()
    elif page == "About": render_about()
    else: st.header("📚 Library")
