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
# 1. INITIALIZATION & DATABASE FUNCTIONS (RESTORED)
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
    c.execute("""
        SELECT role, content FROM history 
        JOIN cases ON history.case_id = cases.id 
        WHERE cases.email=? AND cases.case_name=? 
        ORDER BY history.id ASC
    """, (email, case_name))
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
        msg['Subject'] = f"Case Summary: {case_name}"
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
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY, temperature=0.3)

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
# 3. PAGE RENDERING
# ==============================================================================

def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        if not cases:
            # Create a default case if none exists
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                         (st.session_state.user_email, "General Consultation", datetime.datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            cases = ["General Consultation"]

        st.session_state.active_case = st.selectbox("📁 Case File", cases)
        
        if st.button("📧 Email Chat History"):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.success("Sent!")

    st.header(f"💼 Chambers: {st.session_state.active_case}")
    
    # Quick Actions
    c1, c2, c3 = st.columns(3)
    quick_q = None
    if c1.button("🧠 Infer Path"): quick_q = "What is the recommended legal path forward?"
    if c2.button("📜 Ruling"): quick_q = "Give a preliminary legal observation."
    if c3.button("📝 Summarize"): quick_q = "Summarize the facts of this case."

    st.divider()

    # History Display
    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for m in history:
        with st.chat_message(m["role"]): st.write(m["content"])

    # Inputs
    m_col, i_col = st.columns([1, 8])
    with m_col:
        voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col:
        text_in = st.chat_input("Consult Alpha Apex...")

    query = quick_q or voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        with st.chat_message("user"): st.write(query)
        
        prompt = f"Expert Pakistani Lawyer. Respond in {target_lang}. Query: {query}"
        response = load_llm().invoke(prompt).content
        
        with st.chat_message("assistant"):
            st.write(response)
            db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
            play_voice_js(response, lang_code)
            st.rerun()

def render_library():
    st.header("📚 Legal Library")
    st.info("Browse Pakistan Penal Code (PPC), Constitution, and Case Law.")
    st.markdown("### Major Statutes\n1. **PPC 1860**\n2. **CrPC 1898**\n3. **Qanoon-e-Shahadat 1984**")

def render_about():
    st.header("ℹ️ About Alpha Apex")
    st.success("AI-Powered Legal Intelligence System for Sindh & Pakistan.")
    st.write("Developed to bridge the gap between complex law and accessible justice.")

# ==============================================================================
# 4. MAIN APP FLOW
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex AI Login")
    email = st.text_input("Login with Email")
    if st.button("Start Consultation"):
        if "@" in email:
            st.session_state.logged_in = True
            st.session_state.user_email = email
            # Ensure user exists in DB
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("INSERT OR IGNORE INTO users (email, username, joined_date) VALUES (?,?,?)", 
                         (email, email.split("@")[0], datetime.datetime.now().strftime("%Y-%m-%d")))
            conn.commit()
            conn.close()
            st.rerun()
else:
    page = st.sidebar.radio("Navigation", ["Chambers", "Legal Library", "About"])
    if page == "Chambers": render_chambers()
    elif page == "Legal Library": render_library()
    else: render_about()
