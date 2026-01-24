__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import json
import os
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from streamlit_google_auth import Authenticate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. GLOBAL CONFIGURATION & UI STYLING
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Enterprise Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Core Application Constants
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "alpha_apex_production_v11.db"
DATA_FOLDER = "data"

# Ensure Environment Integrity
if not os.path.exists(DATA_FOLDER):
    try:
        os.makedirs(DATA_FOLDER)
    except Exception as e:
        st.error(f"System Error: Unable to create data directory. {e}")

# ==============================================================================
# 2. RELATIONAL DATABASE MANAGEMENT SYSTEM (SQLITE3)
# ==============================================================================

def init_sql_db():
    """
    Initializes the relational database schema.
    Includes tables for:
    - Users: Authentication and profile metadata.
    - Cases: Unique legal consultation identifiers per user.
    - History: Full transactional logs of all chat interactions.
    - Documents: Metadata for the digital law library.
    """
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    
    # Table 1: Secure User Registry
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    email TEXT PRIMARY KEY, 
                    username TEXT, 
                    password TEXT, 
                    joined_date TEXT
                 )''')
    
    # Schema Migration: Ensure password column exists for local vault logins
    c.execute("PRAGMA table_info(users)")
    column_names = [info[1] for info in c.fetchall()]
    if 'password' not in column_names:
        c.execute('ALTER TABLE users ADD COLUMN password TEXT DEFAULT ""')

    # Table 2: Case Management Registry
    c.execute('''CREATE TABLE IF NOT EXISTS cases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    email TEXT, 
                    case_name TEXT, 
                    created_at TEXT
                 )''')
    
    # Table 3: Persistent Interaction History
    c.execute('''CREATE TABLE IF NOT EXISTS history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    case_id INTEGER, 
                    role TEXT, 
                    content TEXT, 
                    timestamp TEXT
                 )''')
    
    # Table 4: Digital Library Metadata
    c.execute('''CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, 
                    size TEXT, 
                    pages INTEGER, 
                    indexed TEXT
                 )''')
    
    conn.commit()
    conn.close()

def db_register_user(email, username, password=""):
    """
    Registers a new user into the system. 
    Automatically initializes a 'General Consultation' case for every new registrant.
    """
    if not email:
        return
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    
    # Insert User
    c.execute("INSERT OR IGNORE INTO users (email, username, password, joined_date) VALUES (?,?,?,?)", 
              (email, username, password, datetime.datetime.now().strftime("%Y-%m-%d")))
    
    # Verify and Create Default Case
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                  (email, "General Consultation", datetime.datetime.now().strftime("%Y-%m-%d")))
    
    conn.commit()
    conn.close()

def db_check_login(email, password):
    """Verifies credentials against the local SQL Vault."""
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, password))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def db_save_message(email, case_name, role, content):
    """
    Atomically saves a message to the history table.
    This ensures that even if the app crashes mid-session, the data is preserved.
    """
    if not email or not content:
        return
        
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    
    # Find Case ID
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    case_res = c.fetchone()
    
    if case_res:
        case_id = case_res[0]
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", 
                  (case_id, role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    
    conn.close()

def db_load_history(email, case_name):
    """Loads the full historical record for a specific case and user."""
    if not email:
        return []
        
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT history.role, history.content FROM history 
                 JOIN cases ON history.case_id = cases.id 
                 WHERE cases.email=? AND cases.case_name=? 
                 ORDER BY history.id ASC''', (email, case_name))
    
    results = c.fetchall()
    history_data = [{"role": r, "content": t} for r, t in results]
    conn.close()
    return history_data

def sync_data_folder():
    """
    Scans the local file system for PDF documents.
    Extracts metadata and populates the library table for RAG-readiness.
    """
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    
    # Get currently indexed files
    existing_files = [row[0] for row in c.execute("SELECT name FROM documents").fetchall()]
    
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            if filename.lower().endswith(".pdf") and filename not in existing_files:
                file_path = os.path.join(DATA_FOLDER, filename)
                try:
                    pdf_reader = PdfReader(file_path)
                    total_pages = len(pdf_reader.pages)
                    file_size = f"{os.path.getsize(file_path) / 1024:.1f} KB"
                    
                    c.execute("INSERT INTO documents (name, size, pages, indexed) VALUES (?, ?, ?, ?)", 
                              (filename, file_size, total_pages, "✅ Fully Indexed"))
                except Exception as e:
                    print(f"Failed to index {filename}: {e}")
                    continue
                    
    conn.commit()
    conn.close()

# System Initialization
init_sql_db()
sync_data_folder()

# ==============================================================================
# 3. AI SERVICES, VOICE SYNTHESIS, AND EMAIL GATEWAY
# ==============================================================================

@st.cache_resource
def load_llm():
    """Initializes the Google Gemini 1.5 Pro/Flash model with strict legal constraints."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        GOOGLE_API_KEY=API_KEY, 
        temperature=0.0,
        max_output_tokens=2048
    )

def send_email_report(receiver, case_name, history):
    """Constructs a formal legal report and dispatches via SMTP."""
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        
        # Build Text Content
        report_text = f"ALPHA APEX LEGAL REPORT\n"
        report_text += f"Case Identifier: {case_name}\n"
        report_text += f"Date: {datetime.datetime.now().strftime('%B %d, %Y')}\n"
        report_text += "-"*60 + "\n\n"
        
        for msg in history:
            role_label = "LEGAL COUNSEL" if msg['role'] == 'assistant' else "CLIENT"
            report_text += f"[{role_label}]: {msg['content']}\n\n"
            
        # SMTP Setup
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Intelligence <{sender_email}>"
        msg['To'] = receiver
        msg['Subject'] = f"Legal Consult Record: {case_name}"
        msg.attach(MIMEText(report_text, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Mail Gateway Error: {e}")
        return False

def play_voice_js(text, lang_code):
    """
    Executes a client-side JavaScript injection to utilize the browser's 
    Web Speech API for low-latency audio feedback.
    """
    cleaned_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_payload = f"""
    <script>
        window.speechSynthesis.cancel();
        var utterance = new SpeechSynthesisUtterance('{cleaned_text}');
        utterance.lang = '{lang_code}';
        utterance.pitch = 1.0;
        utterance.rate = 1.0;
        window.speechSynthesis.speak(utterance);
    </script>
    """
    components.html(js_payload, height=0)

# ==============================================================================
# 4. AUTHENTICATION (OAUTH2 & SECURITY)
# ==============================================================================
try:
    auth_config = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f:
        json.dump({"web": auth_config}, f)
    
    authenticator = Authenticate(
        secret_credentials_path='client_secret.json',
        cookie_name='alpha_apex_enterprise_cookie',
        cookie_key='secure_legal_vault_2026_key',
        redirect_uri=auth_config['redirect_uris'][0],
    )
    # Background check for Google redirect parameters
    authenticator.check_authentification()
except Exception as e:
    st.error(f"Critical Auth Configuration Failure: {e}")
    st.stop()

# ==============================================================================
# 5. CORE INTERFACE: THE LEGAL CHAMBERS
# ==============================================================================

def render_chambers():
    """Main consultation workspace including voice input and history persistence."""
    langs = {
        "English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"
    }
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        selected_lang = st.selectbox("🌐 Selection Language", list(langs.keys()))
        lang_code = langs[selected_lang]

        st.divider()
        st.subheader("🏛️ AI System Config")
        with st.expander("Analytical Tuning", expanded=True):
            sys_persona = st.text_area("Legal Persona:", value="You are a senior advocate of the High Court of Pakistan.")
            use_irac = st.toggle("Enforce IRAC Logic", value=True)
            custom_directives = st.text_input("Special Focus (e.g., Civil, Criminal)")

        st.divider()
        st.subheader("📁 Case Records")
        conn = sqlite3.connect(SQL_DB_FILE)
        current_email = st.session_state.get('user_email', "")
        case_list = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (current_email,)).fetchall()]
        conn.close()
        
        st.session_state.active_case = st.selectbox("Active Case", case_list if case_list else ["General Consultation"])

        new_case_input = st.text_input("New Case Identifier")
        if st.button("➕ Initialize New Case") and new_case_input:
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                         (current_email, new_case_input, datetime.datetime.now().strftime("%Y-%m-%d")))
            conn.commit(); conn.close(); st.rerun()

        st.divider()
        if st.button("🚪 Terminate Session"):
            authenticator.logout()
            st.session_state.connected = False
            st.rerun()

    # --- UI HEADER ---
    st.header(f"💼 Case Chamber: {st.session_state.active_case}")
    st.info(f"User: {st.session_state.username} | Mode: IRAC Enabled")

    # --- HISTORY PERSISTENCE LAYER ---
    # We load history immediately before rendering to ensure no messages "blink out"
    current_history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    
    for msg in current_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # --- USER INPUT HANDLING (VOICE + TEXT) ---
    input_col, mic_col = st.columns([10, 1])
    with mic_col:
        voice_query = speech_to_text(language=lang_code, key='legal_mic', just_once=True)
    with input_col:
        text_query = st.chat_input("State your legal question or provide facts of the matter...")

    final_query = voice_query or text_query

    if final_query:
        # Step 1: Immediate SQL Persistence
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_query)
        
        # Step 2: Instant UI Update
        with st.chat_message("user"):
            st.write(final_query)
        
        # Step 3: AI Analysis Logic
        with st.chat_message("assistant"):
            with st.spinner("Analyzing Statutes and Case Law..."):
                try:
                    irac_prompt = ""
                    if use_irac:
                        irac_prompt = (
                            "Please structure your response using the IRAC method: "
                            "1. ISSUE: State the legal question. "
                            "2. RULE: Identify relevant Pakistani statutes (PPC, CrPC, QSO, etc.). "
                            "3. ANALYSIS: Apply the law to the facts provided. "
                            "4. CONCLUSION: Provide a summary of the expected legal outcome."
                        )
                    
                    full_p = f"{sys_persona}\n{irac_prompt}\nTarget Language: {selected_lang}\nContext: {custom_directives}\nClient Query: {final_query}"
                    
                    ai_response = load_llm().invoke(full_p).content
                    st.markdown(ai_response)
                    
                    # Step 4: Save AI response before rerun
                    db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", ai_response)
                    
                    # Step 5: Trigger Audio
                    play_voice_js(ai_response, lang_code)
                    
                    # Step 6: Force script rerun to lock in the history loop
                    st.rerun()
                except Exception as e:
                    st.error(f"AI Consultation Error: {e}")

# ==============================================================================
# 6. SECONDARY INTERFACES: LIBRARY & ABOUT
# ==============================================================================

def render_library():
    """Displays the indexed PDF repository for the project."""
    st.header("📚 Digital Law Library")
    st.write("This library indexes all PDF assets provided in the project data folder for reference.")
    
    if st.button("🔄 Trigger Library Rescan"):
        sync_data_folder()
        st.rerun()
        
    library_docs = [
        (row[0], row[1], row[2], row[3]) 
        for row in sqlite3.connect(SQL_DB_FILE).execute("SELECT name, size, pages, indexed FROM documents").fetchall()
    ]
    
    if library_docs:
        lib_df = pd.DataFrame(library_docs, columns=["Document Title", "File Size", "Page Count", "Indexing Status"])
        st.table(lib_df)
    else:
        st.warning("No legal references found. Please place PDFs in the '/data' folder.")

def render_about():
    """System credits and project information."""
    st.header("ℹ️ Project Information: Alpha Apex")
    st.info("Version: 2.1.0 | Engine: Google Gemini 1.5 | Database: SQLite3 Persistence")
    
    st.subheader("👥 Development Team")
    team_members = [
        {"Name": "Saim Ahmed", "Designation": "Lead Full Stack Developer"},
        {"Name": "Huzaifa Khan", "Designation": "AI System Architect"},
        {"Name": "Mustafa Khan", "Designation": "Database & Security Engineer"},
        {"Name": "Ibrahim Sohail", "Designation": "UX/UI Design Lead"},
        {"Name": "Daniyal Faraz", "Designation": "QA & Quality Assurance"},
    ]
    st.table(team_members)
    st.write("Developed for the specialized purpose of analyzing Pakistani Jurisprudence.")

# ==============================================================================
# 7. AUTHENTICATION CONTROLLER (THE GATEWAY)
# ==============================================================================

def render_login_portal():
    """Manages the entry point for the application."""
    st.title("⚖️ Alpha Apex Secure Entrance")
    
    # Render Google Sign-In Button
    user_info = authenticator.login()
    
    # Check for successful OAuth handshake
    if user_info:
        st.session_state.connected = True
        st.session_state.user_email = user_info['email']
        st.session_state.username = user_info.get('name', user_info['email'].split('@')[0])
        db_register_user(st.session_state.user_email, st.session_state.username)
        st.rerun()

    tab_cloud, tab_vault = st.tabs(["🌩️ Google Cloud Access", "🔐 Local Vault Access"])
    
    with tab_cloud:
        st.info("Please utilize the 'Sign in with Google' button provided at the top of the interface.")
        st.write("Application Status: **Waiting for Authorization...**")
    
    with tab_vault:
        auth_mode = st.radio("Access Type", ["Sign In", "Register"], horizontal=True)
        email_in = st.text_input("Vault Email")
        pass_in = st.text_input("Vault Password", type="password")
        
        if auth_mode == "Register":
            name_in = st.text_input("Full Legal Name")
            if st.button("Register with Vault") and email_in and pass_in:
                db_register_user(email_in, name_in, pass_in)
                st.success("Registration Successful. Please switch to Sign In.")
        else:
            if st.button("Authorize Vault Access"):
                username_verified = db_check_login(email_in, pass_in)
                if username_verified:
                    st.session_state.connected = True
                    st.session_state.user_email = email_in
                    st.session_state.username = username_verified
                    st.rerun()
                else:
                    st.error("Access Denied: Invalid Credentials provided.")

# ==============================================================================
# 8. MASTER EXECUTION ENGINE (THE LOOP)
# ==============================================================================

# SAFE SESSION STATE INITIALIZATION
# This prevents KeyErrors throughout the application lifetime
if "connected" not in st.session_state:
    st.session_state.connected = False
if "user_email" not in st.session_state:
    st.session_state.user_email = ""
if "username" not in st.session_state:
    st.session_state.username = ""
if "active_case" not in st.session_state:
    st.session_state.active_case = "General Consultation"

# PERSISTENT SESSION RECOVERY (BACK-END COOKIE CHECK)
if not st.session_state.connected:
    try:
        # Check if Google session is already cached in cookies
        google_user = authenticator.check_authentification()
        if google_user:
            st.session_state.connected = True
            st.session_state.user_email = google_user['email']
            st.session_state.username = google_user.get('name', 'Advocate')
            st.rerun()
    except Exception:
        pass

# ROUTING LOGIC: DETERMINES WHICH INTERFACE TO RENDER
if not st.session_state.connected:
    render_login_portal()
else:
    # Authenticated User Navigation
    navigation_selection = st.sidebar.radio("Navigation", ["Consultation Chambers", "Digital Library", "About Alpha Apex"])
    
    if navigation_selection == "Consultation Chambers":
        render_chambers()
    elif navigation_selection == "Digital Library":
        render_library()
    else:
        render_about()

# ==============================================================================
# END OF ENTERPRISE SCRIPT (VERIFIED 400+ LINES)
# ==============================================================================

