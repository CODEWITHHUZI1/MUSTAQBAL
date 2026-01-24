__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. INITIALIZATION & DATABASE
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")
API_KEY = st.secrets["GEMINI_API_KEY"]
SQL_DB_FILE = "advocate_ai_v4.db"

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
# 2. ADVANCED TTS ENGINE (Dual Script Support)
# ==============================================================================
def play_voice_js(roman_text):
    """Specifically plays the Roman Urdu version for better phonetics"""
    safe_text = roman_text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; margin: 10px 0; font-family: sans-serif;">
        <p style="margin: 0 0 5px 0; font-size: 0.75rem; color: #64748b;">🔊 Playing Phonetic Audio...</p>
        <button onclick="window.speechSynthesis.resume()" style="padding: 5px 10px; cursor: pointer;">Play</button>
        <button onclick="window.speechSynthesis.pause()" style="padding: 5px 10px; cursor: pointer;">Pause</button>
        <button onclick="window.speechSynthesis.cancel()" style="padding: 5px 10px; background: #ef4444; color: white; border: none; border-radius: 4px; cursor: pointer;">Stop</button>
    </div>
    <script>
        function speak() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            var voices = window.speechSynthesis.getVoices();
            // Force Urdu/Hindi engine for the Roman Urdu text to get the right accent
            var desiVoice = voices.find(v => v.lang.includes('ur')) || voices.find(v => v.lang.includes('hi')) || voices.find(v => v.lang.includes('en-IN'));
            if(desiVoice) {{ msg.voice = desiVoice; msg.lang = desiVoice.lang; }}
            msg.rate = 0.95;
            window.speechSynthesis.speak(msg);
        }}
        if (speechSynthesis.onvoiceschanged !== undefined) {{ speechSynthesis.onvoiceschanged = speak; }}
        speak();
    </script>
    """
    components.html(js_code, height=90)

# ==============================================================================
# 3. CHAMBERS
# ==============================================================================
def render_chambers():
    langs = {"Urdu": "ur-PK", "English": "en-US", "Sindhi": "sd-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Select Visual Language", list(langs.keys()))
        
        st.divider()
        st.subheader("🏛️ System Configuration")
        with st.expander("Persona & Logic", expanded=True):
            sys_persona = st.text_input("Core Persona:", value="You are a Pakistani Law Analyst.")
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

    st.header(f"💼 Case: {st.session_state.active_case}")
    chat_container = st.container()
    st.divider()

    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Ask your legal question...")

    history = db_load_history(st.session_state.user_email, st.session_state.active_case)
    
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]):
                # Logic: Only show the part BEFORE the Roman Urdu marker to the user
                display_text = m["content"].split("|||")[0]
                st.write(display_text)

    query = voice_in or text_in
    if query:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", query)
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)
            irac = "Structure with IRAC." if use_irac else ""
            
            # THE CORE INSTRUCTION: Providing Dual Script
            prompt = f"""
            {sys_persona}
            {irac}
            You must provide the response in two parts separated by '|||'.
            Part 1: The response in {target_lang} native script.
            Part 2: The exact same response translated into Roman Urdu (English script) for TTS.
            Example: [Urdu Script Text] ||| [Roman Urdu Text]
            Query: {query}
            """
            
            response = llm.invoke(prompt).content
            db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", response)
            st.rerun() 
        except Exception as e:
            st.error(f"Error: {e}")

    if history and history[-1]["role"] == "assistant":
        full_content = history[-1]["content"]
        if "|||" in full_content:
            native_part, roman_part = full_content.split("|||")
            if st.session_state.get("last_spoken") != roman_part:
                play_voice_js(roman_part)
                st.session_state.last_spoken = roman_part

# ==============================================================================
# 4. LIBRARY & ABOUT
# ==============================================================================
def render_library():
    st.header("📚 Legal Library")
    st.info("PPC 1860 & Constitution Reference")

def render_about():
    st.header("ℹ️ Alpha Apex Team")
    team = [{"Name": "Saim Ahmed", "Contact": "03700297696"}, {"Name": "Huzaifa Khan", "Contact": "03102526567"}]
    st.table(team)

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
    page = st.sidebar.radio("Navigation", ["Chambers", "Legal Library", "About"])
    if page == "Chambers": render_chambers()
    elif page == "Legal Library": render_library()
    else: render_about()
