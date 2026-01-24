__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. INITIALIZATION & DATABASE
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")
API_KEY = st.secrets["GEMINI_API_KEY"]
SQL_DB_FILE = "advocate_ai_v5.db"

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
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
# 2. UTILITIES (Voice & Email)
# ==============================================================================
def play_voice_js(roman_text):
    safe_text = roman_text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <script>
        function speakNow() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            var voices = window.speechSynthesis.getVoices();
            var desiVoice = voices.find(v => v.lang.includes('ur')) || voices.find(v => v.lang.includes('hi')) || voices.find(v => v.lang.includes('en-IN'));
            if(desiVoice) {{ msg.voice = desiVoice; msg.lang = desiVoice.lang; }}
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        }}
        if (speechSynthesis.onvoiceschanged !== undefined) {{ speechSynthesis.onvoiceschanged = speakNow; }}
        speakNow();
    </script>
    """
    components.html(js_code, height=0)

def send_email_report(receiver_email, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        body = f"Legal Consultation Summary: {case_name}\n\n"
        for m in history:
            role = "Expert" if m['role'] == 'assistant' else "Client"
            content = m['content'].split("|||")[0]
            body += f"{role}: {content}\n\n"
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex <{sender_email}>"; msg['To'] = receiver_email
        msg['Subject'] = f"Case Report: {case_name}"; msg.attach(MIMEText(body, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
        server.login(sender_email, sender_password); server.send_message(msg); server.quit()
        return True
    except: return False

# ==============================================================================
# 3. CHAMBERS (WITH QUICK ACTIONS)
# ==============================================================================
def render_chambers():
    langs = {"Urdu": "ur-PK", "English": "en-US", "Sindhi": "sd-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Visual Language", list(langs.keys()))
        st.divider()
        st.subheader("🏛️ Configuration")
        with st.expander("Behavior", expanded=True):
            sys_persona = st.text_input("Persona:", value="You are a Pakistani Law Analyst.")
            use_irac = st.toggle("Enable IRAC", value=True)
        st.divider()
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        active_case = st.selectbox("Current Case", cases if cases else ["General"])
        st.session_state.active_case = active_case

    # Top Right Email Action
    h1, h2 = st.columns([8, 2])
    with h1: st.header(f"💼 Case: {active_case}")
    with h2: 
        if st.button("📧 Email Chat"):
            hist = db_load_history(st.session_state.user_email, active_case)
            if send_email_report(st.session_state.user_email, active_case, hist):
                st.success("Sent!")

    chat_container = st.container()
    
    # Quick Action Buttons
    st.write("### Quick Actions")
    q1, q2, q3 = st.columns(3)
    quick_query = None
    if q1.button("🔍 Infer Legal Context"): quick_query = "Please infer the legal implications of our last conversation."
    if q2.button("⚖️ Give Ruling/Opinion"): quick_query = "Based on Pakistani law, give a definitive ruling or opinion on this situation."
    if q3.button("📝 Summarize Case"): quick_query = "Summarize our entire discussion into a concise legal brief."

    st.divider()
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Type here...")

    history = db_load_history(st.session_state.user_email, active_case)
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"].split("|||")[0])

    final_query = voice_in or text_in or quick_query
    if final_query:
        db_save_message(st.session_state.user_email, active_case, "user", final_query)
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)
            prompt = f"{sys_persona} {'Use IRAC.' if use_irac else ''}\nReply in two parts separated by '|||'. Part 1: {target_lang} script. Part 2: Phonetic Roman Urdu.\nQuery: {final_query}"
            response = llm.invoke(prompt).content
            db_save_message(st.session_state.user_email, active_case, "assistant", response)
            st.rerun() 
        except Exception as e: st.error(f"Error: {e}")

    if history and history[-1]["role"] == "assistant":
        if "|||" in history[-1]["content"]:
            roman_part = history[-1]["content"].split("|||")[1]
            if st.session_state.get("last_spoken") != roman_part:
                play_voice_js(roman_part)
                st.session_state.last_spoken = roman_part

# ==============================================================================
# 4. NAVIGATION
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    email = st.text_input("Email")
    if st.button("Login"):
        st.session_state.logged_in = True; st.session_state.user_email = email
        conn = sqlite3.connect(SQL_DB_FILE)
        conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General", "2026-01-24"))
        conn.commit(); conn.close(); st.rerun()
else:
    page = st.sidebar.radio("Nav", ["Chambers", "Library", "About"])
    if page == "Chambers": render_chambers()
    elif page == "Library": st.header("📚 Library")
    else: st.header("ℹ️ About")
