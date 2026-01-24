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
    Includes glassmorphism, neural transitions, and layout overrides for
    side-by-side voice/text components.
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
        
        /* Precision Button Styling with Hover Effects */
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

        /* Vertical Alignment for Sidebar Items */
        .sidebar-content {
            display: flex;
            flex-direction: column;
            gap: 20px;
        }

        /* Input Field Aesthetics */
        .stTextInput>div>div>input {
            background-color: rgba(255,255,255,0.05) !important;
            color: white !important;
            border: 1px solid rgba(56, 189, 248, 0.3) !important;
            border-radius: 15px !important;
            padding: 15px !important;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar { width: 10px; }
        ::-webkit-scrollbar-track { background: #0f172a; }
        ::-webkit-scrollbar-thumb { background: #334155; border-radius: 5px; }
        ::-webkit-scrollbar-thumb:hover { background: #38bdf8; }
    </style>
    """
    if theme_mode == "Dark Mode":
        shader_css += """
        <style>
            .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important; color: #f1f5f9 !important; }
            h1, h2, h3 { color: #38bdf8 !important; text-transform: uppercase; letter-spacing: 2px; }
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
# 2. RELATIONAL DATABASE PERSISTENCE ENGINE (EXHAUSTIVE RDBMS)
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v24.db"
DATA_FOLDER = "law_library_assets"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

def init_leviathan_db():
    """Builds the comprehensive SQL schema for multi-tenant enterprise support."""
    connection = sqlite3.connect(SQL_DB_FILE)
    cursor = connection.cursor()
    
    # Table 1: Sovereign User Records
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                        email TEXT PRIMARY KEY, 
                        full_name TEXT, 
                        vault_key TEXT, 
                        registration_date TEXT,
                        membership_tier TEXT DEFAULT 'Senior Counsel',
                        account_status TEXT DEFAULT 'Active'
                     )''')
    
    # Table 2: Case Chamber Registry
    cursor.execute('''CREATE TABLE IF NOT EXISTS chambers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        owner_email TEXT, 
                        chamber_name TEXT, 
                        init_date TEXT,
                        chamber_type TEXT DEFAULT 'General Litigation'
                     )''')
    
    # Table 3: Transactional Consultation History
    cursor.execute('''CREATE TABLE IF NOT EXISTS message_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        chamber_id INTEGER, 
                        sender_role TEXT, 
                        message_body TEXT, 
                        ts_created TEXT,
                        token_count INTEGER DEFAULT 0
                     )''')
    
    # Table 4: Digital Jurisprudence Assets
    cursor.execute('''CREATE TABLE IF NOT EXISTS law_assets (
                        id INTEGER PRIMARY KEY AUTOINCREMENT, 
                        filename TEXT, 
                        filesize_kb REAL, 
                        page_count INTEGER, 
                        sync_timestamp TEXT,
                        asset_status TEXT DEFAULT 'Verified'
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
                  (email, "Default High Court Chamber", now))
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
# 3. CORE ANALYTICAL SERVICES (AI & SMTP GATEWAY)
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    """Initializes Gemini with strictly tuned legal parameters."""
    api_key_vault = st.secrets["GOOGLE_API_KEY"]
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=api_key_vault, 
        temperature=0.2,
        max_output_tokens=4000
    )

def execute_neural_synthesis(text, language_code):
    """JavaScript neural synthesis for client-side audio playback."""
    escaped_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_payload = f"""
    <script>
        (function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{escaped_text}');
            msg.lang = '{language_code}';
            msg.rate = 1.0;
            msg.pitch = 1.0;
            window.speechSynthesis.speak(msg);
        }})();
    </script>
    """
    components.html(js_payload, height=0)

def dispatch_legal_brief_smtp(target_email, chamber_id, history_data):
    """Enterprise SMTP Gateway for automated brief delivery."""
    try:
        smtp_sender = st.secrets["EMAIL_USER"]
        smtp_pass = st.secrets["EMAIL_PASS"]
        
        email_content = f"ALPHA APEX OFFICIAL LEGAL BRIEF\n"
        email_content += f"CHAMBER: {chamber_id}\n"
        email_content += f"GENERATED ON: {datetime.datetime.now()}\n"
        email_content += "-"*50 + "\n\n"
        
        for entry in history_data:
            speaker = "ADVOCATE" if entry['role'] == 'assistant' else "CLIENT"
            email_content += f"[{speaker}]: {entry['content']}\n\n"
            
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Chambers <{smtp_sender}>"
        msg['To'] = target_email
        msg['Subject'] = f"Legal Consult Brief: {chamber_id}"
        msg.attach(MIMEText(email_content, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_sender, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Critical SMTP Failure: {e}"); return False

def synchronize_law_library():
    """Scans and indexes PDF jurisprudence assets."""
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
# 4. UI: SOVEREIGN CHAMBERS (SIDE-BY-SIDE INTERFACE)
# ==============================================================================

def render_chamber_workstation():
    """The primary legal workstation interface."""
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ ALPHA APEX")
        st.caption("Leviathan Production Suite v24")
        
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
        
        if st.button("➕ Open New Chamber"):
            st.session_state.trigger_chamber_init = True
            
        if st.session_state.get('trigger_chamber_init'):
            n_chamber = st.text_input("Chamber Identifier")
            if st.button("Confirm Initialization") and n_chamber:
                conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
                c.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", 
                          (u_mail, n_chamber, str(datetime.date.today())))
                conn.commit(); conn.close()
                st.session_state.trigger_chamber_init = False; st.rerun()

        st.divider()
        if st.button("📧 Dispatch Brief"):
            h_context = db_fetch_chamber_history(u_mail, st.session_state.current_chamber)
            if dispatch_legal_brief_smtp(u_mail, st.session_state.current_chamber, h_context):
                st.toast("Legal Brief Dispatched to " + u_mail)

        if st.button("🚪 System Logout"):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

    # --- MAIN CONSULTATION AREA ---
    st.header(f"💼 Chamber: {st.session_state.current_chamber}")
    st.write("---")
    
    # Render Transactional History
    logs = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
    for entry in logs:
        with st.chat_message(entry["role"]):
            st.write(entry["content"])

    st.write("") # Structural Buffer
    
    # --- RESTORED: SIDE-BY-SIDE PROMPT & MIC ---
    ui_cols = st.columns([0.85, 0.15])
    
    with ui_cols[0]:
        t_input = st.text_input("Enter Legal Query", placeholder="Describe your legal issue or greet the advocate...", label_visibility="collapsed", key="master_text_box")
    
    with ui_cols[1]:
        v_input = speech_to_text(language=l_code, key='leviathan_mic', just_once=True, use_container_width=True)

    final_input = v_input or t_input

    if final_input:
        # Step 1: SQL Transaction Logging
        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_input)
        
        with st.chat_message("user"):
            st.write(final_input)
        
        with st.chat_message("assistant"):
            with st.spinner("Consulting Statutes & Precedents..."):
                try:
                    # ADVANCED CONTEXT-AWARE PROMPT LOGIC
                    p_logic = f"""
                    SYSTEM PERSONA: You are a Senior High Court Advocate of Pakistan.
                    BEHAVIORAL RULES:
                    1. Check the user input for intent.
                    2. If input is a GREETING (e.g., Hi, Hello, Salam), respond warmly like a human advocate. DO NOT use IRAC.
                    3. If input is a LEGAL PROBLEM, use strict IRAC format (Issue, Rule, Analysis, Conclusion).
                    4. Cite Pakistan Penal Code (PPC), CrPC, or Civil Code where relevant.
                    5. Language: {active_lang}.
                    USER INPUT: {final_input}
                    """
                    
                    ai_response = get_analytical_engine().invoke(p_logic).content
                    st.markdown(ai_response)
                    
                    # Step 2: AI Response SQL Logging
                    db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", ai_response)
                    
                    # Step 3: Synthesis Trigger
                    execute_neural_synthesis(ai_response, l_code)
                    st.rerun()
                except Exception as e:
                    st.error(f"Analytical Error: {e}")

# ==============================================================================
# 5. UI: SOVEREIGN PORTAL (VAULT LOGIN)
# ==============================================================================

def render_sovereign_portal():
    """The secure gateway for the Leviathan System."""
    st.title("⚖️ ALPHA APEX LEVIATHAN PORTAL")
    st.markdown("### Public Legal Intelligence Access Point")
    
    t1, t2 = st.tabs(["🔐 Vault Login", "📝 Registry New Account"])
    
    with t1:
        st.subheader("Authorize Access")
        le = st.text_input("Vault Email")
        lp = st.text_input("Security Key", type="password")
        if st.button("Enter Vault"):
            u_name = db_verify_vault_access(le, lp)
            if u_name:
                st.session_state.logged_in = True
                st.session_state.user_email = le
                st.session_state.username = u_name
                st.rerun()
            else:
                st.error("ACCESS DENIED: Credentials Not Recognized.")
                
    with t2:
        st.subheader("Initialize Sovereign Account")
        st.info("Registration establishes your private chamber on our local database.")
        re = st.text_input("Primary Email")
        ru = st.text_input("Full Professional Name")
        rp = st.text_input("Set Security Key", type="password")
        if st.button("Execute Registration"):
            if db_create_vault_user(re, ru, rp):
                st.success("VAULT INITIALIZED. Please proceed to Login.")
            else:
                st.error("REGISTRATION ERROR: Identifier already exists.")

# ==============================================================================
# 6. MASTER EXECUTION ENGINE
# ==============================================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    render_sovereign_portal()
else:
    # Router for Authenticated Users
    view = st.sidebar.radio("Navigation Hub", ["Chambers", "Law Library", "Admin Console"])
    
    if view == "Chambers":
        render_chamber_workstation()
    elif view == "Law Library":
        st.header("📚 Digital Jurisprudence Library")
        if st.button("🔄 Sync Library Assets"):
            synchronize_law_library(); st.rerun()
        
        conn = sqlite3.connect(SQL_DB_FILE)
        assets_df = pd.read_sql_query("SELECT filename, filesize_kb, page_count, sync_timestamp FROM law_assets", conn)
        conn.close()
        
        if not assets_df.empty:
            st.dataframe(assets_df, use_container_width=True)
        else:
            st.warning("Library is empty. Upload PDFs to the law_library_assets folder.")
            
    elif view == "Admin Console":
        st.header("🛡️ System Administration")
        st.write("Authorized access for system architects.")
        
        conn = sqlite3.connect(SQL_DB_FILE)
        u_df = pd.read_sql_query("SELECT full_name, email, registration_date FROM users", conn)
        c_df = pd.read_sql_query("SELECT owner_email, chamber_name FROM chambers", conn)
        conn.close()
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Verified Users")
            st.dataframe(u_df)
        with col2:
            st.subheader("Active Chambers")
            st.dataframe(c_df)
        
        st.divider()
        st.subheader("Architect Credentials")
        devs = [
            {"Name": "Saim Ahmed", "Role": "System Architect"},
            {"Name": "Huzaifa Khan", "Role": "Analytical AI Engine"},
            {"Name": "Mustafa Khan", "Role": "RDBMS Database Lead"},
            {"Name": "Ibrahim Sohail", "Role": "UI/UX & Synthesis"},
            {"Name": "Daniyal Faraz", "Role": "SMTP Gateway & QA"}
        ]
        st.table(devs)

# ==============================================================================
# END OF SCRIPT - 500+ LINES OF OMNIPOTENCE PRODUCTION CODE
# ==============================================================================
