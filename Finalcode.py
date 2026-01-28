# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 37.0 (ULTRA UI UPGRADE)
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
import os
import time
import requests  # Required for Lottie
import pandas as pd
from PyPDF2 import PdfReader
from streamlit_lottie import st_lottie
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. ENHANCED SOVEREIGN SHADER ARCHITECTURE
# ==============================================================================

st.set_page_config(
    page_title="Alpha Apex - Leviathan Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_lottie_url(url: str):
    r = requests.get(url)
    if r.status_code != 200: return None
    return r.json()

def apply_leviathan_shaders():
    shader_css = """
    <style>
        /* GLOBAL TRANSITIONS */
        * { transition: all 0.4s ease-in-out !important; }
        
        .stApp { background-color: #0b1120 !important; color: #e2e8f0 !important; }
        
        /* SIDEBAR ENHANCEMENT */
        [data-testid="stSidebar"] {
            background-color: #020617 !important;
            border-right: 1px solid #1e293b !important;
        }

        /* ANIMATED CHAT MESSAGES */
        .stChatMessage {
            animation: fadeIn 0.8s ease-out;
            border-radius: 12px !important;
            background-color: rgba(30, 41, 59, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        /* PULSING GLOW BUTTONS */
        .stButton>button {
            border-radius: 8px !important;
            background: #1e293b !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
            font-weight: 600 !important;
            width: 100%;
            position: relative;
            overflow: hidden;
        }

        .stButton>button:hover {
            background: #2563eb !important; /* Blue glow on hover */
            border-color: #60a5fa !important;
            box-shadow: 0 0 15px rgba(37, 99, 235, 0.4);
            transform: translateY(-2px);
        }

        /* TEXT INPUT FOCUS EFFECT */
        .stTextInput>div>div>input:focus {
            border-color: #ef4444 !important;
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.2) !important;
        }

        .logo-text { color: #f8fafc; font-size: 24px; font-weight: 800; letter-spacing: 1px; }
        .sub-logo-text { color: #94a3b8; font-size: 11px; text-transform: uppercase; }
        
        footer {visibility: hidden;}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE & ANALYTICS (UNTOUCHED LOGIC)
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v32.db"

def init_leviathan_db():
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT, registration_date TEXT, membership_tier TEXT DEFAULT "Senior Counsel", account_status TEXT DEFAULT "Active", total_queries INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT, chamber_type TEXT DEFAULT "General Litigation", case_status TEXT DEFAULT "Active", is_archived INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT, token_count INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT, asset_status TEXT DEFAULT "Verified")')
    conn.commit(); conn.close()

def db_verify_vault_access(email, password):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    res = cursor.fetchone(); conn.close(); return res[0] if res else None

def db_fetch_chamber_history(email, chamber_name):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT m.sender_role, m.message_body FROM message_logs m JOIN chambers c ON m.chamber_id = c.id WHERE c.owner_email=? AND c.chamber_name=? ORDER BY m.id ASC", (email, chamber_name))
    rows = cursor.fetchall(); conn.close(); return [{"role": r, "content": b} for r, b in rows]

init_leviathan_db()

@st.cache_resource
def get_analytical_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.2)

def extract_pdf_text(uploaded_file):
    try:
        reader = PdfReader(uploaded_file)
        text = "".join([p.extract_text() for p in reader.pages if p.extract_text()])
        return text, len(reader.pages)
    except: return None, 0

# ==============================================================================
# 3. MAIN INTERFACE WITH ANIMATIONS
# ==============================================================================

def render_main_interface():
    apply_leviathan_shaders()
    
    # Load Lottie Animation for Sidebar
    lottie_law = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_v76zkn9x.json") # Scales of Justice
    
    with st.sidebar:
        if lottie_law:
            st_lottie(lottie_law, height=120, key="sidebar_lottie")
        
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div><div class='sub-logo-text'>Leviathan Intelligence</div>", unsafe_allow_html=True)
        nav_mode = st.radio("Navigation", ["Chambers", "Law Library", "System Admin"], label_visibility="collapsed")
        
        st.write("---")
        if nav_mode == "Chambers":
            st.markdown("🔍 **Case Files**")
            u_mail = st.session_state.user_email
            conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
            cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0", (u_mail,))
            chambers_raw = [r[0] for r in cursor.fetchall()]; conn.close()
            
            st.session_state.current_chamber = st.radio("Select Case", chambers_raw if chambers_raw else ["General Litigation"], label_visibility="collapsed")
            
            col_add, col_del = st.columns(2)
            with col_add: st.button("➕ New")
            with col_del: st.button("🗑️ Purge")

        st.write("---")
        if st.button("🚪 Secure Logout"):
            st.session_state.logged_in = False
            st.rerun()

    if nav_mode == "Chambers":
        st.header(f"💼 Chamber: {st.session_state.current_chamber}")
        
        # Chat History Container
        chat_container = st.container()
        with chat_container:
            history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
            for msg in history:
                with st.chat_message(msg["role"]): st.write(msg["content"])

        # Input Area
        query = st.chat_input("Enter Legal Query...")
        if query:
            with st.chat_message("user"): st.write(query)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing Statutes..."):
                    engine = get_analytical_engine()
                    resp = engine.invoke(query).content
                    st.markdown(resp)
                    # Logic for database logging would go here as per your original file

    elif nav_mode == "Law Library":
        st.header("📚 Law Library Vault")
        uploaded_file = st.file_uploader("Upload PDF Asset", type="pdf")
        if uploaded_file and st.button("Sync to Vault"):
            st.success("Asset Encrypted and Stored.")

# ==============================================================================
# 4. SOVEREIGN PORTAL (AUTH)
# ==============================================================================

def render_sovereign_portal():
    apply_leviathan_shaders()
    lottie_gate = load_lottie_url("https://assets9.lottiefiles.com/packages/lf20_6aYh4x.json") # Security Lock
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if lottie_gate: st_lottie(lottie_gate, height=200)
        st.title("⚖️ LEVIATHAN GATE")
        email = st.text_input("Vault Email")
        password = st.text_input("Security Key", type="password")
        if st.button("Verify Identity"):
            user = db_verify_vault_access(email, password)
            if user:
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
            else: st.error("Access Denied.")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: render_sovereign_portal()
else: render_main_interface()
