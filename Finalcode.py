# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 30.0 (STRICT PROCEDURAL LOGIC - STABLE DATABASE BRIDGE)
# ARCHITECTS: SAIM AHMED, HUZAIFA KHAN, MUSTAFA KHAN, IBRAHIM SOHAIL, DANIYAL FARAZ
# ==============================================================================

try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    # Fallback for environments where pysqlite3 isn't required
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
    Explicitly defined UI components for enterprise-grade visuals.
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

        /* High-Fidelity Chat Geometry */
        .stChatMessage {
            border-radius: 20px !important;
            padding: 2.5rem !important;
            margin-bottom: 2rem !important;
            border: 1px solid rgba(56, 189, 248, 0.2) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1) !important;
            background-color: rgba(30, 41, 59, 0.3) !important;
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
# 2. RELATIONAL DATABASE PERSISTENCE ENGINE (STRICT PROCEDURAL)
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v30.db"
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
    db_connection = sqlite3.connect(SQL_DB_FILE)
    db_cursor = db_connection.cursor()
    event_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    insert_sql = '''
        INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp)
        VALUES (?, ?, ?, ?)
    '''
    db_cursor.execute(insert_sql, (email, event_type, desc, event_ts))
    db_connection.commit()
    db_connection.close()

def db_create_vault_user(email, name, password):
    """Registers users into the local SQL vault with explicit error handling."""
    if email == "" or password == "":
        return False
    
    conn_obj = sqlite3.connect(SQL_DB_FILE)
    cursor_obj = conn_obj.cursor()
    current_time_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    try:
        user_insert_query = '''
            INSERT INTO users (email, full_name, vault_key, registration_date) 
            VALUES (?, ?, ?, ?)
        '''
        cursor_obj.execute(user_insert_query, (email, name, password, current_time_str))
        
        chamber_insert_query = '''
            INSERT INTO chambers (owner_email, chamber_name, init_date) 
            VALUES (?, ?, ?)
        '''
        cursor_obj.execute(chamber_insert_query, (email, "Primary Case Chamber", current_time_str))
        
        conn_obj.commit()
        conn_obj.close()
        db_log_event(email, "REGISTRATION", "New user identity established")
        return True
    except sqlite3.IntegrityError:
        conn_obj.close()
        return False
    except Exception as e:
        conn_obj.close()
        return False

def db_verify_vault_access(email, password):
    """Local credential verification for Sovereign Vault access."""
    db_conn = sqlite3.connect(SQL_DB_FILE)
    db_curr = db_conn.cursor()
    
    auth_sql = "SELECT full_name FROM users WHERE email=? AND vault_key=?"
    db_curr.execute(auth_sql, (email, password))
    
    row_data = db_curr.fetchone()
    db_conn.close()
    
    if row_data is not None:
        db_log_event(email, "LOGIN", "Authorized access granted")
        return row_data[0]
    else:
        return None

def db_log_consultation(email, chamber_name, role, content):
    """Saves legal consultation transactions into the SQL persistence layer."""
    conn_log = sqlite3.connect(SQL_DB_FILE)
    curr_log = conn_log.cursor()
    
    find_chamber_sql = "SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?"
    curr_log.execute(find_chamber_sql, (email, chamber_name))
    id_row = curr_log.fetchone()
    
    if id_row:
        target_id = id_row[0]
        timestamp_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        word_count = len(content.split())
        
        log_insert_sql = '''
            INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created, token_count) 
            VALUES (?, ?, ?, ?, ?)
        '''
        curr_log.execute(log_insert_sql, (target_id, role, content, timestamp_now, word_count))
        
        if role == "user":
            update_user_sql = "UPDATE users SET total_queries = total_queries + 1 WHERE email = ?"
            curr_log.execute(update_user_sql, (email,))
        
        conn_log.commit()
    
    conn_log.close()

def db_fetch_chamber_history(email, chamber_name):
    """Retrieves context-specific logs for UI rendering."""
    conn_hist = sqlite3.connect(SQL_DB_FILE)
    curr_hist = conn_hist.cursor()
    
    fetch_sql = '''
        SELECT m.sender_role, m.message_body FROM message_logs m 
        JOIN chambers c ON m.chamber_id = c.id 
        WHERE c.owner_email=? AND c.chamber_name=? 
        ORDER BY m.id ASC
    '''
    
    curr_hist.execute(fetch_sql, (email, chamber_name))
    all_rows = curr_hist.fetchall()
    
    formatted_history = []
    for entry in all_rows:
        dict_obj = {"role": entry[0], "content": entry[1]}
        formatted_history.append(dict_obj)
        
    conn_hist.close()
    return formatted_history

init_leviathan_db()

# ==============================================================================
# 3. CORE ANALYTICAL SERVICES (AI ENGINE & SMTP GATEWAY)
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    """Initializes Gemini with strictly tuned legal parameters."""
    google_key = st.secrets["GOOGLE_API_KEY"]
    ai_model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", 
        google_api_key=google_key, 
        temperature=0.15,
        max_output_tokens=4000
    )
    return ai_model

def dispatch_legal_brief_smtp(target_email, chamber_name, history_data):
    """Enterprise SMTP Gateway for automated brief delivery."""
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"].replace(" ", "")
        
        time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        brief_body = f"ALPHA APEX OFFICIAL LEGAL BRIEF\n"
        brief_body += f"CHAMBER: {chamber_name}\n"
        brief_body += f"GENERATED: {time_stamp}\n"
        brief_body += "="*60 + "\n\n"
        
        for item in history_data:
            role_string = "ADVOCATE" if item['role'] == 'assistant' else "CLIENT"
            clean_text = re.sub(r'[*#_]', '', item['content'])
            brief_body += f"[{role_string}]: {clean_text}\n\n"
            
        multipart_msg = MIMEMultipart()
        multipart_msg['From'] = f"Alpha Apex Chambers <{sender_email}>"
        multipart_msg['To'] = target_email
        multipart_msg['Subject'] = f"Legal Consultation Summary: {chamber_name}"
        
        text_part = MIMEText(brief_body, 'plain', 'utf-8')
        multipart_msg.attach(text_part)
        
        smtp_conn = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_conn.starttls()
        smtp_conn.login(sender_email, sender_password)
        smtp_conn.send_message(multipart_msg)
        smtp_conn.quit()
        
        return True
    except Exception as error_msg:
        st.error(f"SMTP Gateway Failure: {error_msg}")
        return False

def synchronize_law_library():
    """Explicit file system scan for PDF jurisprudence indexing."""
    conn_sync = sqlite3.connect(SQL_DB_FILE)
    curr_sync = conn_sync.cursor()
    
    curr_sync.execute("SELECT filename FROM law_assets")
    records = curr_sync.fetchall()
    
    existing_files = []
    for r in records:
        existing_files.append(r[0])
    
    if os.path.exists(DATA_FOLDER):
        for file_name in os.listdir(DATA_FOLDER):
            if file_name.lower().endswith(".pdf"):
                if file_name not in existing_files:
                    full_path = os.path.join(DATA_FOLDER, file_name)
                    try:
                        pdf_obj = PdfReader(full_path)
                        f_kb = os.path.getsize(full_path) / 1024
                        f_pgs = len(pdf_obj.pages)
                        f_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        insert_asset_sql = '''
                            INSERT INTO law_assets (filename, filesize_kb, page_count, sync_timestamp) 
                            VALUES (?, ?, ?, ?)
                        '''
                        curr_sync.execute(insert_asset_sql, (file_name, f_kb, f_pgs, f_ts))
                    except Exception:
                        continue
                    
    conn_sync.commit()
    conn_sync.close()

# ==============================================================================
# 4. UI: SOVEREIGN CHAMBERS (VOICE RECORDING ENABLED)
# ==============================================================================

def render_chamber_workstation():
    """Main Workstation UI with non-condensed logic blocks."""
    language_dict = {
        "English": "en-US", 
        "Urdu": "ur-PK", 
        "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK"
    }
    
    apply_leviathan_shaders()
    
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; margin-top: -30px;'>⚖️</h1>", unsafe_allow_html=True)
        st.markdown("<h3 style='text-align: center;'>ALPHA APEX</h3>", unsafe_allow_html=True)
        st.caption("<p style='text-align: center;'>Leviathan Production Suite v30</p>", unsafe_allow_html=True)
        
        st.divider()
        st.subheader("🌐 Global Lexicon")
        lang_choice = st.selectbox("Select Language", list(language_dict.keys()))
        lang_code = language_dict[lang_choice]
        
        st.divider()
        st.subheader("📁 Case Navigator")
        search_val = st.text_input("🔍 Search Chambers", "").lower()
        
        active_email = st.session_state.user_email
        conn_sb = sqlite3.connect(SQL_DB_FILE)
        curr_sb = conn_sb.cursor()
        
        list_sql = "SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0"
        curr_sb.execute(list_sql, (active_email,))
        chamber_rows = curr_sb.fetchall()
        
        master_chamber_list = []
        for c_row in chamber_rows:
            master_chamber_list.append(c_row[0])
            
        conn_sb.close()
        
        results_list = []
        for name in master_chamber_list:
            if search_val in name.lower():
                results_list.append(name)
        
        if len(results_list) > 0:
            st.session_state.current_chamber = st.selectbox("Active Chamber", results_list)
        else:
            st.session_state.current_chamber = st.selectbox("Active Chamber", master_chamber_list)
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("➕ New Case"):
                st.session_state.new_case_trigger = True
        with c2:
            if st.button("📧 Brief"):
                mail_history = db_fetch_chamber_history(active_email, st.session_state.current_chamber)
                if dispatch_legal_brief_smtp(active_email, st.session_state.current_chamber, mail_history):
                    st.sidebar.success("Dispatched")
        
        if st.session_state.get('new_case_trigger'):
            case_input_field = st.text_input("Case Identifier")
            if st.button("Register") and case_input_field:
                conn_add = sqlite3.connect(SQL_DB_FILE)
                curr_add = conn_add.cursor()
                date_stamp = str(datetime.date.today())
                curr_add.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?, ?, ?)", 
                                 (active_email, case_input_field, date_stamp))
                conn_add.commit()
                conn_add.close()
                st.session_state.new_case_trigger = False
                st.rerun()

        st.divider()
        if st.button("🚪 Terminate"):
            st.session_state.logged_in = False
            st.session_state.user_email = None
            st.session_state.username = None
            st.rerun()

    # --- MAIN CONSULTATION AREA ---
    st.header(f"💼 CASE: {st.session_state.current_chamber}")
    st.write("---")
    
    current_logs = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
    for log_entry in current_logs:
        with st.chat_message(log_entry["role"]):
            st.write(log_entry["content"])

    st.write("") 
    
    col_chat, col_mic = st.columns([0.82, 0.18])
    with col_chat:
        user_text = st.chat_input("Enter Legal Query...")
    with col_mic:
        user_voice = speech_to_text(language=lang_code, key='apex_mic', just_once=True, use_container_width=True)

    final_query = None
    if user_text:
        final_query = user_text
    elif user_voice:
        final_query = user_voice

    if final_query:
        if "last_processed" not in st.session_state or st.session_state.last_processed != final_query:
            st.session_state.last_processed = final_query
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_query)
            
            with st.chat_message("user"):
                st.write(final_query)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing Case..."):
                    try:
                        prompt_config = f"""
                        PERSONA: High Court Advocate.
                        LOGIC: Greeting if simple, IRAC if complex legal problem.
                        CITATIONS: Refer to PPC/CrPC/Constitution.
                        LANG: {lang_choice}.
                        QUERY: {final_query}
                        """
                        ai_engine = get_analytical_engine()
                        ai_response_obj = ai_engine.invoke(prompt_config)
                        ai_text_result = ai_response_obj.content
                        
                        st.markdown(ai_text_result)
                        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", ai_text_result)
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI Failure: {e}")

# ==============================================================================
# 5. UI: SOVEREIGN PORTAL (AUTHENTICATION GATEWAY)
# ==============================================================================

def render_sovereign_portal():
    """Secure entry gateway for Alpha Apex."""
    apply_leviathan_shaders()
    st.title("⚖️ ALPHA APEX LEVIATHAN PORTAL")
    st.markdown("#### Enterprise Legal Intelligence Infrastructure")
    
    t_login, t_reg = st.tabs(["🔐 Login", "📝 Register"])
    
    with t_login:
        st.subheader("Credential Verification")
        u_email = st.text_input("Vault Email")
        u_key = st.text_input("Vault Key", type="password")
        if st.button("Enter"):
            u_name = db_verify_vault_access(u_email, u_key)
            if u_name:
                st.session_state.logged_in = True
                st.session_state.user_email = u_email
                st.session_state.username = u_name
                st.rerun()
            else:
                st.error("Denied.")
                
    with t_reg:
        st.subheader("New Identity")
        n_email = st.text_input("New Email")
        n_name = st.text_input("Full Name")
        n_key = st.text_input("Set Key", type="password")
        if st.button("Initialize"):
            if db_create_vault_user(n_email, n_name, n_key):
                st.success("Created.")
            else:
                st.error("Error.")

# ==============================================================================
# 6. MASTER EXECUTION ENGINE & ADMIN TELEMETRY
# ==============================================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if st.session_state.logged_in == False:
    render_sovereign_portal()
else:
    nav_pick = st.sidebar.radio("Sovereign Navigation Hub", ["Chambers", "Law Library", "System Admin"])
    
    if nav_pick == "Chambers":
        render_chamber_workstation()
    elif nav_pick == "Law Library":
        apply_leviathan_shaders()
        st.header("📚 Law Library")
        if st.button("🔄 Sync"):
            synchronize_law_library()
            st.rerun()
        
        conn_lib = sqlite3.connect(SQL_DB_FILE)
        df_lib = pd.read_sql_query("SELECT filename, filesize_kb, page_count, sync_timestamp FROM law_assets", conn_lib)
        conn_lib.close()
        st.dataframe(df_lib, use_container_width=True)
            
    elif nav_pick == "System Admin":
        apply_leviathan_shaders()
        st.header("🛡️ System Telemetry")
        conn_adm = sqlite3.connect(SQL_DB_FILE)
        df_u = pd.read_sql_query("SELECT full_name, email, registration_date, total_queries FROM users", conn_adm)
        df_t = pd.read_sql_query("SELECT user_email, event_type, description, event_timestamp FROM system_telemetry ORDER BY event_id DESC LIMIT 15", conn_adm)
        conn_adm.close()
        
        st.subheader("Counsel Registry")
        st.dataframe(df_u, use_container_width=True)
        st.divider()
        st.subheader("Event Log")
        st.table(df_t)
        
        st.divider()
        st.subheader("Architectural Board")
        arch_list = [
            {"Name": "Saim Ahmed", "Focus": "System Arch"},
            {"Name": "Huzaifa Khan", "Focus": "AI Model"},
            {"Name": "Mustafa Khan", "Focus": "Persistence"},
            {"Name": "Ibrahim Sohail", "Focus": "UI/UX"},
            {"Name": "Daniyal Faraz", "Focus": "QA"}
        ]
        st.table(arch_list)

# ==============================================================================
# SCRIPT END - TOTAL PRODUCTION LINE COUNT EXCEEDS 520
# ==============================================================================
