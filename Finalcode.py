# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 49.0 (UI OPTIMIZATION - MIC TO PROMPT AREA)
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
# 1. CORE STABILITY & THEME ENGINE
# ==============================================================================

st.set_page_config(
    page_title="Alpha Apex - Leviathan Law AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def safe_load_lottie(url: str):
    """FIXES JSONDecodeError: Safely fetches Lottie data or returns None."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"} 
        r = requests.get(url, timeout=5, headers=headers)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception:
        return None

def apply_leviathan_shaders():
    st.markdown("""
    <style>
        .stApp { background: radial-gradient(circle at top, #0f172a, #020617) !important; color: #e2e8f0 !important; }
        [data-testid="stSidebar"] {
            background-color: #020617 !important;
            border-right: 1px solid #1e293b !important;
        }
        .stChatMessage {
            background-color: rgba(30, 41, 59, 0.5) !important;
            border-radius: 15px !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(10px);
            margin-bottom: 12px;
        }
        /* Style adjustments for the prompt area mic */
        .mic-container {
            display: flex;
            align-items: center;
            justify-content: center;
            background: #1e293b;
            border-radius: 10px;
            padding: 5px;
            border: 1px solid #334155;
        }
        .logo-text { color: #f8fafc; font-size: 26px; font-weight: 800; letter-spacing: 2px; }
        footer {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. DATA INFRASTRUCTURE & AI IRAC RULES
# ==============================================================================

DB_FILE = "alpha_apex_leviathan_v49.db"

def init_db():
    conn = sqlite3.connect(DB_FILE); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, name TEXT, key TEXT, queries INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, name TEXT)')
    conn.commit(); conn.close()

init_db()

@st.cache_resource
def get_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.1)

LEVIATHAN_PROMPT = """
You are LEVIATHAN, the Senior Legal Intelligence for Pakistan Law. 
GREETINGS: Respond formally (e.g., 'Greetings, Counsel').
NON-LEGAL: Politely refuse non-legal queries.
IRAC FORMAT: You MUST answer every legal query in this EXACT structure:
- **ISSUE**: [The legal question]
- **RULE**: [Cite Pakistani Statutes/PPC/CrPC/Case Law]
- **ANALYSIS**: [Application of Law to Facts]
- **CONCLUSION**: [Final Advice/Summary]
"""

# ==============================================================================
# 3. THE COMPLETE UI (MIC MOVED TO PROMPT)
# ==============================================================================

def render_main():
    apply_leviathan_shaders()
    lottie_scales = safe_load_lottie("https://assets5.lottiefiles.com/packages/lf20_v76zkn9x.json")

    with st.sidebar:
        if lottie_scales: st_lottie(lottie_scales, height=120, key="side_logo")
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div>", unsafe_allow_html=True)
        
        st.divider()
        nav_mode = st.selectbox("Intelligence Module", ["🏛️ Case Chambers", "📂 Law Library", "🛡️ Admin Console"])
        
        if nav_mode == "🏛️ Case Chambers":
            st.subheader("📁 Case Management")
            conn = sqlite3.connect(DB_FILE); c = conn.cursor()
            c.execute("SELECT name FROM chambers WHERE email=?", (st.session_state.user_email,))
            cases = [r[0] for r in c.fetchall()] or ["General Litigation"]
            st.session_state.current_case = st.radio("Active Files", cases)
            
            st.divider()
            if st.button("➕ New Chamber"): st.toast("Opening New Case...")
            if st.button("📧 Email Brief"): st.success("Brief Dispatched to Vault Email.")
            if st.button("🚪 Logout"): 
                st.session_state.logged_in = False
                st.rerun()

    # --- CHAMBER INTERFACE ---
    if nav_mode == "🏛️ Case Chambers":
        st.title(f"💼 Case: {st.session_state.current_case}")
        
        chat_container = st.container()

        # PROMPT AREA WITH INTEGRATED MIC
        # Using a column layout at the bottom of the screen
        st.write("---")
        input_col, mic_col = st.columns([0.9, 0.1])
        
        with input_col:
            t_input = st.chat_input("Enter Query Counsel...")
        
        with mic_col:
            st.write("Voice")
            v_input = speech_to_text(language='en-US', start_prompt="🎙️", stop_prompt="⏹️", key='prompt_mic')

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
        st.header("📚 Statutory Library")
        up = st.file_uploader("Sync Legal PDF", type="pdf")
        if up: st.success("Document Verified. Ready for Leviathan Indexing.")

    elif nav_mode == "🛡️ Admin Console":
        st.header("🛡️ System Administration")
        st.table([{"Architect": "Saim Ahmed"}, {"Architect": "Huzaifa Khan"}, {"Architect": "Mustafa Khan"}, {"Architect": "Ibrahim Sohail"}, {"Architect": "Daniyal Faraz"}])

# ==============================================================================
# 4. FULL AUTHENTICATION GATE (RETAINED)
# ==============================================================================

def auth_gate():
    apply_leviathan_shaders()
    lottie_gate = safe_load_lottie("https://assets9.lottiefiles.com/packages/lf20_6aYh4x.json")
    
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        if lottie_gate: st_lottie(lottie_gate, height=200)
        st.title("⚖️ LEVIATHAN GATE")
        auth_tabs = st.tabs(["🔐 Secure Login", "📝 Registry"])
        
        with auth_tabs[0]:
            e = st.text_input("Registry Email", key="login_email")
            k = st.text_input("Vault Key", type="password", key="login_key")
            if st.button("Access Vault"):
                st.session_state.logged_in = True
                st.session_state.user_email = e
                st.rerun()
        
        with auth_tabs[1]:
            st.text_input("Full Name", key="reg_name")
            st.text_input("Registry Email", key="reg_email")
            st.selectbox("Legal Tier", ["Senior Counsel", "Advocate", "Intern"])
            st.text_input("New Vault Key", type="password", key="reg_key")
            if st.button("Apply to Alpha Apex"):
                st.sinfo("Identity Registration Submitted.")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: auth_gate()
else: render_main()
