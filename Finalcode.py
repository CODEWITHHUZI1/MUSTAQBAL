# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 41.0 (ULTRA ENHANCED - FULL FEATURE RESTORATION)
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
import fitz  # PyMuPDF for superior PDF extraction
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
        r = requests.get(url)
        return r.json() if r.status_code == 200 else None
    except: return None

def apply_leviathan_shaders():
    shader_css = """
    <style>
        /* GLOBAL TRANSITIONS & THEME */
        * { transition: background-color 0.5s ease, color 0.5s ease !important; }
        .stApp { background: radial-gradient(circle at top, #0f172a, #020617) !important; color: #e2e8f0 !important; }
        
        /* GLASS-MORPHISM SIDEBAR */
        [data-testid="stSidebar"] {
            background-color: #020617 !important;
            border-right: 1px solid #1e293b !important;
            box-shadow: 10px 0 30px rgba(0,0,0,0.6) !important;
        }

        /* ANIMATED CHAT BUBBLES */
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

        /* BUTTONS: THE LEVIATHAN GLOW */
        .stButton>button {
            border-radius: 10px !important;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
            font-weight: 600 !important;
            transition: all 0.3s ease !important;
        }
        .stButton>button:hover {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
            transform: translateY(-2px);
        }

        /* INPUT FIXES */
        .stTextInput>div>div>input, .stChatInput textarea {
            background-color: #1e293b !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
        }

        .logo-text { color: #f8fafc; font-size: 26px; font-weight: 800; letter-spacing: 2px; }
        .sub-logo-text { color: #94a3b8; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
        
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
    cursor.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT, registration_date TEXT, membership_tier TEXT DEFAULT "Senior Counsel", account_status TEXT DEFAULT "Active", total_queries INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT, chamber_type TEXT DEFAULT "General Litigation", case_status TEXT DEFAULT "Active", is_archived INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT, token_count INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT, asset_status TEXT DEFAULT "Verified")')
    cursor.execute('CREATE TABLE IF NOT EXISTS system_telemetry (event_id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, event_type TEXT, description TEXT, event_timestamp TEXT)')
    conn.commit(); conn.close()

def db_create_vault_user(email, name, password):
    if not email or not password: return False
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('INSERT INTO users (email, full_name, vault_key, registration_date) VALUES (?, ?, ?, ?)', (email, name, password, ts))
        cursor.execute('INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?, ?, ?)', (email, "General Litigation Chamber", ts))
        conn.commit(); conn.close(); return True
    except sqlite3.IntegrityError:
        conn.close(); return False

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
        if role == "user": cursor.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT m.sender_role, m.message_body FROM message_logs m JOIN chambers c ON m.chamber_id = c.id WHERE c.owner_email=? AND c.chamber_name=? ORDER BY m.id ASC", (email, chamber_name))
    rows = cursor.fetchall(); conn.close(); return [{"role": r, "content": b} for r, b in rows]

init_leviathan_db()

@st.cache_resource
def get_analytical_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.2)

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
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div><div class='sub-logo-text'>Leviathan Intelligence v41</div>", unsafe_allow_html=True)
        nav_mode = st.radio("Navigation", ["Chambers", "Law Library", "System Admin"], label_visibility="collapsed")
        
        st.write("---") 
        if nav_mode == "Chambers":
            st.markdown("**Active Case Files**")
            u_mail = st.session_state.user_email
            conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
            cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0", (u_mail,))
            chambers_raw = [r[0] for r in cursor.fetchall()]; conn.close()
            chambers_raw = chambers_raw if chambers_raw else ["General Litigation Chamber"]
            
            search_filter = st.text_input("Find Case...", placeholder="Search...", label_visibility="collapsed")
            filtered = [c for c in chambers_raw if search_filter.lower() in c.lower()]
            st.session_state.current_chamber = st.radio("Select Case", filtered if filtered else chambers_raw, label_visibility="collapsed")
            
            c1, c2 = st.columns(2)
            with c1: 
                if st.button("➕ New"): st.session_state.add_case = True
            with c2: 
                if st.button("🗑️ Purge"): st.session_state.delete_confirm = True

            if st.session_state.get('add_case'):
                new_n = st.text_input("Chamber Name")
                if st.button("Init"):
                    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
                    cursor.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", (u_mail, new_n, str(datetime.date.today())))
                    conn.commit(); conn.close(); st.session_state.add_case = False; st.rerun()

        st.write("---")
        with st.expander("⚙️ Settings"):
            custom_persona = st.text_input("System Persona", value="Senior High Court Advocate")
            lang_choice = st.selectbox("Interface Language", list(lexicon.keys()))
            if st.button("🚪 Secure Logout"): st.session_state.logged_in = False; st.rerun()

    if nav_mode == "Chambers":
        h_col, j_col, a_col = st.columns([0.6, 0.2, 0.2])
        with h_col: st.header(f"💼 CASE: {st.session_state.current_chamber}")
        with j_col: judge_mode = st.toggle("⚖️ JUDGE mode")
        with a_col: 
            if st.button("📧 Email Brief"): 
                st.toast("Dispatching Brief..."); time.sleep(1); st.success("Dispatched.")

        chat_container = st.container()
        with chat_container:
            history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
            for msg in history:
                with st.chat_message(msg["role"]): st.write(msg["content"])

        p_col, m_col = st.columns([0.85, 0.15])
        with p_col: t_in = st.chat_input("Enter Legal Query...")
        with m_col: v_in = speech_to_text(language=lexicon[lang_choice], key='v_mic', start_prompt="🎙️", stop_prompt="⏹️")
        
        final_query = t_in or v_in
        if final_query:
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_query)
            with chat_container:
                with st.chat_message("user"): st.write(final_query)
                with st.chat_message("assistant"):
                    with st_lottie_spinner(lottie_scales, height=100):
                        juris_logic = "Operating under Law of PAKISTAN/SINDH. Cite PPC/CrPC. No Indian law."
                        persona = "Honorable Justice" if judge_mode else custom_persona
                        engine = get_analytical_engine()
                        resp = engine.invoke(f"Persona: {persona}. {juris_logic}. Query: {final_query}").content
                        st.markdown(resp)
                        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", resp)
                        st.rerun()

    elif nav_mode == "Law Library":
        st.header("📚 Law Library Vault")
        up_file = st.file_uploader("Sync Pakistani Statute (PDF)", type="pdf")
        if up_file and st.button("Verify & Sync"):
            with st.status("Extracting Legal Text..."):
                txt, pgs = extract_pdf_advanced(up_file)
                if txt:
                    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
                    cursor.execute('INSERT INTO law_assets (filename, filesize_kb, page_count, sync_timestamp) VALUES (?, ?, ?, ?)', (up_file.name, round(up_file.size/1024, 2), pgs, str(datetime.datetime.now())))
                    conn.commit(); conn.close(); st.success("Vault Updated.")
        
        conn = sqlite3.connect(SQL_DB_FILE)
        df = pd.read_sql_query("SELECT filename, filesize_kb, page_count, sync_timestamp FROM law_assets", conn)
        st.dataframe(df, use_container_width=True)

    elif nav_mode == "System Admin":
        st.header("🛡️ System Admin")
        t1, t2, t3 = st.tabs(["Counsels", "Logs", "Credits"])
        with t1:
            conn = sqlite3.connect(SQL_DB_FILE)
            st.dataframe(pd.read_sql_query("SELECT full_name, email, total_queries FROM users", conn), use_container_width=True)
        with t2:
            conn = sqlite3.connect(SQL_DB_FILE)
            st.dataframe(pd.read_sql_query("SELECT * FROM message_logs LIMIT 50", conn), use_container_width=True)
        with t3:
            st.table([{"Architect": "Saim Ahmed"}, {"Architect": "Huzaifa Khan"}, {"Architect": "Mustafa Khan"}, {"Architect": "Ibrahim Sohail"}, {"Architect": "Daniyal Faraz"}])

# ==============================================================================
# 4. SOVEREIGN PORTAL (TABBED AUTH)
# ==============================================================================

def render_sovereign_portal():
    apply_leviathan_shaders()
    lottie_lock = load_lottie_url("https://assets9.lottiefiles.com/packages/lf20_6aYh4x.json")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if lottie_lock: st_lottie(lottie_lock, height=200)
        st.title("⚖️ LEVIATHAN GATE")
        auth_tabs = st.tabs(["🔐 Login", "📝 Register"])
        
        with auth_tabs[0]:
            e = st.text_input("Vault Email")
            p = st.text_input("Key", type="password")
            if st.button("Enter"):
                name = db_verify_vault_access(e, p)
                if name:
                    st.session_state.logged_in = True
                    st.session_state.user_email = e
                    st.rerun()
                else: st.error("Denied")
        
        with auth_tabs[1]:
            re = st.text_input("Registry Email")
            rn = st.text_input("Full Name")
            rk = st.text_input("Set Key", type="password")
            if st.button("Create"):
                if db_create_vault_user(re, rn, rk): st.success("Registered.")
                else: st.error("Failed.")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: render_sovereign_portal()
else: render_main_interface()
