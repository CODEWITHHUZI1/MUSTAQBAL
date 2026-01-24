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
        [data-testid="stSidebarNav"] {{ padding-top: 0rem !important; }}
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {{ color: {t['text']} !important; }}
        .stButton>button {{ background-color: {t['accent']}; color: white !important; border-radius: 8px; width: 100%; }}
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)

if "current_theme" not in st.session_state:
    st.session_state.current_theme = "Obsidian (Dark)"
apply_custom_theme(st.session_state.current_theme)

API_KEY = st.secrets["GOOGLE_API_KEY"]
SQL_DB_FILE = "alpha_apex_production_v11.db"

# ==============================================================================
# 2. VIDEO RECORDING COMPONENT (PLAY/PAUSE LOGIC)
# ==============================================================================
def video_recorder_component():
    """Custom JS Video Recorder with Play/Pause functionality."""
    st.subheader("📹 Evidence/Consultation Recorder")
    video_html = """
    <div style="background: #2D3748; padding: 15px; border-radius: 10px; color: white; text-align: center;">
        <video id="preview" width="100%" height="auto" autoplay muted style="border-radius: 5px; background: black;"></video>
        <div style="margin-top: 10px;">
            <button id="startBtn" onclick="startRecording()" style="padding: 8px 15px; background: #48BB78; border: none; color: white; border-radius: 5px; cursor: pointer;">⏺ Record</button>
            <button id="pauseBtn" onclick="pauseRecording()" disabled style="padding: 8px 15px; background: #ECC94B; border: none; color: white; border-radius: 5px; cursor: pointer;">⏸ Pause</button>
            <button id="resumeBtn" onclick="resumeRecording()" disabled style="padding: 8px 15px; background: #4299E1; border: none; color: white; border-radius: 5px; cursor: pointer;">▶ Resume</button>
            <button id="stopBtn" onclick="stopRecording()" disabled style="padding: 8px 15px; background: #F56565; border: none; color: white; border-radius: 5px; cursor: pointer;">⏹ Stop</button>
        </div>
        <p id="status" style="font-size: 12px; margin-top: 5px;">Ready</p>
    </div>

    <script>
        let recorder;
        let stream;
        let chunks = [];

        async function startRecording() {
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
            document.getElementById('preview').srcObject = stream;
            recorder = new MediaRecorder(stream);
            
            recorder.ondataavailable = (e) => chunks.push(e.data);
            recorder.onstop = () => {
                const blob = new MediaBlob(chunks, { type: 'video/webm' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url; a.download = 'legal_consult_record.webm'; a.click();
            };

            recorder.start();
            document.getElementById('status').innerText = "🔴 Recording...";
            toggleButtons(true, true, false, true);
        }

        function pauseRecording() {
            if (recorder.state === "recording") {
                recorder.pause();
                document.getElementById('status').innerText = "⏸ Paused";
                toggleButtons(true, false, true, true);
            }
        }

        function resumeRecording() {
            if (recorder.state === "paused") {
                recorder.resume();
                document.getElementById('status').innerText = "🔴 Recording...";
                toggleButtons(true, true, false, true);
            }
        }

        function stopRecording() {
            recorder.stop();
            stream.getTracks().forEach(track => track.stop());
            document.getElementById('status').innerText = "✅ Saved";
            toggleButtons(true, false, false, false);
        }

        function toggleButtons(start, pause, resume, stop) {
            document.getElementById('startBtn').disabled = !start;
            document.getElementById('pauseBtn').disabled = !pause;
            document.getElementById('resumeBtn').disabled = !resume;
            document.getElementById('stopBtn').disabled = !stop;
        }
    </script>
    """
    components.html(video_html, height=400)

# ==============================================================================
# 3. AI & EMAIL SERVICES
# ==============================================================================
@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", GOOGLE_API_KEY=API_KEY, temperature=0.0)

def send_email_report(receiver, case_name, history):
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"].replace(" ", "")
        report_text = f"ALPHA APEX LEGAL REPORT\nCase: {case_name}\nDate: {datetime.datetime.now()}\n" + "-"*40 + "\n\n"
        for msg in history:
            role = "ASSISTANT" if msg['role'] == 'assistant' else "USER"
            report_text += f"[{role}]: {msg['content']}\n\n"
        msg = MIMEMultipart(); msg['From'] = f"Alpha Apex <{sender_email}>"; msg['To'] = receiver; msg['Subject'] = f"Record: {case_name}"
        msg.attach(MIMEText(report_text, 'plain'))
        server = smtplib.SMTP('smtp.gmail.com', 587); server.starttls(); server.login(sender_email, sender_password); server.send_message(msg); server.quit()
        return True
    except Exception as e: st.error(f"Error: {e}"); return False

# ==============================================================================
# 4. CHAMBERS INTERFACE
# ==============================================================================
def db_load_history(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('''SELECT history.role, history.content FROM history JOIN cases ON history.case_id = cases.id WHERE cases.email=? AND cases.case_name=? ORDER BY history.id ASC''', (email, case_name))
    results = c.fetchall(); conn.close()
    return [{"role": r, "content": t} for r, t in results]

def render_chambers(selected_lang, lang_code, sys_persona, use_irac):
    h_col, e_col = st.columns([8, 2])
    with h_col: st.header(f"💼 {st.session_state.active_case}")
    with e_col:
        if st.button("📧 Email Transcript"):
            hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
            if hist and send_email_report(st.session_state.user_email, st.session_state.active_case, hist):
                st.toast("Sent!")

    col1, col2 = st.columns([1, 1])
    with col1:
        video_recorder_component()
    with col2:
        st.subheader("💬 Legal Chat")
        hist = db_load_history(st.session_state.user_email, st.session_state.active_case)
        for msg in hist:
            with st.chat_message(msg["role"]): st.write(msg["content"])

    q = st.chat_input("Ask...")
    if q:
        with st.chat_message("assistant"):
            irac = "Use IRAC." if use_irac else ""
            res = load_llm().invoke(f"{sys_persona}. {irac} Language: {selected_lang}. Query: {q}").content
            st.markdown(res)
            # Add DB Save logic here as per original script
            st.rerun()

# ==============================================================================
# 5. MASTER EXECUTION & SIDEBAR
# ==============================================================================
if "connected" not in st.session_state: st.session_state.connected = False
if "active_case" not in st.session_state: st.session_state.active_case = "General Consultation"

# Mock Auth for demonstration - use your existing Authenticator logic here
if not st.session_state.connected:
    st.title("⚖️ Alpha Apex")
    if st.button("Enter Chambers (Demo Mode)"): 
        st.session_state.connected = True
        st.session_state.user_email = "test@law.com"
        st.session_state.username = "Counsel"
        st.rerun()
else:
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        
        # Appearance moved to top
        st.subheader("🎨 Appearance")
        theme_options = ["Crystal (Light)", "Slate (Muted)", "Obsidian (Dark)", "Midnight (Deep Dark)"]
        st.session_state.current_theme = st.selectbox("Theme", theme_options, index=theme_options.index(st.session_state.current_theme))
        
        st.divider()
        
        # Language/Config
        st.subheader("🌐 Config")
        langs = {"English": "en-US", "Urdu": "ur-PK"}
        sel_lang = st.selectbox("Language", list(langs.keys()))
        
        st.divider()
        
        # Case Records
        st.subheader("📁 Records")
        st.session_state.active_case = st.selectbox("Active Case", ["General Consultation"])
        
        st.divider()
        
        nav = st.radio("Navigation", ["Chambers", "About"])
        if st.button("Logout"): st.session_state.connected = False; st.rerun()

    if nav == "Chambers": render_chambers(sel_lang, langs[sel_lang], "Senior Advocate", True)
    else: st.write("About Content")
