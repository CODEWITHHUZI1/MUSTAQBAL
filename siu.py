__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import time
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
# 2. CORE UTILITIES & VOICE ENGINE
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
        msg['From'] = f"Alpha Apex <{sender_email}>"; msg['To'] = receiver_email
        msg['Subject'] = f"Legal Summary: {case_name}"
        msg.attach(MIMEText(report_content, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls()
        server.login(sender_email, sender_password); server.send_message(msg); server.quit()
        return True
    except Exception as e:
        st.error(f"Email Failed: {e}"); return False

@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", google_api_key=API_KEY, temperature=0.2,
        safety_settings={"HARM_CATEGORY_HARASSMENT": "BLOCK_NONE", "HARM_CATEGORY_HATE_SPEECH": "BLOCK_NONE", "HARM_CATEGORY_SEXUALLY_EXPLICIT": "BLOCK_NONE", "HARM_CATEGORY_DANGEROUS_CONTENT": "BLOCK_NONE"}
    )

def play_voice_js(text, lang_code):
    safe_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f8f9fa; padding: 12px; border-radius: 8px; border: 1px solid #dee2e6; margin: 10px 0;">
        <span style="font-size: 0.85rem; font-weight: bold; color: #495057; margin-right: 10px;">🔊 Audio Control:</span>
        <button onclick="window.speechSynthesis.resume()" style="border: 1px solid #ced4da; background: white; padding: 4px 10px; border-radius: 4px; cursor: pointer;">Play</button>
        <button onclick="window.speechSynthesis.pause()" style="border: 1px solid #ced4da; background: white; padding: 4px 10px; border-radius: 4px; cursor: pointer;">Pause</button>
        <button onclick="window.speechSynthesis.cancel()" style="border: none; background: #dc3545; color: white; padding: 4px 10px; border-radius: 4px; cursor: pointer;">Stop</button>
        <select id="rate" onchange="window.updateSpeed(this.value)" style="margin-left: 10px; padding: 2px;">
            <option value="0.8">0.8x</option>
            <option value="1.0" selected>1.0x</option>
            <option value="1.2">1.2x</option>
        </select>
    </div>
    <script>
        window.speechRate = 1.0;
        window.updateSpeed = function(v) {{ window.speechRate = parseFloat(v); window.triggerSpeak(); }};
        window.triggerSpeak = function() {{
            window.speechSynthesis.cancel();
            var utterance = new SpeechSynthesisUtterance("{safe_text}");
            utterance.rate = window.speechRate;
            var voices = window.speechSynthesis.getVoices();
            var targetLang = "{lang_code}".split('-')[0];
            var voice = voices.find(v => v.lang.startsWith(targetLang)) || 
                        voices.find(v => v.lang.startsWith('ur')) || 
                        voices.find(v => v.lang.startsWith('hi'));
            if(voice) utterance.voice = voice;
            window.speechSynthesis.speak(utterance);
        }};
        if (window.speechSynthesis.onvoiceschanged !== undefined) {{ window.speechSynthesis.onvoiceschanged = window.triggerSpeak; }}
        window.triggerSpeak();
    </script>
    """
    components.html(js_code, height=100)

# ==============================================================================
# 3. CHAMBERS
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    if "last_spoken" not in st.session_state: st.session_state.last_spoken = None

    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        lang_code = langs[target_lang]

        st.divider()
        st.subheader("🏛️ System Configuration")
        with st.expander("Custom Instructions & Behavior", expanded=True):
            sys_persona = st.text_input("Core Persona:", value="#You are a Pakistani law analyst")
            custom_instructions = st.text_area("Custom System Instructions:", 
                placeholder="e.g. Focus on inheritance law, always cite PPC 302, etc.")
            use_irac = st.toggle("Enable IRAC Style", value=True)
        
        st.divider()
        st.subheader("📁 Case Management")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        active_case = st.selectbox("Current Case", cases if cases else ["General Consultation"])
        st.session_state.active_case = active_case

        new_case = st.text_input("New Case Name")
        if st.button("➕ Create"):
            if new_case:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (st.session_state.user_email, new_case, "2026-01-24"))
                conn.commit(); conn.close(); st.rerun()

        if st.button("🗑️ Delete"):
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("DELETE FROM cases WHERE email=? AND case_name=?", (st.session_state.user_email, active_case))
            conn.commit(); conn.close(); st.rerun()

        if st.button("📧 Email History"):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.success("Sent!")

    st.header(f"💼 Chambers: {st.session_state.active_case}")
    
    # UI Layout: History ABOVE input
    chat_container = st.container()
    st.divider()
    
    # Input Area
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Start legal consultation...")

    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"])

    query = voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        try:
            irac_style = "Structure response using IRAC." if use_irac else "Professional response."
            full_system_prompt = f"{sys_persona}\n{irac_style}\nADDITIONAL: {custom_instructions}\nLANGUAGE: {target_lang}"
            response = load_llm().invoke(f"{full_system_prompt}\n\nClient Query: {query}").content
            db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
            st.rerun() 
        except Exception as e:
            st.error(f"Error: {e}")

    if history and history[-1]["role"] == "assistant":
        if st.session_state.last_spoken != history[-1]["content"]:
            play_voice_js(history[-1]["content"], lang_code)
            st.session_state.last_spoken = history[-1]["content"]

# ==============================================================================
# 4. LIBRARY & ABOUT
# ==============================================================================
def render_library():
    st.header("📚 Legal Library")
    st.info("Direct access to Pakistan Penal Code (PPC) and Constitutional Amendments.")
    st.write("Current selection: **Pakistan Penal Code 1860**")
    st.write("---")
    st.markdown("- **Section 302:** Punishment of qatl-i-amd.")
    st.markdown("- **Section 420:** Cheating and dishonestly inducing delivery of property.")

def render_about():
    st.header("ℹ️ About Alpha Apex")
    st.write("Alpha Apex is an AI-powered legal intelligence system.")
    team = [
        {"Name": "Saim Ahmed", "Contact": "03700297696", "Email": "saimahmed.work733@gmail.com"},
        {"Name": "Huzaifa Khan", "Contact": "03102526567", "Email": "m.huzaifa.khan471@gmail.com"},
        {"Name": "Mustafa Khan", "Contact": "03460222290", "Email": "muhammadmustafakhan430@gmail.com"},
        {"Name": "Ibrahim Sohail", "Contact": "03212046403", "Email": "ibrahimsohailkhan10@gmail.com"},
        {"Name": "Daniyal Faraz", "Contact": "03333502530", "Email": "daniyalfarazkhan2012@gmail.com"},
    ]
    st.table(team)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    email = st.text_input("Email Address")
    if st.button("Access"):
        if "@" in email:
            st.session_state.logged_in = True; st.session_state.user_email = email
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General Consultation", "2026-01-24"))
            conn.commit(); conn.close(); st.rerun()
else:
    page = st.sidebar.radio("Navigation", ["Chambers", "Legal Library", "About"])
    if page == "Chambers": render_chambers()
    elif page == "Legal Library": render_library()
    else: render_about()
