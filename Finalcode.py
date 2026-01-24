# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 24.0 (MAXIMUM VERBOSITY - SOVEREIGN PRODUCTION)
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
# 1. THEME ENGINE & ADVANCED SHADER ARCHITECTURE
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Leviathan Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_leviathan_shaders(theme_mode):
    """
    Injects an exhaustive CSS architecture into the Streamlit DOM.
    Includes glassmorphism, neural transitions, and layout overrides.
    """
    shader_css = """
    <style>
        /* Global Animation Layer */
        * { transition: background-color 0.8s cubic-bezier(0.4, 0, 0.2, 1), color 0.8s ease !important; }
        .stApp { transition: background 0.8s ease !important; }
        
        /* Glassmorphism Sidebar Architecture */
        [data-testid="stSidebar"] {
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            background: rgba(15, 23, 42, 0.9) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
            box-shadow: 5px 0 15px rgba(0,0,0,0.5) !important;
        }

        /* High-Fidelity Chat Geometry */
        .stChatMessage {
            border-radius: 25px !important;
            padding: 2.5rem !important;
            margin-bottom: 2rem !important;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2) !important;
            animation: slideUpFade 0.7s ease-out;
            border-left: 5px solid #38bdf8 !important;
        }

        @keyframes slideUpFade {
            from { opacity: 0; transform: translateY(30px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Precision Button Styling */
        .stButton>button {
            width: 100% !important;
            border-radius: 15px !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 2px !important;
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%) !important;
            color: #38bdf8 !important;
            border: 1px solid #38bdf8 !important;
            height: 3.5rem !important;
            transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-5px) scale(1.02) !important;
            box-shadow: 0 15px 30px rgba(56, 189, 248, 0.4) !important;
            background: #38bdf8 !important;
            color: #0f172a !important;
        }

        /* Sidebar Briefing Text Box */
        .sidebar-briefing {
            background: rgba(255, 255, 255, 0.05);
            padding: 15px;
            border-radius: 10px;
            border: 1px solid rgba(56, 189, 248, 0.2);
            font-size: 0.85rem;
            color: #f1f5f9;
            margin-top: 10px;
        }

        .stTextInput>div>div>input {
            background-color: rgba(255,255,255,0.05) !important;
            color: white !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 15px !important;
        }
    </style>
    """
    if theme_mode == "Dark Mode":
        shader_css += """
        <style>
            .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important; color: #ffffff !important; }
            .stChatMessage div, .stChatMessage p { color: #ffffff !important; }
            h1, h2, h3 { color: #38bdf8 !important; }
        </style>
        """
    else:
        shader_css += """
        <style>
            .stApp { background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%) !important; color: #0f172a !important; }
            .stChatMessage { background: #ffffff !important; border-left: 5px solid #0284c7 !important; }
            h1, h2, h3 { color: #0284c7 !important; }
        </style>
        """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. RELATIONAL DATABASE PERSISTENCE ENGINE
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v24.db"
DATA_FOLDER = "law_library_assets"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def init_leviathan_db():
    connection = sqlite3.connect(SQL_DB_FILE)
    cursor = connection.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT, registration_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT)''')
    connection.commit()
    connection.close()

def db_create_vault_user(email, name, password):
    if not email or not password: return False
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO users (email, full_name, vault_key, registration_date) VALUES (?,?,?,?)", (email, name, password, now))
        c.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", (email, "Default High Court Chamber", now))
        conn.commit(); conn.close(); return True
    except:
        conn.close(); return False

def db_verify_vault_access(email, password):
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    result = c.fetchone(); conn.close()
    return result[0] if result else None

def db_log_consultation(email, chamber_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    chamber_id = c.fetchone()
    if chamber_id:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) VALUES (?,?,?,?)", (chamber_id[0], role, content, timestamp))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    query = 'SELECT m.sender_role, m.message_body FROM message_logs m JOIN chambers c ON m.chamber_id = c.id WHERE c.owner_email=? AND c.chamber_name=? ORDER BY m.id ASC'
    c.execute(query, (email, chamber_name))
    rows = [{"role": r, "content": b} for r, b in c.fetchall()]
    conn.close(); return rows

init_leviathan_db()

# ==============================================================================
# 3. CORE ANALYTICAL SERVICES (AI & SMTP)
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    api_key_vault = st.secrets["GOOGLE_API_KEY"]
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=api_key_vault, temperature=0.2)

def execute_neural_synthesis(text, language_code):
    clean_text = re.sub(r'[*#_]', '', text).replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_payload = f"<script>window.speechSynthesis.cancel(); var msg = new SpeechSynthesisUtterance('{clean_text}'); msg.lang = '{language_code}'; window.speechSynthesis.speak(msg);</script>"
    components.html(js_payload, height=0)

def dispatch_legal_brief_smtp(target_email, chamber_name, history_data):
    try:
        smtp_sender = st.secrets["EMAIL_USER"]
        smtp_pass = st.secrets["EMAIL_PASS"].replace(" ", "")
        email_content = f"ALPHA APEX BRIEF - {chamber_name}\n" + "-"*30 + "\n"
        for entry in history_data:
            email_content += f"[{entry['role'].upper()}]: {entry['content']}\n\n"
        msg = MIMEMultipart(); msg['From'] = smtp_sender; msg['To'] = target_email; msg['Subject'] = f"Legal Brief: {chamber_name}"
        msg.attach(MIMEText(email_content, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(smtp_sender, smtp_pass)
        server.send_message(msg); server.quit(); return True
    except: return False

# ==============================================================================
# 4. UI: SOVEREIGN CHAMBERS
# ==============================================================================

def render_chamber_workstation():
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ ALPHA APEX")
        theme_sel = st.radio("System Theme", ["Dark Mode", "Light Mode"], horizontal=True)
        apply_leviathan_shaders(theme_sel)
        
        st.divider()
        st.subheader("🌐 Global Lexicon")
        active_lang = st.selectbox("Select Language", list(lexicon.keys()))
        l_code = lexicon[active_lang]
        
        st.divider()
        st.subheader("📁 Vault Navigator")
        u_mail = st.session_state.user_email
        conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
        chamber_list = [r[0] for r in c.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (u_mail,)).fetchall()]
        conn.close()
        st.session_state.current_chamber = st.selectbox("Active Chamber", chamber_list if chamber_list else ["Default Chamber"])

        # CUSTOM SYSTEM BRIEFING IN SIDEBAR
        st.markdown('<div class="sidebar-briefing"><b>🤖 SYSTEM PERSONA BRIEF:</b><br>'
                    'Role: Senior High Court Advocate<br>'
                    'Methodology: Strict IRAC Compliance<br>'
                    'Jurisdiction: Laws of Pakistan<br>'
                    'Logic: Statutes > Precedents</div>', unsafe_allow_html=True)
        
        st.divider()
        if st.button("📧 Dispatch Brief"):
            if dispatch_legal_brief_smtp(u_mail, st.session_state.current_chamber, db_fetch_chamber_history(u_mail, st.session_state.current_chamber)):
                st.sidebar.success("Brief Sent")
        
        if st.button("🚪 Logout"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    st.header(f"💼 Chamber: {st.session_state.current_chamber}")
    logs = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
    for entry in logs:
        with st.chat_message(entry["role"]): st.write(entry["content"])

    t_input = st.chat_input("Enter Legal Query...")
    v_input = speech_to_text(language=l_code, key='mic', just_once=True)
    final_input = t_input or v_input

    if final_input and (st.session_state.get("last_processed_query") != final_input):
        st.session_state.last_processed_query = final_input
        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_input)
        with st.chat_message("user"): st.write(final_input)
        
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                p_logic = f"PERSONA: Senior High Court Advocate Pakistan. Format: IRAC for legal problems, warm for greetings. Language: {active_lang}. INPUT: {final_input}"
                ai_response = get_analytical_engine().invoke(p_logic).content
                st.markdown(ai_response)
                db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", ai_response)
                execute_neural_synthesis(ai_response, l_code)
                st.rerun()

# ==============================================================================
# 5. UI: SOVEREIGN PORTAL
# ==============================================================================

def render_sovereign_portal():
    st.title("⚖️ ALPHA APEX LEVIATHAN PORTAL")
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        le = st.text_input("Email"); lp = st.text_input("Key", type="password")
        if st.button("Login"):
            u_name = db_verify_vault_access(le, lp)
            if u_name: st.session_state.update({"logged_in": True, "user_email": le, "username": u_name}); st.rerun()
    with t2:
        re = st.text_input("Email (New)"); ru = st.text_input("Name"); rp = st.text_input("Key (New)", type="password")
        if st.button("Register"):
            if db_create_vault_user(re, ru, rp): st.success("Registered.")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: render_sovereign_portal()
else: render_chamber_workstation()
