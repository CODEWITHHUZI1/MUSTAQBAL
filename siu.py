__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import time
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

def db_save_message(email, case_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    res = c.fetchone()
    if res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", 
                  (res[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = f"Legal Summary: {case_name}"
        msg.attach(MIMEText(report_content, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email Failed: {e}")
        return False

@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=API_KEY, 
        temperature=0.3,
        max_retries=3,
        safety_settings={
            "HARM_CATEGORY_HARASSMENT": "BLOCK_NONE",
            "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE",
            "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE",
            "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE",
        }
    )

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
# 3. PAGES
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        st.divider()
        st.subheader("📁 Case Management")
        
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        if not cases: cases = ["General Consultation"]
        active_case = st.selectbox("Select Case", cases)
        st.session_state.active_case = active_case

        new_case_name = st.text_input("New Case Name")
        if st.button("➕ Create New Case"):
            if new_case_name:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (st.session_state.user_email, new_case_name, str(datetime.date.today())))
                conn.commit(); conn.close()
                st.rerun()

        rename_to = st.text_input("Rename Current Case to:")
        if st.button("✏️ Rename Case"):
            if rename_to and active_case:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("UPDATE cases SET case_name=? WHERE email=? AND case_name=?", (rename_to, st.session_state.user_email, active_case))
                conn.commit(); conn.close()
                st.rerun()

        if st.button("🗑️ Delete Current Case"):
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("DELETE FROM cases WHERE email=? AND case_name=?", (st.session_state.user_email, active_case))
            conn.commit(); conn.close()
            st.rerun()

        st.divider()
        if st.button("📧 Email Chat History"):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.success("Sent!")

    st.header(f"💼 Chambers: {st.session_state.active_case}")
    c1, c2, c3 = st.columns(3)
    quick_q = None
    if c1.button("🧠 Infer Legal Path"): quick_q = "What is the recommended legal path?"
    if c2.button("📜 Give Ruling"): quick_q = "Give a preliminary observation."
    if c3.button("📝 Summarize"): quick_q = "Summarize the case history."
    st.divider()

    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]): st.write(m["content"])

    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Consult Alpha Apex...")

    query = quick_q or voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        with st.chat_message("user"): st.write(query)
        
        with st.chat_message("assistant"):
            try:
                prompt = f"Expert Lawyer. Respond in {target_lang}. Query: {query}"
                response = load_llm().invoke(prompt).content
                st.write(response)
                db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
                play_voice_js(response, lang_code)
                st.rerun()
            except Exception as e:
                st.error(f"Error: {e}")

def render_library():
    st.header("📚 Legal Library")
    st.info("Browse Pakistan Penal Code (PPC) and Constitution.")

def render_about():
    st.header("ℹ️ About Alpha Apex")
    
    st.markdown("""
    ### 🤖 The Chatbot
    **Alpha Apex** is a specialized Legal AI Assistant designed for the Pakistani legal landscape. 
    It leverages advanced Large Language Models to provide instant preliminary legal observations, 
    summarize complex case facts, and offer procedural guidance based on the **Pakistan Penal Code (PPC)** and the **Constitution of Pakistan**. Available in multiple regional languages including Urdu, Sindhi, 
    Punjabi, Pashto, and Balochi.
    
    ---
    ### 👥 Our Team
    Meet the developers and legal tech enthusiasts behind Alpha Apex:
    """)

    team = [
        {"Name": "Saim Ahmed", "Contact": "03700297696", "Email": "saimahmed.work733@gmail.com"},
        {"Name": "Huzaifa Khan", "Contact": "03102526567", "Email": "m.huzaifa.khan471@gmail.com"},
        {"Name": "Mustafa Khan", "Contact": "03460222290", "Email": "muhammadmustafakhan430@gmail.com"},
        {"Name": "Ibrahim Sohail", "Contact": "03212046403", "Email": "ibrahimsohailkhan10@gmail.com"},
        {"Name": "Daniyal Faraz", "Contact": "03333502530", "Email": "daniyalfarazkhan2012@gmail.com"},
    ]

    st.table(team)

# ==============================================================================
# 4. MAIN FLOW
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    email = st.text_input("Enter Email")
    if st.button("Log In"):
        if "@" in email:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("INSERT OR IGNORE INTO users (email, username, joined_date) VALUES (?,?,?)", (email, email.split("@")[0], "2026-01-24"))
            conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General Consultation", "2026-01-24"))
            conn.commit(); conn.close()
            st.rerun()
else:
    page = st.sidebar.radio("Navigation", ["Chambers", "Legal Library", "About"])
    if page == "Chambers": render_chambers()
    elif page == "Legal Library": render_library()
    else: render_about()
