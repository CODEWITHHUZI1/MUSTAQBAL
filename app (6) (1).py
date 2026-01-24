# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM (V24.2 - STABLE)
# ==============================================================================

__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import smtplib
import os
import re
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. THEME ENGINE & SHADER ARCHITECTURE (RESTORED)
# ==============================================================================
st.set_page_config(page_title="Alpha Apex - Leviathan Law AI", page_icon="⚖️", layout="wide")

def apply_leviathan_shaders(theme_mode):
    shader_css = """
    <style>
        * { transition: background-color 0.8s ease, color 0.8s ease !important; }
        [data-testid="stSidebar"] { backdrop-filter: blur(20px); background: rgba(15, 23, 42, 0.9) !important; }
        .stChatMessage { border-radius: 20px !important; border-left: 5px solid #38bdf8 !important; margin-bottom: 1rem; }
        .stButton>button { border-radius: 12px !important; background: linear-gradient(135deg, #1e293b, #334155) !important; color: #38bdf8 !important; border: 1px solid #38bdf8 !important; }
        .block-container { max-width: 1100px; margin: auto; padding-top: 2rem; }
    </style>
    """
    if theme_mode == "Dark Mode":
        shader_css += "<style>.stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a, #020617) !important; color: #f1f5f9 !important; }</style>"
    else:
        shader_css += "<style>.stApp { background: #f8fafc !important; color: #0f172a !important; }</style>"
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. RDBMS ENGINE (UNTOUCHED)
# ==============================================================================
SQL_DB_FILE = "alpha_apex_leviathan_master_v24.db"

def db_log_consultation(email, chamber_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    cid = c.fetchone()
    if cid:
        c.execute("INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) VALUES (?,?,?,?)", 
                  (cid[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT m.sender_role, m.message_body FROM message_logs m JOIN chambers c ON m.chamber_id = c.id WHERE c.owner_email=? AND c.chamber_name=? ORDER BY m.id ASC", (email, chamber_name))
    rows = [{"role": r, "content": b} for r, b in c.fetchall()]
    conn.close(); return rows

# ==============================================================================
# 3. AI & CLEAN VOICE SYNTHESIS
# ==============================================================================
@st.cache_resource
def get_analytical_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.2)

def execute_neural_synthesis(text, language_code):
    # This Regex removes asterisks (*), hashtags (#), and underscores (_) so the bot doesn't read them
    clean_text = re.sub(r'[*#_]', '', text)
    clean_text = clean_text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    
    js_payload = f"""
    <script>
        window.speechSynthesis.cancel();
        var msg = new SpeechSynthesisUtterance('{clean_text}');
        msg.lang = '{language_code}';
        window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_payload, height=0)

# ==============================================================================
# 4. SOVEREIGN CHAMBERS WORKSTATION
# ==============================================================================
def render_chamber_workstation():
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    
    with st.sidebar:
        st.title("⚖️ ALPHA APEX")
        theme_sel = st.radio("System Theme", ["Dark Mode", "Light Mode"], horizontal=True)
        apply_leviathan_shaders(theme_sel)
        
        st.divider()
        st.subheader("🌐 Global Lexicon")
        active_lang = st.selectbox("Select Language", list(lexicon.keys()))
        l_code = lexicon[active_lang]
        
        st.divider()
        st.subheader("📁 Vault Navigator")
        conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
        chamber_list = [r[0] for r in c.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        st.session_state.current_chamber = st.selectbox("Active Chamber", chamber_list if chamber_list else ["Default Chamber"])
        
        if st.button("➕ Open New Chamber"):
            st.session_state.trigger_chamber_init = True
        
        if st.session_state.get('trigger_chamber_init'):
            n_chamber = st.text_input("Chamber Identifier")
            if st.button("Confirm Initialization") and n_chamber:
                conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
                c.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", (st.session_state.user_email, n_chamber, str(datetime.date.today())))
                conn.commit(); conn.close(); st.session_state.trigger_chamber_init = False; st.rerun()

        st.divider()
        if st.button("📧 Dispatch Brief"):
            st.toast("Synthesizing Brief...")
            
        if st.button("🚪 System Logout"):
            st.session_state.logged_in = False; st.rerun()

    # Main Workspace
    st.header(f"💼 Chamber: {st.session_state.current_chamber}")
    
    # Render History
    history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
    for entry in history:
        with st.chat_message(entry["role"]): st.write(entry["content"])

    # Unified Input to prevent repetition
    ui_cols = st.columns([0.85, 0.15])
    with ui_cols[1]:
        v_input = speech_to_text(language=l_code, key='mic', just_once=True, use_container_width=True)
    with ui_cols[0]:
        t_input = st.chat_input("Enter Legal Query...")

    final_input = t_input or v_input

    if final_input:
        # Prevent processing if it's the same as last message (Repetition Fix)
        if "last_processed" not in st.session_state or st.session_state.last_processed != final_input:
            st.session_state.last_processed = final_input
            
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_input)
            with st.chat_message("user"): st.write(final_input)
            
            with st.chat_message("assistant"):
                with st.spinner("Consulting Statutes..."):
                    p_logic = f"Persona: Senior Advocate Pakistan. Rule: IRAC for legal, warm for greetings. Language: {active_lang}. Input: {final_input}"
                    ai_response = get_analytical_engine().invoke(p_logic).content
                    st.markdown(ai_response)
                    db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", ai_response)
                    execute_neural_synthesis(ai_response, l_code)
                    st.rerun()

# ==============================================================================
# 5. AUTH & ROUTING
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("⚖️ ALPHA APEX LEVIATHAN")
    le = st.text_input("Vault Email")
    lp = st.text_input("Security Key", type="password")
    if st.button("Enter Vault"):
        st.session_state.logged_in = True
        st.session_state.user_email = le
        st.rerun()
else:
    nav_hub = st.sidebar.radio("Navigation Hub", ["Chambers", "Law Library", "Admin Console"])
    if nav_hub == "Chambers": render_chamber_workstation()
    else: st.info(f"Accessing {nav_hub}...")
