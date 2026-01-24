__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import os
import sqlite3
import re
import time
from datetime import datetime
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. CONFIG & DB
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "advocate_ai_v3.db"

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, joined_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

def db_register_user(email, username):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (email, username, datetime.now().strftime("%Y-%m-%d")))
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General Consultation", datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_save_message(email, case_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    res = c.fetchone()
    if res:
        c.execute("INSERT INTO history (id, case_id, role, content, timestamp) VALUES (NULL,?,?,?,?)", (res[0], role, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
# 2. VOICE COMPONENT (JS)
# ==============================================================================
def play_voice_js(text, lang_code):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            msg.lang = '{lang_code}';
            window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

# ==============================================================================
# 3. AI ENGINE
# ==============================================================================
@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY, temperature=0.3)

ai_engine = load_llm()

# ==============================================================================
# 4. MAIN INTERFACE
# ==============================================================================
def render_chambers_page():
    # --- Sidebar Language & Case Logic ---
    langs = {
        "English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK",
        "Pashto": "ps-PK", "Arabic": "ar-SA", "French": "fr-FR", "Spanish": "es-ES",
        "German": "de-DE", "Chinese": "zh-CN", "Japanese": "ja-JP", "Russian": "ru-RU",
        "Hindi": "hi-IN", "Bengali": "bn-BD", "Portuguese": "pt-PT", "Italian": "it-IT",
        "Turkish": "tr-TR", "Korean": "ko-KR", "Persian": "fa-IR", "Marathi": "mr-IN"
    }
    
    with st.sidebar:
        st.title("👨‍⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Select Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        st.divider()
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        if "active_case" not in st.session_state: st.session_state.active_case = cases[0]
        st.selectbox("Active Case", cases, key="active_case_select")
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False
            st.rerun()

    # --- Chat History ---
    st.header(f"💼 Case: {st.session_state.active_case}")
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]): st.write(m["content"])

    # --- Quick Actions ---
    st.divider()
    q_col1, q_col2, q_col3 = st.columns(3)
    quick_q = None
    if q_col1.button("🧠 Infer Legal Path"): quick_q = "Based on our discussion, what is the best legal path forward?"
    if q_col2.button("📜 Give Preliminary Ruling"): quick_q = "Provide a preliminary judicial observation based on the facts."
    if q_col3.button("📝 Summarize Facts"): quick_q = "Summarize the key legal facts of this case."

    # --- Bottom Left Mic & Input ---
    m_col, i_col = st.columns([1, 6])
    with m_col:
        voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col:
        text_in = st.chat_input("Ask about Sindh Law...")

    # --- Logic Handling ---
    final_q = quick_q or voice_in or text_in
    if final_q:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_q)
        prompt = f"You are a Senior Legal Expert. Respond ONLY in {target_lang}. User Query: {final_q}"
        
        with st.chat_message("assistant"):
            with st.spinner("⚖️ Thinking..."):
                ans = ai_engine.invoke(prompt).content
                st.write(ans)
                db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", ans)
                play_voice_js(ans, lang_code)
                st.rerun()

# ==============================================================================
# 5. ENTRY POINT
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex AI Login")
    email = st.text_input("Email")
    if st.button("Enter"):
        if "@" in email:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            db_register_user(email, email.split("@")[0])
            st.rerun()
else:
    render_chambers_page()

