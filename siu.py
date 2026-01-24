import streamlit as st
import os
import sqlite3
import glob
import time
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit.components.v1 as components

# ==============================================================================
# 1. DATABASE & UTILITY FUNCTIONS (Defined First to avoid NameError)
# ==============================================================================

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

def db_load_history(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT role, content FROM history 
        JOIN cases ON history.case_id = cases.id 
        WHERE cases.email=? AND cases.case_name=? 
        ORDER BY history.id ASC
    """, (email, case_name))
    data = [{"role": r, "content": t} for r, t in c.fetchall()]
    conn.close()
    return data

def db_save_message(email, case_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    res = c.fetchone()
    if res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", 
                  (res[0], role, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def db_get_cases(email):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT case_name FROM cases WHERE email=? ORDER BY id DESC", (email,))
    rows = c.fetchall()
    conn.close()
    return [row[0] for row in rows] if rows else ["General Consultation"]

def db_create_case(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, case_name, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_rename_case(email, old_name, new_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE cases SET case_name = ? WHERE email = ? AND case_name = ?", (new_name, email, old_name))
    conn.commit()
    conn.close()

def send_email_report(receiver_email, case_name, content):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Legal <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = f"Legal Analysis: {case_name}"
        body = f"Respected Counsel,\n\nAlpha Apex has generated a report for '{case_name}':\n\n{content}\n\nRegards,\nAlpha Apex Team"
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Mail failed: {e}")
        return False

# Start DB
init_sql_db()

# ==============================================================================
# 2. AI & VOICE CONFIG
# ==============================================================================

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass 

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from streamlit_mic_recorder import speech_to_text

st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")

API_KEY = st.secrets["GEMINI_API_KEY"]
MODEL_NAME = "gemini-1.5-flash"

def play_voice_js(text, lang_code):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            msg.lang = '{lang_code}';
            function speak() {{
                var v = window.speechSynthesis.getVoices();
                if (v.length > 0) {{ window.speechSynthesis.speak(msg); }}
                else {{ setTimeout(speak, 100); }}
            }}
            speak();
        </script>
    """
    components.html(js_code, height=0)

@st.cache_resource
def load_models():
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.3, google_api_key=API_KEY)
    embed = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, embed

ai_engine, vector_embedder = load_models()

# ==============================================================================
# 3. CHAMBERS PAGE
# ==============================================================================

def render_chambers_page():
    # Session Initialization
    cases = db_get_cases(st.session_state.user_email)
    if "active_case" not in st.session_state: st.session_state.active_case = cases[0]
    if "target_lang" not in st.session_state: st.session_state.target_lang = "English"

    langs = {
        "English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK",
        "Pashto": "ps-PK", "Arabic": "ar-SA", "French": "fr-FR", "Spanish": "es-ES",
        "German": "de-DE", "Chinese": "zh-CN", "Japanese": "ja-JP", "Russian": "ru-RU",
        "Hindi": "hi-IN", "Bengali": "bn-BD", "Portuguese": "pt-PT", "Italian": "it-IT",
        "Turkish": "tr-TR", "Korean": "ko-KR", "Persian": "fa-IR", "Marathi": "mr-IN"
    }

    with st.sidebar:
        st.title("👨‍⚖️ Alpha Apex")
        st.session_state.target_lang = st.selectbox("🌐 Language", list(langs.keys()), 
                                                   index=list(langs.keys()).index(st.session_state.target_lang))
        
        st.divider()
        st.subheader("📁 Case Management")
        sel = st.selectbox("Switch Case", cases, index=cases.index(st.session_state.active_case))
        if sel != st.session_state.active_case:
            st.session_state.active_case = sel
            st.rerun()
            
        if st.button("➕ New Case"):
            db_create_case(st.session_state.user_email, f"New Consultation {len(cases)+1}")
            st.rerun()

        st.divider()
        st.subheader("📤 Reports")
        history = db_load_history(st.session_state.user_email, st.session_state.active_case)
        if st.button("🕒 Extract Timeline"):
            if history:
                st.session_state.report = ai_engine.invoke(f"Extract timeline from: {history}").content
                st.info(st.session_state.report)
            else: st.warning("No chat data.")
            
        if "report" in st.session_state and st.button("📧 Email to Me"):
            if send_email_report(st.session_state.user_email, st.session_state.active_case, st.session_state.report):
                st.success("Report Sent!")

    # UI Header & Quick Toggle
    st.header(f"💼 Case: {st.session_state.active_case}")
    t1, t2, _ = st.columns([1, 1, 5])
    if t1.button("🇺🇸 English"): 
        st.session_state.target_lang = "English"
        st.rerun()
    if t2.button("🇵🇰 Urdu"): 
        st.session_state.target_lang = "Urdu"
        st.rerun()

    # Chat Display (Above input)
    for m in history:
        with st.chat_message(m["role"]): st.write(m["content"])

    # Quick Actions
    st.divider()
    q1, q2, q3 = st.columns(3)
    quick_q = None
    if q1.button("🧠 Infer Path"): quick_q = "What is the recommended legal path?"
    if q2.button("📜 Give Ruling"): quick_q = "Provide a preliminary judicial observation."
    if q3.button("📝 Summarize"): quick_q = "Summarize the legal facts discussed."

    # Input Bar
    c_txt, c_mic = st.columns([10, 1])
    with c_txt: text_in = st.chat_input("Consulting Counsel...")
    with c_mic: voice_in = speech_to_text(language=langs[st.session_state.target_lang], key='mic', just_once=True)

    final_q = quick_q or voice_in or text_in
    if final_q:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_q)
        ans = ai_engine.invoke(f"Expert in {st.session_state.target_lang}. User says: {final_q}").content
        db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", ans)
        play_voice_js(ans, langs[st.session_state.target_lang])
        st.rerun()

# ==============================================================================
# 4. LOGIN & MAIN
# ==============================================================================

if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex AI")
    email = st.text_input("Enter Email to Access Chambers")
    if st.button("Login"):
        if "@" in email:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            st.session_state.username = email.split("@")[0].capitalize()
            db_register_user(email, st.session_state.username)
            st.rerun()
else:
    render_chambers_page()
