# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM (V24.1 - FIXED)
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
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ==============================================================================
# 1. THEME ENGINE & ADVANCED SHADER ARCHITECTURE
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Leviathan Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_leviathan_shaders(theme_mode):
    shader_css = """
    <style>
        * { transition: background-color 0.8s cubic-bezier(0.4, 0, 0.2, 1), color 0.8s ease !important; }
        [data-testid="stSidebar"] {
            backdrop-filter: blur(20px);
            background: rgba(15, 23, 42, 0.9) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        .stChatMessage {
            border-radius: 25px !important;
            padding: 1.5rem !important;
            margin-bottom: 1rem !important;
            border-left: 5px solid #38bdf8 !important;
        }
        .stButton>button {
            width: 100% !important;
            border-radius: 15px !important;
            font-weight: 800 !important;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
            color: #38bdf8 !important;
            border: 1px solid #38bdf8 !important;
        }
        .block-container { max-width: 1100px; margin: auto; }
    </style>
    """
    if theme_mode == "Dark Mode":
        shader_css += "<style>.stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important; color: #f1f5f9 !important; }</style>"
    else:
        shader_css += "<style>.stApp { background: white !important; color: #0f172a !important; }</style>"
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. RDBMS PERSISTENCE ENGINE
# ==============================================================================
SQL_DB_FILE = "alpha_apex_leviathan_master_v24.db"

def init_leviathan_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT, registration_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT)')
    conn.commit()
    conn.close()

def db_verify_vault_access(email, password):
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    res = c.fetchone(); conn.close()
    return res[0] if res else None

def db_log_consultation(email, chamber_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    cid = c.fetchone()
    if cid:
        c.execute("INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) VALUES (?,?,?,?)", 
                  (cid[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT m.sender_role, m.message_body FROM message_logs m JOIN chambers c ON m.chamber_id = c.id WHERE c.owner_email=? AND c.chamber_name=? ORDER BY m.id ASC", (email, chamber_name))
    rows = [{"role": r, "content": b} for r, b in c.fetchall()]
    conn.close(); return rows

init_leviathan_db()

# ==============================================================================
# 3. AI SERVICES
# ==============================================================================
@st.cache_resource
def get_analytical_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.2)

def execute_neural_synthesis(text, language_code):
    clean = text.replace("'", "").replace('"', "").replace("\n", " ")
    js = f"<script>window.speechSynthesis.cancel(); var m = new SpeechSynthesisUtterance('{clean}'); m.lang='{language_code}'; window.speechSynthesis.speak(m);</script>"
    components.html(js, height=0)

# ==============================================================================
# 4. CHAMBER WORKSTATION (FIXED INPUT LOGIC)
# ==============================================================================
def render_chamber_workstation():
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ ALPHA APEX")
        theme_sel = st.radio("System Theme", ["Dark Mode", "Light Mode"], horizontal=True)
        apply_leviathan_shaders(theme_sel)
        active_lang = st.selectbox("Language", list(lexicon.keys()))
        l_code = lexicon[active_lang]
        
        conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
        chamber_list = [r[0] for r in c.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        st.session_state.current_chamber = st.selectbox("Active Chamber", chamber_list if chamber_list else ["Default Chamber"])
        
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False; st.rerun()

    st.header(f"💼 Chamber: {st.session_state.current_chamber}")
    
    # Display History
    logs = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
    for entry in logs:
        with st.chat_message(entry["role"]): st.write(entry["content"])

    st.write("---")
    
    # INPUT SECTION
    cols = st.columns([0.8, 0.2])
    with cols[1]:
        v_input = speech_to_text(language=l_code, key='mic', just_once=True, use_container_width=True)
    with cols[0]:
        t_input = st.chat_input("Enter Legal Query...")

    # Determine final input and prevent duplication
    final_query = t_input or v_input

    if final_query:
        # 1. Log User Message immediately to DB
        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_query)
        
        # 2. Show User Message in UI
        with st.chat_message("user"): st.write(final_query)
        
        # 3. Generate and Log AI Response
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Statutes..."):
                prompt = f"Persona: Senior Advocate. Mode: IRAC for legal, warm for greetings. Language: {active_lang}. Query: {final_query}"
                response = get_analytical_engine().invoke(prompt).content
                st.markdown(response)
                db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", response)
                execute_neural_synthesis(response, l_code)
        
        # 4. Forced Rerun to clear the chat_input buffer and avoid repetition
        time.sleep(0.5)
        st.rerun()

# ==============================================================================
# 5. MASTER ROUTER
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚖️ ALPHA APEX LEVIATHAN")
    le = st.text_input("Vault Email")
    lp = st.text_input("Security Key", type="password")
    if st.button("Enter Vault"):
        name = db_verify_vault_access(le, lp)
        if name:
            st.session_state.logged_in = True
            st.session_state.user_email = le
            st.rerun()
        else: st.error("Access Denied")
else:
    render_chamber_workstation()
