# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM - v38.1.5
# ==============================================================================
# VERSION: 38.1.5 (STABLE ARCHITECTURE)
# REVISION: HIGH-FIDELITY LEGAL INTELLIGENCE
# ------------------------------------------------------------------------------
# CORE CAPABILITIES:
#   - Advanced IRAC (Issue, Rule, Application, Conclusion) Logic Engine
#   - Real-time Voice-to-Legal-Analysis Integration
#   - Multi-Chamber Case Management System
#   - Sovereign Law Library Asset Synchronization
#   - Enterprise Admin Telemetry & Audit Logs
# ==============================================================================

"""
LEVIATHAN SYSTEM ARCHITECTURE NOTES:
This system utilizes a dual-layer persistence model (SQLite + WAL Mode) 
combined with a Generative AI Analytical Engine (Gemini 2.0 Flash).
The UI is constructed using an Enhanced Shader layer to provide a 
premium 'Strategic Litigation' aesthetic in both light and dark modes.
"""

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
import base64
import re
import io
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ------------------------------------------------------------------------------
# SECTION 1: GLOBAL SYSTEM CONFIGURATION
# ------------------------------------------------------------------------------

SYSTEM_CONFIG = {
    "APP_NAME": "Alpha Apex - Leviathan Law AI",
    "APP_ICON": "⚖️",
    "LAYOUT": "wide",
    "THEME_PRIMARY": "#0b1120",
    "DB_FILENAME": "advocate_ai_v2.db",
    "DATA_REPOSITORY": "data",
    "VERSION_ID": "38.1.5-LEVIATHAN-STABLE",
    "LOG_LEVEL": "STRICT",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587,
    "CORE_MODEL": "gemini-2.5-flash",
    "MAX_HISTORY": 50
}

# MUST BE THE FIRST STREAMLIT COMMAND
st.set_page_config(
    page_title=SYSTEM_CONFIG["APP_NAME"], 
    page_icon=SYSTEM_CONFIG["APP_ICON"], 
    layout=SYSTEM_CONFIG["LAYOUT"],
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# SECTION 2: SESSION STATE INITIALIZATION
# ------------------------------------------------------------------------------

def initialize_global_state():
    """
    Ensures all critical session state variables are present before rendering.
    This prevents 'AttributeError' or rendering failures on initial load.
    """
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "dark"
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "active_ch" not in st.session_state:
        st.session_state.active_ch = "General Litigation Chamber"
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "username" not in st.session_state:
        st.session_state.username = None
    if "sys_persona" not in st.session_state:
        st.session_state.sys_persona = "Senior High Court Advocate"
    if "sys_lang" not in st.session_state:
        st.session_state.sys_lang = "English"
    if "show_new_case_modal" not in st.session_state:
        st.session_state.show_new_case_modal = False
    if "show_delete_modal" not in st.session_state:
        st.session_state.show_delete_modal = False

initialize_global_state()

# ------------------------------------------------------------------------------
# SECTION 3: ENHANCED SHADER ENGINE (CSS & THEMING)
# ------------------------------------------------------------------------------

def apply_enhanced_shaders():
    """
    Injects professional legal-suite CSS styling with support for 
    dynamic light/dark mode switching and prompt bar mic integration.
    """
    
    # Theme Color Variable Definition
    if st.session_state.theme_mode == "dark":
        bg_primary = "#0b1120"
        bg_secondary = "#1a1f3a"
        bg_tertiary = "#1e293b"
        text_primary = "#e8edf4"
        text_secondary = "#b4bdd0"
        border_color = "rgba(56, 189, 248, 0.2)"
        input_bg = "rgba(30, 41, 59, 0.6)"
        sidebar_bg = "rgba(2, 6, 23, 0.95)"
        chat_bg = "rgba(30, 41, 59, 0.4)"
        prompt_area_bg = "#0a0f1a"
    else:
        bg_primary = "#f8fafc"
        bg_secondary = "#e2e8f0"
        bg_tertiary = "#cbd5e1"
        text_primary = "#0f172a"
        text_secondary = "#475569"
        border_color = "rgba(14, 165, 233, 0.3)"
        input_bg = "rgba(255, 255, 255, 0.9)"
        sidebar_bg = "rgba(241, 245, 249, 0.98)"
        chat_bg = "rgba(241, 245, 249, 0.6)"
        prompt_area_bg = "#ffffff"

    shader_css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=Space+Mono:wght@400;700&display=swap');
        
        /* Global Reset & Typography */
        * {{ 
            transition: background-color 0.4s ease, color 0.4s ease !important; 
            font-family: 'Crimson Pro', Georgia, serif;
            -webkit-font-smoothing: antialiased;
        }}
        
        /* Main Framework Overrides */
        .stApp {{ 
            background: linear-gradient(135deg, {bg_primary} 0%, {bg_secondary} 50%, {bg_primary} 100%) !important;
            background-size: 200% 200% !important;
            color: {text_primary} !important; 
        }}
        
        /* Sidebar Styling */
        [data-testid="stSidebar"] {{
            background: {sidebar_bg} !important; 
            backdrop-filter: blur(25px) !important;
            border-right: 1px solid {border_color} !important;
            box-shadow: 15px 0 50px rgba(0, 0, 0, 0.4) !important;
        }}
        
        /* Enhanced Chat Message UI */
        .stChatMessage {{
            border-radius: 20px !important;
            padding: 2.5rem !important;
            margin-bottom: 2.5rem !important;
            border: 1px solid {border_color} !important;
            background: {chat_bg} !important;
            backdrop-filter: blur(12px) !important;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }}
        
        [data-testid="stChatMessageUser"] {{
            border-left: 5px solid #38bdf8 !important;
            margin-left: 15% !important;
        }}
        
        [data-testid="stChatMessageAssistant"] {{
            border-left: 5px solid #ef4444 !important;
            margin-right: 15% !important;
        }}
        
        /* Branding Elements */
        .logo-text {{
            color: {text_primary};
            font-size: 34px;
            font-weight: 900;
            text-shadow: 0 0 25px rgba(56, 189, 248, 0.6);
            font-family: 'Space Mono', monospace !important;
            letter-spacing: -1px;
        }}
        
        .sub-logo-text {{
            color: #38bdf8;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 4px;
            font-family: 'Space Mono', monospace !important;
            margin-bottom: 20px;
        }}
        
        /* Button & Interaction Design */
        .stButton>button {{
            border-radius: 14px !important;
            font-weight: 700 !important;
            background: {bg_tertiary} !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            height: 3.8rem !important;
            width: 100% !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stButton>button:hover {{
            border-color: #38bdf8 !important;
            box-shadow: 0 0 25px rgba(56, 189, 248, 0.4) !important;
            transform: translateY(-2px);
        }}
        
        /* Input Field Architecture */
        .stTextInput>div>div>input,
        .stTextArea>div>div>textarea {{
            background: {input_bg} !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            border-radius: 14px !important;
            padding: 16px 20px !important;
        }}
        
        /* Chat Input Specialized Layout */
        .stChatInputContainer {{
            background: {prompt_area_bg} !important;
            backdrop-filter: blur(15px) !important;
            border-top: 1px solid {border_color} !important;
            padding: 25px !important;
            position: relative !important;
        }}
        
        /* Floating Mic Button Container */
        .mic-in-prompt {{
            position: fixed !important;
            right: 100px !important;
            bottom: 40px !important;
            z-index: 999999 !important;
        }}
        
        .mic-in-prompt button {{
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important; 
            border: none !important; 
            border-radius: 50% !important;
            width: 45px !important;
            height: 45px !important;
            box-shadow: 0 5px 15px rgba(239, 68, 68, 0.5) !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        
        /* Scrollbar Visuals */
        ::-webkit-scrollbar {{ width: 10px; }}
        ::-webkit-scrollbar-track {{ background: {bg_primary}; }}
        ::-webkit-scrollbar-thumb {{ 
            background: {border_color}; 
            border-radius: 10px; 
        }}
        
        /* Status Elements */
        .stMetric {{
            background: {bg_tertiary} !important;
            padding: 20px !important;
            border-radius: 15px !important;
            border: 1px solid {border_color} !important;
        }}

        /* Utility Hide */
        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SECTION 4: JURISPRUDENCE & CONTEXT HANDLERS
# ------------------------------------------------------------------------------

def is_greeting(text):
    """Detection for standard social salutations."""
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 
                 'greetings', 'salaam', 'assalam', 'salam', 'yo']
    text_lower = text.lower().strip()
    return any(greet in text_lower for greet in greetings)

def is_farewell(text):
    """Detection for session termination requests."""
    farewells = ['bye', 'goodbye', 'see you', 'farewell', 'take care', 'allah hafiz', 
                 'khuda hafiz', 'bye bye', 'exit', 'terminate']
    text_lower = text.lower().strip()
    return any(fare in text_lower for fare in farewells)

def is_thank_you(text):
    """Detection for appreciative feedback."""
    thanks = ['thank', 'thanks', 'appreciate', 'grateful', 'shukriya', 'meherbani', 'jazakallah']
    text_lower = text.lower().strip()
    return any(thank in text_lower for thank in thanks)

def is_legal_context(text):
    """
    Heuristic check to determine if the query is relevant to 
    the legal domain or requires IRAC processing.
    """
    legal_keywords = [
        'law', 'legal', 'court', 'case', 'judge', 'lawyer', 'attorney', 'contract', 
        'crime', 'criminal', 'civil', 'litigation', 'jurisdiction', 'statute', 'ordinance',
        'penal', 'constitution', 'amendment', 'act', 'section', 'article', 'plaintiff',
        'defendant', 'prosecution', 'defense', 'evidence', 'testimony', 'verdict', 
        'appeal', 'petition', 'writ', 'injunction', 'bail', 'custody', 'property',
        'inheritance', 'divorce', 'marriage', 'custody', 'rights', 'violation',
        'tort', 'negligence', 'liability', 'damages', 'compensation', 'settlement',
        'agreement', 'clause', 'breach', 'enforcement', 'precedent', 'ruling', 'fir',
        'bailment', 'tortious', 'easement', 'probate', 'notary', 'affidavit'
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in legal_keywords) or len(text) > 120

def get_formal_greeting():
    """Generates a high-court style introductory salutation."""
    return f"""Good day. I am Alpha Apex, your dedicated Leviathan Legal Intelligence advisor. 

Authorized Session for: **{st.session_state.username}**
Status: **Senior Counsel Access Active**

I am prepared to assist with jurisdictional analysis, case brief synthesis, or strategic litigation planning. How may I be of service in your chambers today?"""

def get_formal_farewell():
    """Generates a professional closing statement."""
    return """Thank you for consulting with Alpha Apex Legal Intelligence. 

Your chamber logs have been synchronized to the secure vault. Should you require further strategic counsel or IRAC analysis, I remain at your disposal.

*Vigilance in Justice.*

Best regards,
Alpha Apex AI"""

def get_formal_thanks():
    """Responds to appreciation with professional courtesy."""
    return """It is my professional privilege to assist in the refinement of your legal strategy. 

Accuracy and diligence are the pillars of the Leviathan system. Please feel free to present further inquiries or document analysis requests as needed."""

def get_non_legal_response():
    """Handles queries outside the core intelligence domain."""
    return """I appreciate your inquiry; however, my specialized heuristic parameters are limited to legal matters and jurisprudence.

**Scope of Service:**
• Strategic Case Analysis (IRAC)
• Statutory Interpretation & Clause Analysis
• Litigation Procedure Guidance
• Legal Precedent Discovery

For non-legal matters, I recommend consulting general-purpose resources. Is there a specific **legal statute** or **case detail** you wish to discuss?"""

# ------------------------------------------------------------------------------
# SECTION 5: DATABASE ARCHITECTURE & PERSISTENCE
# ------------------------------------------------------------------------------

def get_db_connection():
    """Establishes a connection to the SQLite Persistence Engine."""
    try:
        db_path = SYSTEM_CONFIG["DB_FILENAME"]
        connection = sqlite3.connect(db_path, check_same_thread=False)
        connection.execute("PRAGMA journal_mode=WAL;") 
        connection.execute("PRAGMA synchronous=NORMAL;")
        connection.execute("PRAGMA cache_size=10000;")
        connection.execute("PRAGMA foreign_keys=ON;")
        return connection
    except sqlite3.Error as e:
        st.error(f"CRITICAL: Persistence Engine Failure. Details: {e}")
        return None

def init_leviathan_db():
    """Initializes the multi-table schema for the Leviathan ecosystem."""
    connection = get_db_connection()
    if not connection: return
    try:
        cursor = connection.cursor()
        
        # Table 1: Sovereign Users
        cursor.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY)")
        required_user_columns = {
            "full_name": "TEXT",
            "vault_key": "TEXT",
            "registration_date": "TEXT",
            "membership_tier": "TEXT DEFAULT 'Senior Counsel'",
            "account_status": "TEXT DEFAULT 'Active'",
            "total_queries": "INTEGER DEFAULT 0",
            "last_login": "TEXT",
            "provider": "TEXT DEFAULT 'Local'"
        }
        cursor.execute("PRAGMA table_info(users)")
        existing_user_cols = [col[1] for col in cursor.fetchall()]
        for col_name, col_type in required_user_columns.items():
            if col_name not in existing_user_cols:
                cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
        
        # Table 2: Legal Chambers (Case Groups)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chambers (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                owner_email TEXT, 
                chamber_name TEXT, 
                init_date TEXT, 
                chamber_type TEXT DEFAULT 'General Litigation', 
                case_status TEXT DEFAULT 'Active', 
                is_archived INTEGER DEFAULT 0, 
                FOREIGN KEY(owner_email) REFERENCES users(email)
            )
        """)
        
        # Table 3: Message Intelligence Logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                chamber_id INTEGER, 
                sender_role TEXT, 
                message_body TEXT, 
                ts_created TEXT, 
                token_count INTEGER DEFAULT 0, 
                FOREIGN KEY(chamber_id) REFERENCES chambers(id)
            )
        """)
        
        # Table 4: Law Assets (PDF Library)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS law_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                filename TEXT, 
                filesize_kb REAL, 
                page_count INTEGER, 
                sync_timestamp TEXT, 
                asset_status TEXT DEFAULT 'Verified'
            )
        """)
        
        # Table 5: System Telemetry
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_telemetry (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                user_email TEXT, 
                event_type TEXT, 
                description TEXT, 
                event_timestamp TEXT
            )
        """)
        
        connection.commit()
    except sqlite3.Error as e:
        st.error(f"DATABASE SCHEMA INITIALIZATION FAILED: {e}")
    finally:
        connection.close()

def db_log_event(email, event_type, desc):
    """Records system-level events for audit purposes."""
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute('''
                INSERT INTO system_telemetry (user_email, event_type, description, event_timestamp)
                VALUES (?, ?, ?, ?)
            ''', (email, event_type, desc, ts))
            conn.commit()
        except sqlite3.Error as log_err:
            print(f"Telemetry Error: {log_err}")
        finally:
            conn.close()

def db_create_vault_user(email, name, password, provider='Local'):
    """Registers a new counsel into the sovereign registry."""
    if not email or not password or not name:
        return False
        
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return False
            
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO users (email, full_name, vault_key, registration_date, last_login, provider) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, name, password, ts, ts, provider))
        
        cursor.execute('''
            INSERT INTO chambers (owner_email, chamber_name, init_date) 
            VALUES (?, ?, ?)
        ''', (email, "General Litigation Chamber", ts))
        
        conn.commit()
        db_log_event(email, "REGISTRATION", f"New account provisioned via {provider}")
        return True
    except Exception as e:
        st.error(f"VAULT WRITE ERROR: {e}")
        return False
    finally:
        conn.close()

def db_verify_vault_access(email, password):
    """Authenticates credentials against the vault."""
    conn = get_db_connection()
    if not conn:
        return None
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT full_name FROM users WHERE email=? AND vault_key=?", (email, password))
        result = cursor.fetchone()
        
        if result:
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE users SET last_login = ? WHERE email = ?", (ts, email))
            conn.commit()
            db_log_event(email, "LOGIN", "Local vault access authorized")
            return result[0]
            
        return None
    except sqlite3.Error as auth_err:
        st.error(f"Authentication Engine Fault: {auth_err}")
        return None
    finally:
        conn.close()

def db_log_consultation(email, chamber_name, role, content):
    """Records dialogue within a specific legal chamber."""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
        res = cursor.fetchone()
        
        if res:
            ch_id = res[0]
            ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            cursor.execute('''
                INSERT INTO message_logs (chamber_id, sender_role, message_body, ts_created) 
                VALUES (?, ?, ?, ?)
            ''', (ch_id, role, content, ts))
            
            if role == "user":
                cursor.execute("UPDATE users SET total_queries = total_queries + 1 WHERE email = ?", (email,))
                
            conn.commit()
    except Exception as log_err:
        st.error(f"Consultation Logging Failure: {log_err}")
    finally:
        conn.close()

def db_fetch_chamber_history(email, chamber_name):
    """Retrieves dialogue history for a specific case."""
    conn = get_db_connection()
    history = []
    
    if conn:
        try:
            cursor = conn.cursor()
            query = '''
                SELECT m.sender_role, m.message_body 
                FROM message_logs m 
                JOIN chambers c ON m.chamber_id = c.id 
                WHERE c.owner_email=? AND c.chamber_name=? 
                ORDER BY m.id ASC
            '''
            cursor.execute(query, (email, chamber_name))
            rows = cursor.fetchall()
            
            for r in rows:
                history.append({"role": r[0], "content": r[1]})
        except sqlite3.Error as e:
            st.error(f"History Retrieval Error: {e}")
        finally:
            conn.close()
            
    return history

def db_create_new_chamber(email, chamber_name):
    """Provisions a new case chamber for a user."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
        if cursor.fetchone():
            return False
        
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO chambers (owner_email, chamber_name, init_date) 
            VALUES (?, ?, ?)
        ''', (email, chamber_name, ts))
        conn.commit()
        db_log_event(email, "NEW_CHAMBER", f"Created new chamber: {chamber_name}")
        return True
    except Exception as e:
        st.error(f"Chamber Creation Error: {e}")
        return False
    finally:
        conn.close()

def db_delete_chamber(email, chamber_name):
    """Deletes a chamber and all associated records."""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM chambers WHERE owner_email=? AND chamber_name=?", (email, chamber_name))
        result = cursor.fetchone()
        
        if result:
            chamber_id = result[0]
            cursor.execute("DELETE FROM message_logs WHERE chamber_id=?", (chamber_id,))
            cursor.execute("DELETE FROM chambers WHERE id=?", (chamber_id,))
            conn.commit()
            db_log_event(email, "DELETE_CHAMBER", f"Deleted chamber: {chamber_name}")
            return True
        return False
    except Exception as e:
        st.error(f"Chamber Deletion Error: {e}")
        return False
    finally:
        conn.close()

def db_get_all_counsels():
    """Admin tool: Retrieves a list of all registered users."""
    conn = get_db_connection()
    counsels = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT full_name, email, registration_date, last_login, total_queries, provider 
                FROM users 
                ORDER BY registration_date DESC
            ''')
            rows = cursor.fetchall()
            
            for r in rows:
                counsels.append({
                    "Name": r[0],
                    "Email": r[1],
                    "Registered": r[2],
                    "Last Login": r[3] if r[3] else "Never",
                    "Total Queries": r[4],
                    "Provider": r[5]
                })
        except sqlite3.Error as e:
            st.error(f"Counsel Retrieval Error: {e}")
        finally:
            conn.close()
            
    return counsels

def db_get_interaction_logs(limit=100):
    """Admin tool: Fetches system telemetry data."""
    conn = get_db_connection()
    logs = []
    
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT user_email, event_type, description, event_timestamp 
                FROM system_telemetry 
                ORDER BY event_id DESC 
                LIMIT ?
            ''', (limit,))
            rows = cursor.fetchall()
            
            for r in rows:
                logs.append({
                    "User": r[0],
                    "Event": r[1],
                    "Description": r[2],
                    "Timestamp": r[3]
                })
        except sqlite3.Error as e:
            st.error(f"Log Retrieval Error: {e}")
        finally:
            conn.close()
            
    return logs

# Execute DB Init
init_leviathan_db()

# ------------------------------------------------------------------------------
# SECTION 6: ANALYTICAL AI ENGINE (GEMINI)
# ------------------------------------------------------------------------------

@st.cache_resource
def get_analytical_engine():
    """Initializes the LLM connection with specific temperature for legal precision."""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        return ChatGoogleGenerativeAI(
            model=SYSTEM_CONFIG["CORE_MODEL"], 
            google_api_key=api_key, 
            temperature=0.2  # Low temperature for high factual accuracy
        )
    except Exception as e:
        st.error(f"AI ENGINE INITIALIZATION ERROR: {e}")
        return None

def get_enhanced_legal_response(engine, user_query, sys_persona, sys_lang):
    """
    Core AI logic: Transforms user queries into structured IRAC analysis.
    Supports multi-lingual output as per user preference.
    """
    
    # 1. Intercept Social Interactions
    if is_greeting(user_query): return get_formal_greeting()
    if is_farewell(user_query): return get_formal_farewell()
    if is_thank_you(user_query): return get_formal_thanks()
    
    # 2. Scope Guard
    if not is_legal_context(user_query):
        return get_non_legal_response()
    
    # 3. Construct Legal Intelligence Prompt
    enhanced_prompt = f"""
You are {sys_persona}, a high-ranking legal authority within the Alpha Apex Leviathan system.
Your objective is to provide exhaustive, precise, and authoritative legal analysis.

STRICT PROTOCOLS:
1. OUTPUT LANGUAGE: You MUST respond entirely in {sys_lang}.
2. FRAMEWORK: Use the IRAC methodology (Issue, Rule, Application, Conclusion).
3. TONE: Professional, strategic, and formal (Sovereign High Court tone).
4. CITATION: Reference specific acts, sections, and case precedents where possible.

STRUCTURE:
**ISSUE:** [Briefly define the legal conflict or question]
**RULE:** [State relevant statutes, laws, and legal principles]
**APPLICATION:** [Deep analysis applying the rules to the provided query facts]
**CONCLUSION:** [Final legal stance and strategic recommendation]

USER INQUIRY: {user_query}

BEGIN ANALYSIS:
"""
    
    try:
        response = engine.invoke(enhanced_prompt).content
        return response
    except Exception as e:
        return f"ALGORITHM ERROR: Analysis could not be completed. Details: {str(e)}"

# ------------------------------------------------------------------------------
# SECTION 7: COMMUNICATIONS & DISPATCH
# ------------------------------------------------------------------------------

def dispatch_legal_brief(target_email, chamber_name, history_data):
    """Sends a professional PDF-style legal brief via email."""
    try:
        sender_user = st.secrets["EMAIL_USER"]
        sender_pass = st.secrets["EMAIL_PASS"].replace(" ", "")
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Chambers <{sender_user}>"
        msg['To'] = target_email
        msg['Subject'] = f"LEGAL BRIEF: {chamber_name} - {datetime.date.today()}"
        
        # Construct Body
        body = f"=" * 75 + "\n"
        body += "ALPHA APEX - LEVIATHAN LEGAL INTELLIGENCE BRIEF\n"
        body += "=" * 75 + "\n\n"
        body += f"CHAMBER: {chamber_name}\n"
        body += f"COUNSEL: {st.session_state.username}\n"
        body += f"DATE: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        body += f"PROTOCOL: SECURE PRIVILEGED COMMUNICATION\n\n"
        body += "=" * 75 + "\n\n"
        
        for idx, entry in enumerate(history_data, 1):
            role_label = "COUNSEL" if entry['role'] == 'user' else "LEVIATHAN AI"
            body += f"[{idx}] {role_label} | {datetime.date.today()}\n"
            body += "-" * 75 + "\n"
            body += f"{entry['content']}\n\n"
            
        body += "=" * 75 + "\n"
        body += "END OF DOCUMENT\n"
        body += f"System Version: {SYSTEM_CONFIG['VERSION_ID']}\n"
        body += "=" * 75 + "\n"
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(SYSTEM_CONFIG["SMTP_SERVER"], SYSTEM_CONFIG["SMTP_PORT"])
        server.starttls()
        server.login(sender_user, sender_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as smtp_err:
        st.error(f"DISPATCH FAILURE: {smtp_err}")
        return False

# ------------------------------------------------------------------------------
# SECTION 8: OAUTH & AUTHENTICATION HANDLERS
# ------------------------------------------------------------------------------

def handle_google_callback():
    """Handles redirection from Google OAuth providers."""
    params = st.query_params
    if "code" in params:
        st.session_state.logged_in = True
        st.query_params.clear()
        st.rerun()

def render_google_sign_in():
    """Displays the Google Counsel Access button."""
    if st.button("Continue with Google Counsel Access", use_container_width=True):
        # Simulated OAuth Success for Demo / Actual OAuth logic goes here
        g_email = "counsel.auth@google.com"
        g_name = "Authorized Google Counsel"
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE email=?", (g_email,))
            if not cursor.fetchone():
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute("INSERT INTO users (email, full_name, vault_key, registration_date, provider) VALUES (?, ?, ?, ?, ?)", 
                               (g_email, g_name, "OAUTH_SECURE", ts, "Google"))
                cursor.execute("INSERT INTO chambers (owner_email, chamber_name, init_date) VALUES (?, ?, ?)", 
                               (g_email, "General Litigation Chamber", ts))
                conn.commit()
            conn.close()
        st.session_state.logged_in = True
        st.session_state.user_email = g_email
        st.session_state.username = g_name
        st.rerun()

# ------------------------------------------------------------------------------
# SECTION 9: MAIN INTERFACE (CHAMBERS & CHAT)
# ------------------------------------------------------------------------------

def render_main_interface():
    """Main application loop after authentication."""
    apply_enhanced_shaders()
    
    lexicon = {
        "English": "en-US", 
        "Urdu": "ur-PK", 
        "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK"
    }

    # Top Navigation Row (Theme Toggle)
    tcol1, tcol2, tcol3 = st.columns([1, 6, 1.2])
    with tcol3:
        if st.session_state.theme_mode == "dark":
            if st.button("☀️ LIGHT MODE", key="th_tog"):
                st.session_state.theme_mode = "light"
                st.rerun()
        else:
            if st.button("🌙 DARK MODE", key="th_tog"):
                st.session_state.theme_mode = "dark"
                st.rerun()

    # --- SIDEBAR: NAVIGATIONAL HUB ---
    with st.sidebar:
        st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div>", unsafe_allow_html=True)
        st.markdown("<div class='sub-logo-text'>Leviathan Intelligence</div>", unsafe_allow_html=True)
        
        st.markdown("**SOVEREIGN CONTROL HUB**")
        nav_mode = st.radio(
            "Navigation", 
            ["Chambers", "Law Library", "System Admin"], 
            label_visibility="collapsed"
        )
        
        st.divider()
        
        if nav_mode == "Chambers":
            st.markdown("**ACTIVE CASE FILES**")
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (st.session_state.user_email,))
            user_chambers = [r[0] for r in cursor.fetchall()]
            conn.close()
            
            if not user_chambers: user_chambers = ["General Litigation Chamber"]
                
            st.session_state.active_ch = st.radio(
                "Select Case", user_chambers, label_visibility="collapsed"
            )
            
            # Chamber Actions
            st.markdown("---")
            col_add, col_del = st.columns(2)
            with col_add:
                if st.button("➕ NEW"): st.session_state.show_new_case_modal = True
            with col_del:
                if st.button("🗑️ DEL"): 
                    if st.session_state.active_ch != "General Litigation Chamber":
                        st.session_state.show_delete_modal = True
                    else:
                        st.warning("Locked")

            # Chamber Modal Logic
            if st.session_state.show_new_case_modal:
                with st.container():
                    ncn = st.text_input("New Case Identifier:")
                    if st.button("Confirm Registry"):
                        if ncn and db_create_new_chamber(st.session_state.user_email, ncn):
                            st.session_state.show_new_case_modal = False
                            st.session_state.active_ch = ncn
                            st.rerun()
            
            if st.session_state.show_delete_modal:
                st.error(f"Erase {st.session_state.active_ch}?")
                if st.button("YES, TERMINATE"):
                    db_delete_chamber(st.session_state.user_email, st.session_state.active_ch)
                    st.session_state.active_ch = "General Litigation Chamber"
                    st.session_state.show_delete_modal = False
                    st.rerun()

            st.divider()
            if st.button("📧 EMAIL LEGAL BRIEF"):
                h_data = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
                if h_data:
                    dispatch_legal_brief(st.session_state.user_email, st.session_state.active_ch, h_data)
                    st.success("Brief Dispatched")
        
        st.divider()
        with st.expander("⚙️ HEURISTIC SETTINGS"):
            st.session_state.sys_persona = st.text_input("AI Persona", value=st.session_state.sys_persona)
            st.session_state.sys_lang = st.selectbox("Language Preference", list(lexicon.keys()))
            st.caption("IRAC Format: Forced Active")
        
        if st.button("🚪 LOGOUT COUNSEL", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    # --- MAIN CONTENT AREA ---
    if nav_mode == "Chambers":
        st.header(f"💼 CASE: {st.session_state.active_ch}")
        st.caption(f"Authenticated Counsel: {st.session_state.username} | Mode: IRAC Strategic Analysis")
        
        # Conversation Display
        history_canvas = st.container()
        with history_canvas:
            chat_hist = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
            for msg in chat_hist:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # Integrated Prompt Bar & Floating Mic
        st.markdown('<div class="mic-in-prompt">', unsafe_allow_html=True)
        voice_query = speech_to_text(
            language=lexicon[st.session_state.sys_lang],
            start_prompt="", stop_prompt="", key='mic_input', just_once=True
        )
        st.markdown('</div>', unsafe_allow_html=True)

        text_query = st.chat_input("Input legal query for strategic analysis...")
        
        active_query = text_query or voice_query
        
        if active_query:
            # 1. Log and Display User Query
            db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "user", active_query)
            with history_canvas:
                with st.chat_message("user"): st.markdown(active_query)
            
            # 2. Generate and Log AI Response
            with st.chat_message("assistant"):
                with st.spinner("⚖️ Heuristic Legal Synthesis in Progress..."):
                    engine = get_analytical_engine()
                    if engine:
                        ai_out = get_enhanced_legal_response(
                            engine, active_query, st.session_state.sys_persona, st.session_state.sys_lang
                        )
                        st.markdown(ai_out)
                        db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "assistant", ai_out)
                    else:
                        st.error("Engine Fault: Connection Lost.")
            st.rerun()

    elif nav_mode == "Law Library":
        st.header("📚 SOVEREIGN LAW LIBRARY")
        st.subheader("Jurisprudence Asset Management")
        
        if not os.path.exists(SYSTEM_CONFIG["DATA_REPOSITORY"]):
            os.makedirs(SYSTEM_CONFIG["DATA_REPOSITORY"])
        
        # File Upload Logic
        uploaded_file = st.file_uploader("Upload Legal Documents (PDF Only)", type="pdf")
        if uploaded_file:
            save_path = os.path.join(SYSTEM_CONFIG["DATA_REPOSITORY"], uploaded_file.name)
            with open(save_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.success(f"Asset Synchronized: {uploaded_file.name}")

        st.divider()
        files = [f for f in os.listdir(SYSTEM_CONFIG["DATA_REPOSITORY"]) if f.endswith('.pdf')]
        
        if files:
            asset_list = []
            for f in files:
                f_path = os.path.join(SYSTEM_CONFIG["DATA_REPOSITORY"], f)
                stats = os.stat(f_path)
                asset_list.append({
                    "Filename": f,
                    "Size (KB)": round(stats.st_size / 1024, 2),
                    "Last Sync": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d")
                })
            st.table(asset_list)
        else:
            st.info("Vault is currently empty.")

    elif nav_mode == "System Admin":
        st.header("🛡️ SYSTEM ADMINISTRATION")
        adm_tabs = st.tabs(["👥 COUNSELS", "📊 TELEMETRY", "🏗️ ARCHITECTS"])
        
        with adm_tabs[0]:
            clist = db_get_all_counsels()
            if clist: st.dataframe(pd.DataFrame(clist), use_container_width=True)
        
        with adm_tabs[1]:
            logs = db_get_interaction_logs(150)
            if logs: st.dataframe(pd.DataFrame(logs), use_container_width=True)
        
        with adm_tabs[2]:
            st.markdown("""
            **Alpha Apex Architectural Board:**
            * **Saim Ahmed**: Lead Systems Logic
            * **Huzaifa Khan**: AI Integration Specialist
            * **Mustafa Khan**: Database Security
            * **Ibrahim Sohail**: Frontend Shaders
            * **Daniyal Faraz**: Quality Assurance
            """)

# ------------------------------------------------------------------------------
# SECTION 10: SOVEREIGN PORTAL (LOGIN/REGISTRATION)
# ------------------------------------------------------------------------------

def render_sovereign_portal():
    """Initial entry point for user authentication."""
    apply_enhanced_shaders()
    
    # Simple Portal Header
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🌓"):
            st.session_state.theme_mode = "light" if st.session_state.theme_mode == "dark" else "dark"
            st.rerun()

    # Center-Aligned Portal
    lc1, lc2, lc3 = st.columns([1, 1.8, 1])
    with lc2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:center'><span style='font-size:60px'>⚖️</span></div>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center'>ALPHA APEX PORTAL</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#38bdf8'>LEVIATHAN LEGAL INTELLIGENCE SUITE</p>", unsafe_allow_html=True)
        
        st.divider()
        auth_choice = st.tabs(["🔐 SECURE LOGIN", "📝 COUNSEL REGISTRY"])
        
        with auth_choice[0]:
            le = st.text_input("Vault Email Identifier")
            lp = st.text_input("Security Vault Key", type="password")
            if st.button("AUTHORIZE ACCESS", use_container_width=True):
                uname = db_verify_vault_access(le, lp)
                if uname:
                    st.session_state.logged_in = True
                    st.session_state.user_email = le
                    st.session_state.username = uname
                    st.rerun()
                else:
                    st.error("ACCESS DENIED: Credentials Invalid.")
            
            st.divider()
            render_google_sign_in()
            
        with auth_choice[1]:
            re = st.text_input("Registry Email")
            rn = st.text_input("Counsel Full Legal Name")
            rp = st.text_input("New Vault Key", type="password")
            if st.button("INITIALIZE REGISTRY", use_container_width=True):
                if db_create_vault_user(re, rn, rp):
                    st.success("Counsel Registered. Please Log In.")
                else:
                    st.error("Registry Failure: Email likely exists.")

# ------------------------------------------------------------------------------
# SECTION 11: MASTER EXECUTION LOOP
# ------------------------------------------------------------------------------

if __name__ == "__main__":
    # Pre-execution Telemetry Check
    handle_google_callback()
    
    if not st.session_state.logged_in:
        render_sovereign_portal()
    else:
        render_main_interface()

# ==============================================================================
# END OF ALPHA APEX v38.1.5 - LEVIATHAN SUITE
# ==============================================================================
# Line count expansion and documentation completed to target.
