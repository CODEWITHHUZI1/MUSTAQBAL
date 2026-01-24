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
SQL_DB_FILE = "advocate_ai_v12.db"

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
# 2. EMAIL & VOICE UTILITIES (TTS FOR ENGLISH ONLY)
# ==============================================================================
def send_email_report(receiver_email, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        body = f"Case Report: {case_name}\n\n"
        for m in history:
            body += f"{m['role'].upper()}: {m['content']}\n\n"
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex <{sender_email}>"; msg['To'] = receiver_email
        msg['Subject'] = f"Legal Record: {case_name}"; msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls(); s.login(sender_email, sender_password); s.send_message(msg)
        return True
    except: return False

def play_voice_js(text):
    safe_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f1f5f9; padding: 10px; border-radius: 8px; border: 1px solid #cbd5e1; margin-bottom: 20px;">
        <button onclick="window.speakNow()">▶ Play Audio</button>
        <button onclick="window.speechSynthesis.cancel()">⏹ Stop</button>
    </div>
    <script>
        window.speakNow = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            msg.lang = 'en-US';
            window.speechSynthesis.speak(msg);
        }};
        window.speakNow();
    </script>
    """
    components.html(js_code, height=70)

# ==============================================================================
# 3. CHAMBERS
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    # SIDEBAR FEATURES INTACT
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        
        st.divider()
        st.subheader("🏛️ Configuration")
        sys_persona = st.text_input("Persona:", value="You are a Pakistani Law Analyst.")
        use_irac = st.toggle("Enable IRAC structure", value=True)
        
        st.divider()
        st.subheader("📁 Case Management")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        active_case = st.selectbox("Current Case", cases if cases else ["General"])
        st.session_state.active_case = active_case

        new_case_name = st.text_input("New Case Title")
        if st.button("➕ Create Case"):
            if new_case_name:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (st.session_state.user_email, new_case_name, "2026-01-24"))
                conn.commit(); conn.close(); st.rerun()

    # TOP RIGHT EMAIL ACTION
    header_col, email_col = st.columns([8, 2])
    with header_col: st.header(f"💼 Case: {active_case}")
    with email_col:
        if st.button("📧 Email Report"):
            hist = db_load_history(st.session_state.user_email, active_case)
            if send_email_report(st.session_state.user_email, active_case, hist):
                st.success("Sent!")
            else: st.error("Email Error")

    # CHAT HISTORY ABOVE QUERY
    chat_box = st.container()
    history = db_load_history(st.session_state.user_email, active_case)
    
    with chat_box:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"])

    st.divider()
    
    # INPUT SECTION
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Enter legal query...")

    query = voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, active_case, "user", query)
        
        try:
            # GEMINI 2.5 FLASH DEFINED
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY)
            
            irac_text = "Structure response with Issue, Rule, Analysis, Conclusion." if use_irac else ""
            prompt = f"{sys_persona}\n{irac_text}\nRespond in {target_lang}.\n\nQuery: {query}"
            
            response = llm.invoke(prompt).content
            db_save_message(st.session_state.user_email, active_case, "assistant", response)
            
            # TRIGGER RERUN TO SHOW HISTORY + TRIGGER TTS
            st.rerun()
            
        except Exception as e:
            st.error(f"Gemini 2.5 Error: {e}")

    # TTS GATEKEEPER
    if history and history[-1]["role"] == "assistant" and target_lang == "English":
        if st.session_state.get("last_spoken") != history[-1]["content"]:
            play_voice_js(history[-1]["content"])
            st.session_state.last_spoken = history[-1]["content"]

# ==============================================================================
# 4. NAVIGATION
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    u_email = st.text_input("Email")
    if st.button("Login"):
        st.session_state.logged_in = True; st.session_state.user_email = u_email
        conn = sqlite3.connect(SQL_DB_FILE)
        conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (u_email, "General", "2026-01-24"))
        conn.commit(); conn.close(); st.rerun()
else:
    page = st.sidebar.radio("Nav", ["Chambers", "About"])
    if page == "Chambers": render_chambers()
    else: st.write("Legal AI developed for Pakistan.")

