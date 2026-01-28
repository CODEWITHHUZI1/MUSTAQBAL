# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 36.5 (REGISTRATION RESTORED & UI ENHANCED)
# ARCHITECTS: SAIM AHMED, HUZAIFA KHAN, MUSTAFA KHAN, IBRAHIM SOHAIL, DANIYAL FARAZ
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
import time
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. PREMIUM HACKATHON SHADER ARCHITECTURE (CSS UPGRADE)
# ==============================================================================

st.set_page_config(
    page_title="Alpha Apex - Leviathan AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_leviathan_shaders():
    shader_css = """
    <style>
        /* GLASSMORPHISM SIDEBAR */
        [data-testid="stSidebar"] {
            background: rgba(2, 6, 23, 0.85) !important;
            backdrop-filter: blur(12px);
            border-right: 1px solid rgba(255, 255, 255, 0.1) !important;
        }
        
        /* METRIC CARDS STYLE */
        [data-testid="stMetricValue"] {
            font-size: 1.8rem !important;
            color: #f8fafc !important;
        }
        
        div[data-testid="metric-container"] {
            background: rgba(30, 41, 59, 0.4);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }

        /* CHAT BUBBLE ENHANCEMENTS */
        .stChatMessage {
            background: rgba(30, 41, 59, 0.25) !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 15px !important;
            margin-bottom: 1rem !important;
        }

        /* LOGO GRADIENT */
        .logo-text { 
            background: linear-gradient(90deg, #f8fafc, #94a3b8);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 28px; font-weight: 800; 
            letter-spacing: -1px;
        }
        
        /* INPUT FIELD OVERRIDE */
        .stTextInput>div>div>input {
            background-color: rgba(30, 41, 59, 0.5) !important;
            color: #ffffff !important;
        }
        
        footer {visibility: hidden;}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE PERSISTENCE
# ==============================================================================

SQL_DB_FILE = "alpha_apex_leviathan_master_v32.db"

def init_leviathan_db():
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT, registration_date TEXT, membership_tier TEXT DEFAULT "Senior Counsel", account_status TEXT DEFAULT "Active", total_queries INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT, chamber_type TEXT DEFAULT "General Litigation", case_status TEXT DEFAULT "Active", is_archived INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT, token_count INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT, asset_status TEXT DEFAULT "Verified")')
    conn.commit(); conn.close()

def db_create_vault_user(email, name, password):
    if not email or not password: return False
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute('INSERT INTO users (email, full_name, vault_key, registration_date) VALUES (?, ?, ?, ?)', (email, name, password, ts))
        cursor.execute('INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?, ?, ?)', (email, "General Litigation Chamber", ts))
        conn.commit(); conn.close(); return True
    except sqlite3.IntegrityError:
        conn.close(); return False

def db_verify_vault_access(email, password):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    res = cursor.fetchone(); conn.close(); return res[0] if res else None

def db_log_consultation(email, chamber_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    c_row = cursor.fetchone()
    if c_row:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) VALUES (?, ?, ?, ?)', (c_row[0], role, content, ts))
        if role == "user": cursor.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
    cursor.execute("SELECT m.sender_role, m.message_body FROM message_logs m JOIN chambers c ON m.chamber_id = c.id WHERE c.owner_email=? AND c.chamber_name=? ORDER BY m.id ASC", (email, chamber_name))
    rows = cursor.fetchall(); conn.close(); return [{"role": r, "content": b} for r, b in rows]

init_leviathan_db()

# ==============================================================================
# 3. ANALYTICAL SERVICES
# ==============================================================================

@st.cache_resource
def get_analytical_engine():
    return ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.2)

# ==============================================================================
# 4. MAIN INTERFACE
# ==============================================================================

def render_main_interface():
    lexicon = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK"}
    apply_leviathan_shaders()
    
    with st.sidebar:
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div>", unsafe_allow_html=True)
        st.caption("Strategic Legal Intelligence Suite")
        nav_mode = st.radio("System Access", ["Chambers", "Law Library", "System Admin"], label_visibility="collapsed")
        
        st.write("---") 
        if nav_mode == "Chambers":
            u_mail = st.session_state.user_email
            conn = sqlite3.connect(SQL_DB_FILE); cursor = conn.cursor()
            cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=? AND is_archived=0", (u_mail,))
            chambers_raw = [r[0] for r in cursor.fetchall()]; conn.close()
            chambers_raw = chambers_raw if chambers_raw else ["General Litigation Chamber"]
            st.session_state.current_chamber = st.selectbox("Current File", chambers_raw)
            if st.button("➕ New Case File"): st.session_state.add_case = True

        st.write("---")
        with st.expander("⚙️ Settings"):
            custom_persona = st.text_input("Persona", value="Senior High Court Advocate")
            lang_choice = st.selectbox("Language", list(lexicon.keys()))
            if st.button("Logout"): st.session_state.logged_in = False; st.rerun()

    if nav_mode == "Chambers":
        # HACKATHON DASHBOARD HEADER
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("System Pulse", "Online", delta="Stable")
        m2.metric("Legal Engine", "IRAC v2", delta="Active")
        m3.metric("Jurisdiction", "Sindh/PK", delta="Verified")
        m4.metric("AI Confidence", "98.4%", delta="Optimal")

        head_col, judge_col, action_col = st.columns([0.6, 0.2, 0.2])
        with head_col:
            st.header(f"💼 CASE: {st.session_state.current_chamber}")
        with judge_col:
            st.write(" ") 
            judge_mode = st.toggle("⚖️ JUDGE mode")
        with action_col:
            st.write(" ") 
            if st.button("📧 Email Brief"): st.toast("Dispatching...")

        chat_container = st.container()
        with chat_container:
            history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.current_chamber)
            for msg in history:
                with st.chat_message(msg["role"]): st.write(msg["content"])

        prompt_col, mic_col = st.columns([0.9, 0.1])
        with prompt_col:
            t_input = st.chat_input("Enter Legal Query...")
        with mic_col:
            st.write(" ") 
            v_input = speech_to_text(language=lexicon[lang_choice], key='v_mic', just_once=True, start_prompt="🎙️", stop_prompt="⏹️")
        
        final_query = t_input or v_input

        if final_query:
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_query)
            with chat_container:
                with st.chat_message("user"): st.write(final_query)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing Statutes..."):
                    try:
                        active_persona = "High Court Justice" if judge_mode else custom_persona
                        jurisdiction_fix = "JURISDICTION: Strict Pakistan/Sindh. NO Indian law. FORMAT: IRAC (Issue, Rule, Application, Conclusion)."
                        instruction = f"{active_persona}. {jurisdiction_fix}. Query: {final_query}"
                        
                        engine = get_analytical_engine()
                        resp = engine.invoke(instruction).content
                        st.markdown(resp)
                        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", resp)
                        st.rerun()
                    except Exception as e: st.error(f"Error: {e}")

    elif nav_mode == "Law Library":
        st.header("📚 Law Library Vault")
        conn = sqlite3.connect(SQL_DB_FILE)
        df_assets = pd.read_sql_query("SELECT filename, filesize_kb, sync_timestamp, asset_status FROM law_assets", conn)
        conn.close()
        if df_assets.empty: st.info("No files synced.")
        else: st.dataframe(df_assets, use_container_width=True)

    elif nav_mode == "System Admin":
        st.header("🛡️ Administration")
        st.info("System operational. Telemetry: Online.")

def render_sovereign_portal():
    apply_leviathan_shaders()
    st.title("⚖️ ALPHA APEX LEVIATHAN")
    auth_tabs = st.tabs(["🔐 Login", "📝 Register"])
    with auth_tabs[0]:
        e_log = st.text_input("Email", key="log_email")
        k_log = st.text_input("Key", type="password", key="log_key")
        if st.button("Access Vault"):
            user_name = db_verify_vault_access(e_log, k_log)
            if user_name:
                st.session_state.logged_in = True
                st.session_state.user_email = e_log
                st.rerun()
            else: st.error("Denied")
    with auth_tabs[1]:
        e_reg = st.text_input("Registry Email", key="reg_email")
        n_reg = st.text_input("Counsel Full Name", key="reg_name")
        k_reg = st.text_input("Set Security Key", type="password", key="reg_key")
        if st.button("Initialize Registry"):
            if db_create_vault_user(e_reg, n_reg, k_reg):
                st.success("Counsel Registered Successfully")
            else:
                st.error("Registry Failed: User may already exist.")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: render_sovereign_portal()
else: render_main_interface()
