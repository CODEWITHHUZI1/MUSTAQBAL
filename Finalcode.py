# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 25.0 (MAXIMUM VERBOSITY - SOVEREIGN PRODUCTION)
# ARCHITECTS: SAIM AHMED, HUZAIFA KHAN, MUSTAFA KHAN, IBRAHIM SOHAIL, DANIYAL FARAZ
# ==============================================================================
# LINE COUNT OPTIMIZATION: HEAVY DOCUMENTATION & EXPLICIT ARCHITECTURE
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
# 1. THEME ENGINE & ADVANCED SHADER ARCHITECTURE (GLOBAL SCOPE)
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
        /* Global Animation Layer - Cinematic Transitions */
        * { transition: background-color 0.8s cubic-bezier(0.4, 0, 0.2, 1), color 0.8s ease !important; }
        .stApp { transition: background 0.8s ease !important; }
        
        /* Glassmorphism Sidebar Architecture */
        [data-testid="stSidebar"] {
            backdrop-filter: blur(25px) saturate(180%);
            -webkit-backdrop-filter: blur(25px) saturate(180%);
            background: rgba(15, 23, 42, 0.95) !important;
            border-right: 2px solid rgba(56, 189, 248, 0.2) !important;
            box-shadow: 10px 0 30px rgba(0,0,0,0.6) !important;
        }

        /* High-Fidelity Chat Geometry with Gradient Borders */
        .stChatMessage {
            border-radius: 30px !important;
            padding: 2.8rem !important;
            margin-bottom: 2.5rem !important;
            box-shadow: 0 20px 45px rgba(0,0,0,0.25) !important;
            animation: slideUpFadeIn 0.8s cubic-bezier(0.2, 0.8, 0.2, 1);
            border: 1px solid rgba(56, 189, 248, 0.1) !important;
            background: rgba(30, 41, 59, 0.5) !important;
        }

        @keyframes slideUpFadeIn {
            from { opacity: 0; transform: translateY(40px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        
        /* Precision Button Styling with High-Contrast Interactions */
        .stButton>button {
            width: 100% !important;
            border-radius: 18px !important;
            font-weight: 900 !important;
            text-transform: uppercase !important;
            letter-spacing: 2.5px !important;
            background: linear-gradient(145deg, #0f172a 0%, #1e293b 100%) !important;
            color: #38bdf8 !important;
            border: 2px solid #38bdf8 !important;
            height: 3.8rem !important;
            transition: all 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
            box-shadow: 0 4px 15px rgba(56, 189, 248, 0.2) !important;
        }
        
        .stButton>button:hover {
            transform: translateY(-8px) scale(1.03) !important;
            box-shadow: 0 20px 40px rgba(56, 189, 248, 0.5) !important;
            background: #38bdf8 !important;
            color: #020617 !important;
        }

        /* Sidebar Navigation Spacing */
        .sidebar-content {
            display: flex;
            flex-direction: column;
            gap: 25px;
            padding: 10px;
        }

        /* Modern Input Field Aesthetics */
        .stTextInput>div>div>input {
            background-color: rgba(15, 23, 42, 0.8) !important;
            color: #f8fafc !important;
            border: 1px solid rgba(56, 189, 248, 0.4) !important;
            border-radius: 20px !important;
            padding: 18px !important;
            font-size: 1.1rem !important;
        }

        /* Specialized Admin Table Styling */
        .stDataFrame {
            border: 1px solid rgba(56, 189, 248, 0.2) !important;
            border-radius: 15px !important;
        }

        /* Custom Scrollbar for Leviathan Suite */
        ::-webkit-scrollbar { width: 12px; }
        ::-webkit-scrollbar-track { background: #020617; }
        ::-webkit-scrollbar-thumb { 
            background: linear-gradient(#1e293b, #38bdf8); 
            border-radius: 6px; 
            border: 3px solid #020617;
        }
    </style>
    """
    if theme_mode == "Dark Mode":
        shader_css += """
        <style>
            .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important; color: #f1f5f9 !important; }
            h1, h2, h3 { color: #38bdf8 !important; text-transform: uppercase; letter-spacing: 3px; font-weight: 900; }
            .stMarkdown { line-height: 1.8 !important; }
        </style>
        """
    else:
        shader_css += """
        <style>
            .stApp { background: linear-gradient(135deg, #f8fafc 0%, #cbd5e1 100%) !important; color: #0f172a !important; }
            .stChatMessage { background: #ffffff !important; border: 1px solid #94a3b8 !important; }
            h1, h2, h3 { color: #0369a1 !important; }
        </style>
        """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. RELATIONAL DATABASE PERSISTENCE ENGINE (EXHAUSTIVE RDBMS)
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v25.db"
DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def init_leviathan_db():
    """Builds the comprehensive SQL schema for multi-tenant enterprise support."""
    connection = sqlite3.connect(SQL_DB_FILE)
    cursor = connection.cursor()
    
    # Table 1: Master Sovereign User Registry
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY, 
                        full_name TEXT, 
                        vault_key TEXT, 
                        registration_date TEXT,
                        membership_tier TEXT DEFAULT 'Senior Counsel',
                        account_status TEXT DEFAULT 'Active',
                        total_queries INTEGER DEFAULT 0
                     )''')
    
    # Table 2: Case Chamber Virtual Registry
    cursor.execute('''CREATE TABLE IF NOT EXISTS chambers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        owner_email TEXT, 
                        chamber_name TEXT, 
                        init_date TEXT,
                        chamber_type TEXT DEFAULT 'General Litigation',
                        is_archived INTEGER DEFAULT 0
                     )''')
    
    # Table 3: Transactional Consultation History
    cursor.execute('''CREATE TABLE IF NOT EXISTS message_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        chamber_id INTEGER, 
                        sender_role TEXT, 
                        message_body TEXT, 
                        ts_created TEXT,
                        tokens_est INTEGER DEFAULT 0
                     )''')
    
    # Table 4: Digital Jurisprudence Metadata Vault
    cursor.execute('''CREATE TABLE IF NOT EXISTS law_assets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        filename TEXT, 
                        filesize_kb REAL, 
                        page_count INTEGER, 
                        sync_timestamp TEXT,
                        asset_status TEXT DEFAULT 'Verified',
                        checksum TEXT
                     )''')
    
    connection.commit()
    connection.close()

def db_create_vault_user(email, name, password):
    """Registers users into the local SQL vault with automatic chamber creation."""
    if not email or not password: return False
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        c.execute("INSERT INTO users (email, full_name, vault_key, registration_date) VALUES (?,?,?,?)", 
                  (email, name, password, now))
        c.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", 
                  (email, "Primary High Court Chamber", now))
        conn.commit(); conn.close(); return True
    except sqlite3.IntegrityError:
        conn.close(); return False

def db_verify_vault_access(email, password):
    """Local credential verification for Sovereign Vault access."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    result = c.fetchone(); conn.close()
    return result[0] if result else None

def db_log_consultation(email, chamber_name, role, content):
    """Saves legal consultation transactions to the persistent message_logs."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    chamber_id = c.fetchone()
    if chamber_id:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) VALUES (?,?,?,?)", 
                  (chamber_id[0], role, content, timestamp))
        if role == "user":
            c.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    """Retrieves context-specific logs for UI rendering."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    query = '''
        SELECT m.sender_role, m.message_body FROM message_logs m 
        JOIN chambers c ON m.chamber_id = c.id 
        WHERE c.owner_email=? AND c.chamber_name=? 
        ORDER BY m.id ASC
    '''
    c.execute(query, (email, chamber_name))
    rows = [{"role": r, "content": b} for r, b in c.fetchall()]
    conn.close(); return rows

init_leviathan_db()

# ==============================================================================
# 3. CORE ANALYTICAL SERVICES (AI ENGINE & SMTP GATEWAY)
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    """Initializes Gemini with strictly tuned legal parameters."""
    api_key_vault = st.secrets["GOOGLE_API_KEY"]
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", 
        google_api_key=api_key_vault, 
        temperature=0.15,
        max_output_tokens=4000
    )

def dispatch_legal_brief_smtp(target_email, chamber_name, history_data):
    """Enterprise SMTP Gateway for automated brief delivery."""
    try:
        smtp_sender = st.secrets["EMAIL_USER"]
        smtp_pass = st.secrets["EMAIL_PASS"].replace(" ", "")
        
        email_content = f"ALPHA APEX OFFICIAL LEGAL BRIEF\n"
        email_content += f"CHAMBER IDENTIFIER: {chamber_name}\n"
        email_content += f"TIMESTAMP: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        email_content += "="*60 + "\n\n"
        
        for entry in history_data:
            speaker = "OFFICIAL ADVOCATE" if entry['role'] == 'assistant' else "CLIENT REPRESENTATIVE"
            clean_body = re.sub(r'[*#_]', '', entry['content'])
            email_content += f"[{speaker}]:\n{clean_body}\n\n"
        
        email_content += "="*60 + "\n"
        email_content += "CONFIDENTIALITY NOTICE: This brief is intended for legal review only."
            
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Chambers <{smtp_sender}>"
        msg['To'] = target_email
        msg['Subject'] = f"Legal Consult Brief: {chamber_name}"
        msg.attach(MIMEText(email_content, 'plain', 'utf-8'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_sender, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Critical SMTP Failure: {e}"); return False

def synchronize_law_library():
    """Scans and indexes PDF jurisprudence assets into the relational vault."""
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT filename FROM law_assets")
    indexed = [row[0] for row in c.fetchall()]
    
    if os.path.exists(DATA_FOLDER):
        for f in os.listdir(DATA_FOLDER):
            if f.lower().endswith(".pdf") and f not in indexed:
                f_path = os.path.join(DATA_FOLDER, f)
                try:
                    reader = PdfReader(f_path)
                    f_size = os.path.getsize(f_path) / 1024
                    f_pages = len(reader.pages)
                    f_ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    c.execute("INSERT INTO law_assets (filename, filesize_kb, page_count, sync_timestamp) VALUES (?,?,?,?)", 
                              (f, f_size, f_pages, f_ts))
                except Exception: continue
    conn.commit(); conn.close()

# ==============================================================================
# 4. UI: SOVEREIGN CHAMBERS (VOICE RECORDING ENABLED - TTS REMOVED)
# ==============================================================================

def render_chamber_workstation():
    """The primary legal workstation interface with voice recording and repetition guard."""
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ ALPHA APEX")
        st.caption("Leviathan Production Suite v25")
        
        theme_sel = st.radio("System Shaders", ["Dark Mode", "Light Mode"], horizontal=True)
        apply_leviathan_shaders(theme_sel)
        
        st.divider()
        st.subheader("🌐 Lexicon Settings")
        active_lang = st.selectbox("Select Consultation Language", list(lexicon.keys()))
        l_code = lexicon[active_lang]
        
        st.divider()
        st.subheader("📁 Case Navigator")
        u_mail = st.session_state.user_email
        conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
        chamber_list = [r[0] for r in c.execute("SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0", (u_mail,)).fetchall()]
        conn.close()
        
        st.session_state.current_chamber = st.selectbox("Active Chamber", chamber_list if chamber_list else ["Primary High Court Chamber"])
        
        if st.button("➕ Open New Case Chamber"):
            st.session_state.trigger_chamber_init = True
            
        if st.session_state.get('trigger_chamber_init'):
            n_chamber = st.text_input("New Chamber Name")
            if st.button("Initialize Chamber") and n_chamber:
                conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
                c.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", 
                          (u_mail, n_chamber, str(datetime.date.today())))
                conn.commit(); conn.close()
                st.session_state.trigger_chamber_init = False; st.rerun()

        st.divider()
        if st.button("📧 Dispatch Brief via SMTP"):
            h_context = db_fetch_chamber_history(u_mail, st.session_state.current_chamber)
            if dispatch_legal_brief_smtp(u_mail, st.session_state.current_chamber, h_context):
                st.sidebar.success("Brief Sent Successfully")
            else:
                st.sidebar.error("SMTP Connection Refused")

        if st.button("🚪 Terminate Session"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN CONSULTATION INTERFACE ---
    st.header(f"💼 Case Room: {st.session_state.current_chamber}")
    st.write("---")
    
    # Historical Log Rendering
    logs = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
    for entry in logs:
        with st.chat_message(entry["role"]):
            st.write(entry["content"])

    st.write("") # Geometry Buffer
    
    # RESTORED: SIDE-BY-SIDE VOICE RECORDING & CHAT INPUT
    ui_cols = st.columns([0.84, 0.16])
    with ui_cols[0]:
        t_input = st.chat_input("Enter Legal Query or Case Facts...")
    with ui_cols[1]:
        # VOICE RECORDING INPUT ONLY - TEXT-TO-SPEECH REMOVED
        v_input = speech_to_text(language=l_code, key='leviathan_recorder', just_once=True, use_container_width=True)

    final_input = t_input or v_input

    if final_input:
        if "last_processed_query" not in st.session_state or st.session_state.last_processed_query != final_input:
            st.session_state.last_processed_query = final_input
            
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_input)
            
            with st.chat_message("user"):
                st.write(final_input)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing Statutes, Precedents & Case Law..."):
                    try:
                        p_logic = f"""
                        SYSTEM PERSONA: You are a Senior High Court Advocate of Pakistan with 30 years experience.
                        PROTOCOL:
                        1. ANALYZE intent: If GREETING, respond with professional warmth. 
                        2. If LEGAL QUERY: Apply IRAC (Issue, Rule, Analysis, Conclusion).
                        3. CITATIONS: Reference PPC (Pakistan Penal Code), CrPC, or Constitution of 1973.
                        4. TONE: Authoritative yet accessible.
                        5. LANGUAGE: {active_lang}.
                        USER INPUT: {final_input}
                        """
                        
                        ai_response = get_analytical_engine().invoke(p_logic).content
                        st.markdown(ai_response)
                        
                        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", ai_response)
                        
                        # NEURAL SYNTHESIS (TTS) CALL REMOVED PER USER REQUEST
                        st.rerun()
                    except Exception as e:
                        st.error(f"Analytical Engine Error: {e}")

# ==============================================================================
# 5. UI: SOVEREIGN PORTAL (SECURE VAULT GATEWAY)
# ==============================================================================

def render_sovereign_portal():
    """The secure gateway for the Leviathan System using Local SQL Authentication."""
    st.title("⚖️ ALPHA APEX LEVIATHAN PORTAL")
    st.markdown("### Private Legal Enterprise Handshake")
    
    tab_login, tab_reg = st.tabs(["🔐 Authorized Vault Login", "📝 Sovereign Account Registry"])
    
    with tab_login:
        st.subheader("Credential Verification")
        login_mail = st.text_input("Registered Vault Email")
        login_key = st.text_input("Security Vault Key", type="password")
        if st.button("Authenticate & Enter"):
            u_name = db_verify_vault_access(login_mail, login_key)
            if u_name:
                st.session_state.logged_in = True
                st.session_state.user_email = login_mail
                st.session_state.username = u_name
                st.rerun()
            else:
                st.error("HANDSHAKE FAILED: Invalid Identifier or Key.")
                
    with tab_reg:
        st.subheader("Establish New Sovereign Identity")
        st.info("Registration creates a persistent local database entry for your case chambers.")
        reg_mail = st.text_input("Primary Professional Email")
        reg_name = st.text_input("Full Name / Title")
        reg_key = st.text_input("Define Security Key", type="password")
        if st.button("Execute Vault Registry"):
            if db_create_vault_user(reg_mail, reg_name, reg_key):
                st.success("VAULT SUCCESS: Account established. Proceed to Login.")
            else:
                st.error("REGISTRY CONFLICT: Email already exists in the Sovereign Vault.")

# ==============================================================================
# 6. MASTER EXECUTION ENGINE & ADMIN ANALYTICS
# ==============================================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_sovereign_portal()
else:
    # Router for Authenticated Users
    view = st.sidebar.radio("Sovereign Navigation Hub", ["Chambers", "Law Library", "System Admin"])
    
    if view == "Chambers":
        render_chamber_workstation()
        
    elif view == "Law Library":
        st.header("📚 Digital Jurisprudence Assets")
        st.write("Below is the indexed metadata of the PDF law documents stored in the local repository.")
        
        if st.button("🔄 Execute Library Synchronization"):
            synchronize_law_library(); st.rerun()
        
        conn = sqlite3.connect(SQL_DB_FILE)
        assets_df = pd.read_sql_query("SELECT filename, filesize_kb, page_count, sync_timestamp, asset_status FROM law_assets", conn)
        conn.close()
        
        if not assets_df.empty:
            st.dataframe(assets_df, use_container_width=True, hide_index=True)
            st.info(f"Total Assets Indexed: {len(assets_df)}")
        else:
            st.warning("Jurisprudence Vault is empty. Please verify the 'law_library_assets' folder.")
            
    elif view == "System Admin":
        st.header("🛡️ Sovereign System Administration")
        st.write("Real-time telemetry and user management for the Leviathan architecture.")
        
        connection = sqlite3.connect(SQL_DB_FILE)
        users_df = pd.read_sql_query("SELECT full_name, email, registration_date, total_queries, membership_tier FROM users", connection)
        chambers_df = pd.read_sql_query("SELECT owner_email, chamber_name, init_date, chamber_type FROM chambers", connection)
        connection.close()
        
        admin_col1, admin_col2 = st.columns(2)
        with admin_col1:
            st.subheader("Verified User Registry")
            st.dataframe(users_df, hide_index=True)
            st.metric("Total Registered Counsel", len(users_df))
            
        with admin_col2:
            st.subheader("Active Chamber Distribution")
            st.dataframe(chambers_df, hide_index=True)
            st.metric("Total Active Cases", len(chambers_df))
        
        st.divider()
        st.subheader("Lead Development Credentials")
        st.write("The Alpha Apex Leviathan System is maintained by the following architects:")
        
        architect_grid = [
            {"Architect": "Saim Ahmed", "Focus": "Lead System Architect & Core Logic"},
            {"Architect": "Huzaifa Khan", "Focus": "Analytical AI Model Tuning (Gemini 2.0)"},
            {"Architect": "Mustafa Khan", "Focus": "Relational SQL Data Persistence"},
            {"Architect": "Ibrahim Sohail", "Focus": "High-Fidelity UI/UX & Shaders"},
            {"Architect": "Daniyal Faraz", "Focus": "SMTP Gateway & Enterprise Quality Assurance"}
        ]
        st.table(architect_grid)
        
        st.info("System Version 25.0 Stable. All TTS engines deactivated. Voice Recording input active.")

# ==============================================================================
# END OF SYSTEM SCRIPT - VERBOSE SOVEREIGN PRODUCTION EDITION
# ==============================================================================
