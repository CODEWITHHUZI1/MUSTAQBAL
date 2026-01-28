# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 50.0 (HIGH CONTRAST & VISIBILITY OPTIMIZATION)
# ==============================================================================

try:
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
except ImportError:
    import sqlite3

import streamlit as st
import sqlite3
import datetime
import os
import requests
import pandas as pd
import fitz  # PyMuPDF
from streamlit_lottie import st_lottie, st_lottie_spinner
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. ENHANCED VISIBILITY SHADERS
# ==============================================================================

st.set_page_config(
    page_title="Alpha Apex - Leviathan Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def safe_load_lottie(url: str):
    try:
        headers = {"User-Agent": "Mozilla/5.0"} 
        r = requests.get(url, timeout=5, headers=headers)
        return r.json() if r.status_code == 200 else None
    except: return None

def apply_leviathan_shaders():
    st.markdown("""
    <style>
        /* GLOBAL BACKGROUND */
        .stApp { background: radial-gradient(circle at top, #0f172a, #020617) !important; }

        /* HIGH-CONTRAST TEXT FOR VISIBILITY */
        p, li, label, .stMarkdown {
            color: #f8fafc !important; /* Ultra-light Slate for readability */
            font-size: 1.05rem !important;
            line-height: 1.6 !important;
        }

        /* HEADINGS */
        h1, h2, h3 { color: #ffffff !important; font-weight: 800 !important; }

        /* SIDEBAR */
        [data-testid="stSidebar"] {
            background-color: #020617 !important;
            border-right: 1px solid #334155 !important;
        }

        /* CHAT BUBBLES */
        .stChatMessage {
            background-color: rgba(30, 41, 59, 0.7) !important;
            border-radius: 12px !important;
            border: 1px solid #475569 !important;
            margin-bottom: 15px;
        }

        /* INPUT AREA */
        .stTextInput>div>div>input {
            color: #ffffff !important;
            background-color: #1e293b !important;
        }

        .logo-text { color: #f8fafc; font-size: 26px; font-weight: 800; letter-spacing: 2px; }
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. DATA & AI INFRASTRUCTURE
# ==============================================================================

DB_FILE = "alpha_apex_v50.db"

def init_db():
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, name TEXT, key TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, name TEXT)')
    conn.commit(); conn.close()

init_db()

@st.cache_resource
def get_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.1)

LEVIATHAN_PROMPT = """
You are LEVIATHAN, the Senior Legal Intelligence for Pakistan Law. 
GREETINGS: Respond formally (e.g., 'Greetings, Counsel').
IRAC FORMAT: Answer legal queries in this structure:
- **ISSUE**: [Legal question]
- **RULE**: [Cite Statute/PPC/CrPC/CPC]
- **ANALYSIS**: [Apply law to facts]
- **CONCLUSION**: [Final Advice]
"""

# ==============================================================================
# 3. INTERFACE RENDERER
# ==============================================================================

def render_main():
    apply_leviathan_shaders()
    lottie_scales = safe_load_lottie("https://assets5.lottiefiles.com/packages/lf20_v76zkn9x.json")

    with st.sidebar:
        if lottie_scales: st_lottie(lottie_scales, height=120)
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div>", unsafe_allow_html=True)
        st.divider()
        nav_mode = st.selectbox("Module Selection", ["🏛️ Case Chambers", "📂 Law Library", "🛡️ Admin Console"])
        
        if nav_mode == "🏛️ Case Chambers":
            st.subheader("📁 Case Files")
            conn = sqlite3.connect(DB_FILE); c = conn.cursor()
            c.execute("SELECT name FROM chambers WHERE email=?", (st.session_state.user_email,))
            cases = [r[0] for r in c.fetchall()] or ["General Litigation"]
            st.session_state.current_case = st.radio("Select Case", cases)
            st.divider()
            if st.button("📧 Email Brief"): st.success("Brief Dispatched.")
            if st.button("🚪 Logout"): 
                st.session_state.logged_in = False
                st.rerun()

    if nav_mode == "🏛️ Case Chambers":
        st.title(f"💼 Case: {st.session_state.current_case}")
        chat_container = st.container()

        # MIC IN PROMPT AREA
        st.write("---")
        input_col, mic_col = st.columns([0.85, 0.15])
        with input_col:
            t_input = st.chat_input("Query the Law...")
        with mic_col:
            v_input = speech_to_text(language='en-US', start_prompt="🎙️ Talk", stop_prompt="⏹️ Save", key='prompt_mic')

        query = t_input or v_input
        if query:
            with chat_container:
                with st.chat_message("user"): st.write(query)
                with st.chat_message("assistant"):
                    if lottie_scales:
                        with st_lottie_spinner(lottie_scales, height=100):
                            resp = get_engine().invoke(f"{LEVIATHAN_PROMPT}\nQUERY: {query}").content
                            st.markdown(resp)
                    else:
                        with st.spinner("Analyzing Statutes..."):
                            resp = get_engine().invoke(f"{LEVIATHAN_PROMPT}\nQUERY: {query}").content
                            st.markdown(resp)

    elif nav_mode == "📂 Law Library":
        st.header("📚 Law Library")
        st.file_uploader("Upload Legal Documents", type="pdf")

    elif nav_mode == "🛡️ Admin Console":
        st.header("🛡️ System Admins")
        st.table([{"Architect": "Saim Ahmed"}, {"Architect": "Huzaifa Khan"}, {"Architect": "Mustafa Khan"}, {"Architect": "Ibrahim Sohail"}, {"Architect": "Daniyal Faraz"}])

# ==============================================================================
# 4. AUTHENTICATION GATE
# ==============================================================================

def auth_gate():
    apply_leviathan_shaders()
    lottie_gate = safe_load_lottie("https://assets9.lottiefiles.com/packages/lf20_6aYh4x.json")
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        if lottie_gate: st_lottie(lottie_gate, height=200)
        st.title("⚖️ LEVIATHAN GATE")
        auth_tabs = st.tabs(["🔐 Login", "📝 Register"])
        with auth_tabs[0]:
            e = st.text_input("Email", key="le")
            k = st.text_input("Key", type="password", key="lk")
            if st.button("Enter Vault"):
                st.session_state.logged_in = True
                st.session_state.user_email = e
                st.rerun()
        with auth_tabs[1]:
            st.text_input("Name")
            st.text_input("Email", key="re")
            st.text_input("Set Key", type="password", key="rk")
            if st.button("Register Identity"): st.success("Registered.")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: auth_gate()
else: render_main()
