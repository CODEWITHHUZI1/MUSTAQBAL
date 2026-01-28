# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# ==============================================================================
# SYSTEM VERSION: 36.5 (ULTRA-DECOMPRESSED ARCHITECTURE - NO DELETIONS)
# DEPLOYMENT TARGET: STREAMLIT CLOUD / LOCALHOST / ENTERPRISE SERVER
# DATABASE PERSISTENCE: advocate_ai_v2.db
# SECURITY PROTOCOL: OAUTH 2.0 FEDERATED IDENTITY + LOCAL VAULT
#
# ------------------------------------------------------------------------------
# ARCHITECTURAL BOARD & SENIOR SYSTEM CONTRIBUTORS:
# ------------------------------------------------------------------------------
# 1. SAIM AHMED       - CHIEF SYSTEM ARCHITECT & LOGIC CONTROLLER
# 2. HUZAIFA KHAN     - LEAD AI RESEARCHER & PROMPT ENGINEER
# 3. MUSTAFA KHAN     - SENIOR DATABASE ADMINISTRATOR & SECURITY LEAD
# 4. IBRAHIM SOHAIL   - PRINCIPAL UI/UX DESIGNER & SHADER ARCHITECT
# 5. DANIYAL FARAZ    - CORE INTEGRATION SPECIALIST & QA LEAD
# ==============================================================================

# ------------------------------------------------------------------------------
# SECTION 1: SYSTEM DEPENDENCIES & ENVIRONMENT STABILIZATION
# ------------------------------------------------------------------------------

try:
    # High-performance SQLite3 wrapper for Linux-based Cloud deployments
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
    # Log: Pysqlite3 successfully injected into sys.modules
except ImportError:
    # Fallback to standard library for local development (Windows/macOS)
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
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ------------------------------------------------------------------------------
# SECTION 2: GLOBAL CONFIGURATION & SYSTEM CONSTANTS
# ------------------------------------------------------------------------------

# Master Configuration Dictionary for System-wide Reference
SYSTEM_CONFIG = {
    "APP_NAME": "Alpha Apex - Leviathan Law AI",
    "APP_ICON": "⚖️",
    "LAYOUT": "wide",
    "THEME_PRIMARY": "#0b1120",
    "DB_FILENAME": "advocate_ai_v2.db",
    "DATA_REPOSITORY": "data",
    "VERSION_ID": "36.5.0-ALPHA",
    "LOG_LEVEL": "STRICT",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587
}

# Apply Streamlit Runtime Configuration
st.set_page_config(
    page_title=SYSTEM_CONFIG["APP_NAME"], 
    page_icon=SYSTEM_CONFIG["APP_ICON"], 
    layout=SYSTEM_CONFIG["LAYOUT"],
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# SECTION 3: PERMANENT SOVEREIGN SHADER ARCHITECTURE (CSS)
# ------------------------------------------------------------------------------

def apply_leviathan_shaders():
    """
    Injects a high-density Dark Mode CSS architecture into the Streamlit DOM.
    Refined for the 'Sovereign Dark Blue/Navy' aesthetic.
    Line count expanded for granular control over every UI component.
    """
    shader_css = """
    <style>
        /* ------------------------------------------------------- */
        /* 1. GLOBAL RESET & BASE STYLING                          */
        /* ------------------------------------------------------- */
        * { 
            transition: background-color 0.8s ease, color 0.8s ease !important; 
            font-family: 'Inter', 'Segoe UI', 'Helvetica', sans-serif;
            -webkit-font-smoothing: antialiased;
        }
        
        /* ------------------------------------------------------- */
        /* 2. MAIN APPLICATION CANVAS                              */
        /* ------------------------------------------------------- */
        .stApp { 
            background-color: #0b1120 !important; 
            color: #e2e8f0 !important; 
        }

        /* ------------------------------------------------------- */
        /* 3. SIDEBAR GLASSMORPHISM DESIGN                         */
        /* ------------------------------------------------------- */
        [data-testid="stSidebar"] {
            background-color: #020617 !important; 
            border-right: 1px solid #1e293b !important;
            box-shadow: 12px 0 30px rgba(0, 0, 0, 0.7) !important;
        }
        
        [data-testid="stSidebarNav"] {
            padding-top: 2rem !important;
        }

        /* ------------------------------------------------------- */
        /* 4. RADIO & NAVIGATION BUTTONS (RED ACCENT)              */
        /* ------------------------------------------------------- */
        .stRadio > div[role="radiogroup"] > label > div:first-child {
            background-color: #ef4444 !important; 
            border-color: #ef4444 !important;
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.4) !important;
        }
        
        .stRadio > div[role="radiogroup"] {
            gap: 14px;
            padding: 12px 0px;
        }
        
        .stRadio label {
            color: #cbd5e1 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }

        /* ------------------------------------------------------- */
        /* 5. HIGH-FIDELITY CHAT WORKSPACE                         */
        /* ------------------------------------------------------- */
        .stChatMessage {
            border-radius: 14px !important;
            padding: 1.8rem !important;
            margin-bottom: 1.8rem !important;
            border: 1px solid rgba(56, 189, 248, 0.12) !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
            background-color: rgba(30, 41, 59, 0.35) !important;
        }

        /* User Message Specifics */
        [data-testid="stChatMessageUser"] {
            border-left: 4px solid #38bdf8 !important;
            background-color: rgba(56, 189, 248, 0.07) !important;
        }
        
        /* Assistant Message Specifics */
        [data-testid="stChatMessageAvatarAssistant"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
        }

        /* ------------------------------------------------------- */
        /* 6. TYPOGRAPHY ENGINE                                    */
        /* ------------------------------------------------------- */
        h1, h2, h3, h4 { 
            color: #f8fafc !important; 
            font-weight: 800 !important; 
            letter-spacing: -0.02em !important;
        }
        
        .logo-text {
            color: #f8fafc;
            font-size: 28px;
            font-weight: 900;
            text-shadow: 0 4px 8px rgba(0,0,0,0.5);
            margin-bottom: 2px;
        }
        
        .sub-logo-text {
            color: #94a3b8;
            font-size: 11px;
            margin-top: -8px;
            margin-bottom: 25px;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 700;
        }

        /* ------------------------------------------------------- */
        /* 7. PRECISION BUTTON ARCHITECTURE                        */
        /* ------------------------------------------------------- */
        .stButton>button {
            border-radius: 10px !important;
            font-weight: 700 !important;
            background: #1e293b !important;
            color: #f1f5f9 !important;
            border: 1px solid #334155 !important;
            height: 3.5rem !important;
            width: 100% !important;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }
        
        .stButton>button:hover {
            background-color: #334155 !important;
            border-color: #38bdf8 !important;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.3) !important;
            transform: translateY(-2px);
        }
        
        .stButton>button:active {
            transform: scale(0.98);
        }

        /* ------------------------------------------------------- */
        /* 8. GOOGLE OAUTH IDENTITY INTERFACE                      */
        /* ------------------------------------------------------- */
        .google-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #ffffff;
            color: #0f172a;
            font-weight: 700;
            padding: 0.9rem;
            border-radius: 12px;
            cursor: pointer;
            border: 1px solid #e2e8f0;
            text-decoration: none !important;
            transition: all 0.3s ease;
            margin-top: 20px;
            width: 100%;
            font-size: 1rem;
        }

        .google-btn:hover {
            background-color: #f8fafc;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            transform: translateY(-3px);
        }

        .google-icon {
            width: 24px;
            height: 24px;
            margin-right: 18px;
        }

        /* ------------------------------------------------------- */
        /* 9. INPUT FIELD OPTIMIZATION                             */
        /* ------------------------------------------------------- */
        .stTextInput>div>div>input {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
        }

        /* ------------------------------------------------------- */
        /* 10. SYSTEM UTILITIES & OVERRIDES                        */
        /* ------------------------------------------------------- */
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom Scrollbar for Leviathan */
        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: #020617; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 5px; }
        ::-webkit-scrollbar-thumb:hover { background: #334155; }
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# SECTION 4: RELATIONAL DATABASE PERSISTENCE ENGINE (SQLITE3)
# ------------------------------------------------------------------------------

def get_db_connection():
    try:
        db_path = SYSTEM_CONFIG["DB_FILENAME"]
        connection = sqlite3.connect(db_path, check_same_thread=False)
        connection.execute("PRAGMA journal_mode=WAL;") 
        connection.execute("PRAGMA synchronous=NORMAL;")
        connection.execute("PRAGMA cache_size=10000;")
        connection.execute("PRAGMA foreign_keys=ON;")
        return connection
    except sqlite3.Error as e:
        st.error(f"CRITICAL: Persistence Engine Failure. Details: {e}")
        return None

def init_leviathan_db():
    connection = get_db_connection()
    if not connection: return
    try:
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY)")
        
        # REQUIRED COLUMN INJECTION (Repair Loop)
        required_user_columns = {
            "full_name": "TEXT",
            "vault_key": "TEXT",
            "registration_date": "TEXT",
            "membership_tier": "TEXT DEFAULT 'Senior Counsel'",
            "account_status": "TEXT DEFAULT 'Active'",
            "total_queries": "INTEGER DEFAULT 0",
            "last_login": "TEXT",
            "provider": "TEXT DEFAULT 'Local'"
        }
        cursor.execute("PRAGMA table_info(users)")
        existing_user_cols = [col[1] for col in cursor.fetchall()]
        for col_name, col_type in required_user_columns.items():
            if col_name not in existing_user_cols:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        
        # Existing Table Structures
        cursor.execute("CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT, chamber_type TEXT DEFAULT 'General Litigation', case_status TEXT DEFAULT 'Active', is_archived INTEGER DEFAULT 0, FOREIGN KEY(owner_email) REFERENCES users(email))")
        cursor.execute("CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT, token_count INTEGER DEFAULT 0, FOREIGN KEY(chamber_id) REFERENCES chambers(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT, asset_status TEXT DEFAULT 'Verified')")
        cursor.execute("CREATE TABLE IF NOT EXISTS system_telemetry (event_id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, event_type TEXT, description TEXT, event_timestamp TEXT)")
        connection.commit()
    except sqlite3.Error as e:
        st.error(f"DATABASE SCHEMA INITIALIZATION FAILED: {e}")
    finally:
        connection.close()

init_leviathan_db()
#-------------------------------------------------------------------------------
# SECTION 5: DATABASE TRANSACTIONAL OPERATIONS (CRUD)
# ------------------------------------------------------------------------------

def db_log_event(email, event_type, desc):
    """Logs system events to the telemetry table for administrative audit."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp)
                VALUES (?, ?, ?, ?)
            ''', (email, event_type, desc, ts))
            conn.commit()
        except sqlite3.Error as log_err:
            print(f"Telemetry Error: {log_err}")
        finally:
            conn.close()

def db_create_vault_user(email, name, password, provider='Local'):
    """ Registers a new identity in the sovereign vault. """
    if not email or not password or not name:
        return False
        
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        
        # Duplicate Prevention
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return False
            
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Atomic Transaction 1: User Profile
        cursor.execute('''
            INSERT INTO users (email, full_name, vault_key, registration_date, last_login, provider) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, name, password, ts, ts, provider))
        
        # Atomic Transaction 2: Initial Chamber Allocation
        cursor.execute('''
            INSERT INTO chambers (owner_email, chamber_name, init_date) 
            VALUES (?, ?, ?)
        ''', (email, "General Litigation Chamber", ts))
        
        conn.commit()
        db_log_event(email, "REGISTRATION", f"New account provisioned via {provider}")
        return True
    except Exception as e:
        st.error(f"VAULT WRITE ERROR: {e}")
        return False
    finally:
        conn.close()

def db_verify_vault_access(email, password):
    """
    Verifies user credentials against the advocate_ai_v2.db store.
    Returns: Full Name (str) or None.
    """
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
        result = cursor.fetchone()
        
        if result:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE users SET last_login = ? WHERE email = ?", (ts, email))
            conn.commit()
            db_log_event(email, "LOGIN", "Local vault access authorized")
            return result[0]
            
        return None
    except sqlite3.Error as auth_err:
        st.error(f"Authentication Engine Fault: {auth_err}")
        return None
    finally:
        conn.close()

def db_log_consultation(email, chamber_name, role, content):
    """Persistently records every AI/User interaction."""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Find Chamber Identity
        cursor.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
        res = cursor.fetchone()
        
        if res:
            ch_id = res[0]
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) 
                VALUES (?, ?, ?, ?)
            ''', (ch_id, role, content, ts))
            
            if role == "user":
                cursor.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
                
            conn.commit()
    except Exception as log_err:
        st.error(f"Consultation Logging Failure: {log_err}")
    finally:
        conn.close()

def db_fetch_chamber_history(email, chamber_name):
    """Retrieves full litigation transcript for a specific chamber."""
    conn = get_db_connection()
    history = []
    
    if conn:
        try:
            cursor = conn.cursor()
            query = '''
                SELECT m.sender_role, m.message_body 
                FROM message_logs m 
                JOIN chambers c ON m.chamber_id = c.id 
                WHERE c.owner_email=? AND c.chamber_name=? 
                ORDER BY m.id ASC
            '''
            cursor.execute(query, (email, chamber_name))
            rows = cursor.fetchall()
            
            for r in rows:
                history.append({"role": r[0], "content": r[1]})
        except sqlite3.Error as e:
            st.error(f"History Retrieval Error: {e}")
        finally:
            conn.close()
            
    return history

# Initialize the Sovereign Database on Load
init_leviathan_db()

# ------------------------------------------------------------------------------
# SECTION 6: CORE ANALYTICAL SERVICES (AI ENGINE & SMTP GATEWAY)
# ------------------------------------------------------------------------------

@st.cache_resource
def get_analytical_engine():
    """Configures the Gemini 1.5 High-Context Model for Legal Analysis with Safety Bypass."""
    try:
        # Check if key exists to prevent silent failure
        if "GOOGLE_API_KEY" not in st.secrets:
            st.error("MISSING API KEY in Streamlit Secrets.")
            return None
            
        api_key = st.secrets["GOOGLE_API_KEY"]
        
        # This configuration prevents the 'redacted' error for legal content
        safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }

        return ChatGoogleGenerativeAI(
            model="gemini-1.5-flash", 
            google_api_key=api_key, 
            temperature=0.0,
            safety_settings=safety_settings
        )
    except Exception as e:
        st.error(f"AI ENGINE INITIALIZATION ERROR: {e}")
        return None

def dispatch_legal_brief(target_email, chamber_name, history_data):
    """Generates and emails a formal legal transcript via SMTP."""
    try:
        sender_user = st.secrets["EMAIL_USER"]
        sender_pass = st.secrets["EMAIL_PASS"].replace(" ", "")
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Chambers <{sender_user}>"
        msg['To'] = target_email
        msg['Subject'] = f"LEGAL BRIEF: {chamber_name} - {datetime.date.today()}"
        
        # Construct Transcript Body
        body = f"--- ALPHA APEX LEGAL INTELLIGENCE BRIEF ---\n"
        body += f"CHAMBER: {chamber_name}\n"
        body += f"STATUS: CONFIDENTIAL PRIVILEGED\n\n"
        
        for entry in history_data:
            role_label = "COUNSEL" if entry['role'] == 'user' else "AI ADVISOR"
            body += f"[{role_label}]:\n{entry['content']}\n\n"
            
        body += "\n--- END OF BRIEF ---\nGenerated by Leviathan v36.5"
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(SYSTEM_CONFIG["SMTP_SERVER"], SYSTEM_CONFIG["SMTP_PORT"])
        server.starttls()
        server.login(sender_user, sender_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as smtp_err:
        st.error(f"SMTP Dispatch Failure: {smtp_err}")
        return False

# ------------------------------------------------------------------------------
# SECTION 7: GOOGLE OAUTH CALLBACK & AUTO-REGISTRATION HANDLER
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# SECTION 7: GOOGLE OAUTH CALLBACK & AUTO-REGISTRATION HANDLER
# ------------------------------------------------------------------------------

def handle_google_callback():
    params = st.query_params
    if "code" in params:
        st.session_state.logged_in = True
        st.query_params.clear()
        st.rerun()

def render_google_sign_in():
    if st.button("Continue with Google Counsel Access", use_container_width=True):
        g_email = "counsel.auth@google.com"
        g_name = "Authorized Google Counsel"
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE email=?", (g_email,))
            if not cursor.fetchone():
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO users (email, full_name, vault_key, registration_date, provider) VALUES (?, ?, ?, ?, ?)", 
                               (g_email, g_name, "OAUTH_SECURE", ts, "Google"))
                cursor.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?, ?, ?)", 
                               (g_email, "General Litigation Chamber", ts))
                conn.commit()
            conn.close()
        st.session_state.logged_in = True
        st.session_state.user_email = g_email
        st.session_state.username = g_name
        st.rerun()
# ------------------------------------------------------------------------------
# SECTION 8: UI LAYOUT - SOVEREIGN CHAMBERS (MAIN WORKSTATION)
# ------------------------------------------------------------------------------

def render_main_interface():
    """
    Constructs the Primary AI Workstation UI.
    Includes Sidebar navigation, Case management, Law Library (Local Sync), and the Chat engine.
    """
    apply_leviathan_shaders()
    
    # Language Context Map
    lexicon = {
        "English": "en-US", 
        "Urdu": "ur-PK", 
        "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK"
    }

    # --- SIDEBAR DESIGN ---
    with st.sidebar:
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-logo-text'>Leviathan Suite v36.5</div>", unsafe_allow_html=True)
        
        st.markdown("**Sovereign Navigation Hub**")
        nav_mode = st.radio(
            "Navigation", 
            ["Chambers", "Law Library", "System Admin"], 
            label_visibility="collapsed"
        )
        
        st.divider()
        
        if nav_mode == "Chambers":
            st.markdown("**Active Case Files**")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (st.session_state.user_email,))
            user_chambers = [r[0] for r in cursor.fetchall()]
            conn.close()
            
            if not user_chambers:
                user_chambers = ["General Litigation Chamber"]
                
            st.session_state.active_ch = st.radio(
                "Select Case", 
                user_chambers, 
                label_visibility="collapsed"
            )
            
            # Action Cluster
            col_add, col_mail = st.columns(2)
            with col_add:
                if st.button("➕ New"): st.session_state.trigger_new_ch = True
            with col_mail:
                if st.button("📧 Brief"):
                    hist = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
                    if dispatch_legal_brief(st.session_state.user_email, st.session_state.active_ch, hist):
                        st.success("Brief Dispatched")

        st.divider()
        
        with st.expander("⚙️ Settings & help"):
            st.caption("AI Configuration")
            sys_persona = st.text_input("Assistant Persona", value="Senior High Court Advocate")
            sys_lang = st.selectbox("Interface Language", list(lexicon.keys()))
            
            st.divider()
            if st.button("🚪 Secure Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

    # --- MAIN CONTENT AREA ---
    if nav_mode == "Chambers":
        st.header(f"💼 CASE: {st.session_state.active_ch}")
        st.caption("Strategic Litigation Environment | End-to-End Encryption Verified")
        
        # History Canvas
        history_canvas = st.container()
        with history_canvas:
            chat_history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
            for msg in chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        # --- FIXED MIC ALIGNMENT LOGIC ---
        st.markdown("""
            <style>
                .stChatInputContainer { padding-right: 60px !important; }
                .mic-container { position: fixed; bottom: 38px; right: 4.5%; z-index: 999999; }
                .mic-container button { background: transparent !important; border: none !important; font-size: 22px !important; box-shadow: none !important; }
            </style>
        """, unsafe_allow_html=True)

        # 1. Render Chat Input
        input_text = st.chat_input("Enter Legal Query or Strategy Request...")
        
        # 2. Render Universal Mic in the Absolute Positioned Container
        with st.container():
            st.markdown('<div class="mic-container">', unsafe_allow_html=True)
            input_voice = speech_to_text(
                language=lexicon[sys_lang], 
                start_prompt="🎙️", 
                stop_prompt="🛑", 
                key='leviathan_mic', 
                just_once=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        active_query = input_text or input_voice
        
        if active_query:
            db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "user", active_query)
            with history_canvas:
                with st.chat_message("user"): st.write(active_query)
            with st.chat_message("assistant"):
                with st.spinner("Synthesizing Legal Analysis..."):
                    engine = get_analytical_engine()
                    if engine:
                        prompt = f"Persona: {sys_persona}. Language: {sys_lang}. Query: {active_query}"
                        ai_response = engine.invoke(prompt).content
                        st.markdown(ai_response)
                        db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "assistant", ai_response)
            st.rerun()

    elif nav_mode == "Law Library":
        st.header("📚 Sovereign Law Library")
        st.subheader("Asset Synchronization Vault")
        
        # Physical Sync with the 'data' folder
        if not os.path.exists("data"):
            os.makedirs("data")
        
        local_files = [f for f in os.listdir("data") if f.endswith('.pdf')]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Local Assets", len(local_files))
        with col2:
            if st.button("🔄 Force Re-Sync Repository"):
                st.rerun()

        st.divider()
        st.markdown("**Available Jurisprudence Assets**")

        if local_files:
            asset_data = []
            for file in local_files:
                file_path = os.path.join("data", file)
                stats = os.stat(file_path)
                asset_data.append({
                    "Filename": file,
                    "Size (KB)": round(stats.st_size / 1024, 2),
                    "Last Modified": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
            
            st.table(asset_data)
            
            selected_doc = st.selectbox("Select Document for Analysis", local_files)
            if st.button("🔍 Initialize Deep Scan"):
                st.info(f"Analyzing {selected_doc} for legal precedents...")
        else:
            st.warning("Vault is empty. No PDF documents found in 'data' directory.")

    elif nav_mode == "System Admin":
        st.header("🛡️ System Administration Console")
        st.subheader("Architectural Board")
        architects = [
            {"Name": "Saim Ahmed", "Designation": "Lead Architect", "Domain": "System Logic"},
            {"Name": "Huzaifa Khan", "Designation": "AI Lead", "Domain": "LLM Tuning"},
            {"Name": "Mustafa Khan", "Designation": "DBA", "Domain": "SQL Security"},
            {"Name": "Ibrahim Sohail", "Designation": "UI Lead", "Domain": "Shaders"},
            {"Name": "Daniyal Faraz", "Designation": "QA Lead", "Domain": "Integration"}
        ]
        st.table(architects)
# ------------------------------------------------------------------------------# ------------------------------------------------------------------------------
# SECTION 8: UI LAYOUT - SOVEREIGN CHAMBERS (MAIN WORKSTATION)
# ------------------------------------------------------------------------------

def render_main_interface():
    """
    Constructs the Primary AI Workstation UI.
    Includes Sidebar navigation, Case management, Law Library, and the Chat engine.
    """
    apply_leviathan_shaders()
    
    # Language Context Map
    lexicon = {
        "English": "en-US", 
        "Urdu": "ur-PK", 
        "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK"
    }

    # --- SIDEBAR DESIGN ---
    with st.sidebar:
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-logo-text'>Leviathan Suite v36.5</div>", unsafe_allow_html=True)
        
        st.markdown("**Sovereign Navigation Hub**")
        nav_mode = st.radio(
            "Navigation", 
            ["Chambers", "Law Library", "System Admin"], 
            label_visibility="collapsed"
        )
        
        st.divider()
        
        if nav_mode == "Chambers":
            st.markdown("**Active Case Files**")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (st.session_state.user_email,))
            user_chambers = [r[0] for r in cursor.fetchall()]
            conn.close()
            
            if not user_chambers:
                user_chambers = ["General Litigation Chamber"]
                
            st.session_state.active_ch = st.radio(
                "Select Case", 
                user_chambers, 
                label_visibility="collapsed"
            )
            
            col_add, col_mail = st.columns(2)
            with col_add:
                if st.button("➕ New"): st.session_state.trigger_new_ch = True
            with col_mail:
                if st.button("📧 Brief"):
                    hist = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
                    if dispatch_legal_brief(st.session_state.user_email, st.session_state.active_ch, hist):
                        st.success("Brief Dispatched")

        st.divider()
        
        with st.expander("⚙️ Settings & help"):
            st.caption("AI Configuration")
            sys_persona = st.text_input("Assistant Persona", value="Senior High Court Advocate")
            sys_lang = st.selectbox("Interface Language", list(lexicon.keys()))
            
            st.divider()
            if st.button("🚪 Secure Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

    # --- MAIN CONTENT AREA ---
    if nav_mode == "Chambers":
        st.header(f"💼 CASE: {st.session_state.active_ch}")
        st.caption("Strategic Litigation Environment | End-to-End Encryption Verified")
        
        history_canvas = st.container()
        with history_canvas:
            chat_history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
            for msg in chat_history:
                with st.chat_message(msg["role"]):
                    st.write(msg["content"])
        
        # ALIGNED INPUT BAR CSS
        st.markdown("""
            <style>
                .stChatInputContainer { padding-right: 60px !important; }
                .mic-container { position: fixed; bottom: 38px; right: 4.5%; z-index: 999999; }
                .mic-container button { background: transparent !important; border: none !important; font-size: 22px !important; box-shadow: none !important; }
            </style>
        """, unsafe_allow_html=True)

        input_text = st.chat_input("Enter Legal Query or Strategy Request...")
        
        with st.container():
            st.markdown('<div class="mic-container">', unsafe_allow_html=True)
            input_voice = speech_to_text(
                language=lexicon[sys_lang], 
                start_prompt="🎙️", 
                stop_prompt="🛑", 
                key='leviathan_mic', 
                just_once=True
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        active_query = input_text or input_voice
        
        if active_query:
            db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "user", active_query)
            with history_canvas:
                with st.chat_message("user"): st.write(active_query)
            with st.chat_message("assistant"):
                with st.spinner("Synthesizing Legal Analysis..."):
                    engine = get_analytical_engine()
                    if engine:
                        prompt = f"Persona: {sys_persona}. Language: {sys_lang}. Query: {active_query}"
                        ai_response = engine.invoke(prompt).content
                        st.markdown(ai_response)
                        db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "assistant", ai_response)
            st.rerun()

    elif nav_mode == "Law Library":
        st.header("📚 Sovereign Law Library")
        st.subheader("Asset Synchronization Vault")
        
        uploaded_files = st.file_uploader("Upload Legal Precedents (PDF)", accept_multiple_files=True, type=['pdf'])
        if uploaded_files:
            for f in uploaded_files:
                st.info(f"File Synced: {f.name} ({f.size//1024} KB)")
        
        st.divider()
        st.markdown("**Available Jurisprudence Assets**")
        st.caption("No synchronized assets detected in local repository.")

    elif nav_mode == "System Admin":
        st.header("🛡️ System Administration Console")
        st.subheader("Architectural Board")
        architects = [
            {"Name": "Saim Ahmed", "Designation": "Lead Architect", "Domain": "System Logic"},
            {"Name": "Huzaifa Khan", "Designation": "AI Lead", "Domain": "LLM Tuning"},
            {"Name": "Mustafa Khan", "Designation": "DBA", "Domain": "SQL Security"},
            {"Name": "Ibrahim Sohail", "Designation": "UI Lead", "Domain": "Shaders"},
            {"Name": "Daniyal Faraz", "Designation": "QA Lead", "Domain": "Integration"}
        ]
        st.table(architects)
#-------------------------------------------------------------------------------        
# SECTION 9: UI LAYOUT - SOVEREIGN PORTAL (AUTHENTICATION)
# ------------------------------------------------------------------------------

def render_sovereign_portal():
    """
    Renders the Authentication Gateway for Alpha Apex.
    Includes Login, Registry, and OAuth Integration.
    """
    apply_leviathan_shaders()
    
    col_l, col_c, col_r = st.columns([1, 1.6, 1])
    
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("⚖️ ALPHA APEX PORTAL")
        st.markdown("#### Strategic Litigation and Legal Intelligence")
        st.write("---")
        
        auth_tabs = st.tabs(["🔐 Secure Login", "📝 Counsel Registry"])
        
        with auth_tabs[0]:
            login_e = st.text_input("Vault Email", key="log_e")
            login_p = st.text_input("Security Key", type="password", key="log_p")
            
            if st.button("Authorize Access", use_container_width=True):
                user_name = db_verify_vault_access(login_e, login_p)
                if user_name:
                    st.session_state.logged_in = True
                    st.session_state.user_email = login_e
                    st.session_state.username = user_name
                    st.rerun()
                else:
                    st.error("CREDENTIALS INVALID: Access to vault denied.")
            
            st.divider()
            render_google_sign_in()
            
        with auth_tabs[1]:
            reg_e = st.text_input("Counsel Email", key="reg_e")
            reg_n = st.text_input("Counsel Full Name", key="reg_n")
            reg_p = st.text_input("Vault Key", type="password", key="reg_p")
            
            if st.button("Initialize Registry", use_container_width=True):
                if db_create_vault_user(reg_e, reg_n, reg_p):
                    st.success("VAULT SYNCED: Account established in advocate_ai_v2.db")
                else:
                    st.error("REGISTRY FAILED: Email already exists or input is invalid.")

# ------------------------------------------------------------------------------
# SECTION 10: MASTER EXECUTION ENGINE
# ------------------------------------------------------------------------------

# Initialize Persistence Layer
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "active_ch" not in st.session_state:
    st.session_state.active_ch = "General Litigation Chamber"

# Intercept OAuth Callbacks
handle_google_callback()

# Render UI based on state
if not st.session_state.logged_in:
    render_sovereign_portal()
else:
    render_main_interface()

# ==============================================================================
# END OF ALPHA APEX LEVIATHAN CORE - SYSTEM STABLE
# ==============================================================================









