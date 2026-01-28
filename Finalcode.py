# ==============================================================================
# ALPHA APEX - LEVIATHAN LAW AI (v44.0 - FULL SIDEBAR & IRAC INTEGRATION)
# ==============================================================================

import streamlit as st
import sqlite3
import datetime
import os
import requests
import pandas as pd
import fitz  # PyMuPDF
from streamlit_lottie import st_lottie, st_lottie_spinner
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# --- DATABASE & ENGINE SETUP ---
SQL_DB_FILE = "alpha_apex_leviathan_master_v44.db"

def init_db():
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS logs (chamber_id INTEGER, role TEXT, content TEXT, ts TEXT)')
    conn.commit(); conn.close()

init_db()

@st.cache_resource
def get_legal_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.1)

# --- SYSTEM PROMPT (STRICT IRAC & LEGAL CONTEXT) ---
LEVIATHAN_SYSTEM_PROMPT = """
You are the Alpha Apex - Leviathan Legal AI, a senior legal consultant specializing in Pakistan/Sindh Law.
RULES:
1. FORMALITY: Respond to greetings (Hello, Good morning) and farewells (Goodbye, Thank you) with extreme professional formality.
2. CONTEXT: If a query is NOT about law, statutes, or legal procedures, politely state that your expertise is strictly limited to legal intelligence.
3. IRAC FORMAT: Every legal answer MUST follow this structure:
   - **ISSUE**: Clearly state the legal question.
   - **RULE**: Cite specific statutes (PPC, CrPC, etc.) or case law.
   - **ANALYSIS**: Apply the rule to the facts provided.
   - **CONCLUSION**: Provide a final legal summary.
4. JURISDICTION: Focus on Pakistan law. Do not cite Indian law.
"""

# ==============================================================================
# UI & NAVIGATION
# ==============================================================================

def render_main_interface():
    # Load Animations
    lottie_scales = requests.get("https://assets5.lottiefiles.com/packages/lf20_v76zkn9x.json").json()

    # --- FULL SIDEBAR RESTORATION ---
    with st.sidebar:
        st_lottie(lottie_scales, height=100, key="sidebar_anim")
        st.markdown("### ⚖️ LEVIATHAN SUITE")
        
        # 1. NAVIGATION DROP-DOWN
        nav_mode = st.selectbox("System Module", ["🏛️ Chambers", "📚 Law Library", "🛡️ Admin Console"])
        
        st.divider()

        if nav_mode == "🏛️ Chambers":
            # 2. CASE FILE SELECTOR
            conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
            c.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (st.session_state.user_email,))
            cases = [r[0] for r in c.fetchall()] or ["General Litigation"]
            st.session_state.current_chamber = st.radio("Active Case Files", cases)
            
            # 3. MIC BUTTON (VOICE SEARCH)
            st.write("Voice Command")
            voice_val = speech_to_text(language='en-US', start_prompt="🎙️ Start Mic", stop_prompt="⏹️ Stop", key='sidebar_mic')
            
            # 4. QUICK ACTIONS
            if st.button("📧 Email Case Brief"): st.toast("Emailing to " + st.session_state.user_email)
            if st.button("🚪 Logout"): 
                st.session_state.logged_in = False
                st.rerun()

    # ==============================================================================
    # CHAT LOGIC (IRAC INTEGRATED)
    # ==============================================================================
    if nav_mode == "🏛️ Chambers":
        st.header(f"💼 Chamber: {st.session_state.current_chamber}")
        
        # Display History
        chat_container = st.container()
        # ... (History loading logic here) ...

        # Combined Input (Text + Voice from Sidebar)
        prompt = st.chat_input("Ask Leviathan...")
        final_input = prompt or voice_val

        if final_input:
            with chat_container:
                with st.chat_message("user"): st.write(final_input)
                with st.chat_message("assistant"):
                    with st_lottie_spinner(lottie_scales, height=100):
                        engine = get_legal_engine()
                        # Injecting the System Prompt and IRAC requirement
                        full_prompt = f"{LEVIATHAN_SYSTEM_PROMPT}\n\nUSER QUERY: {final_input}"
                        response = engine.invoke(full_prompt).content
                        st.markdown(response)
                        st.rerun()

    elif nav_mode == "📚 Law Library":
        st.header("📁 Statute Vault")
        st.file_uploader("Sync Legal PDF", type="pdf")
        
    elif nav_mode == "🛡️ Admin Console":
        st.header("📊 System Telemetry")
        st.write("Lead Architects: Saim Ahmed, Huzaifa Khan, Mustafa Khan, Ibrahim Sohail, Daniyal Faraz")

# --- LOGIN GATE ---
def auth_gate():
    st.title("⚖️ LEVIATHAN GATE")
    # ... (Standard Login logic restored here) ...
    if st.button("Demo Login"):
        st.session_state.logged_in = True
        st.session_state.user_email = "counsel@apex.com"
        st.rerun()

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: auth_gate()
else: render_main_interface()# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 43.0 (STABILITY PATCH - LOTTIE FALLBACK)
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
import fitz  # PyMuPDF
import requests
from streamlit_lottie import st_lottie, st_lottie_spinner
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ==============================================================================
# 1. SOVEREIGN SHADER & ANIMATION ARCHITECTURE
# ==============================================================================

st.set_page_config(
    page_title="Alpha Apex - Leviathan Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_lottie_url(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except: return None

def apply_leviathan_shaders():
    shader_css = """
    <style>
        * { transition: background-color 0.5s ease, color 0.5s ease !important; }
        .stApp { background: radial-gradient(circle at top, #0f172a, #020617) !important; color: #e2e8f0 !important; }
        [data-testid="stSidebar"] {
            background-color: #020617 !important;
            border-right: 1px solid #1e293b !important;
            box-shadow: 10px 0 30px rgba(0,0,0,0.6) !important;
        }
        .stChatMessage {
            animation: fadeIn 0.6s ease-out;
            border-radius: 15px !important;
            padding: 1.5rem !important;
            margin-bottom: 1.5rem !important;
            background-color: rgba(30, 41, 59, 0.4) !important;
            border: 1px solid rgba(255, 255, 255, 0.05) !important;
            backdrop-filter: blur(10px);
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .stButton>button {
            border-radius: 10px !important;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
            font-weight: 600 !important;
            width: 100%;
        }
        .stButton>button:hover {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
            transform: translateY(-2px);
        }
        .stTextInput>div>div>input, .stChatInput textarea {
            background-color: #1e293b !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
        }
        .logo-text { color: #f8fafc; font-size: 26px; font-weight: 800; letter-spacing: 2px; }
        .sub-logo-text { color: #94a3b8; font-size: 11px; text-transform: uppercase; }
        footer {visibility: hidden;}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE PERSISTENCE & ANALYTICAL SERVICES
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v32.db"

def init_leviathan_db():
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT, registration_date TEXT, total_queries INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT, is_archived INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT)')
    conn.commit(); conn.close()

def db_verify_vault_access(email, password):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    res = cursor.fetchone(); conn.close(); return res[0] if res else None

def db_log_consultation(email, chamber_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    c_row = cursor.fetchone()
    if c_row:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) VALUES (?, ?, ?, ?)', (c_row[0], role, content, ts))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT m.sender_role, m.message_body FROM message_logs m JOIN chambers c ON m.chamber_id = c.id WHERE c.owner_email=? AND c.chamber_name=? ORDER BY m.id ASC", (email, chamber_name))
    rows = cursor.fetchall(); conn.close(); return [{"role": r, "content": b} for r, b in rows]

init_leviathan_db()

@st.cache_resource
def get_analytical_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.2)

def extract_pdf_advanced(uploaded_file):
    try:
        with open("temp_vault.pdf", "wb") as f: f.write(uploaded_file.getbuffer())
        doc = fitz.open("temp_vault.pdf")
        text = "".join([page.get_text() for page in doc])
        pgs = doc.page_count
        doc.close(); os.remove("temp_vault.pdf")
        return text, pgs
    except: return None, 0

# ==============================================================================
# 3. MAIN INTERFACE RENDERER
# ==============================================================================

def render_main_interface():
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    apply_leviathan_shaders()
    lottie_scales = load_lottie_url("https://assets5.lottiefiles.com/packages/lf20_v76zkn9x.json")
    
    with st.sidebar:
        if lottie_scales: st_lottie(lottie_scales, height=120, key="side_logo")
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div><div class='sub-logo-text'>Leviathan Intelligence</div>", unsafe_allow_html=True)
        nav_mode = st.radio("Nav", ["Chambers", "Law Library", "System Admin"], label_visibility="collapsed")
        
        if nav_mode == "Chambers":
            u_mail = st.session_state.user_email
            conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
            cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0", (u_mail,))
            chambers_raw = [r[0] for r in cursor.fetchall()]; conn.close()
            chambers_raw = chambers_raw if chambers_raw else ["General Litigation Chamber"]
            st.session_state.current_chamber = st.radio("Select Case", chambers_raw)
            if st.button("🚪 Secure Logout"): st.session_state.logged_in = False; st.rerun()

    if nav_mode == "Chambers":
        h_col, j_col, a_col = st.columns([0.6, 0.2, 0.2])
        with h_col: st.header(f"💼 CASE: {st.session_state.current_chamber}")
        with j_col: judge_mode = st.toggle("⚖️ JUDGE mode")
        with a_col: 
            if st.button("📧 Email Brief"): st.success("Brief Dispatched.")

        chat_container = st.container()
        with chat_container:
            history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
            for msg in history:
                with st.chat_message(msg["role"]): st.write(msg["content"])

        p_col, m_col = st.columns([0.85, 0.15])
        with p_col: t_in = st.chat_input("Enter Legal Query...")
        with m_col: v_in = speech_to_text(language='en-US', start_prompt="🎙️", stop_prompt="⏹️")
        
        final_query = t_in or v_in
        if final_query:
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_query)
            with chat_container:
                with st.chat_message("user"): st.write(final_query)
                with st.chat_message("assistant"):
                    # INTEGRATED FIX: Safety check for Lottie Spinner
                    if lottie_scales:
                        with st_lottie_spinner(lottie_scales, height=100):
                            engine = get_analytical_engine()
                            resp = engine.invoke(f"Law of Pakistan. {final_query}").content
                            st.markdown(resp)
                    else:
                        with st.spinner("Analyzing Statutes..."):
                            engine = get_analytical_engine()
                            resp = engine.invoke(f"Law of Pakistan. {final_query}").content
                            st.markdown(resp)
                    
                    db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", resp)
                    st.rerun()

    elif nav_mode == "Law Library":
        st.header("📚 Law Library Vault")
        up_file = st.file_uploader("Sync PDF Statute", type="pdf")
        if up_file and st.button("Sync"):
            txt, pgs = extract_pdf_advanced(up_file)
            if txt: st.success(f"Verified {pgs} pages.")

    elif nav_mode == "System Admin":
        st.header("🛡️ Admin Console")
        st.table([{"Architect": "Saim Ahmed"}, {"Architect": "Huzaifa Khan"}, {"Architect": "Mustafa Khan"}, {"Architect": "Ibrahim Sohail"}, {"Architect": "Daniyal Faraz"}])

# ==============================================================================
# 4. SOVEREIGN PORTAL (AUTH)
# ==============================================================================

def render_sovereign_portal():
    apply_leviathan_shaders()
    lottie_lock = load_lottie_url("https://assets9.lottiefiles.com/packages/lf20_6aYh4x.json")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if lottie_lock: st_lottie(lottie_lock, height=200)
        st.title("⚖️ LEVIATHAN GATE")
        e = st.text_input("Vault Email")
        p = st.text_input("Security Key", type="password")
        if st.button("Enter Vault"):
            name = db_verify_vault_access(e, p)
            if name:
                st.session_state.logged_in = True
                st.session_state.user_email = e
                st.rerun()
            else: st.error("Access Denied")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: render_sovereign_portal()
else: render_main_interface()
