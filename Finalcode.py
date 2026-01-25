# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 31.0 (PERSISTENCE RECOVERY - MAXIMUM PROCEDURAL DENSITY)
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
    """
    Injects a permanent Dark Mode CSS architecture.
    Updated with high-visibility sidebar toggle persistence.
    """
    shader_css = """
    <style>
        /* Global Reset and Stability Layer */
        * { transition: background-color 0.8s ease, color 0.8s ease !important; }
        
        /* Permanent Dark App Canvas */
        .stApp { 
            background-color: #020617 !important; 
            color: #f1f5f9 !important; 
        }

        /* Sidebar Glassmorphism Architecture */
        [data-testid="stSidebar"] {
            background-color: rgba(15, 23, 42, 0.98) !important;
            border-right: 2px solid #38bdf8 !important;
            box-shadow: 10px 0 20px rgba(0,0,0,0.5) !important;
        }

        /* Sidebar Reopen Button Persistence (High Visibility) */
        button[kind="headerNoPadding"] {
            background-color: #38bdf8 !important;
            color: #020617 !important;
            border-radius: 50% !important;
            padding: 5px !important;
            box-shadow: 0 0 15px #38bdf8 !important;
            left: 10px !important;
            top: 10px !important;
        }

        /* High-Fidelity Chat Geometry */
        .stChatMessage {
            border-radius: 20px !important;
            padding: 2.5rem !important;
            margin-bottom: 2rem !important;
            border: 1px solid rgba(56, 189, 248, 0.2) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
            background-color: rgba(30, 41, 59, 0.4) !important;
        }

        /* Headlines and Typography */
        h1, h2, h3, h4 { 
            color: #38bdf8 !important; 
            font-weight: 900 !important; 
            text-transform: uppercase;
            letter-spacing: 2px;
        }

        /* Precision Button Styling */
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
            transition: all 0.4s ease !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-3px) !important;
            box-shadow: 0 10px 20px rgba(56, 189, 248, 0.3) !important;
            background-color: #38bdf8 !important;
            color: #0f172a !important;
        }

        /* Input Field Refinement */
        .stTextInput>div>div>input {
            background-color: rgba(255,255,255,0.05) !important;
            color: #ffffff !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 10px !important;
        }

        /* Scrollbar Aesthetics */
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #38bdf8; }

        /* Hide Default Streamlit Elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. RELATIONAL DATABASE PERSISTENCE ENGINE (EXPANDED SCHEMA)
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v31.db"
DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def init_leviathan_db():
    """Builds the comprehensive SQL schema with explicit transactional tables."""
    connection = sqlite3.connect(SQL_DB_FILE)
    cursor = connection.cursor()
    
    # Table 1: Master User Registry
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            email TEXT PRIMARY KEY, 
            full_name TEXT, 
            vault_key TEXT, 
            registration_date TEXT,
            membership_tier TEXT DEFAULT 'Senior Counsel',
            account_status TEXT DEFAULT 'Active',
            total_queries INTEGER DEFAULT 0
        )
    ''')
    
    # Table 2: Case Chamber Virtual Registry
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chambers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            owner_email TEXT, 
            chamber_name TEXT, 
            init_date TEXT,
            chamber_type TEXT DEFAULT 'General Litigation',
            case_status TEXT DEFAULT 'Active',
            is_archived INTEGER DEFAULT 0
        )
    ''')
    
    # Table 3: Transactional Consultation History
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            chamber_id INTEGER, 
            sender_role TEXT, 
            message_body TEXT, 
            ts_created TEXT,
            token_count INTEGER DEFAULT 0
        )
    ''')
    
    # Table 4: Digital Jurisprudence Metadata Vault
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS law_assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            filename TEXT, 
            filesize_kb REAL, 
            page_count INTEGER, 
            sync_timestamp TEXT,
            asset_status TEXT DEFAULT 'Verified'
        )
    ''')
    
    # Table 5: System Telemetry Log
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_telemetry (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT,
            event_type TEXT,
            description TEXT,
            event_timestamp TEXT
        )
    ''')
    
    connection.commit()
    connection.close()

def db_log_event(email, event_type, desc):
    """Explicitly logs system events for admin telemetry."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp)
        VALUES (?, ?, ?, ?)
    ''', (email, event_type, desc, ts))
    conn.commit()
    conn.close()

def db_create_vault_user(email, name, password):
    """Registers users into the local SQL vault."""
    if email == "" or password == "":
        return False
    
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        cursor.execute('''
            INSERT INTO users (email, full_name, vault_key, registration_date) 
            VALUES (?, ?, ?, ?)
        ''', (email, name, password, ts))
        
        cursor.execute('''
            INSERT INTO chambers (owner_email, chamber_name, init_date) 
            VALUES (?, ?, ?)
        ''', (email, "General Litigation Chamber", ts))
        
        conn.commit()
        conn.close()
        db_log_event(email, "REGISTRATION", "Account initialized")
        return True
    except sqlite3.IntegrityError:
        conn.close()
        return False

def db_verify_vault_access(email, password):
    """Credential verification logic."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    res = cursor.fetchone()
    conn.close()
    if res:
        db_log_event(email, "LOGIN", "Successful entry")
        return res[0]
    return None

def db_log_consultation(email, chamber_name, role, content):
    """Saves message with explicit ID lookup to avoid loss."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    c_row = cursor.fetchone()
    if c_row:
        c_id = c_row[0]
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) 
            VALUES (?, ?, ?, ?)
        ''', (c_id, role, content, ts))
        if role == "user":
            cursor.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    """Retrieves context-specific logs."""
    conn = sqlite3.connect(SQL_DB_FILE)
    cursor = conn.cursor()
    sql = '''
        SELECT m.sender_role, m.message_body FROM message_logs m 
        JOIN chambers c ON m.chamber_id = c.id 
        WHERE c.owner_email=? AND c.chamber_name=? 
        ORDER BY m.id ASC
    '''
    cursor.execute(sql, (email, chamber_name))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": r, "content": b} for r, b in rows]

init_leviathan_db()

# ==============================================================================
# 3. CORE ANALYTICAL SERVICES (AI ENGINE & SMTP GATEWAY)
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    """Initializes Gemini with strictly tuned legal parameters."""
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=st.secrets["GOOGLE_API_KEY"], 
        temperature=0.15,
        max_output_tokens=4000
    )

def dispatch_legal_brief_smtp(target_email, chamber_name, history_data):
    """Enterprise SMTP Gateway for automated brief delivery."""
    try:
        s_user = st.secrets["EMAIL_USER"]
        s_pass = st.secrets["EMAIL_PASS"].replace(" ", "")
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Chambers <{s_user}>"
        msg['To'] = target_email
        msg['Subject'] = f"Legal Brief: {chamber_name}"
        
        brief = f"CHAMBER: {chamber_name}\nDATE: {datetime.datetime.now()}\n\n"
        for h in history_data:
            brief += f"[{h['role'].upper()}]: {h['content']}\n\n"
        
        msg.attach(MIMEText(brief, 'plain', 'utf-8'))
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls(); server.login(s_user, s_pass)
        server.send_message(msg); server.quit()
        return True
    except Exception as e:
        st.error(f"Email Error: {e}"); return False

def synchronize_law_library():
    """Indexes PDF assets in the vault."""
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT filename FROM law_assets")
    indexed = [r[0] for r in cursor.fetchall()]
    if os.path.exists(DATA_FOLDER):
        for f in os.listdir(DATA_FOLDER):
            if f.lower().endswith(".pdf") and f not in indexed:
                try:
                    pdf = PdfReader(os.path.join(DATA_FOLDER, f))
                    cursor.execute("INSERT INTO law_assets (filename, filesize_kb, page_count, sync_timestamp) VALUES (?,?,?,?)", 
                                   (f, os.path.getsize(os.path.join(DATA_FOLDER, f))/1024, len(pdf.pages), datetime.datetime.now().strftime("%Y-%m-%d")))
                except: continue
    conn.commit(); conn.close()

# ==============================================================================
# 4. UI: SOVEREIGN CHAMBERS (FIXED PERSISTENCE LOGIC)
# ==============================================================================

def render_chamber_workstation():
    """The workstation UI with explicit message preservation."""
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    apply_leviathan_shaders()
    
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; margin-top: -30px;'>⚖️</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>ALPHA APEX</h3>", unsafe_allow_html=True)
        st.divider()
        lang_choice = st.selectbox("Language", list(lexicon.keys()))
        l_code = lexicon[lang_choice]
        st.divider()
        search_filter = st.text_input("🔍 Search Chambers").lower()
        
        u_mail = st.session_state.user_email
        conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
        cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0", (u_mail,))
        chambers = [r[0] for r in cursor.fetchall()]; conn.close()
        
        filtered = [c for c in chambers if search_filter in c.lower()]
        st.session_state.current_chamber = st.selectbox("Active Chamber", filtered if filtered else chambers)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("➕ New Case"): st.session_state.add_case = True
        with c2:
            if st.button("📧 Brief"):
                if dispatch_legal_brief_smtp(u_mail, st.session_state.current_chamber, db_fetch_chamber_history(u_mail, st.session_state.current_chamber)):
                    st.sidebar.success("Sent")
        
        if st.session_state.get('add_case'):
            new_name = st.text_input("Name")
            if st.button("Create") and new_name:
                conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
                cursor.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", 
                               (u_mail, new_name, str(datetime.date.today())))
                conn.commit(); conn.close()
                st.session_state.add_case = False; st.rerun()

        st.divider()
        if st.button("🚪 Logout"):
            st.session_state.logged_in = False; st.rerun()

    # --- CHAT INTERFACE ---
    st.header(f"💼 CASE: {st.session_state.current_chamber}")
    st.write("---")
    
    chat_container = st.container()
    with chat_container:
        history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
        for msg in history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])

    st.write("") 
    
    chat_col, mic_col = st.columns([0.85, 0.15])
    with chat_col:
        t_input = st.chat_input("Enter Query...")
    with mic_col:
        v_input = speech_to_text(language=l_code, key='v_mic', just_once=True, use_container_width=True)

    final_query = t_input or v_input

    if final_query:
        if "last_processed" not in st.session_state or st.session_state.last_processed != final_query:
            st.session_state.last_processed = final_query
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_query)
            with chat_container:
                with st.chat_message("user"):
                    st.write(final_query)
            with st.chat_message("assistant"):
                with st.spinner("Processing Strategy..."):
                    try:
                        p = f"""
                        SYSTEM PERSONA: You are a Senior High Court Advocate. 
                        STRICT BOUNDARY: You ONLY answer questions related to Law, Jurisprudence, Statutes, and Legal Procedures.
                        OFF-TOPIC BEHAVIOR: If the user asks about anything outside of legal context, respond with: 
                        "As your Legal Intelligence Advocate, I am strictly authorized to consult on matters of law and jurisprudence. Please provide a legal query."
                        
                        Language: {lang_choice}. 
                        Query: {final_query}
                        """
                        response = get_analytical_engine().invoke(p).content
                        st.markdown(response)
                        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", response)
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI Error: {e}")

# ==============================================================================
# 5. UI: SOVEREIGN PORTAL (AUTHENTICATION)
# ==============================================================================

def render_sovereign_portal():
    """Secure gateway logic."""
    apply_leviathan_shaders()
    st.title("⚖️ ALPHA APEX LEVIATHAN PORTAL")
    st.markdown("#### Enterprise Legal Intelligence Infrastructure")
    
    t1, t2 = st.tabs(["🔐 Login", "📝 Register"])
    with t1:
        e = st.text_input("Vault Email")
        k = st.text_input("Key", type="password")
        if st.button("Enter Vault"):
            n = db_verify_vault_access(e, k)
            if n:
                st.session_state.logged_in = True
                st.session_state.user_email = e
                st.session_state.username = n
                st.rerun()
            else: st.error("Access Denied")
    with t2:
        re = st.text_input("Reg Email")
        rn = st.text_input("Full Name")
        rk = st.text_input("Set Key", type="password")
        if st.button("Initialize"):
            if db_create_vault_user(re, rn, rk): st.success("Created")
            else: st.error("Exists")

# ==============================================================================
# 6. MASTER EXECUTION ENGINE & ADMIN TELEMETRY
# ==============================================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_sovereign_portal()
else:
    view = st.sidebar.radio("Navigation", ["Chambers", "Law Library", "System Admin"])
    
    if view == "Chambers":
        render_chamber_workstation()
    elif view == "Law Library":
        apply_leviathan_shaders()
        st.header("📚 Law Library")
        if st.button("🔄 Sync Vault"): synchronize_law_library(); st.rerun()
        conn = sqlite3.connect(SQL_DB_FILE)
        df = pd.read_sql_query("SELECT filename, filesize_kb, page_count FROM law_assets", conn)
        conn.close()
        st.dataframe(df, use_container_width=True)
    elif view == "System Admin":
        apply_leviathan_shaders()
        st.header("🛡️ System Admin")
        conn = sqlite3.connect(SQL_DB_FILE)
        u_df = pd.read_sql_query("SELECT full_name, email, total_queries FROM users", conn)
        t_df = pd.read_sql_query("SELECT * FROM system_telemetry ORDER BY event_id DESC LIMIT 10", conn)
        conn.close()
        st.subheader("Users")
        st.dataframe(u_df, use_container_width=True)
        st.subheader("Event Log")
        st.table(t_df)
        st.divider()
        st.subheader("Architectural Board")
        architects = [
            {"Name": "Saim Ahmed", "Focus": "Prompt Engineering"},
            {"Name": "Huzaifa Khan", "Focus": "Backend Developer"},
            {"Name": "Mustafa Khan", "Focus": "Main Coder"},
            {"Name": "Ibrahim Sohail", "Focus": "Presentation Lead"},
            {"Name": "Daniyal Faraz", "Focus": "Debugger and Modifier"}
        ]
        st.table(architects)

# ==============================================================================
# SCRIPT END - TOTAL FUNCTIONAL LINE COUNT: 520+
# ==============================================================================
