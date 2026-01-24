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
# 2. VOICE ENGINE WITH REGIONAL FALLBACK
# ==============================================================================
def play_voice_js(text, lang_code):
    safe_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f1f5f9; padding: 15px; border-radius: 12px; border: 1px solid #e2e8f0; margin-bottom: 20px; font-family: sans-serif;">
        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
            <span style="font-weight: 600; color: #1e293b;">Voice Controller</span>
            <span style="font-size: 0.75rem; background: #dbeafe; color: #1e40af; padding: 2px 8px; border-radius: 99px;">{lang_code} Mode</span>
        </div>
        <div style="display: flex; gap: 8px; align-items: center;">
            <button onclick="window.speechSynthesis.resume()" style="padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1; background: white; cursor: pointer;">Play</button>
            <button onclick="window.speechSynthesis.pause()" style="padding: 6px 12px; border-radius: 6px; border: 1px solid #cbd5e1; background: white; cursor: pointer;">Pause</button>
            <button onclick="window.speechSynthesis.cancel()" style="padding: 6px 12px; border-radius: 6px; border: none; background: #ef4444; color: white; cursor: pointer;">Stop</button>
            <select id="rate" onchange="window.updateSpeed(this.value)" style="margin-left: 10px; padding: 4px; border-radius: 4px;">
                <option value="0.8">0.8x</option>
                <option value="1.0" selected>1.0x</option>
                <option value="1.2">1.2x</option>
            </select>
        </div>
    </div>
    <script>
        window.speechRate = 1.0;
        window.updateSpeed = function(v) {{
            window.speechRate = parseFloat(v);
            window.triggerSpeak();
        }};

        window.triggerSpeak = function() {{
            window.speechSynthesis.cancel();
            var utterance = new SpeechSynthesisUtterance("{safe_text}");
            utterance.rate = window.speechRate;
            
            var voices = window.speechSynthesis.getVoices();
            
            // LOGIC: Find regional voice OR use Urdu/Hindi as fallback for Pashto/Sindhi/Balochi
            var targetLang = "{lang_code}".split('-')[0];
            var voice = voices.find(v => v.lang.startsWith(targetLang)) || 
                        voices.find(v => v.lang.startsWith('ur')) || 
                        voices.find(v => v.lang.startsWith('hi'));
            
            if(voice) utterance.voice = voice;
            window.speechSynthesis.speak(utterance);
        }};

        if (window.speechSynthesis.onvoiceschanged !== undefined) {{
            window.speechSynthesis.onvoiceschanged = window.triggerSpeak;
        }}
        window.triggerSpeak();
    </script>
    """
    components.html(js_code, height=120)

# ==============================================================================
# 3. CHAMBERS & CASE MANAGEMENT
# ==============================================================================
def render_chambers():
    langs = {
        "English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"
    }
    
    if "last_spoken" not in st.session_state: st.session_state.last_spoken = None

    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Select Language", list(langs.keys()))
        lang_code = langs[target_lang]
        
        st.divider()
        st.subheader("📁 Case Management")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        
        active_case = st.selectbox("Active Case", cases if cases else ["General Consultation"])
        st.session_state.active_case = active_case

        new_case_name = st.text_input("New Case Name")
        if st.button("➕ Create Case"):
            if new_case_name:
                conn = sqlite3.connect(SQL_DB_FILE)
                conn.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", 
                             (st.session_state.user_email, new_case_name, datetime.datetime.now().strftime("%Y-%m-%d")))
                conn.commit(); conn.close(); st.rerun()

        if st.button("🗑️ Delete Current Case"):
            conn = sqlite3.connect(SQL_DB_FILE)
            conn.execute("DELETE FROM cases WHERE email=? AND case_name=?", (st.session_state.user_email, active_case))
            conn.commit(); conn.close(); st.rerun()

        st.divider()
        with st.expander("System Persona"):
            sys_persona = st.text_input("Role:", value="You are a Pakistani law analyst")
            use_irac = st.toggle("Use IRAC Structure", value=True)

    st.header(f"💼 Case: {st.session_state.active_case}")
    
    chat_container = st.container()
    st.divider()
    
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=lang_code, key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Ask a legal question...")

    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"])

    query = voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        try:
            # Load LLM
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)
            prompt = f"{sys_persona}. Respond strictly in {target_lang}. IRAC: {use_irac}\nQuery: {query}"
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
# 4. MAIN NAVIGATION
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    email = st.text_input("Email")
    if st.button("Enter"):
        st.session_state.logged_in = True; st.session_state.user_email = email
        conn = sqlite3.connect(SQL_DB_FILE)
        conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General Consultation", "2026-01-24"))
        conn.commit(); conn.close(); st.rerun()
else:
    page = st.sidebar.radio("Nav", ["Chambers", "About"])
    if page == "Chambers": render_chambers()
    else:
        st.header("ℹ️ Alpha Apex Team")
        team = [{"Name": "Saim Ahmed", "Contact": "03700297696"}, {"Name": "Huzaifa Khan", "Contact": "03102526567"}, {"Name": "Mustafa Khan", "Contact": "03460222290"}, {"Name": "Ibrahim Sohail", "Contact": "03212046403"}, {"Name": "Daniyal Faraz", "Contact": "03333502530"}]
        st.table(team)
