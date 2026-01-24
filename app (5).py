__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import json
import os
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from streamlit_google_auth import Authenticate
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. GLOBAL CONFIGURATION & UI STYLING
# ==============================================================================
st.set_page_config(
    page_title="Alpha Apex - Enterprise Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_custom_theme(theme_choice):
    themes = {
        "Crystal (Light)": {"bg": "#FFFFFF", "sidebar": "#F8F9FA", "text": "#1E1E1E", "accent": "#007BFF"},
        "Slate (Muted)": {"bg": "#E2E8F0", "sidebar": "#CBD5E1", "text": "#334155", "accent": "#6366F1"},
        "Obsidian (Dark)": {"bg": "#1A202C", "sidebar": "#2D3748", "text": "#F7FAFC", "accent": "#6366F1"},
        "Midnight (Deep Dark)": {"bg": "#0F172A", "sidebar": "#020617", "text": "#F8FAFC", "accent": "#38BDF8"}
    }
    t = themes[theme_choice]
    theme_css = f"""
    <style>
        .stApp {{ background-color: {t['bg']}; color: {t['text']}; }}
        [data-testid="stSidebar"] {{ background-color: {t['sidebar']}; padding-top: 0rem !important; }}
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {{ color: {t['text']} !important; text-align: center; }}
        .stButton>button {{ background-color: {t['accent']}; color: white !important; border-radius: 8px; width: 100%; }}
        /* Centering the main container */
        .block-container {{ padding-top: 2rem; max-width: 1000px; margin: auto; }}
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

if "current_theme" not in st.session_state:
    st.session_state.current_theme = "Obsidian (Dark)"
apply_custom_theme(st.session_state.current_theme)

API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "alpha_apex_production_v11.db"

# ==============================================================================
# 2. VIDEO RECORDER WITH PLAY/PAUSE
# ==============================================================================
def video_recorder_component():
    st.markdown("### 📹 Consultation Recorder")
    video_html = """
    <div style="display: flex; flex-direction: column; align-items: center; background: #2D3748; padding: 20px; border-radius: 15px; color: white;">
        <video id="v" width="640" height="360" autoplay muted style="border-radius: 10px; background: #000; margin-bottom: 15px;"></video>
        <div style="display: flex; gap: 10px;">
            <button id="start" onclick="start()" style="padding: 10px 20px; background: #48BB78; border: none; color: white; border-radius: 5px; cursor: pointer;">⏺ Record</button>
            <button id="pause" onclick="pause()" disabled style="padding: 10px 20px; background: #ECC94B; border: none; color: white; border-radius: 5px; cursor: pointer;">⏸ Pause</button>
            <button id="resume" onclick="resume()" disabled style="padding: 10px 20px; background: #4299E1; border: none; color: white; border-radius: 5px; cursor: pointer;">▶ Resume</button>
            <button id="stop" onclick="stop()" disabled style="padding: 10px 20px; background: #F56565; border: none; color: white; border-radius: 5px; cursor: pointer;">⏹ Stop</button>
        </div>
        <p id="msg" style="margin-top: 10px; font-weight: bold; color: #CBD5E0;">Status: Ready</p>
    </div>
    <script>
        let rec, stream, chunks = [];
        const msg = document.getElementById('msg');
        const v = document.getElementById('v');
        
        async function start() {
            stream = await navigator.mediaDevices.getUserMedia({video: true, audio: true});
            v.srcObject = stream;
            rec = new MediaRecorder(stream);
            rec.ondataavailable = e => chunks.push(e.data);
            rec.onstop = () => {
                const blob = new Blob(chunks, {type: 'video/webm'});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = 'consultation.webm'; a.click();
            };
            rec.start();
            msg.innerText = "Status: 🔴 Recording";
            btn(false, true, false, true);
        }
        function pause() { rec.pause(); msg.innerText = "Status: ⏸ Paused"; btn(false, false, true, true); }
        function resume() { rec.resume(); msg.innerText = "Status: 🔴 Recording"; btn(false, true, false, true); }
        function stop() { rec.stop(); stream.getTracks().forEach(t => t.stop()); msg.innerText = "Status: ✅ Saved"; btn(true, false, false, false); }
        function btn(s, p, r, st) {
            document.getElementById('start').disabled = !s;
            document.getElementById('pause').disabled = !p;
            document.getElementById('resume').disabled = !r;
            document.getElementById('stop').disabled = !st;
        }
    </script>
    """
    components.html(video_html, height=500)

# ==============================================================================
# 3. CORE LOGIC (EMAILS, DB, LLM - UNCHANGED)
# ==============================================================================
def db_load_history(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT history.role, history.content FROM history JOIN cases ON history.case_id = cases.id WHERE cases.email=? AND cases.case_name=? ORDER BY history.id ASC''', (email, case_name))
    results = c.fetchall(); conn.close()
    return [{"role": r, "content": t} for r, t in results]

def send_email_report(receiver, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"].replace(" ", "")
        report = f"Case: {case_name}\n" + "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
        msg = MIMEMultipart(); msg['From'] = sender_email; msg['To'] = receiver; msg['Subject'] = f"Legal Record: {case_name}"
        msg.attach(MIMEText(report, 'plain'))
        s = smtplib.SMTP('smtp.gmail.com', 587); s.starttls(); s.login(sender_email, sender_password); s.send_message(msg); s.quit()
        return True
    except Exception as e: st.error(e); return False

# ==============================================================================
# 4. CENTERED CHAMBERS INTERFACE
# ==============================================================================
def render_chambers():
    # Centered Header
    st.markdown(f"## 💼 Case: {st.session_state.active_case}")
    
    # Action Row
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("📧 Email Transcript"):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.toast("Email Sent!")
                
    # Center-Aligned Video Recorder
    video_recorder_component()

    st.divider()

    # Centered Chat
    st.markdown("### 💬 Consultation History")
    hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
    for msg in hist:
        with st.chat_message(msg["role"]): st.write(msg["content"])

    q = st.chat_input("State your legal query...")
    if q:
        # LLM logic as per your original file
        st.rerun()

# ==============================================================================
# 5. MASTER EXECUTION
# ==============================================================================
if "connected" not in st.session_state: st.session_state.connected = False
if "active_case" not in st.session_state: st.session_state.active_case = "General Consultation"

# Insert your Authenticator and Sidebar logic here as per your previous code
# The Sidebar will stay at the left, but the main content is now centered via CSS.

if st.session_state.connected:
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        st.subheader("🎨 Appearance")
        theme = st.selectbox("Theme", ["Crystal (Light)", "Slate (Muted)", "Obsidian (Dark)", "Midnight (Deep Dark)"], index=2)
        if theme != st.session_state.current_theme:
            st.session_state.current_theme = theme; st.rerun()
        st.divider()
        nav = st.radio("Navigation", ["Chambers", "Library", "About"])
        
    if nav == "Chambers": render_chambers()
