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
SQL_DB_FILE = "advocate_ai_v15.db"

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
    return [{"role": r, "content": t} for r, t in c.fetchall()]

init_sql_db()

# ==============================================================================
# 2. VOICE ENGINE (JS COMPONENT)
# ==============================================================================
def play_voice_js(text, speed):
    safe_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <script>
        window.speakNow = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            msg.lang = 'en-US';
            msg.rate = {speed};
            window.speechSynthesis.speak(msg);
        }};
        window.pauseNow = function() {{ window.speechSynthesis.pause(); }};
        window.resumeNow = function() {{ window.speechSynthesis.resume(); }};
        window.stopNow = function() {{ window.speechSynthesis.cancel(); }};
        
        // Auto-play on first load
        window.speakNow();
    </script>
    """
    components.html(js_code, height=0)

# ==============================================================================
# 3. CHAMBERS UI
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    # --- SIDEBAR (Features Intact) ---
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        st.divider()
        st.subheader("🏛️ Configuration")
        sys_persona = st.text_input("Persona:", value="You are a Pakistani Law Analyst.")
        use_irac = st.toggle("Enable IRAC structure", value=True)
        st.divider()
        st.subheader("📁 Cases")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        active_case = st.selectbox("Active Case", cases if cases else ["General"])
        st.session_state.active_case = active_case

    # --- TOP HEADER ---
    h1, h2 = st.columns([8, 2])
    with h1: st.header(f"💼 {active_case}")
    with h2: 
        if st.button("📧 Email Chat"): st.info("Report Sent to Email.")

    # --- MAIN CHAT AREA ---
    history = db_load_history(st.session_state.user_email, active_case)
    chat_subcontainer = st.container()
    with chat_subcontainer:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"])
    
    # Padding to prevent overlap with fixed bottom bar
    st.markdown("<br><br><br><br><br><br>", unsafe_allow_code=True)

    # --- FIXED BOTTOM PROMPT BAR ---
    with st.container():
        st.markdown("---")
        
        # Audio Settings (Appear only if Headphones clicked AND language is English)
        if st.session_state.get("show_audio_tools", False) and target_lang == "English":
            audio_col1, audio_col2 = st.columns([3, 7])
            with audio_col1:
                st.write("Playback Controls")
                c1, c2, c3 = st.columns(3)
                if c1.button("▶️"): components.html("<script>window.parent.speakNow()</script>", height=0)
                if c2.button("⏸️"): components.html("<script>window.parent.pauseNow()</script>", height=0)
                if c3.button("⏹️"): components.html("<script>window.parent.stopNow()</script>", height=0)
            with audio_col2:
                voice_speed = st.slider("Voice Speed", 0.5, 2.0, 1.0, 0.1)
                st.session_state.voice_speed = voice_speed

        # The Actual Prompt Bar
        b1, b2, b3, b4 = st.columns([1, 1, 7, 1])
        with b1: 
            if st.button("🎧"): 
                st.session_state.show_audio_tools = not st.session_state.get("show_audio_tools", False)
                st.rerun()
        with b2: st.file_uploader("Upload", label_visibility="collapsed")
        with b3: text_in = st.chat_input("Ask a legal question...")
        with b4: mic_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)

    # --- PROCESSING ---
    query = text_in or mic_in
    if query:
        db_save_message(st.session_state.user_email, active_case, "user", query)
        try:
            # GEMINI 2.5 FLASH
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY)
            irac = "Use IRAC structure." if use_irac else ""
            prompt = f"{sys_persona}\n{irac}\nRespond in {target_lang}. Query: {query}"
            response = llm.invoke(prompt).content
            db_save_message(st.session_state.user_email, active_case, "assistant", response)
            st.rerun()
        except Exception as e: st.error(f"Error: {e}")

    # Trigger TTS Logic
    if history and history[-1]["role"] == "assistant" and target_lang == "English" and st.session_state.get("show_audio_tools", False):
        if st.session_state.get("last_spoken") != history[-1]["content"]:
            play_voice_js(history[-1]["content"], st.session_state.get("voice_speed", 1.0))
            st.session_state.last_spoken = history[-1]["content"]

# ==============================================================================
# 4. LOGIN
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex")
    email = st.text_input("Email")
    if st.button("Login"):
        st.session_state.logged_in = True; st.session_state.user_email = email
        conn = sqlite3.connect(SQL_DB_FILE)
        conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General", "2026-01-24"))
        conn.commit(); conn.close(); st.rerun()
else:
    render_chambers()
