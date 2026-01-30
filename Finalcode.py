# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM - v39.0
# ==============================================================================
# SYSTEM VERSION: 39.0 (ALL FEATURES COMPLETE)
# ALL 12 REQUESTED UPGRADES IMPLEMENTED
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
import json
import os
import time
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ------------------------------------------------------------------------------
# SECTION 1: CONFIGURATION
# ------------------------------------------------------------------------------

SYSTEM_CONFIG = {
    "APP_NAME": "Alpha Apex - Leviathan Law AI",
    "APP_ICON": "⚖️",
    "LAYOUT": "wide",
    "DB_FILENAME": "advocate_ai_v2.db",
    "DATA_REPOSITORY": "data",
    "VERSION_ID": "39.0.0-COMPLETE",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587
}

LEGAL_KEYWORDS = [
    'law', 'legal', 'court', 'case', 'judge', 'lawyer', 'attorney', 'contract', 
    'crime', 'criminal', 'civil', 'litigation', 'jurisdiction', 'statute', 'ordinance',
    'penal', 'constitution', 'amendment', 'act', 'section', 'article', 'plaintiff',
    'defendant', 'prosecution', 'defense', 'evidence', 'testimony', 'verdict', 
    'appeal', 'petition', 'writ', 'injunction', 'bail', 'custody', 'property',
    'inheritance', 'divorce', 'marriage', 'rights', 'violation', 'tort', 
    'negligence', 'liability', 'damages', 'compensation', 'settlement', 'agreement', 
    'clause', 'breach', 'enforcement', 'precedent', 'ruling', 'kicked out', 'house',
    'eviction', 'tenant', 'landlord', 'mother', 'father', 'family', 'dispute'
]

st.set_page_config(
    page_title=SYSTEM_CONFIG["APP_NAME"], 
    page_icon=SYSTEM_CONFIG["APP_ICON"], 
    layout=SYSTEM_CONFIG["LAYOUT"],
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# SECTION 2: SESSION STATE
# ------------------------------------------------------------------------------

def initialize_state():
    defaults = {
        "theme_mode": "dark",
        "logged_in": False,
        "active_ch": "General Litigation Chamber",
        "user_email": None,
        "username": None,
        "sys_persona": "Senior High Court Advocate",
        "sys_lang": "English",
        "show_new_case_modal": False,
        "show_delete_modal": False,
        "new_case_name": ""
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_state()

# ------------------------------------------------------------------------------
# SECTION 3: CSS STYLING (NO WHITE BAR)
# ------------------------------------------------------------------------------

def apply_shaders():
    """Enhanced CSS - WHITE BAR REMOVED"""
    
    if st.session_state.theme_mode == "dark":
        bg_primary = "#0b1120"
        bg_secondary = "#1a1f3a"
        text_primary = "#e8edf4"
        text_secondary = "#b4bdd0"
        border_color = "rgba(56, 189, 248, 0.2)"
        accent_color = "#38bdf8"
        sidebar_bg = "rgba(2, 6, 23, 0.95)"
        chat_bg = "rgba(30, 41, 59, 0.4)"
        prompt_bg = "#0a0f1a"
    else:
        bg_primary = "#f8fafc"
        bg_secondary = "#e2e8f0"
        text_primary = "#0f172a"
        text_secondary = "#475569"
        border_color = "rgba(14, 165, 233, 0.3)"
        accent_color = "#0284c7"
        sidebar_bg = "rgba(241, 245, 249, 0.98)"
        chat_bg = "rgba(241, 245, 249, 0.6)"
        prompt_bg = "#ffffff"

    css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=Space+Mono:wght@400;700&display=swap');
        
        * {{ 
            font-family: 'Crimson Pro', Georgia, serif;
            margin: 0;
            padding: 0;
        }}
        
        /* Main App */
        .stApp {{ 
            background: linear-gradient(135deg, {bg_primary} 0%, {bg_secondary} 50%, {bg_primary} 100%) !important;
            color: {text_primary} !important; 
        }}
        
        /* REMOVE WHITE BAR - Hide all Streamlit headers */
        header {{
            visibility: hidden !important;
            height: 0 !important;
            display: none !important;
        }}
        
        [data-testid="stHeader"] {{
            display: none !important;
            visibility: hidden !important;
        }}
        
        .stApp > header {{
            background-color: transparent !important;
            display: none !important;
        }}
        
        /* Remove top padding caused by hidden header */
        .main .block-container {{
            padding-top: 2rem !important;
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: {sidebar_bg} !important; 
            backdrop-filter: blur(25px) !important;
            border-right: 1px solid {border_color} !important;
        }}
        
        /* Chat Messages */
        .stChatMessage {{
            border-radius: 16px !important;
            padding: 2rem !important;
            border: 1px solid {border_color} !important;
            background: {chat_bg} !important;
            margin-bottom: 1.5rem !important;
        }}
        
        [data-testid="stChatMessageUser"] {{ 
            border-left: 4px solid {accent_color} !important; 
        }}
        
        [data-testid="stChatMessageAssistant"] {{ 
            border-left: 4px solid #ef4444 !important; 
        }}
        
        /* Typography */
        h1, h2, h3 {{ 
            color: {text_primary} !important; 
            font-weight: 700 !important; 
        }}
        
        p, span, div {{ 
            color: {text_primary} !important; 
        }}
        
        /* Logo */
        .logo-text {{
            color: {text_primary};
            font-size: 30px;
            font-weight: 900;
            font-family: 'Space Mono', monospace !important;
            text-shadow: 0 0 15px {accent_color};
        }}
        
        .sub-logo-text {{
            color: {accent_color};
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 3px;
            font-family: 'Space Mono', monospace !important;
            margin-bottom: 20px;
        }}
        
        /* Buttons */
        .stButton>button {{
            border-radius: 10px !important;
            font-weight: 600 !important;
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            padding: 0.6rem 1rem !important;
        }}
        
        .stButton>button:hover {{
            border-color: {accent_color} !important;
            box-shadow: 0 0 15px rgba(56, 189, 248, 0.3) !important;
        }}
        
        /* Quick Action Buttons */
        .quick-action-btn {{
            display: inline-block;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 8px;
            background: {bg_secondary};
            color: {text_primary};
            border: 1px solid {border_color};
            font-size: 14px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .quick-action-btn:hover {{
            background: {accent_color};
            transform: translateY(-2px);
        }}
        
        /* Input Fields */
        .stTextInput>div>div>input,
        .stTextArea>div>div>textarea {{
            background: rgba(30, 41, 59, 0.6) !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            border-radius: 10px !important;
        }}
        
        /* Chat Input Area - NO WHITE BAR */
        .stChatInputContainer {{
            background: {prompt_bg} !important;
            border-top: 1px solid {border_color} !important;
            padding: 15px !important;
        }}
        
        .stChatInput>div>div>textarea {{
            background: rgba(30, 41, 59, 0.6) !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            border-radius: 10px !important;
            padding: 12px !important;
        }}
        
        /* Mic Button Position - NEXT TO PROMPT BAR */
        [data-testid="stChatInput"] {{
            position: relative !important;
        }}
        
        .mic-next-to-prompt {{
            position: absolute !important;
            right: 15px !important;
            bottom: 12px !important;
            z-index: 100 !important;
        }}
        
        .mic-next-to-prompt button {{
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
            border: none !important;
            border-radius: 50% !important;
            width: 42px !important;
            height: 42px !important;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important;
            cursor: pointer !important;
        }}
        
        .mic-next-to-prompt button:hover {{
            transform: scale(1.1) !important;
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.6) !important;
        }}
        
        /* Tables */
        table {{
            color: {text_primary} !important;
        }}
        
        thead tr th {{
            background-color: {bg_secondary} !important;
            color: {text_primary} !important;
        }}
        
        /* Radio Buttons */
        .stRadio > div[role="radiogroup"] > label > div:first-child {{
            background-color: #ef4444 !important; 
        }}
        
        /* Hide Streamlit Branding */
        footer {{ visibility: hidden; }}
        #MainMenu {{ visibility: hidden; }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SECTION 4: LEGAL CONTEXT & RESPONSE HANDLERS
# ------------------------------------------------------------------------------

def is_greeting(text):
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 
                 'greetings', 'salaam', 'salam', 'assalam o alaikum', 'kaise hain']
    return any(g in text.lower() for g in greetings)

def is_farewell(text):
    farewells = ['bye', 'goodbye', 'see you', 'farewell', 'take care', 'allah hafiz', 
                 'khuda hafiz', 'alvida']
    return any(f in text.lower() for f in farewells)

def is_thank_you(text):
    thanks = ['thank', 'thanks', 'appreciate', 'grateful', 'shukriya', 'meherbani']
    return any(t in text.lower() for t in thanks)

def is_legal_context(text):
    """Enhanced to catch queries like 'my mother kicked me out'"""
    text_lower = text.lower()
    # Check for legal keywords OR length-based heuristic
    has_keywords = any(kw in text_lower for kw in LEGAL_KEYWORDS)
    # Questions about personal legal situations
    personal_legal = any(word in text_lower for word in ['should i', 'what can i', 'my rights', 'kicked out', 'evict'])
    
    return has_keywords or personal_legal or len(text) > 100

def get_formal_greeting():
    return f"""Good day! I am Alpha Apex, your dedicated legal intelligence advisor.

Welcome, **{st.session_state.username}**. How may I assist you with your legal matters today?"""

def get_formal_farewell():
    return """Thank you for consulting with Alpha Apex Legal Intelligence.

Should you require further assistance, I remain at your service. Wishing you success in your legal endeavors."""

def get_formal_thanks():
    return """You are most welcome. It is my privilege to assist you.

Should you have any further questions, please do not hesitate to reach out."""

def get_non_legal_response():
    return """I appreciate your inquiry, however, my expertise is limited to legal matters and jurisprudence.

I can assist with:
• Legal case analysis and strategy
• Contract review and interpretation
• Litigation support
• Legal research

Please provide a legal query for analysis."""

# ------------------------------------------------------------------------------
# SECTION 5: DATABASE FUNCTIONS
# ------------------------------------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(SYSTEM_CONFIG["DB_FILENAME"], check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Users table
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        email TEXT PRIMARY KEY, 
        full_name TEXT, 
        vault_key TEXT, 
        registration_date TEXT,
        last_login TEXT,
        total_queries INTEGER DEFAULT 0, 
        provider TEXT DEFAULT 'Local'
    )""")
    
    # Chambers table
    c.execute("""CREATE TABLE IF NOT EXISTS chambers (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        owner_email TEXT, 
        chamber_name TEXT, 
        init_date TEXT,
        FOREIGN KEY(owner_email) REFERENCES users(email)
    )""")
    
    # Message logs
    c.execute("""CREATE TABLE IF NOT EXISTS message_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        chamber_id INTEGER, 
        sender_role TEXT, 
        message_body TEXT, 
        ts_created TEXT,
        FOREIGN KEY(chamber_id) REFERENCES chambers(id)
    )""")
    
    # System telemetry
    c.execute("""CREATE TABLE IF NOT EXISTS system_telemetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        user_email TEXT, 
        event_type TEXT, 
        description TEXT, 
        event_timestamp TEXT
    )""")
    
    conn.commit()
    conn.close()

def db_verify_vault_access(email, password):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
    res = c.fetchone()
    
    if res:
        # Update last login
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("UPDATE users SET last_login=? WHERE email=?", (ts, email))
        c.execute("INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp) VALUES (?, ?, ?, ?)",
                 (email, "LOGIN", "User logged in", ts))
        conn.commit()
    
    conn.close()
    return res[0] if res else None

def db_create_user(email, name, password):
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if exists
    c.execute("SELECT email FROM users WHERE email=?", (email,))
    if c.fetchone():
        conn.close()
        return False
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO users (email, full_name, vault_key, registration_date, last_login) VALUES (?, ?, ?, ?, ?)",
             (email, name, password, ts, ts))
    
    # Create default chamber
    c.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?, ?, ?)",
             (email, "General Litigation Chamber", ts))
    
    # Log registration
    c.execute("INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp) VALUES (?, ?, ?, ?)",
             (email, "REGISTRATION", "New user registered", ts))
    
    conn.commit()
    conn.close()
    return True

def db_log_consultation(email, chamber_name, role, content):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    res = c.fetchone()
    
    if res:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) VALUES (?, ?, ?, ?)",
                 (res[0], role, content, ts))
        
        if role == "user":
            c.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email=?", (email,))
        
        conn.commit()
    conn.close()

def db_fetch_chamber_history(email, chamber_name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""SELECT m.sender_role, m.message_body 
                 FROM message_logs m 
                 JOIN chambers c ON m.chamber_id = c.id 
                 WHERE c.owner_email=? AND c.chamber_name=? 
                 ORDER BY m.id ASC""", (email, chamber_name))
    rows = c.fetchall()
    conn.close()
    return [{"role": r[0], "content": r[1]} for r in rows]

def db_create_chamber(email, chamber_name):
    """NEW: Create new chamber"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Check if exists
    c.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    if c.fetchone():
        conn.close()
        return False
    
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?, ?, ?)",
             (email, chamber_name, ts))
    c.execute("INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp) VALUES (?, ?, ?, ?)",
             (email, "NEW_CHAMBER", f"Created chamber: {chamber_name}", ts))
    conn.commit()
    conn.close()
    return True

def db_delete_chamber(email, chamber_name):
    """NEW: Delete chamber"""
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
    res = c.fetchone()
    
    if res:
        chamber_id = res[0]
        # Delete messages
        c.execute("DELETE FROM message_logs WHERE chamber_id=?", (chamber_id,))
        # Delete chamber
        c.execute("DELETE FROM chambers WHERE id=?", (chamber_id,))
        
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp) VALUES (?, ?, ?, ?)",
                 (email, "DELETE_CHAMBER", f"Deleted chamber: {chamber_name}", ts))
        conn.commit()
        conn.close()
        return True
    
    conn.close()
    return False

def db_get_interaction_logs(limit=100):
    """Get system logs"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT user_email, event_type, description, event_timestamp FROM system_telemetry ORDER BY id DESC LIMIT ?", (limit,))
    rows = c.fetchall()
    conn.close()
    return [{"User": r[0], "Event": r[1], "Description": r[2], "Timestamp": r[3]} for r in rows]

# ------------------------------------------------------------------------------
# SECTION 6: AI ENGINE
# ------------------------------------------------------------------------------

@st.cache_resource
def get_ai_engine():
    try:
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=st.secrets["GOOGLE_API_KEY"],
            temperature=0.19
        )
    except:
        return None

def get_legal_response(engine, query, persona, lang):
    """IRAC FORMAT FOR LEGAL QUERIES ONLY"""
    
    # Handle greetings
    if is_greeting(query):
        return get_formal_greeting()
    
    # Handle farewells
    if is_farewell(query):
        return get_formal_farewell()
    
    # Handle thanks
    if is_thank_you(query):
        return get_formal_thanks()
    
    # Check legal context
    if not is_legal_context(query):
        return get_non_legal_response()
    
    # Legal query - use IRAC format
    prompt = f"""You are {persona}, a distinguished legal expert.

CRITICAL INSTRUCTIONS:
1. Respond in {lang} language
2. Use IRAC format (Issue, Rule, Application, Conclusion)
3. Be formal and professional
4. Cite relevant legal provisions when applicable

Structure:

**ISSUE:**
[Identify the legal issue]

**RULE:**
[State relevant legal rules, statutes, or precedents]

**APPLICATION:**
[Apply rules to the specific facts]

**CONCLUSION:**
[Provide clear conclusion]

User Query: {query}

Provide IRAC analysis:"""
    
    try:
        response = engine.invoke(prompt).content
        return response
    except Exception as e:
        return f"Error generating analysis: {str(e)}"

# ------------------------------------------------------------------------------
# SECTION 7: EMAIL DISPATCH
# ------------------------------------------------------------------------------

def send_email_brief(target_email, chamber_name, history):
    """Send full conversation via email"""
    try:
        sender = st.secrets["EMAIL_USER"]
        password = st.secrets["EMAIL_PASS"].replace(" ", "")
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex <{sender}>"
        msg['To'] = target_email
        msg['Subject'] = f"Legal Brief: {chamber_name} - {datetime.date.today()}"
        
        body = "=" * 70 + "\n"
        body += "ALPHA APEX LEGAL INTELLIGENCE BRIEF\n"
        body += "=" * 70 + "\n\n"
        body += f"CHAMBER: {chamber_name}\n"
        body += f"DATE: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        body += f"STATUS: CONFIDENTIAL\n\n"
        body += "=" * 70 + "\n\n"
        
        for idx, msg_item in enumerate(history, 1):
            role = "COUNSEL" if msg_item['role'] == 'user' else "AI ADVISOR"
            body += f"[MESSAGE {idx} - {role}]\n"
            body += "-" * 70 + "\n"
            body += f"{msg_item['content']}\n\n"
        
        body += "=" * 70 + "\n"
        body += f"Generated by Alpha Apex v{SYSTEM_CONFIG['VERSION_ID']}\n"
        body += "=" * 70 + "\n"
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(SYSTEM_CONFIG["SMTP_SERVER"], SYSTEM_CONFIG["SMTP_PORT"])
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Email error: {e}")
        return False

# ------------------------------------------------------------------------------
# SECTION 8: MAIN INTERFACE
# ------------------------------------------------------------------------------

def render_main_interface():
    apply_shaders()
    
    # Language map with NEW languages
    lang_map = {
        "English": "en-US",
        "Urdu": "ur-PK",
        "Sindhi": "sd-PK",
        "Punjabi": "pa-PK",
        "Pashto": "ps-AF",  # NEW
        "Balochi": "bal-PK"  # NEW
    }
    
    # Sidebar
    with st.sidebar:
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-logo-text'>Leviathan v39.0</div>", unsafe_allow_html=True)
        
        nav = st.radio("Navigation", ["Chambers", "Law Library", "System Admin"])
        
        st.divider()
        
        if nav == "Chambers":
            st.markdown("**Active Cases**")
            
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (st.session_state.user_email,))
            chambers = [r[0] for r in c.fetchall()]
            conn.close()
            
            if not chambers:
                chambers = ["General Litigation Chamber"]
            
            st.session_state.active_ch = st.radio("Select Case", chambers, label_visibility="collapsed")
            
            # NEW CASE BUTTON - FUNCTIONAL
            col1, col2 = st.columns(2)
            with col1:
                if st.button("➕ New Case"):
                    st.session_state.show_new_case_modal = True
            
            with col2:
                if st.button("🗑️ Delete"):
                    if st.session_state.active_ch != "General Litigation Chamber":
                        st.session_state.show_delete_modal = True
                    else:
                        st.warning("Cannot delete default chamber")
            
            # NEW CASE MODAL - FUNCTIONAL
            if st.session_state.get('show_new_case_modal', False):
                new_name = st.text_input("Enter case name:", key="new_case_input")
                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Create", key="create_btn"):
                        if new_name:
                            if db_create_chamber(st.session_state.user_email, new_name):
                                st.success(f"✓ Created: {new_name}")
                                st.session_state.active_ch = new_name
                                st.session_state.show_new_case_modal = False
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Case already exists")
                with col_b:
                    if st.button("Cancel", key="cancel_btn"):
                        st.session_state.show_new_case_modal = False
                        st.rerun()
            
            # DELETE MODAL - FUNCTIONAL
            if st.session_state.get('show_delete_modal', False):
                st.warning(f"⚠️ Delete '{st.session_state.active_ch}'?")
                col_x, col_y = st.columns(2)
                with col_x:
                    if st.button("Yes", key="del_yes"):
                        if db_delete_chamber(st.session_state.user_email, st.session_state.active_ch):
                            st.success("✓ Deleted")
                            st.session_state.active_ch = "General Litigation Chamber"
                            st.session_state.show_delete_modal = False
                            time.sleep(1)
                            st.rerun()
                with col_y:
                    if st.button("No", key="del_no"):
                        st.session_state.show_delete_modal = False
                        st.rerun()
            
            st.divider()
            
            # EMAIL BRIEF BUTTON - FUNCTIONAL
            if st.button("📧 Email Brief", use_container_width=True):
                history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
                if history:
                    with st.spinner("Sending..."):
                        if send_email_brief(st.session_state.user_email, st.session_state.active_ch, history):
                            st.success("✓ Email sent!")
                        else:
                            st.error("Failed to send")
                else:
                    st.warning("No conversation to send")
        
        st.divider()
        
        with st.expander("⚙️ Settings"):
            st.session_state.sys_lang = st.selectbox("Language", list(lang_map.keys()))
            st.session_state.sys_persona = st.text_input("Persona", value="Senior High Court Advocate")
            
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()
    
    # Main Content
    if nav == "Chambers":
        st.header(f"💼 CASE: {st.session_state.active_ch}")
        
        # QUICK ACTIONS - NEW FEATURE
        st.markdown("### ⚡ Quick Actions")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 Infer", use_container_width=True):
                st.session_state.quick_action = "Provide a legal inference based on the conversation so far."
        with col2:
            if st.button("📝 Summarize", use_container_width=True):
                st.session_state.quick_action = "Summarize this legal case in IRAC format."
        with col3:
            if st.button("⚖️ Analyze", use_container_width=True):
                st.session_state.quick_action = "Provide detailed legal analysis of this matter."
        with col4:
            if st.button("📋 Draft", use_container_width=True):
                st.session_state.quick_action = "Draft a legal document based on this case."
        
        # Execute quick action if set
        if st.session_state.get('quick_action'):
            query = st.session_state.quick_action
            st.session_state.quick_action = None
            
            db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "user", query)
            with st.chat_message("user"):
                st.markdown(query)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    engine = get_ai_engine()
                    if engine:
                        response = get_legal_response(engine, query, st.session_state.sys_persona, st.session_state.sys_lang)
                        st.markdown(response)
                        db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "assistant", response)
            st.rerun()
        
        st.divider()
        
        # Chat History
        history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Input Area with Mic
        text_input = st.chat_input("Enter your legal query...")
        
        # Mic button NEXT TO PROMPT BAR
        st.markdown('<div class="mic-next-to-prompt">', unsafe_allow_html=True)
        voice_input = speech_to_text(
            language=lang_map[st.session_state.sys_lang],
            start_prompt="🎙️",
            stop_prompt="🛑",
            key='mic_main',
            just_once=True
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
        query = text_input or voice_input
        
        if query:
            db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "user", query)
            
            with st.chat_message("user"):
                st.markdown(query)
            
            with st.chat_message("assistant"):
                with st.spinner("⚖️ Analyzing..."):
                    engine = get_ai_engine()
                    if engine:
                        response = get_legal_response(engine, query, st.session_state.sys_persona, st.session_state.sys_lang)
                        st.markdown(response)
                        db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "assistant", response)
            st.rerun()
    
    elif nav == "Law Library":
        st.header("📚 Law Library")
        st.subheader("Synchronized Legal Assets")
        
        if not os.path.exists(SYSTEM_CONFIG["DATA_REPOSITORY"]):
            os.makedirs(SYSTEM_CONFIG["DATA_REPOSITORY"])
        
        files = [f for f in os.listdir(SYSTEM_CONFIG["DATA_REPOSITORY"]) if f.endswith('.pdf')]
        
        st.metric("Total PDFs", len(files))
        
        if files:
            st.markdown("**Available Documents**")
            data = []
            
            for file in files:
                path = os.path.join(SYSTEM_CONFIG["DATA_REPOSITORY"], file)
                size = os.path.getsize(path)
                
                # Try to get page count
                try:
                    reader = PdfReader(path)
                    pages = len(reader.pages)
                    status = "✓ Verified"
                except:
                    pages = "N/A"
                    status = "⚠️ Error"
                
                data.append({
                    "Filename": file,
                    "Size (KB)": round(size / 1024, 2),
                    "Pages": pages,
                    "Status": status
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No PDF files found in data directory")
    
    elif nav == "System Admin":
        st.header("🛡️ System Administration")
        
        tabs = st.tabs(["📊 Interaction Logs", "👥 Our Team"])
        
        with tabs[0]:
            st.subheader("System Interaction Logs")
            
            log_limit = st.selectbox("Show entries:", [50, 100, 200], index=1)
            logs = db_get_interaction_logs(log_limit)
            
            if logs:
                df = pd.DataFrame(logs)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"Showing {len(logs)} most recent events")
            else:
                st.info("No logs available")
        
        with tabs[1]:
            st.subheader("🏗️ Architectural Board")
            team = [
                {"Name": "Saim Ahmed", "Role": "Lead Architect", "Domain": "System Logic"},
                {"Name": "Huzaifa Khan", "Role": "AI Lead", "Domain": "LLM Engineering"},
                {"Name": "Mustafa Khan", "Role": "DBA", "Domain": "Database Security"},
                {"Name": "Ibrahim Sohail", "Role": "UI Lead", "Domain": "Frontend Design"},
                {"Name": "Daniyal Faraz", "Role": "QA Lead", "Domain": "Integration Testing"}
            ]
            df = pd.DataFrame(team)
            st.table(df)

# ------------------------------------------------------------------------------
# SECTION 9: AUTHENTICATION
# ------------------------------------------------------------------------------

def render_portal():
    apply_shaders()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("⚖️ ALPHA APEX PORTAL")
        st.markdown("### Legal Intelligence System")
        
        st.divider()
        
        tabs = st.tabs(["🔐 Login", "📝 Register"])
        
        with tabs[0]:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_pass")
            
            if st.button("Authorize Access", use_container_width=True):
                user = db_verify_vault_access(email, password)
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_email = email
                    st.session_state.username = user
                    st.rerun()
                else:
                    st.error("Invalid credentials")
        
        with tabs[1]:
            reg_email = st.text_input("Email", key="reg_email")
            reg_name = st.text_input("Full Name", key="reg_name")
            reg_pass = st.text_input("Password", type="password", key="reg_pass")
            
            if st.button("Create Account", use_container_width=True):
                if db_create_user(reg_email, reg_name, reg_pass):
                    st.success("✓ Account created! Please login.")
                else:
                    st.error("Email already exists")

# ------------------------------------------------------------------------------
# SECTION 10: MAIN EXECUTION
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    init_db()
    
    if not st.session_state.logged_in:
        render_portal()
    else:
        render_main_interface()

# ==============================================================================
# END OF ALPHA APEX v39.0 - ALL 12 FEATURES COMPLETE
# ==============================================================================
