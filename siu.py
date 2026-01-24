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
# 1. CORE LOGIC & DATABASE
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
from streamlit_google_auth import Authenticate

API_KEY = st.secrets["GEMINI_API_KEY"]
DATA_FOLDER = "DATA"
DB_PATH = "./chroma_db"
SQL_DB_FILE = "advocate_ai_v3.db"

def send_email_report(receiver_email, case_name, content):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Legal AI <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = f"Legal Analysis Report: {case_name}"
        body = f"Respected Counsel,\n\nAlpha Apex has generated a report for '{case_name}':\n\n{content}\n\nRegards,\nAlpha Apex Team"
        msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except: return False

# Database functions (init, register, get_cases, save_msg, load_history)
def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, joined_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

def db_get_cases(email):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT case_name FROM cases WHERE email=? ORDER BY id DESC", (email,))
    return [row[0] for row in c.fetchall()] or ["General Consultation"]

init_sql_db()

# ==============================================================================
# 2. IMPROVED VOICE ENGINE & UI
# ==============================================================================

st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")

def play_voice_js(text, lang_code):
    """Enhanced Voice Engine with retry logic for browsers"""
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            msg.lang = '{lang_code}';
            msg.rate = 1.0;
            
            function speak() {{
                var voices = window.speechSynthesis.getVoices();
                if (voices.length > 0) {{
                    window.speechSynthesis.speak(msg);
                }} else {{
                    setTimeout(speak, 100);
                }}
            }}
            speak();
        </script>
    """
    components.html(js_code, height=0)

@st.cache_resource
def load_models():
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3, google_api_key=API_KEY)
    embed = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, embed

ai_engine, vector_embedder = load_models()

# ==============================================================================
# 3. MAIN CHAMBERS
# ==============================================================================

def render_chambers_page():
    # 1. State Setup
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

    # 2. Sidebar
    with st.sidebar:
        st.title("👨‍⚖️ Alpha Apex")
        st.session_state.target_lang = st.selectbox("🌐 Global Language", list(langs.keys()), index=list(langs.keys()).index(st.session_state.target_lang))
        
        st.divider()
        st.subheader("📁 Cases")
        st.session_state.active_case = st.selectbox("Select Case", cases, index=cases.index(st.session_state.active_case))
        
        if st.button("🕒 Extract Timeline"):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            st.session_state.report = ai_engine.invoke(f"Extract timeline: {hist}").content
            st.info(st.session_state.report)
            
        if "report" in st.session_state and st.button("📧 Email Report"):
            send_email_report(st.session_state.user_email, st.session_state.active_case, st.session_state.report)
            st.success("Mailed!")

    # 3. Main Interface
    st.header(f"💼 {st.session_state.active_case}")
    
    # --- QUICK TOGGLE BAR ---
    t1, t2, _ = st.columns([1, 1, 5])
    with t1:
        if st.button("🇺🇸 English"): 
            st.session_state.target_lang = "English"
            st.rerun()
    with t2:
        if st.button("🇵🇰 Urdu"): 
            st.session_state.target_lang = "Urdu"
            st.rerun()

    # Chat Display
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    chat_box = st.container()
    with chat_box:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"])

    # Quick Actions
    st.divider()
    q1, q2, q3 = st.columns(3)
    quick_q = None
    if q1.button("🧠 Infer Path"): quick_q = "What is the best legal path for this?"
    if q2.button("📜 Give Ruling"): quick_q = "Give a preliminary ruling."
    if q3.button("📝 Summarize"): quick_q = "Summarize the facts."

    # Input
    c_in, c_mic = st.columns([10, 1])
    with c_in: user_txt = st.chat_input("Consulting Counsel...")
    with c_mic: user_voc = speech_to_text(language=langs[st.session_state.target_lang], key='mic')

    final_q = quick_q or user_voc or user_txt
    if final_q:
        # Save & Process
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_q)
        ans = ai_engine.invoke(f"Legal expert in {st.session_state.target_lang}. Context: {final_q}").content
        db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", ans)
        play_voice_js(ans, langs[st.session_state.target_lang])
        st.rerun()

# 4. Auth (Standard simplified version)
if not st.session_state.get("logged_in"):
    email = st.text_input("Enter Email")
    if st.button("Login"):
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.session_state.username = email.split("@")[0]
        st.rerun()
else:
    render_chambers_page()
