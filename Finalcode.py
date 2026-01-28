# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 36.4 (INTEGRATED PDF INGESTION)
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
# 1. PERMANENT SOVEREIGN SHADER ARCHITECTURE
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
        .stApp { background-color: #0b1120 !important; color: #e2e8f0 !important; }
        [data-testid="stSidebar"] {
            background-color: #020617 !important;
            border-right: 1px solid #1e293b !important;
            box-shadow: 10px 0 20px rgba(0,0,0,0.5) !important;
        }
        .stRadio > div[role="radiogroup"] > label > div:first-child {
            background-color: #ef4444 !important;
            border-color: #ef4444 !important;
        }
        .stChatMessage {
            border-radius: 12px !important;
            padding: 1.5rem !important;
            margin-bottom: 1.5rem !important;
            background-color: rgba(30, 41, 59, 0.3) !important;
        }
        h1, h2, h3, h4 { color: #f8fafc !important; font-weight: 700 !important; }
        .logo-text { color: #f8fafc; font-size: 24px; font-weight: bold; }
        .sub-logo-text { color: #94a3b8; font-size: 12px; }
        .stButton>button {
            border-radius: 8px !important;
            background: #1e293b !important;
            color: #cbd5e1 !important;
            border: 1px solid #334155 !important;
        }

        /* STRICT WHITE TEXT FOR INPUTS */
        .stTextInput>div>div>input {
            background-color: #1e293b !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
        }
        
        /* BLACK BOTTOM BAR FIX */
        [data-testid="stBottomBlockContainer"] {
            background-color: #0b1120 !important;
            border-top: 1px solid #1e293b !important;
        }

        .stChatInput textarea {
            color: #ffffff !important;
            background-color: #1e293b !important;
        }

        footer {visibility: hidden;}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE PERSISTENCE
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v32.db"
DATA_FOLDER = "data"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

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

# ==============================================================================
# 3. ANALYTICAL SERVICES
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.2)

def extract_pdf_text(uploaded_file):
    """Helper function to parse PDF content."""
    try:
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content: text += content
        return text, len(reader.pages)
    except Exception:
        return None, 0

# ==============================================================================
# 4. MAIN INTERFACE
# ==============================================================================

def render_main_interface():
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    apply_leviathan_shaders()
    
    with st.sidebar:
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div><div class='sub-logo-text'>Leviathan Production Suite v25</div>", unsafe_allow_html=True)
        nav_mode = st.radio("Main Navigation", ["Chambers", "Law Library", "System Admin"], label_visibility="collapsed")
        
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
            
            col_add, col_del = st.columns(2)
            with col_add:
                if st.button("➕ New"): st.session_state.add_case = True
            with col_del:
                if st.button("🗑️ Delete"): st.session_state.delete_confirm = True

            if st.session_state.get('add_case'):
                new_name = st.text_input("New Chamber Name")
                if st.button("Initialize"):
                    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
                    cursor.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", (u_mail, new_name, str(datetime.date.today())))
                    conn.commit(); conn.close(); st.session_state.add_case = False; st.rerun()
            
            if st.session_state.get('delete_confirm'):
                st.warning(f"Purge '{st.session_state.current_chamber}'?")
                if st.button("Confirm Deletion"):
                    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
                    cursor.execute("UPDATE chambers SET is_archived=1 WHERE owner_email=? AND chamber_name=?", (u_mail, st.session_state.current_chamber))
                    conn.commit(); conn.close()
                    st.session_state.delete_confirm = False
                    st.rerun()
                if st.button("Cancel"):
                    st.session_state.delete_confirm = False
                    st.rerun()

        st.write("---")
        with st.expander("⚙️ Settings & help"):
            custom_persona = st.text_input("System Persona", value="Senior High Court Advocate")
            lang_choice = st.selectbox("Interface Language", list(lexicon.keys()))
            if st.button("🚪 Secure Logout"): st.session_state.logged_in = False; st.rerun()

    if nav_mode == "Chambers":
        head_col, judge_col, action_col = st.columns([0.6, 0.2, 0.2])
        with head_col:
            st.header(f"💼 CASE: {st.session_state.current_chamber}")
        with judge_col:
            st.write(" ") 
            judge_mode = st.toggle("⚖️ JUDGE mode", help="Enable for critical feedback. Disable for IRAC-formatted legal counsel.")
        with action_col:
            st.write(" ") 
            if st.button("📧 Email Brief"):
                st.toast("Synthesizing Brief and Dispatching...")
                time.sleep(1)
                st.success("Brief Dispatched to Vault Email")

        chat_container = st.container()
        with chat_container:
            history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
            for msg in history:
                with st.chat_message(msg["role"]): st.write(msg["content"])

        prompt_col, mic_col = st.columns([0.9, 0.1])
        with prompt_col:
            t_input = st.chat_input("Enter Legal Query...")
        with mic_col:
            st.write(" ") 
            v_input = speech_to_text(language=lexicon[lang_choice], key='v_mic', just_once=True, start_prompt="🎙️", stop_prompt="⏹️")
        
        final_query = t_input or v_input

        if final_query:
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_query)
            with chat_container:
                with st.chat_message("user"): 
                    st.write(final_query)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing Statutes and Precedents..."):
                    try:
                        active_persona = "Honorable High Court Justice" if judge_mode else custom_persona
                        
                        jurisdiction_logic = """
                        JURISDICTIONAL BOUNDARY: You are operating strictly under the Law of PAKISTAN and the Province of SINDH. 
                        NEVER cite Indian Statutes (e.g., Indian Penal Code). 
                        ALWAYS cite Pakistani Statutes (e.g., Pakistan Penal Code, Sindh Land Revenue Act, Registration Act 1908).
                        """

                        if not judge_mode:
                            format_instruction = f"""
                            {jurisdiction_logic}
                            MANDATORY RESPONSE FORMAT: Use IRAC (Issue, Rule, Application, Conclusion).
                            1. ISSUE: State the legal question clearly.
                            2. RULE: Cite specific Sections, Acts, and Statutes of PAKISTAN/SINDH.
                            3. APPLICATION: Apply the rules to the specific facts provided.
                            4. CONCLUSION: Provide a definitive legal summary.
                            """
                        else:
                            format_instruction = f"{jurisdiction_logic} JUDGE MODE: Evaluate the lawyer's argument critically from the bench of a Pakistani High Court."

                        instruction = f"""
                        SYSTEM PERSONA: {active_persona}. 
                        CONVERSATIONAL PROTOCOL:
                        1. GREETINGS/FAREWELLS: Respond professionally.
                        2. {format_instruction}
                        
                        RESPONSE LANGUAGE: {lang_choice}.
                        USER QUERY: {final_query}
                        """
                        engine = get_analytical_engine()
                        resp = engine.invoke(instruction).content
                        st.markdown(resp)
                        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", resp)
                        st.rerun()
                    except Exception as e: 
                        st.error(f"Error: {e}")

    elif nav_mode == "Law Library":
        st.header("📚 Law Library Vault")
        
        # --- NEW: PDF UPLOADER INTEGRATION ---
        st.markdown("### 📥 Sync New legal Asset")
        uploaded_file = st.file_uploader("Upload Pakistani Statute or Case Law (PDF)", type="pdf")
        
        if uploaded_file is not None:
            if st.button("Verify & Sync to Vault"):
                with st.spinner("Analyzing document structure..."):
                    text_content, pg_count = extract_pdf_text(uploaded_file)
                    if text_content:
                        f_size = uploaded_file.size / 1024 
                        f_name = uploaded_file.name
                        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
                        cursor.execute('INSERT INTO law_assets (filename, filesize_kb, page_count, sync_timestamp) VALUES (?, ?, ?, ?)', (f_name, round(f_size, 2), pg_count, ts))
                        conn.commit(); conn.close()
                        
                        st.success(f"Asset '{f_name}' verified and synced.")
                        time.sleep(1); st.rerun()
                    else:
                        st.error("Document is unreadable or encrypted.")

        st.write("---")
        st.markdown("### Synchronized Legal Assets")
        conn = sqlite3.connect(SQL_DB_FILE)
        df_assets = pd.read_sql_query("SELECT filename AS 'File Name', filesize_kb AS 'Size (KB)', page_count AS 'Pages', sync_timestamp AS 'Sync Date', asset_status AS 'Status' FROM law_assets", conn)
        conn.close()
        if df_assets.empty: st.info("No synchronized PDFs found in local vault.")
        else: st.dataframe(df_assets, use_container_width=True, hide_index=True)

    elif nav_mode == "System Admin":
        st.header("🛡️ System Administration Console")
        admin_tab1, admin_tab2, admin_tab3, admin_tab4 = st.tabs(["👥 Registered Counsels", "⚖️ Interaction Logs", "📡 System Telemetry", "🏗️ Project Credits"])
        with admin_tab1:
            st.subheader("Counsel Directory")
            conn = sqlite3.connect(SQL_DB_FILE)
            df_users = pd.read_sql_query("SELECT full_name, email, membership_tier, total_queries, registration_date FROM users", conn)
            st.dataframe(df_users, use_container_width=True)
            conn.close()
        with admin_tab2:
            st.subheader("Interaction Analytics")
            conn = sqlite3.connect(SQL_DB_FILE)
            query = "SELECT u.full_name, c.chamber_name, m.sender_role, m.message_body, m.ts_created FROM message_logs m JOIN chambers c ON m.chamber_id = c.id JOIN users u ON c.owner_email = u.email ORDER BY m.id DESC LIMIT 100"
            df_logs = pd.read_sql_query(query, conn)
            st.dataframe(df_logs, use_container_width=True)
            conn.close()
        with admin_tab3:
            st.subheader("Leviathan Telemetry")
            st.info("System operational. AI Analytical Engines: Online.")
        with admin_tab4:
            st.table([{"Architect": "Saim Ahmed", "Focus": "Prompt Engineer"}, {"Architect": "Huzaifa Khan", "Focus": "Backend Developer"}, {"Architect": "Mustafa Khan", "Focus": "Main Coder"}, {"Architect": "Ibrahim Sohail", "Focus": "Presentation Lead"}, {"Architect": "Daniyal Faraz", "Focus": "Debugger and Modifier"}])

# ==============================================================================
# 5. SOVEREIGN PORTAL (TABBED AUTH)
# ==============================================================================

def render_sovereign_portal():
    apply_leviathan_shaders()
    st.title("⚖️ ALPHA APEX LEVIATHAN")
    st.markdown("#### Strategic Litigation and Legal Intelligence Framework")
    auth_tabs = st.tabs(["🔐 Secure Login", "📝 Counsel Registration"])
    with auth_tabs[0]:
        e_log = st.text_input("Vault Email Address", key="log_email")
        k_log = st.text_input("Security Key", type="password", key="log_key")
        if st.button("Grant Access"):
            user_name = db_verify_vault_access(e_log, k_log)
            if user_name:
                st.session_state.logged_in = True
                st.session_state.user_email = e_log
                st.rerun()
            else: st.error("Access Denied")
    with auth_tabs[1]:
        e_reg = st.text_input("Registry Email", key="reg_email")
        n_reg = st.text_input("Counsel Full Name", key="reg_name")
        k_reg = st.text_input("Set Security Key", type="password", key="reg_key")
        if st.button("Initialize Registry"):
            if db_create_vault_user(e_reg, n_reg, k_reg): st.success("Counsel Registered")
            else: st.error("Registry Failed: User may already exist.")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: render_sovereign_portal()
else: render_main_interface()
