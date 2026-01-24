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

# Ensure session state variables exist
if "show_audio_tools" not in st.session_state: st.session_state.show_audio_tools = False
if "voice_speed" not in st.session_state: st.session_state.voice_speed = 1.0
if "last_spoken" not in st.session_state: st.session_state.last_spoken = ""

API_KEY = st.secrets["GEMINI_API_KEY"]
SQL_DB_FILE = "advocate_ai_final.db"

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
# 2. VOICE CONTROLS (STRICT ENGLISH)
# ==============================================================================
def inject_voice_controls():
    """Injects the JS functions into the app head once."""
    components.html("""
    <script>
        window.speakNow = function(text, speed) {
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance(text);
            msg.lang = 'en-US';
            msg.rate = speed;
            window.speechSynthesis.speak(msg);
        };
        window.pauseNow = function() { window.speechSynthesis.pause(); };
        window.resumeNow = function() { window.speechSynthesis.resume(); };
        window.stopNow = function() { window.speechSynthesis.cancel(); };
    </script>
    """, height=0)

# ==============================================================================
# 3. CHAMBERS UI
# ==============================================================================
def render_chambers():
    inject_voice_controls()
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    # --- SIDEBAR (Features Preserved) ---
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        st.divider()
        st.subheader("🏛️ Configuration")
        sys_persona = st.text_input("Persona:", value="You are a Pakistani Law Analyst.")
        use_irac = st.toggle("Enable IRAC structure", value=True)
        st.divider()
        
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        active_case = st.selectbox("Active Case", cases if cases else ["General"])
        st.session_state.active_case = active_case

    # --- TOP HEADER ---
    h1, h2 = st.columns([8, 2])
    with h1: st.header(f"💼 {active_case}")
    with h2: 
        if st.button("📧 Email Chat"):
            st.toast("Emailing conversation...")

    # --- CHAT CONTAINER ---
    history = db_load_history(st.session_state.user_email, active_case)
    chat_container = st.container()
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]): st.write(m["content"])
    
    # Spacer for bottom bar
    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)

    # --- FIXED BOTTOM UI ---
    bottom_ui = st.container()
    with bottom_ui:
        st.markdown("---")
        
        # Audio Panel (English Only)
        if st.session_state.show_audio_tools and target_lang == "English":
            a_col1, a_col2 = st.columns([4, 6])
            with a_col1:
                st.caption("Audio Playback")
                btn1, btn2, btn3 = st.columns(3)
                if btn1.button("▶️"): 
                    if history: components.html(f"<script>window.parent.speakNow('{history[-1]['content']}', {st.session_state.voice_speed})</script>", height=0)
                if btn2.button("⏸️"): components.html("<script>window.parent.pauseNow()</script>", height=0)
                if btn3.button("⏹️"): components.html("<script>window.parent.stopNow()</script>", height=0)
            with a_col2:
                st.session_state.voice_speed = st.slider("Speed", 0.5, 2.0, st.session_state.voice_speed)

        # Prompt Bar
        b1, b2, b3, b4 = st.columns([1, 1, 7, 1])
        with b1: 
            if st.button("🎧"): 
                st.session_state.show_audio_tools = not st.session_state.show_audio_tools
                st.rerun()
        with b2: st.file_uploader("UP", label_visibility="collapsed")
        with b3: text_in = st.chat_input("Ask Alpha Apex...")
        with b4: mic_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)

    # --- RESPONSE LOGIC ---
    query = text_in or mic_in
    if query:
        db_save_message(st.session_state.user_email, active_case, "user", query)
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY)
            irac = "Structure: Issue, Rule, Analysis, Conclusion." if use_irac else ""
            prompt = f"{sys_persona}\n{irac}\nRespond in {target_lang}. Query: {query}"
            
            response = llm.invoke(prompt).content
            db_save_message(st.session_state.user_email, active_case, "assistant", response)
            st.rerun()
        except Exception as e:
            st.error(f"Error: {e}")

# ==============================================================================
# 4. EXECUTION
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex")
    email = st.text_input("Email")
    if st.button("Login"):
        st.session_state.logged_in = True
        st.session_state.user_email = email
        conn = sqlite3.connect(SQL_DB_FILE)
        conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General", "2026-01-24"))
        conn.commit(); conn.close()
        st.rerun()
else:
    render_chambers()
