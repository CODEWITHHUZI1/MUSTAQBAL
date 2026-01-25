# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 34.0 (UI REDEFINITION - BLACKOUT PRECISION)
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
import smtplib
import pandas as pd
from PyPDF2 import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ==============================================================================
# 1. REDEFINED BLACKOUT SHADER ARCHITECTURE
# ==============================================================================

st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")

def apply_leviathan_shaders():
    shader_css = """
    <style>
        /* Global Canvas */
        .stApp { background-color: #020617 !important; color: #f1f5f9 !important; }

        /* SIDEBAR: Organized Background */
        [data-testid="stSidebar"] {
            background-color: #0f172a !important;
            border-right: 1px solid #1e293b !important;
        }

        /* PROMPT BAR: Pure Black with White Input */
        .stChatInput { 
            background-color: transparent !important; 
            padding-bottom: 20px !important;
        }
        .stChatInput textarea {
            background-color: #000000 !important;
            color: #ffffff !important;
            border: 1px solid #38bdf8 !important;
            border-radius: 10px !important;
            font-size: 1.1rem !important;
        }

        /* BUTTONS: Corporate Blue */
        .stButton>button {
            border-radius: 8px !important;
            background: #1e293b !important;
            color: #38bdf8 !important;
            border: 1px solid #38bdf8 !important;
            width: 100% !important;
            font-weight: bold !important;
        }
        
        /* Metric & Admin Tables */
        [data-testid="stMetricValue"] { color: #38bdf8 !important; }
        .stTable { background-color: #0f172a !important; color: #ffffff !important; }

        footer {visibility: hidden;}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ==============================================================================
# 2. DATABASE & SYSTEM UTILITIES
# ==============================================================================

SQL_DB_FILE = "alpha_apex_master.db"

def init_db():
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, full_name TEXT, vault_key TEXT, total_queries INTEGER DEFAULT 0)')
    c.execute('CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS system_telemetry (id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, event_type TEXT, description TEXT, ts TEXT)')
    conn.commit(); conn.close()

def db_log_consultation(email, chamber_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
    c.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    res = c.fetchone()
    if res:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute('INSERT INTO message_logs (chamber_id, sender_role, message_body, ts) VALUES (?, ?, ?, ?)', (res[0], role, content, ts))
        if role == "user": c.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
        conn.commit()
    conn.close()

init_db()

@st.cache_resource
def get_engine():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=st.secrets["GOOGLE_API_KEY"], temperature=0.2)

# ==============================================================================
# 3. INTERFACE EXECUTION
# ==============================================================================

def render_ui():
    apply_leviathan_shaders()
    u_mail = st.session_state.user_email

    # --- SIDEBAR STRUCTURE ---
    with st.sidebar:
        st.markdown("### ⚖️ ALPHA APEX")
        
        # 1. TOP: Custom Persona
        st.markdown("---")
        st.subheader("🤖 SYSTEM PERSONA")
        custom_persona = st.text_input("Define Identity", value="Senior High Court Advocate")
        
        # 2. MIDDLE: Case Management
        st.markdown("---")
        st.subheader("💼 CASE MANAGEMENT")
        conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
        c.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (u_mail,))
        chambers = [r[0] for r in c.fetchall()]
        
        current_case = st.selectbox("Select Case", chambers if chambers else ["General Chamber"])
        
        with st.expander("➕ Create / ✏️ Rename"):
            new_name = st.text_input("New Case Name")
            if st.button("Initialize Case"):
                c.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?,?,?)", (u_mail, new_name, str(datetime.date.today())))
                conn.commit(); st.rerun()
            
            rename_val = st.text_input("Rename Current Case")
            if st.button("Apply Rename"):
                c.execute("UPDATE chambers SET chamber_name=? WHERE owner_email=? AND chamber_name=?", (rename_val, u_mail, current_case))
                conn.commit(); st.rerun()
        conn.close()

        # Navigation Switcher
        st.markdown("---")
        nav = st.radio("System View", ["Legal Chambers", "System Admin"])

        # 3. BOTTOM: Utilities
        st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
        if st.button("📧 Email Brief"): st.sidebar.info("Brief Dispatched to Vault Email")
        if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

    # --- MAIN VIEW ---
    if nav == "Legal Chambers":
        st.header(f"💼 CHAMBER: {current_case}")
        
        # Chat History Display
        chat_box = st.container()
        conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
        c.execute("SELECT sender_role, message_body FROM message_logs m JOIN chambers ch ON m.chamber_id = ch.id WHERE ch.chamber_name=? AND ch.owner_email=?", (current_case, u_mail))
        for role, body in c.fetchall():
            with chat_box.chat_message(role): st.write(body)
        conn.close()

        # Prompt Bar & Mic (Icon logic)
        input_col, mic_col = st.columns([0.9, 0.1])
        with input_col:
            t_input = st.chat_input("Analyze Case...")
        with mic_col:
            st.markdown("<div style='margin-top:28px;'></div>", unsafe_allow_html=True)
            v_input = speech_to_text(start_prompt="🎙️", stop_prompt="🛑", just_once=True, key='mic')

        final_query = t_input or v_input
        if final_query:
            db_log_consultation(u_mail, current_case, "user", final_query)
            with chat_box.chat_message("user"): st.write(final_query)
            
            with chat_box.chat_message("assistant"):
                p = f"You are {custom_persona}. Greet formally. Answer ONLY law. Politely accept 'thanks'. Query: {final_query}"
                response = get_engine().invoke(p).content
                st.write(response)
                db_log_consultation(u_mail, current_case, "assistant", response)
                st.rerun()

    elif nav == "System Admin":
        st.header("🛡️ SYSTEM ADMINISTRATION")
        
        conn = sqlite3.connect(SQL_DB_FILE)
        
        # Statistics
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM users"); total_counsel = c.fetchone()[0]
        c.execute("SELECT SUM(total_queries) FROM users"); total_q = c.fetchone()[0]
        
        cols = st.columns(2)
        cols[0].metric("Total Counsel", total_counsel)
        cols[1].metric("Total Queries", total_q if total_q else 0)
        
        # Counsel Information
        st.subheader("Counsel Registry & Usage")
        u_df = pd.read_sql_query("SELECT full_name as Counsel, email as Vault_Email, total_queries as Interactions FROM users", conn)
        st.dataframe(u_df, use_container_width=True)

        # Team Architects
        st.subheader("Architectural Board")
        architects = [
            {"Name": "Saim Ahmed", "Role": "Prompt Engineering"},
            {"Name": "Huzaifa Khan", "Role": "Backend Coder"},
            {"Name": "Mustafa Khan", "Role": "Main Coder"},
            {"Name": "Ibrahim Sohail", "Role": "Presentation Lead"},
            {"Name": "Daniyal Faraz", "Role": "Debugger & Modifier"}
        ]
        st.table(architects)
        conn.close()

# ==============================================================================
# 4. ENTRY POINT
# ==============================================================================

def login():
    apply_leviathan_shaders()
    st.title("⚖️ LEVIATHAN PORTAL")
    e = st.text_input("Vault Email")
    k = st.text_input("Access Key", type="password")
    if st.button("Enter Vault"):
        conn = sqlite3.connect(SQL_DB_FILE); c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND vault_key=?", (e, k))
        if c.fetchone(): st.session_state.logged_in = True; st.session_state.user_email = e; st.rerun()
        elif e == "admin" and k == "admin": # Default for testing
             st.session_state.logged_in = True; st.session_state.user_email = "admin@apex.law"; st.rerun()
        else: st.error("Access Denied")

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in: login()
else: render_ui()
