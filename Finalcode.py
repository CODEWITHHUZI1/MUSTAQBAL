# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 33.1 (CONVERSATIONAL LOGIC & CONTRAST FIX)
# ARCHITECTS: SAIM AHMED, HUZAIFA KHAN, MUSTAFA KHAN, IBRAHIM SOHAIL, DANIYAL FARAZ
# ==============================================================================

try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    import sqlite3

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
# 1. PERMANENT SOVEREIGN SHADER ARCHITECTURE (DARK ONLY)
# ==============================================================================

st.set_page_config(
    page_title="Alpha Apex - Leviathan Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_leviathan_shaders():
    shader_css = """
    <style>
        * { transition: background-color 0.8s ease, color 0.8s ease !important; }
        
        .stApp { 
            background-color: #020617 !important; 
            color: #f1f5f9 !important; 
        }

        [data-testid="stSidebar"] {
            background-color: rgba(15, 23, 42, 0.98) !important;
            border-right: 2px solid #38bdf8 !important;
            box-shadow: 10px 0 20px rgba(0,0,0,0.5) !important;
        }

        [data-testid="stSidebarCollapsedControl"] {
            background-color: #38bdf8 !important;
            border-radius: 5px !important;
            color: #0f172a !important;
            display: flex !important;
        }

        .stChatMessage {
            border-radius: 20px !important;
            padding: 2.5rem !important;
            margin-bottom: 2rem !important;
            border: 1px solid rgba(56, 189, 248, 0.2) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
            background-color: rgba(30, 41, 59, 0.4) !important;
        }

        h1, h2, h3, h4 { 
            color: #38bdf8 !important; 
            font-weight: 900 !important; 
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        .stButton>button {
            border-radius: 12px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1.5px !important;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            color: #38bdf8 !important;
            border: 1px solid #38bdf8 !important;
            height: 3.5rem !important;
            width: 100% !important;
        }

        /* DARK INPUT FIELD: Dark box, Bright White Text for visibility */
        .stTextInput>div>div>input {
            background-color: #0f172a !important;
            color: #ffffff !important;
            border: 1.5px solid #38bdf8 !important;
            border-radius: 10px !important;
            font-weight: 500 !important;
        }
        
        .stChatInput textarea {
            background-color: #0f172a !important;
            color: #ffffff !important;
            border: 1px solid #38bdf8 !important;
        }

        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE ENGINE
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v32.db"
DATA_FOLDER = "law_library_assets"

def init_leviathan_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT, registration_date TEXT, total_queries INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT, is_archived INTEGER DEFAULT 0)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS system_telemetry (event_id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, event_type TEXT, description TEXT, event_timestamp TEXT)''')
    conn.commit(); conn.close()

def db_verify_vault_access(email, password):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    res = cursor.fetchone(); conn.close()
    return res[0] if res else None

def db_log_consultation(email, chamber_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    c_row = cursor.fetchone()
    if c_row:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) VALUES (?, ?, ?, ?)', (c_row[0], role, content, ts))
        if role == "user": cursor.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    sql = 'SELECT m.sender_role, m.message_body FROM message_logs m JOIN chambers c ON m.chamber_id = c.id WHERE c.owner_email=? AND c.chamber_name=? ORDER BY m.id ASC'
    cursor.execute(sql, (email, chamber_name)); rows = cursor.fetchall(); conn.close()
    return [{"role": r, "content": b} for r, b in rows]

init_leviathan_db()

# ==============================================================================
# 3. CORE AI ENGINE
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=st.secrets["GOOGLE_API_KEY"], 
        temperature=0.2
    )

# ==============================================================================
# 4. UI: SOVEREIGN CHAMBERS
# ==============================================================================

def render_chamber_workstation():
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    apply_leviathan_shaders()
    
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; margin-top: -30px;'>⚖️</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>ALPHA APEX</h3>", unsafe_allow_html=True)
        st.divider()
        
        st.subheader("System Persona")
        custom_persona = st.text_input("Define Bot Persona", value="Senior High Court Advocate")
        st.info(f"Targeting: {custom_persona}")
        
        st.divider()
        lang_choice = st.selectbox("Language", list(lexicon.keys()))
        l_code = lexicon[lang_choice]; st.divider()
        
        u_mail = st.session_state.user_email
        conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor(); 
        cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0", (u_mail,))
        chambers = [r[0] for r in cursor.fetchall()]; conn.close()
        st.session_state.current_chamber = st.selectbox("Active Chamber", chambers)
        
        if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

    st.header(f"💼 CASE: {st.session_state.current_chamber}")
    st.write("---")
    
    chat_container = st.container()
    with chat_container:
        history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
        for msg in history:
            with st.chat_message(msg["role"]): st.write(msg["content"])

    chat_col, mic_col = st.columns([0.85, 0.15])
    with chat_col: t_input = st.chat_input("Enter Query...")
    with mic_col: v_input = speech_to_text(language=l_code, key='v_mic', just_once=True)

    final_query = t_input or v_input

    if final_query:
        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_query)
        with chat_container:
            with st.chat_message("user"): st.write(final_query)
        
        with st.chat_message("assistant"):
            with st.spinner("Processing Strategy..."):
                try:
                    # UPDATED LOGIC: Allows for conversational politeness without "I only consult on law" spam
                    p = f"""
                    SYSTEM PERSONA: You are {custom_persona}. 
                    
                    SOCIAL PROTOCOL: 
                    - If the user greets you, greet them back formally and professionally.
                    - If the user says "Thank you", respond with professional courtesy (e.g., "It is my honor to assist you").
                    - If the user bids farewell, respond with a professional legal closing.
                    
                    STRICT KNOWLEDGE BOUNDARY: 
                    - You ONLY provide information regarding Law, Statutes, and Legal Procedures.
                    - For all other non-legal topics (weather, sports, general knowledge), say: "As your Legal Intelligence Advocate, I only consult on law."
                    
                    Language: {lang_choice}. 
                    Query: {final_query}
                    """
                    response = get_analytical_engine().invoke(p).content
                    st.markdown(response)
                    db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", response)
                    st.rerun()
                except Exception as e: st.error(f"AI Error: {e}")

# ==============================================================================
# 5. UI: SOVEREIGN PORTAL
# ==============================================================================

def render_sovereign_portal():
    apply_leviathan_shaders()
    st.title("⚖️ ALPHA APEX LEVIATHAN PORTAL")
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        e = st.text_input("Vault Email"); k = st.text_input("Key", type="password")
        if st.button("Enter Vault"):
            n = db_verify_vault_access(e, k)
            if n: st.session_state.logged_in = True; st.session_state.user_email = e; st.rerun()
            else: st.error("Access Denied")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: render_sovereign_portal()
else: render_chamber_workstation()
