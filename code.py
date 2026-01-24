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
# 1. SYSTEM CONFIG & DATABASE
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")
API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "advocate_ai_v3.db"

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, joined_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

def db_save_message(email, case_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    res = c.fetchone()
    if res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", (res[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def db_load_history(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, content FROM history JOIN cases ON history.case_id = cases.id WHERE cases.email=? AND cases.case_name=? ORDER BY history.id ASC", (email, case_name))
    data = [{"role": r, "content": t} for r, t in c.fetchall()]
    conn.close()
    return data

init_sql_db()

# ==============================================================================
# 2. EMAIL & UTILITY FUNCTIONS
# ==============================================================================
def send_email_report(receiver_email, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        
        report_content = f"Legal Consultation Report: {case_name}\n"
        report_content += "="*30 + "\n\n"
        for m in history:
            role = "Counsel" if m['role'] == 'assistant' else "Client"
            report_content += f"[{role}]: {m['content']}\n\n"

        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Legal AI <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = f"Case Summary: {case_name}"
        msg.attach(MIMEText(report_content, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.sidebar.error(f"Email Error: {e}")
        return False

@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=API_KEY, 
        temperature=0.3,
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )

ai_engine = load_llm()

def play_voice_js(text, lang_code):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            msg.lang = '{lang_code}';
            window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

# ==============================================================================
# 3. CHAMBERS INTERFACE
# ==============================================================================
def render_chambers_page():
    # Focused Pakistani Languages
    langs = {
        "English": "en-US",
        "Urdu (اردو)": "ur-PK",
        "Sindhi (سنڌي)": "sd-PK",
        "Punjabi (پنجابی)": "pa-PK",
        "Pashto (پښتو)": "ps-PK",
        "Balochi (بلوچی)": "bal-PK"
    }
    
    with st.sidebar:
        st.title("👨‍⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Choose Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        st.divider()
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        if not cases: cases = ["General Consultation"]
        st.session_state.active_case = st.selectbox("Active Case File", cases)
        
        st.divider()
        if st.button("📧 Extract & Email Conversation"):
            history = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if history:
                with st.spinner("Sending report..."):
                    if send_email_report(st.session_state.user_email, st.session_state.active_case, history):
                        st.sidebar.success("✅ Sent to your email!")
            else:
                st.sidebar.warning("No history found.")

    # --- QUICK ACTIONS ON TOP ---
    st.header(f"💼 Case: {st.session_state.active_case}")
    
    q_col1, q_col2, q_col3 = st.columns(3)
    quick_q = None
    if q_col1.button("🧠 Infer Legal Path"): quick_q = "What is the recommended legal path forward?"
    if q_col2.button("📜 Give Ruling"): quick_q = "Give a preliminary observation on these facts."
    if q_col3.button("📝 Summarize"): quick_q = "Summarize the legal history of this case."
    
    st.divider()

    # Chat Display
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]): st.write(m["content"])

    # Bottom Input
    m_col, i_col = st.columns([1, 8])
    with m_col:
        voice_in = speech_to_text(language=lang_code, key='mic_input', just_once=True)
    with i_col:
        text_in = st.chat_input(f"Consult in {target_lang}...")

    user_query = quick_q or voice_in or text_in
    if user_query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", user_query)
        with st.chat_message("user"): st.write(user_query)
        
        prompt = f"Expert Pakistani Lawyer. Respond ONLY in {target_lang}. Query: {user_query}"
        
        try:
            with st.chat_message("assistant"):
                response = ai_engine.invoke(prompt).content
                st.write(response)
                db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
                play_voice_js(response, lang_code)
                st.rerun()
        except Exception as e:
            st.error(f"AI Error: {e}")

# ==============================================================================
# 4. MAIN EXECUTION
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex AI Login")
    email = st.text_input("Enter Email to start")
    if st.button("Login"):
        if "@" in email:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (email, email.split("@")[0], datetime.datetime.now().strftime("%Y-%m-%d")))
            conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General Consultation", datetime.datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.rerun()
else:
    render_chambers_page()
