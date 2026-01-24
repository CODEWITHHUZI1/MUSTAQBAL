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
# 2. VOICE CONTROLS & ROMAN URDU ENGINE
# ==============================================================================
def play_voice_js(text, lang_code):
    safe_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f1f5f9; padding: 15px; border-radius: 10px; border: 1px solid #cbd5e1; margin: 10px 0; font-family: sans-serif;">
        <p style="margin: 0 0 10px 0; font-size: 0.8rem; font-weight: bold; color: #334155;">🔊 Voice Hub (Roman Urdu Supported)</p>
        <button onclick="window.speechSynthesis.resume()" style="padding: 5px 12px; cursor: pointer; border-radius: 4px; border: 1px solid #94a3b8;">Play</button>
        <button onclick="window.speechSynthesis.pause()" style="padding: 5px 12px; cursor: pointer; border-radius: 4px; border: 1px solid #94a3b8;">Pause</button>
        <button onclick="window.speechSynthesis.cancel()" style="padding: 5px 12px; cursor: pointer; border-radius: 4px; border: none; background: #ef4444; color: white;">Stop</button>
        
        <label style="margin-left: 15px; font-size: 0.8rem;">Speed:</label>
        <select id="rateSelect" onchange="window.setSpeechRate(this.value)" style="padding: 3px; border-radius: 4px;">
            <option value="0.8">0.8x</option>
            <option value="1.0" selected>1.0x</option>
            <option value="1.5">1.5x</option>
        </select>
    </div>

    <script>
        window.currentRate = 1.0;
        window.setSpeechRate = function(v) {{ window.currentRate = parseFloat(v); window.runSpeak(); }};

        window.runSpeak = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            msg.rate = window.currentRate;
            
            var voices = window.speechSynthesis.getVoices();
            // Logic: Force Urdu/Hindi engine for Roman Urdu accent
            var desiVoice = voices.find(v => v.lang.includes('ur')) || voices.find(v => v.lang.includes('hi'));
            
            if(desiVoice) {{
                msg.voice = desiVoice;
                msg.lang = desiVoice.lang;
            }} else {{
                msg.lang = 'en-IN'; // Fallback for better phonetics
            }}
            window.speechSynthesis.speak(msg);
        }};

        if (speechSynthesis.onvoiceschanged !== undefined) {{
            speechSynthesis.onvoiceschanged = window.runSpeak;
        }}
        window.runSpeak();
    </script>
    """
    components.html(js_code, height=110)

# ==============================================================================
# 3. CHAMBERS & SYSTEM PROMPTS
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    if "last_spoken" not in st.session_state: st.session_state.last_spoken = None

    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Select Language", list(langs.keys()))
        lang_code = langs[target_lang]

        st.divider()
        st.subheader("🏛️ System Configuration")
        with st.expander("Persona & Instructions", expanded=True):
            sys_persona = st.text_input("Core Persona:", value="You are a Pakistani Law Analyst.")
            custom_instructions = st.text_area("Instructions:", value="Respond in Roman Urdu (English script) so the user can read it easily.")
            use_irac = st.toggle("Enable IRAC Style", value=True)
        
        st.divider()
        st.subheader("📁 Case Management")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        active_case = st.selectbox("Current Case", cases if cases else ["General Consultation"])
        st.session_state.active_case = active_case

        new_case = st.text_input("New Case Name")
        if st.button("➕ Create Case"):
            if new_case:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (st.session_state.user_email, new_case, "2026-01-24"))
                conn.commit(); conn.close(); st.rerun()

    st.header(f"💼 Chambers: {st.session_state.active_case}")
    chat_container = st.container()
    st.divider()
    
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Enter your legal question...")

    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"])

    query = voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)
            irac = "Structure with Issue, Rule, Analysis, Conclusion." if use_irac else ""
            # Forced Roman Urdu Instruction
            roman_urdu = "Reply ONLY in Roman Urdu (e.g., 'Aapka sawal mil gaya hai')."
            prompt = f"{sys_persona}\n{irac}\n{custom_instructions}\n{roman_urdu}\nQuery: {query}"
            response = llm.invoke(prompt).content
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
    st.info("PPC 1860 and Constitution of Pakistan Reference.")
    st.markdown("---")
    st.subheader("Section 302: Qatl-i-amd")
    st.write("Punishment for intentional murder under Pakistan Penal Code.")

def render_about():
    st.header("ℹ️ Alpha Apex Team")
    team = [{"Name": "Saim Ahmed", "Contact": "03700297696"}, {"Name": "Huzaifa Khan", "Contact": "03102526567"}]
    st.table(team)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    email = st.text_input("Email")
    if st.button("Login"):
        st.session_state.logged_in = True; st.session_state.user_email = email; st.rerun()
else:
    page = st.sidebar.radio("Navigation", ["Chambers", "Legal Library", "About"])
    if page == "Chambers": render_chambers()
    elif page == "Legal Library": render_library()
    else: render_about()

