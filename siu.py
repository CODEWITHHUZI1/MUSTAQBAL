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
SQL_DB_FILE = "advocate_ai_v9.db"

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
# 2. SELECTIVE VOICE UTILITY
# ==============================================================================
def play_voice_js(text):
    """Renders ONLY for English sessions. No local language TTS allowed."""
    safe_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; margin: 10px 0;">
        <span style="font-size: 0.8rem; font-weight: bold; color: #1e293b;">🔊 English Audio:</span>
        <button onclick="window.speakNow()" style="margin-left:10px; cursor:pointer;">Play</button>
        <button onclick="window.speechSynthesis.cancel()" style="cursor:pointer;">Stop</button>
    </div>
    <script>
        window.speakNow = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            msg.lang = 'en-US';
            window.speechSynthesis.speak(msg);
        }};
        window.speakNow();
    </script>
    """
    components.html(js_code, height=90)

# ==============================================================================
# 3. CHAMBERS
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Sindhi": "sd-PK", "Pashto": "ps-PK", "Balochi": "bal-PK", "Urdu": "ur-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Display Language", list(langs.keys()))
        
        st.divider()
        st.subheader("📁 Case Management")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        active_case = st.selectbox("Active Case", cases if cases else ["General"])
        st.session_state.active_case = active_case

        with st.expander("Edit Cases"):
            new_c_name = st.text_input("New Case Name")
            if st.button("➕ Create"):
                if new_c_name:
                    conn = sqlite3.connect(SQL_DB_FILE)
                    conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (st.session_state.user_email, new_c_name, "2026-01-24"))
                    conn.commit(); conn.close(); st.rerun()

        st.subheader("🏛️ Configuration")
        sys_persona = st.text_input("Persona:", value="You are a Pakistani Law Analyst.")
        use_irac = st.toggle("Enable IRAC", value=True)

    st.header(f"💼 Case: {active_case}")
    chat_container = st.container()
    
    st.write("### Quick Actions")
    q1, q2, q3 = st.columns(3)
    quick_query = None
    if q1.button("🔍 Infer Context"): quick_query = "Infer legal context."
    if q2.button("⚖️ Give Ruling"): quick_query = "Give legal ruling."
    if q3.button("📝 Summarize"): quick_query = "Summarize case history."

    st.divider()
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Ask a question...")

    history = db_load_history(st.session_state.user_email, active_case)
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"])

    final_query = voice_in or text_in or quick_query
    if final_query:
        db_save_message(st.session_state.user_email, active_case, "user", final_query)
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)
            prompt = f"{sys_persona} {'Use IRAC.' if use_irac else ''} Respond strictly in {target_lang}. Query: {final_query}"
            response = llm.invoke(prompt).content
            db_save_message(st.session_state.user_email, active_case, "assistant", response)
            st.rerun() 
        except Exception as e: st.error(f"Error: {e}")

    # --- THE STRICT TTS GATEKEEPER ---
    if history and history[-1]["role"] == "assistant":
        # ONLY trigger TTS if the language is English. 
        # For Sindhi, Pashto, Balochi, Urdu, Punjabi: No TTS, No Animation.
        if target_lang == "English":
            if st.session_state.get("last_spoken") != history[-1]["content"]:
                play_voice_js(history[-1]["content"])
                st.session_state.last_spoken = history[-1]["content"]
        else:
            # Explicitly stop any leftover speech if language is changed
            components.html("<script>window.speechSynthesis.cancel();</script>", height=0)

# ==============================================================================
# 4. NAVIGATION
# ==============================================================================
def render_about():
    st.header("ℹ️ About Advocate AI")
    st.markdown("### 🏛️ Digital Justice\nProviding legal analysis in local scripts.")
    st.table([{"Name": "Saim Ahmed", "Role": "Lead Developer"}, {"Name": "Huzaifa Khan", "Role": "Legal AI"}])

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    email = st.text_input("Email")
    if st.button("Login"):
        st.session_state.logged_in = True; st.session_state.user_email = email; st.rerun()
else:
    page = st.sidebar.radio("Nav", ["Chambers", "About"])
    if page == "Chambers": render_chambers()
    else: render_about()
