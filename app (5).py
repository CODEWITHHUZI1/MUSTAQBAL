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

API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "alpha_apex_production_v11.db"
DATA_FOLDER = "DATA"

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER, exist_ok=True)

# ==============================================================================
# 2. RELATIONAL DATABASE MANAGEMENT SYSTEM
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
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    case_res = c.fetchone()
    if case_res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", (case_res[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    conn.close()

def db_load_history(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT history.role, history.content FROM history JOIN cases ON history.case_id = cases.id WHERE cases.email=? AND cases.case_name=? ORDER BY history.id ASC''', (email, case_name))
    results = c.fetchall()
    conn.close()
    return [{"role": r, "content": t} for r, t in results]

init_sql_db()

# ==============================================================================
# 3. AI & EMAIL SERVICES
# ==============================================================================
def send_email_report(receiver, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"].replace(" ", "")
        report_text = f"ALPHA APEX LEGAL REPORT\nCase: {case_name}\nDate: {datetime.datetime.now().strftime('%B %d, %Y')}\n" + "-"*40 + "\n\n"
        for msg in history:
            role = "LEGAL COUNSEL" if msg['role'] == 'assistant' else "CLIENT"
            report_text += f"[{role}]: {msg['content']}\n\n"
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

@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", GOOGLE_API_KEY=API_KEY, temperature=0.0)

def play_voice_js(text, lang_code):
    cleaned = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    components.html(f"<script>window.speechSynthesis.cancel(); var u = new SpeechSynthesisUtterance('{cleaned}'); u.lang = '{lang_code}'; window.speechSynthesis.speak(u);</script>", height=0)

# ==============================================================================
# 4. AUTHENTICATION
# ==============================================================================
try:
    auth_config = dict(st.secrets["google_auth"])
    with open('client_secret.json', 'w') as f: json.dump({"web": auth_config}, f)
    authenticator = Authenticate(secret_credentials_path='client_secret.json', cookie_name='alpha_apex_cookie', cookie_key='secure_key_2026', redirect_uri=auth_config['redirect_uris'][0])
    authenticator.check_authentification()
except Exception as e:
    st.error(f"Auth Failure: {e}"); st.stop()

# ==============================================================================
# 5. CORE INTERFACE
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK"}
    
    # Header with Email
    h_col, e_col = st.columns([8, 2])
    with h_col: st.header(f"💼 {st.session_state.active_case}")
    with e_col:
        if st.button("📧 Email Report", use_container_width=True):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if hist and send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.toast("Report Sent!", icon="✅")

    # Chat
    current_history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for msg in current_history:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    # Input
    input_col, mic_col = st.columns([10, 1])
    with mic_col: voice_query = speech_to_text(language="en-US", key='legal_mic', just_once=True)
    with input_col: text_query = st.chat_input("Ask a legal question...")
    
    final_query = voice_query or text_query
    if final_query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_query)
        with st.chat_message("user"): st.write(final_query)
        with st.chat_message("assistant"):
            response = load_llm().invoke(f"Advocate of Pakistan. Query: {final_query}").content
            st.markdown(response)
            db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
            st.rerun()

def render_login_portal():
    st.title("⚖️ Alpha Apex Entrance")
    user_info = authenticator.login()
    if user_info:
        st.session_state.connected = True
        st.session_state.user_email = user_info['email']
        st.session_state.username = user_info.get('name', 'Advocate')
        db_register_user(st.session_state.user_email, st.session_state.username)
        st.rerun()

# ==============================================================================
# 6. MASTER EXECUTION & REORGANIZED SIDEBAR
# ==============================================================================
if "connected" not in st.session_state: st.session_state.connected = False
if "user_email" not in st.session_state: st.session_state.user_email = ""
if "active_case" not in st.session_state: st.session_state.active_case = "General Consultation"

if not st.session_state.connected:
    render_login_portal()
else:
    # --- REORGANIZED SIDEBAR (MOVED UPWARDS) ---
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        
        # 1. Appearance (Top)
        st.subheader("🎨 Appearance")
        theme_options = ["Crystal (Light)", "Slate (Muted)", "Obsidian (Dark)", "Midnight (Deep Dark)"]
        selected_theme = st.selectbox("Select Shade", theme_options, index=theme_options.index(st.session_state.current_theme))
        if selected_theme != st.session_state.current_theme:
            st.session_state.current_theme = selected_theme
            st.rerun()
            
        st.divider()

        # 2. Case Records (Middle)
        st.subheader("📁 Case Records")
        conn = sqlite3.connect(SQL_DB_FILE)
        case_list = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        st.session_state.active_case = st.selectbox("Active Case", case_list if case_list else ["General Consultation"])
        
        new_case = st.text_input("New Case ID")
        if st.button("➕ Initialize") and new_case:
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (st.session_state.user_email, new_case, datetime.datetime.now().strftime("%Y-%m-%d")))
            conn.commit(); conn.close(); st.rerun()

        st.divider()

        # 3. Navigation
        nav = st.radio("Navigation", ["Consultation Chambers", "Law Library", "About Alpha Apex"])
        
        st.divider()
        if st.button("🚪 Logout"):
            authenticator.logout(); st.session_state.connected = False; st.rerun()

    # Routing
    if nav == "Consultation Chambers": render_chambers()
    elif nav == "Digital Library": st.header("📚 Library")
    else: 
        st.header("ℹ️ About")
        st.table([
            {"Name": "Saim Ahmed", "Designation": "Lead Developer", "Email": "saimahmed@example.com"},
            {"Name": "Huzaifa Khan", "Designation": "AI Architect", "Email": "m.huzaifa.khan471@gmail.com"},
            {"Name": "Ibrahim Sohail", "Designation": "Presentation Lead", "Email": "ibrahimsohailkhan10@gmail.com"},
            {"Name": "Daniyal Faraz", "Designation": "Debugger", "Email": "daniyalfarazkhan2012@gmail.com"},
            {"Name": "Muhammad Mustafa Khan", "Designation": "Prompt Engineer", "Email": "muhammadmustafakhan430@gmail.com"}
        ])

