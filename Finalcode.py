# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 24.0 (MOBILE OPTIMIZED - SOVEREIGN PRODUCTION)
# ARCHITECTS: SAIM AHMED, HUZAIFA KHAN, MUSTAFA KHAN, IBRAHIM SOHAIL, DANIYAL FARAZ
# ==============================================================================

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import json
import os
import time
import base64
import re
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ==============================================================================
# 1. THEME ENGINE & MOBILE SHADER ARCHITECTURE (FIXED)
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Leviathan Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="collapsed" # Better for mobile first-load
)

def apply_leviathan_shaders(theme_mode):
    """
    Injects CSS optimized for mobile viewports.
    """
    shader_css = """
    <style>
        /* Mobile Viewport Fix */
        @media (max-width: 640px) {
            .stChatMessage { padding: 1rem !important; margin-bottom: 1rem !important; }
            .stHeader { font-size: 1.5rem !important; }
            [data-testid="stSidebar"] { width: 80vw !important; }
        }

        * { transition: background-color 0.5s ease; }
        
        [data-testid="stSidebar"] {
            backdrop-filter: blur(15px);
            background: rgba(15, 23, 42, 0.95) !important;
        }

        .stChatMessage {
            border-radius: 15px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1) !important;
            border-left: 5px solid #38bdf8 !important;
        }
        
        .stButton>button {
            width: 100% !important;
            border-radius: 12px !important;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
            color: #38bdf8 !important;
            border: 1px solid #38bdf8 !important;
        }

        .sidebar-briefing {
            background: rgba(255, 255, 255, 0.05);
            padding: 10px;
            border-radius: 8px;
            font-size: 0.8rem;
            color: #f1f5f9;
        }
    </style>
    """
    if theme_mode == "Dark Mode":
        shader_css += "<style>.stApp { background: #020617 !important; color: #ffffff !important; } .stChatMessage div, .stChatMessage p { color: #ffffff !important; }</style>"
    else:
        shader_css += "<style>.stApp { background: #f8fafc !important; color: #0f172a !important; }</style>"
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE PERSISTENCE (CHECK_SAME_THREAD FIX FOR MOBILE)
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v24.db"

def get_db_connection():
    # check_same_thread=False is critical for mobile server requests
    return sqlite3.connect(SQL_DB_FILE, check_same_thread=False)

def init_leviathan_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT, registration_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT)''')
    conn.commit(); conn.close()

def db_create_vault_user(email, name, password):
    if not email or not password: return False
    conn = get_db_connection(); c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO users (email, full_name, vault_key, registration_date) VALUES (?,?,?,?)", (email, name, password, now))
        c.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", (email, "Default High Court Chamber", now))
        conn.commit(); conn.close(); return True
    except: conn.close(); return False

def db_verify_vault_access(email, password):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    res = c.fetchone(); conn.close(); return res[0] if res else None

def db_log_consultation(email, chamber_name, role, content):
    conn = get_db_connection(); c = conn.cursor()
    c.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    cid = c.fetchone()
    if cid:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) VALUES (?,?,?,?)", (cid[0], role, content, ts))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    conn = get_db_connection(); c = conn.cursor()
    q = 'SELECT m.sender_role, m.message_body FROM message_logs m JOIN chambers c ON m.chamber_id = c.id WHERE c.owner_email=? AND c.chamber_name=? ORDER BY m.id ASC'
    c.execute(q, (email, chamber_name))
    rows = [{"role": r, "content": b} for r, b in c.fetchall()]
    conn.close(); return rows

init_leviathan_db()

# ==============================================================================
# 3. CORE ANALYTICAL SERVICES
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.2)

def execute_neural_synthesis(text, language_code):
    clean = re.sub(r'[*#_]', '', text).replace("'", "").replace('"', "").replace("\n", " ").strip()
    js = f"<script>window.speechSynthesis.cancel(); var m = new SpeechSynthesisUtterance('{clean}'); m.lang = '{language_code}'; window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

def dispatch_legal_brief_smtp(target, chamber, history):
    try:
        user, pwd = st.secrets["EMAIL_USER"], st.secrets["EMAIL_PASS"].replace(" ", "")
        content = f"LEGAL BRIEF: {chamber}\n\n"
        for e in history: content += f"[{e['role'].upper()}]: {e['content']}\n\n"
        msg = MIMEMultipart(); msg['From'] = user; msg['To'] = target; msg['Subject'] = f"Brief: {chamber}"
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); s.login(user, pwd); s.send_message(msg); s.quit(); return True
    except: return False

# ==============================================================================
# 4. UI: CHAMBERS
# ==============================================================================

def render_chamber_workstation():
    lex = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    with st.sidebar:
        st.title("⚖️ ALPHA APEX")
        mode = st.radio("Theme", ["Dark Mode", "Light Mode"], horizontal=True)
        apply_leviathan_shaders(mode)
        lang = st.selectbox("Language", list(lex.keys()))
        u_mail = st.session_state.user_email
        conn = get_db_connection(); c = conn.cursor()
        ch_list = [r[0] for r in c.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (u_mail,)).fetchall()]
        conn.close()
        st.session_state.current_chamber = st.selectbox("Chamber", ch_list if ch_list else ["Default"])
        st.markdown('<div class="sidebar-briefing"><b>🤖 PERSONA:</b> Senior Advocate<br><b>METHOD:</b> IRAC</div>', unsafe_allow_html=True)
        if st.button("📧 Send Email"):
            if dispatch_legal_brief_smtp(u_mail, st.session_state.current_chamber, db_fetch_chamber_history(u_mail, st.session_state.current_chamber)):
                st.sidebar.success("Sent")
        if st.button("🚪 Logout"):
            st.session_state.clear(); st.rerun()

    st.header(f"💼 {st.session_state.current_chamber}")
    for e in db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber):
        with st.chat_message(e["role"]): st.write(e["content"])

    t_in = st.chat_input("Enter Query...")
    v_in = speech_to_text(language=lex[lang], key='mic', just_once=True)
    f_in = t_in or v_in

    if f_in and (st.session_state.get("last_query") != f_in):
        st.session_state.last_query = f_in
        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", f_in)
        with st.chat_message("user"): st.write(f_in)
        with st.chat_message("assistant"):
            with st.spinner("Wait..."):
                p = f"Persona: Senior Advocate Pakistan. Rule: IRAC. Lang: {lang}. Query: {f_in}"
                ans = get_analytical_engine().invoke(p).content
                st.markdown(ans)
                db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", ans)
                execute_neural_synthesis(ans, lex[lang])
                st.rerun()

# ==============================================================================
# 5. UI: PORTAL
# ==============================================================================

def render_sovereign_portal():
    st.title("⚖️ LEVIATHAN PORTAL")
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        e = st.text_input("Email"); k = st.text_input("Key", type="password")
        if st.button("Access Vault"):
            n = db_verify_vault_access(e, k)
            if n: st.session_state.update({"logged_in": True, "user_email": e, "username": n}); st.rerun()
    with t2:
        ne = st.text_input("New Email"); nu = st.text_input("Name"); nk = st.text_input("New Key", type="password")
        if st.button("Register"):
            if db_create_vault_user(ne, nu, nk): st.success("Done.")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: render_sovereign_portal()
else: render_chamber_workstation()
