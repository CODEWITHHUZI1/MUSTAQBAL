__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. INITIALIZATION & DATABASE
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")
API_KEY = st.secrets["GEMINI_API_KEY"]
SQL_DB_FILE = "advocate_ai_v3.db"

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, joined_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

init_sql_db()

# ==============================================================================
# 2. CORE UTILITIES
# ==============================================================================
def send_email_report(receiver_email, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        report_content = f"Legal Report: {case_name}\n" + "="*30 + "\n\n"
        for m in history:
            role = "Counsel" if m['role'] == 'assistant' else "Client"
            report_content += f"[{role}]: {m['content']}\n\n"
        
        msg = MIMEMultipart(); msg['From'] = f"Alpha Apex <{sender_email}>"
        msg['To'] = receiver_email; msg['Subject'] = f"Case Summary: {case_name}"
        msg.attach(MIMEText(report_content, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls(); server.login(sender_email, sender_password)
        server.send_message(msg); server.quit()
        return True
    except Exception as e:
        st.error(f"Email Failed: {e}"); return False

@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY, temperature=0.3)

def play_voice_js(text, lang_code):
    """Fixed JS TTS injection"""
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
        <script>
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            msg.lang = '{lang_code}';
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

# ==============================================================================
# 3. PAGE RENDERING
# ==============================================================================

def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    # Sidebar Nav (Restored)
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        st.session_state.active_case = st.selectbox("📁 Case File", cases if cases else ["General Consultation"])
        
        if st.button("📧 Email Chat History"):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.success("Sent!")

    # Top Quick Actions
    st.header(f"💼 Chambers: {st.session_state.active_case}")
    c1, c2, c3 = st.columns(3)
    quick_q = None
    if c1.button("🧠 Infer Path"): quick_q = "Recommended legal path?"
    if c2.button("📜 Ruling"): quick_q = "Preliminary observation?"
    if c3.button("📝 Summarize"): quick_q = "Summarize the case."

    # Chat Logic
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]): st.write(m["content"])

    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Consult...")

    query = quick_q or voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        with st.chat_message("user"): st.write(query)
        
        response = load_llm().invoke(f"Respond in {target_lang}: {query}").content
        with st.chat_message("assistant"):
            st.write(response)
            db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
            play_voice_js(response, lang_code) # Triggers TTS

def render_library():
    st.header("📚 Legal Library")
    st.info("Browse Pakistan Penal Code (PPC), Constitution, and Case Law.")
    st.write("Section 302: Punishment for Qatl-i-Amd...")

def render_about():
    st.header("ℹ️ About Alpha Apex")
    st.write("AI-Powered Legal Assistant for Pakistan.")

# ==============================================================================
# 4. MAIN APP FLOW
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    email = st.text_input("Login with Email")
    if st.button("Start"):
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.rerun()
else:
    # Sidebar Navigation Option (Restored)
    page = st.sidebar.radio("Navigation", ["Chambers", "Legal Library", "About"])
    if page == "Chambers": render_chambers()
    elif page == "Legal Library": render_library()
    else: render_about()
