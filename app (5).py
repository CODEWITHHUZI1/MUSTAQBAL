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

# --- THEME ENGINE ---
def apply_custom_theme(theme_choice):
    themes = {
        "Crystal (Light)": {"bg": "#FFFFFF", "sidebar": "#F8F9FA", "text": "#1E1E1E", "accent": "#007BFF"},
        "Slate (Muted)": {"bg": "#E2E8F0", "sidebar": "#CBD5E1", "text": "#334155", "accent": "#6366F1"},
        "Obsidian (Dark)": {"bg": "#1A202C", "sidebar": "#2D3748", "text": "#F7FAFC", "accent": "#6366F1"},
        "Midnight (Deep Dark)": {"bg": "#0F172A", "sidebar": "#020617", "text": "#F8FAFC", "accent": "#38BDF8"}
    }
    t = themes[theme_choice]
    theme_css = f"""
    <style>
        .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
        [data-testid="stSidebar"] {{ background-color: {t['sidebar']}; }}
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {{ color: {t['text']} !important; }}
        .stButton>button {{ background-color: {t['accent']}; color: white !important; border-radius: 8px; }}
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {{ background-color: {t['sidebar']}; color: {t['text']}; }}
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

if "current_theme" not in st.session_state:
    st.session_state.current_theme = "Obsidian (Dark)"

apply_custom_theme(st.session_state.current_theme)

# Core Application Constants
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "alpha_apex_production_v11.db"
DATA_FOLDER = "DATA"

if not os.path.exists(DATA_FOLDER):
    try:
        os.makedirs(DATA_FOLDER)
    except Exception as e:
        st.error(f"System Error: Unable to create data directory. {e}")

# ==============================================================================
# 2. RELATIONAL DATABASE MANAGEMENT SYSTEM (SQLITE3)
# ==============================================================================

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, password TEXT, joined_date TEXT)''')
    c.execute("PRAGMA table_info(users)")
    if 'password' not in [info[1] for info in c.fetchall()]:
        c.execute('ALTER TABLE users ADD COLUMN password TEXT DEFAULT ""')
    c.execute('''CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS documents (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, size TEXT, pages INTEGER, indexed TEXT)''')
    conn.commit()
    conn.close()

def db_register_user(email, username, password=""):
    if not email: return
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (email, username, password, joined_date) VALUES (?,?,?,?)", (email, username, password, datetime.datetime.now().strftime("%Y-%m-%d")))
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General Consultation", datetime.datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_check_login(email, password):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT username FROM users WHERE email=? AND password=?", (email, password))
    res = c.fetchone()
    conn.close()
    return res[0] if res else None

def db_save_message(email, case_name, role, content):
    if not email or not content: return
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    case_res = c.fetchone()
    if case_res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", (case_res[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    conn.close()

def db_load_history(email, case_name):
    if not email: return []
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT history.role, history.content FROM history JOIN cases ON history.case_id = cases.id WHERE cases.email=? AND cases.case_name=? ORDER BY history.id ASC''', (email, case_name))
    results = c.fetchall()
    conn.close()
    return [{"role": r, "content": t} for r, t in results]

def sync_data_folder():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    existing_files = [row[0] for row in c.execute("SELECT name FROM documents").fetchall()]
    if os.path.exists(DATA_FOLDER):
        for filename in os.listdir(DATA_FOLDER):
            if filename.lower().endswith(".pdf") and filename not in existing_files:
                try:
                    pdf_reader = PdfReader(os.path.join(DATA_FOLDER, filename))
                    c.execute("INSERT INTO documents (name, size, pages, indexed) VALUES (?, ?, ?, ?)", (filename, f"{os.path.getsize(os.path.join(DATA_FOLDER, filename)) / 1024:.1f} KB", len(pdf_reader.pages), "✅ Fully Indexed"))
                except: continue
    conn.commit()
    conn.close()

init_sql_db()
sync_data_folder()

# ==============================================================================
# 3. AI SERVICES, VOICE SYNTHESIS, AND EMAIL GATEWAY
# ==============================================================================

@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", GOOGLE_API_KEY=API_KEY, temperature=0.0, max_output_tokens=2048)

def send_email_report(receiver, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        report_text = f"ALPHA APEX LEGAL REPORT\nCase Identifier: {case_name}\nDate: {datetime.datetime.now().strftime('%B %d, %Y')}\n" + "-"*60 + "\n\n"
        for msg in history:
            role_label = "LEGAL COUNSEL" if msg['role'] == 'assistant' else "CLIENT"
            report_text += f"[{role_label}]: {msg['content']}\n\n"
        msg = MIMEMultipart(); msg['From'] = f"Alpha Apex Intelligence <{sender_email}>"; msg['To'] = receiver; msg['Subject'] = f"Legal Consult Record: {case_name}"
        msg.attach(MIMEText(report_text, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(sender_email, sender_password); server.send_message(msg); server.quit()
        return True
    except Exception as e:
        st.error(f"Mail Gateway Error: {e}"); return False

def play_voice_js(text, lang_code):
    cleaned_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    components.html(f"<script>window.speechSynthesis.cancel(); var utterance = new SpeechSynthesisUtterance('{cleaned_text}'); utterance.lang = '{lang_code}'; window.speechSynthesis.speak(utterance);</script>", height=0)

# ==============================================================================
# 4. AUTHENTICATION (OAUTH2 & SECURITY)
# ==============================================================================
try:
    auth_config = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f: json.dump({"web": auth_config}, f)
    authenticator = Authenticate(secret_credentials_path='client_secret.json', cookie_name='alpha_apex_enterprise_cookie', cookie_key='secure_legal_vault_2026_key', redirect_uri=auth_config['redirect_uris'][0])
    authenticator.check_authentification()
except Exception as e:
    st.error(f"Critical Auth Configuration Failure: {e}"); st.stop()

# ==============================================================================
# 5. CORE INTERFACE: THE LEGAL CHAMBERS
# ==============================================================================

def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        selected_lang = st.selectbox("🌐 Selection Language", list(langs.keys())); lang_code = langs[selected_lang]
        st.divider(); st.subheader("🏛️ AI System Config")
        with st.expander("Analytical Tuning", expanded=True):
            sys_persona = st.text_area("Legal Persona:", value="You are a senior advocate of the High Court of Pakistan.")
            use_irac = st.toggle("Enforce IRAC Logic", value=True)
            custom_directives = st.text_input("Special Focus (e.g., Civil, Criminal)")
        st.divider(); st.subheader("📁 Case Records")
        conn = sqlite3.connect(SQL_DB_FILE); current_email = st.session_state.get('user_email', "")
        case_list = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (current_email,)).fetchall()]; conn.close()
        st.session_state.active_case = st.selectbox("Active Case", case_list if case_list else ["General Consultation"])
        new_case_input = st.text_input("New Case Identifier")
        if st.button("➕ Initialize New Case") and new_case_input:
            conn = sqlite3.connect(SQL_DB_FILE); conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (current_email, new_case_input, datetime.datetime.now().strftime("%Y-%m-%d"))); conn.commit(); conn.close(); st.rerun()
        st.divider()
        if st.button("🚪 Terminate Session"): authenticator.logout(); st.session_state.connected = False; st.rerun()

    # --- UI HEADER WITH EMAIL INTEGRATION ---
    h_col, e_col = st.columns([8, 2])
    with h_col:
        st.header(f"💼 Case Chamber: {st.session_state.active_case}")
    with e_col:
        if st.button("📧 Email Transcript", use_container_width=True):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if hist and send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.toast("Report Sent Successfully!", icon="✅")
            elif not hist:
                st.toast("No history found for this case.", icon="⚠️")

    st.info(f"User: {st.session_state.username} | Mode: IRAC Enabled")

    current_history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for msg in current_history:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    input_col, mic_col = st.columns([10, 1])
    with mic_col: voice_query = speech_to_text(language=lang_code, key='legal_mic', just_once=True)
    with input_col: text_query = st.chat_input("State your legal question...")
    final_query = voice_query or text_query
    if final_query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_query)
        with st.chat_message("user"): st.write(final_query)
        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                try:
                    irac_prompt = "Please structure your response using the IRAC method (ISSUE, RULE, ANALYSIS, CONCLUSION)." if use_irac else ""
                    full_p = f"{sys_persona}\n{irac_prompt}\nTarget Language: {selected_lang}\nContext: {custom_directives}\nClient Query: {final_query}"
                    ai_response = load_llm().invoke(full_p).content
                    st.markdown(ai_response)
                    db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", ai_response)
                    play_voice_js(ai_response, lang_code)
                    st.rerun()
                except Exception as e: st.error(f"AI Consultation Error: {e}")

# ==============================================================================
# 6. SECONDARY INTERFACES & AUTH PORTAL
# ==============================================================================

def render_library():
    st.header("📚 Digital Law Library")
    if st.button("🔄 Trigger Library Rescan"): sync_data_folder(); st.rerun()
    library_docs = sqlite3.connect(SQL_DB_FILE).execute("SELECT name, size, pages, indexed FROM documents").fetchall()
    if library_docs: st.table(pd.DataFrame(library_docs, columns=["Document Title", "File Size", "Page Count", "Indexing Status"]))
    else: st.warning("No legal references found.")

def render_about():
    st.header("ℹ️ About Alpha Apex")
    st.info("Version: 2.1.0 | Engine: Google Gemini 1.5")
   st.table([
    {"Name": "Saim Ahmed", "Designation": "Lead Full Stack Developer", "Email": "saimahmed@example.com"}, 
    {"Name": "Huzaifa Khan", "Designation": "AI System Architect", "Email": "m.huzaifa.khan471@gmail.com"},
    {"Name": "Ibrahim Sohail", "Designation": "Presentation Lead", "Email": "ibrahimsohailkhan10@gmail.com"},
    {"Name": "Daniyal Faraz", "Designation": "Debugger", "Email": "daniyalfarazkhan2012@gmail.com"},
    {"Name": "Muhammad Mustafa Khan", "Designation": "Prompt Engineer", "Email": "muhammadmustafakhan430@gmail.com"}
])

def render_login_portal():
    st.title("⚖️ Alpha Apex Secure Entrance")
    user_info = authenticator.login()
    if user_info:
        st.session_state.connected, st.session_state.user_email = True, user_info['email']
        st.session_state.username = user_info.get('name', user_info['email'].split('@')[0])
        db_register_user(st.session_state.user_email, st.session_state.username); st.rerun()

    tab_cloud, tab_vault = st.tabs(["🌩️ Google Cloud Access", "🔐 Local Vault Access"])
    with tab_vault:
        auth_mode = st.radio("Access Type", ["Sign In", "Register"], horizontal=True)
        email_in, pass_in = st.text_input("Vault Email"), st.text_input("Vault Password", type="password")
        if auth_mode == "Register":
            name_in = st.text_input("Full Legal Name")
            if st.button("Register with Vault") and email_in and pass_in:
                db_register_user(email_in, name_in, pass_in); st.success("Registration Successful.")
        else:
            if st.button("Authorize Vault Access"):
                username_verified = db_check_login(email_in, pass_in)
                if username_verified:
                    st.session_state.connected, st.session_state.user_email, st.session_state.username = True, email_in, username_verified
                    st.rerun()
                else: st.error("Access Denied.")

# ==============================================================================
# 7. MASTER EXECUTION ENGINE
# ==============================================================================
if "connected" not in st.session_state: st.session_state.connected = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "username" not in st.session_state: st.session_state.username = ""
if "active_case" not in st.session_state: st.session_state.active_case = "General Consultation"

if not st.session_state.connected:
    try:
        google_user = authenticator.check_authentification()
        if google_user:
            st.session_state.connected, st.session_state.user_email, st.session_state.username = True, google_user['email'], google_user.get('name', 'Advocate')
            st.rerun()
    except: pass
    render_login_portal()
else:
    with st.sidebar:
        st.divider(); st.subheader("🎨 Appearance")
        theme_options = ["Crystal (Light)", "Slate (Muted)", "Obsidian (Dark)", "Midnight (Deep Dark)"]
        selected_theme = st.selectbox("Select Shade", theme_options, index=theme_options.index(st.session_state.current_theme))
        if selected_theme != st.session_state.current_theme:
            st.session_state.current_theme = selected_theme; st.rerun()
            
    navigation_selection = st.sidebar.radio("Navigation", ["Consultation Chambers", "Digital Library", "About Alpha Apex"])
    if navigation_selection == "Consultation Chambers": render_chambers()
    elif navigation_selection == "Digital Library": render_library()
    else: render_about()




