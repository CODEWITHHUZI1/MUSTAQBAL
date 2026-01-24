__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. INITIALIZATION & DATABASE
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")
API_KEY = st.secrets["GEMINI_API_KEY"]
SQL_DB_FILE = "advocate_ai_v11.db"

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
# 2. SELECTIVE VOICE UTILITY (STRICT ENGLISH LOCK)
# ==============================================================================
def play_voice_js(text):
    """Only renders when target_lang == 'English'. No local script TTS allowed."""
    safe_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f1f5f9; padding: 12px; border-radius: 8px; border: 1px solid #cbd5e1; margin: 10px 0;">
        <span style="font-size: 0.85rem; font-weight: 700; color: #1e293b;">🔊 English Voice Assistant</span>
        <div style="margin-top: 8px;">
            <button onclick="window.speakNow()" style="cursor:pointer; padding: 4px 10px;">Play</button>
            <button onclick="window.speechSynthesis.cancel()" style="cursor:pointer; padding: 4px 10px; background:#fee2e2; border:1px solid #ef4444;">Stop</button>
        </div>
    </div>
    <script>
        window.speakNow = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            msg.lang = 'en-US';
            msg.rate = 1.0;
            window.speechSynthesis.speak(msg);
        }};
        window.speakNow();
    </script>
    """
    components.html(js_code, height=100)

# ==============================================================================
# 3. CHAMBERS & AI LOGIC
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Sindhi": "sd-PK", "Pashto": "ps-PK", "Balochi": "bal-PK", "Urdu": "ur-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Display Language", list(langs.keys()))
        
        st.divider()
        st.subheader("🏛️ AI Configuration")
        sys_persona = st.text_input("Core Persona:", value="You are a Pakistani Law Analyst.")
        use_irac = st.toggle("Enable IRAC structure", value=True)
        
        st.divider()
        st.subheader("📁 Case Management")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        active_case = st.selectbox("Active Case", cases if cases else ["General Consultation"])
        st.session_state.active_case = active_case

        if st.button("➕ New Case"):
            new_name = f"Case {len(cases)+1}"
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (st.session_state.user_email, new_name, "2026-01-24"))
            conn.commit(); conn.close(); st.rerun()

    st.header(f"💼 Chambers: {active_case}")
    
    # Quick Actions
    st.write("### Quick Actions")
    q1, q2, q3 = st.columns(3)
    quick_query = None
    if q1.button("🔍 Infer Context"): quick_query = "Based on our chat, what is the legal context?"
    if q2.button("⚖️ Give Ruling"): quick_query = "Provide a legal ruling based on the PPC or Constitution."
    if q3.button("📝 Summarize"): quick_query = "Summarize the key facts of this case."

    # Chat Display
    history = db_load_history(st.session_state.user_email, active_case)
    for m in history:
        with st.chat_message(m["role"]): st.write(m["content"])

    # Chat Input
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Enter legal query...")

    final_query = voice_in or text_in or quick_query
    
    if final_query:
        # Display and Save User Query
        with st.chat_message("user"): st.write(final_query)
        db_save_message(st.session_state.user_email, active_case, "user", final_query)
        
        # AI Response
        try:
            with st.chat_message("assistant"):
                with st.spinner("Consulting Statutes..."):
                    # MODEL DEFINED HERE
                    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)
                    
                    irac_prompt = "Structure your answer using IRAC (Issue, Rule, Analysis, Conclusion)." if use_irac else ""
                    full_prompt = f"{sys_persona}\n{irac_prompt}\nRespond strictly in {target_lang}.\n\nQuery: {final_query}"
                    
                    response = llm.invoke(full_prompt).content
                    st.write(response)
                    db_save_message(st.session_state.user_email, active_case, "assistant", response)
                    
                    # TTS GATEKEEPER: ONLY ENGLISH
                    if target_lang == "English":
                        play_voice_js(response)
                        st.session_state.last_spoken = response
                    else:
                        # Ensure no ghost-audio from previous English sessions
                        components.html("<script>window.speechSynthesis.cancel();</script>", height=0)
                    
                    st.rerun()
        except Exception as e:
            st.error(f"Gemini Error: {e}")

# ==============================================================================
# 4. LOGIN & NAVIGATION
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    u_email = st.text_input("Enter Email to enter Chambers")
    if st.button("Enter"):
        st.session_state.logged_in = True
        st.session_state.user_email = u_email
        conn = sqlite3.connect(SQL_DB_FILE)
        conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (u_email, "General Consultation", "2026-01-24"))
        conn.commit(); conn.close(); st.rerun()
else:
    page = st.sidebar.radio("Nav", ["Chambers", "About"])
    if page == "Chambers": render_chambers()
    else: 
        st.header("ℹ️ About Advocate AI")
        st.write("Advanced Legal Intelligence powered by Gemini 2.0 Flash.")
