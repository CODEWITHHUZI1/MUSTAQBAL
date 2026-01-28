# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM - v38.1
# ==============================================================================
# SYSTEM VERSION: 38.1 (UPGRADED)
# NEW FEATURES: Sidebar Toggle Button + Mic Button at Prompt Bar
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
import base64
import re
import pandas as pd
from PyPDF2 import PdfReader
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ------------------------------------------------------------------------------
# SECTION 2: GLOBAL CONFIGURATION
# ------------------------------------------------------------------------------

SYSTEM_CONFIG = {
    "APP_NAME": "Alpha Apex - Leviathan Law AI",
    "APP_ICON": "⚖️",
    "LAYOUT": "wide",
    "THEME_PRIMARY": "#0b1120",
    "DB_FILENAME": "advocate_ai_v2.db",
    "DATA_REPOSITORY": "data",
    "VERSION_ID": "38.1.0-UPGRADED",
    "LOG_LEVEL": "STRICT",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587
}

st.set_page_config(
    page_title=SYSTEM_CONFIG["APP_NAME"], 
    page_icon=SYSTEM_CONFIG["APP_ICON"], 
    layout=SYSTEM_CONFIG["LAYOUT"],
    initial_sidebar_state="expanded"
)

# Initialize theme and sidebar state in session state
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"
if "sidebar_visible" not in st.session_state:
    st.session_state.sidebar_visible = True

# ------------------------------------------------------------------------------
# SECTION 3: ENHANCED SHADER WITH LIGHT/DARK MODE + SIDEBAR TOGGLE
# ------------------------------------------------------------------------------

def apply_enhanced_shaders():
    """Enhanced CSS with light/dark mode support and sidebar toggle"""
    
    # Define color schemes
    if st.session_state.theme_mode == "dark":
        bg_primary = "#0b1120"
        bg_secondary = "#1a1f3a"
        bg_tertiary = "#1e293b"
        text_primary = "#e8edf4"
        text_secondary = "#b4bdd0"
        border_color = "rgba(56, 189, 248, 0.2)"
        input_bg = "rgba(30, 41, 59, 0.6)"
        sidebar_bg = "rgba(2, 6, 23, 0.8)"
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
        sidebar_bg = "rgba(241, 245, 249, 0.9)"
        chat_bg = "rgba(241, 245, 249, 0.6)"
        prompt_area_bg = "#ffffff"
    
    # Add JavaScript for sidebar control
    sidebar_script = """
    <script>
        function toggleSidebar() {
            const sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
            const collapseBtn = window.parent.document.querySelector('[data-testid="collapsedControl"]');
            
            if (sidebar) {
                if (sidebar.getAttribute('aria-expanded') === 'true') {
                    // Collapse sidebar
                    if (collapseBtn) {
                        collapseBtn.click();
                    }
                } else {
                    // Expand sidebar
                    if (collapseBtn) {
                        collapseBtn.click();
                    }
                }
            }
        }
        
        // Auto-click toggle on page load if needed
        window.addEventListener('load', function() {
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('toggle_sidebar') === 'true') {
                setTimeout(toggleSidebar, 100);
            }
        });
    </script>
    """
    
    components.html(sidebar_script, height=0)
    
    # Sidebar visibility control
    sidebar_visibility = "visible" if st.session_state.sidebar_visible else "hidden"
    sidebar_transform = "translateX(0)" if st.session_state.sidebar_visible else "translateX(-100%)"
    
    shader_css = f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@400;600;700&family=Space+Mono:wght@400;700&display=swap');
        
        /* Sidebar visibility control */
        [data-testid="stSidebar"] {{
            visibility: {sidebar_visibility} !important;
            transform: {sidebar_transform} !important;
            transition: transform 0.3s ease, visibility 0.3s ease !important;
        }}
        
        /* Menu Button Styling */
        .menu-toggle-btn {{
            position: fixed !important;
            top: 20px !important;
            left: 20px !important;
            z-index: 999999 !important;
            background: linear-gradient(135deg, {bg_tertiary} 0%, {bg_secondary} 100%) !important;
            border: 1px solid {border_color} !important;
            border-radius: 12px !important;
            padding: 10px 15px !important;
            cursor: pointer !important;
            color: {text_primary} !important;
            font-weight: 700 !important;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2) !important;
            transition: all 0.3s ease !important;
        }}
        
        .menu-toggle-btn:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3) !important;
            border-color: #38bdf8 !important;
        }}
        
        /* Theme Toggle Button */
        .theme-toggle {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999999;
            background: linear-gradient(135deg, {bg_tertiary} 0%, {bg_secondary} 100%);
            border: 1px solid {border_color};
            border-radius: 25px;
            padding: 8px 18px;
            cursor: pointer;
            color: {text_primary};
            font-weight: 600;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: all 0.3s ease;
        }}
        
        .theme-toggle:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
        }}
        
        /* Global Styles */
        * {{ 
            transition: background-color 0.3s ease, color 0.3s ease !important; 
            font-family: 'Crimson Pro', Georgia, serif;
            -webkit-font-smoothing: antialiased;
        }}
        
        /* Main Application */
        .stApp {{ 
            background: linear-gradient(135deg, {bg_primary} 0%, {bg_secondary} 50%, {bg_primary} 100%) !important;
            background-size: 200% 200% !important;
            color: {text_primary} !important; 
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: {sidebar_bg} !important; 
            backdrop-filter: blur(20px) !important;
            border-right: 1px solid {border_color} !important;
            box-shadow: 12px 0 40px rgba(0, 0, 0, 0.3) !important;
        }}
        
        /* Chat Messages */
        .stChatMessage {{
            border-radius: 16px !important;
            padding: 2rem !important;
            margin-bottom: 2rem !important;
            border: 1px solid {border_color} !important;
            background: {chat_bg} !important;
            backdrop-filter: blur(10px) !important;
        }}
        
        [data-testid="stChatMessageUser"] {{
            border-left: 4px solid #38bdf8 !important;
        }}
        
        [data-testid="stChatMessageAssistant"] {{
            border-left: 4px solid #ef4444 !important;
        }}
        
        /* Typography */
        h1, h2, h3, h4 {{ 
            color: {text_primary} !important; 
            font-weight: 700 !important; 
        }}
        
        p, span, div {{
            color: {text_primary} !important;
        }}
        
        .logo-text {{
            color: {text_primary};
            font-size: 32px;
            font-weight: 900;
            text-shadow: 0 0 20px rgba(56, 189, 248, 0.5);
            font-family: 'Space Mono', monospace !important;
        }}
        
        .sub-logo-text {{
            color: {text_secondary};
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 3px;
            font-family: 'Space Mono', monospace !important;
        }}
        
        /* Buttons */
        .stButton>button {{
            border-radius: 12px !important;
            font-weight: 700 !important;
            background: {bg_tertiary} !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            height: 3.5rem !important;
            width: 100% !important;
        }}
        
        .stButton>button:hover {{
            border-color: #38bdf8 !important;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.3) !important;
        }}
        
        /* Input Fields */
        .stTextInput>div>div>input,
        .stTextArea>div>div>textarea {{
            background: {input_bg} !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            border-radius: 12px !important;
            padding: 14px 18px !important;
        }}
        
        .stTextInput>div>div>input:focus,
        .stTextArea>div>div>textarea:focus {{
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 3px rgba(56, 189, 248, 0.2) !important;
        }}
        
        /* Chat Input Container */
        .stChatInputContainer {{
            background: {prompt_area_bg} !important;
            backdrop-filter: blur(10px) !important;
            border-top: 1px solid {border_color} !important;
            padding: 20px !important;
            position: relative !important;
        }}
        
        /* Chat Input Field - with space for mic button */
        .stChatInput>div>div>textarea {{
            background: {input_bg} !important;
            color: {text_primary} !important;
            border: 1px solid {border_color} !important;
            border-radius: 12px !important;
            padding: 14px 60px 14px 18px !important;
            min-height: 60px !important;
            font-size: 15px !important;
        }}
        
        /* Microphone Button - INSIDE PROMPT BAR */
        .mic-in-prompt {{
            position: absolute !important;
            right: 30px !important;
            bottom: 35px !important;
            z-index: 1000 !important;
        }}
        
        .mic-in-prompt button {{
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important; 
            border: none !important; 
            border-radius: 50% !important;
            width: 40px !important;
            height: 40px !important;
            min-width: 40px !important;
            min-height: 40px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important;
            cursor: pointer !important;
            transition: all 0.2s ease !important;
        }}
        
        .mic-in-prompt button:hover {{
            transform: scale(1.1) !important;
            box-shadow: 0 6px 20px rgba(239, 68, 68, 0.6) !important;
        }}
        
        .mic-in-prompt button svg {{
            width: 20px !important;
            height: 20px !important;
            fill: white !important;
        }}
        
        /* Radio Buttons */
        .stRadio > div[role="radiogroup"] > label > div:first-child {{
            background-color: #ef4444 !important; 
            border-color: #ef4444 !important;
        }}
        
        .stRadio label {{
            color: {text_secondary} !important;
            font-weight: 600 !important;
        }}
        
        /* Tables */
        .stTable {{
            color: {text_primary} !important;
        }}
        
        table {{
            color: {text_primary} !important;
        }}
        
        thead tr th {{
            background-color: {bg_tertiary} !important;
            color: {text_primary} !important;
        }}
        
        tbody tr td {{
            color: {text_primary} !important;
        }}
        
        /* Metrics */
        [data-testid="stMetricValue"] {{
            color: #38bdf8 !important;
            font-weight: 700 !important;
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 12px; }}
        ::-webkit-scrollbar-track {{ background: {bg_primary}; }}
        ::-webkit-scrollbar-thumb {{ 
            background: {bg_tertiary}; 
            border-radius: 6px; 
        }}
        
        /* Hide Streamlit branding */
        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
        header {{visibility: hidden;}}
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# SECTION 4: LEGAL CONTEXT & RESPONSE HANDLERS
# ------------------------------------------------------------------------------

def is_greeting(text):
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 
                 'greetings', 'salaam', 'assalam', 'salam']
    text_lower = text.lower().strip()
    return any(greet in text_lower for greet in greetings)

def is_farewell(text):
    farewells = ['bye', 'goodbye', 'see you', 'farewell', 'take care', 'allah hafiz', 
                 'khuda hafiz', 'bye bye']
    text_lower = text.lower().strip()
    return any(fare in text_lower for fare in farewells)

def is_thank_you(text):
    thanks = ['thank', 'thanks', 'appreciate', 'grateful', 'shukriya', 'meherbani']
    text_lower = text.lower().strip()
    return any(thank in text_lower for thank in thanks)

def is_legal_context(text):
    legal_keywords = [
        'law', 'legal', 'court', 'case', 'judge', 'lawyer', 'attorney', 'contract', 
        'crime', 'criminal', 'civil', 'litigation', 'jurisdiction', 'statute', 'ordinance',
        'penal', 'constitution', 'amendment', 'act', 'section', 'article', 'plaintiff',
        'defendant', 'prosecution', 'defense', 'evidence', 'testimony', 'verdict', 
        'appeal', 'petition', 'writ', 'injunction', 'bail', 'custody', 'property',
        'inheritance', 'divorce', 'marriage', 'custody', 'rights', 'violation',
        'tort', 'negligence', 'liability', 'damages', 'compensation', 'settlement',
        'agreement', 'clause', 'breach', 'enforcement', 'precedent', 'ruling'
    ]
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in legal_keywords) or len(text) > 100

def get_formal_greeting():
    return """Good day. I am Alpha Apex, your dedicated legal intelligence advisor. 

I am here to assist you with legal queries, case analysis, and strategic litigation guidance. How may I be of service to you today?"""

def get_formal_farewell():
    return """Thank you for consulting with Alpha Apex Legal Intelligence. 

Should you require further legal assistance or strategic counsel, I remain at your service. Wishing you success in your legal endeavors.

Best regards,
Alpha Apex AI"""

def get_formal_thanks():
    return """You are most welcome. It is my privilege to assist you with your legal matters.

Should you have any further questions or require additional analysis, please do not hesitate to reach out.

At your service,
Alpha Apex AI"""

def get_non_legal_response():
    return """I appreciate your inquiry, however, my specialized domain is limited to legal matters and jurisprudence.

I am designed to assist with:
• Legal case analysis and strategy
• Interpretation of statutes and legal precedents
• Contract review and drafting guidance
• Litigation support and procedural advice
• Legal research and documentation

For matters outside the legal domain, I kindly recommend consulting with appropriate specialized services.

Is there a legal matter I may assist you with today?"""

# ------------------------------------------------------------------------------
# SECTION 5: DATABASE FUNCTIONS
# ------------------------------------------------------------------------------

def get_db_connection():
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
    connection = get_db_connection()
    if not connection: return
    try:
        cursor = connection.cursor()
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
        
        cursor.execute("CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT, chamber_type TEXT DEFAULT 'General Litigation', case_status TEXT DEFAULT 'Active', is_archived INTEGER DEFAULT 0, FOREIGN KEY(owner_email) REFERENCES users(email))")
        cursor.execute("CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT, token_count INTEGER DEFAULT 0, FOREIGN KEY(chamber_id) REFERENCES chambers(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT, asset_status TEXT DEFAULT 'Verified')")
        cursor.execute("CREATE TABLE IF NOT EXISTS system_telemetry (event_id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, event_type TEXT, description TEXT, event_timestamp TEXT)")
        connection.commit()
    except sqlite3.Error as e:
        st.error(f"DATABASE SCHEMA INITIALIZATION FAILED: {e}")
    finally:
        connection.close()

def db_log_event(email, event_type, desc):
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
    """Create a new case/chamber"""
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
    """Delete a chamber and all its messages"""
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
    """Get all registered counsels"""
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
    """Get recent interaction logs"""
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

init_leviathan_db()

# ------------------------------------------------------------------------------
# SECTION 6: AI ENGINE
# ------------------------------------------------------------------------------

@st.cache_resource
def get_analytical_engine():
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        return ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=api_key, 
            temperature=0.2
        )
    except Exception as e:
        st.error(f"AI ENGINE INITIALIZATION ERROR: {e}")
        return None

def get_enhanced_legal_response(engine, user_query, sys_persona, sys_lang):
    """Generate AI response with IRAC format"""
    
    if is_greeting(user_query):
        return get_formal_greeting()
    
    if is_farewell(user_query):
        return get_formal_farewell()
    
    if is_thank_you(user_query):
        return get_formal_thanks()
    
    if not is_legal_context(user_query):
        return get_non_legal_response()
    
    enhanced_prompt = f"""
You are {sys_persona}, a distinguished legal expert providing formal legal analysis.

IMPORTANT INSTRUCTIONS:
1. You MUST respond in {sys_lang} language
2. You MUST use the IRAC format (Issue, Rule, Application, Conclusion) for all legal queries
3. Be formal, professional, and precise in your language
4. Only discuss legal matters - decline non-legal queries politely
5. Cite relevant legal provisions, statutes, or precedents when applicable

Structure your response as follows:

**ISSUE:**
[Clearly identify the legal issue or question presented]

**RULE:**
[State the relevant legal rules, statutes, case law, or precedents that apply to this issue]

**APPLICATION:**
[Apply the stated rules to the specific facts and circumstances of this case/query]

**CONCLUSION:**
[Provide a clear, reasoned conclusion based on your analysis]

User Query: {user_query}

Provide your analysis now:
"""
    
    try:
        response = engine.invoke(enhanced_prompt).content
        return response
    except Exception as e:
        return f"Error generating legal analysis: {str(e)}"

def dispatch_legal_brief(target_email, chamber_name, history_data):
    """Send full conversation via email"""
    try:
        sender_user = st.secrets["EMAIL_USER"]
        sender_pass = st.secrets["EMAIL_PASS"].replace(" ", "")
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Chambers <{sender_user}>"
        msg['To'] = target_email
        msg['Subject'] = f"LEGAL BRIEF: {chamber_name} - {datetime.date.today()}"
        
        body = f"=" * 70 + "\n"
        body += "ALPHA APEX LEGAL INTELLIGENCE BRIEF\n"
        body += "=" * 70 + "\n\n"
        body += f"CHAMBER: {chamber_name}\n"
        body += f"DATE: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        body += f"STATUS: CONFIDENTIAL PRIVILEGED\n\n"
        body += "=" * 70 + "\n\n"
        
        for idx, entry in enumerate(history_data, 1):
            role_label = "COUNSEL" if entry['role'] == 'user' else "AI LEGAL ADVISOR"
            body += f"[MESSAGE {idx} - {role_label}]\n"
            body += "-" * 70 + "\n"
            body += f"{entry['content']}\n\n"
            
        body += "=" * 70 + "\n"
        body += "END OF LEGAL BRIEF\n"
        body += f"Generated by Alpha Apex Leviathan v{SYSTEM_CONFIG['VERSION_ID']}\n"
        body += "=" * 70 + "\n"
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        server = smtplib.SMTP(SYSTEM_CONFIG["SMTP_SERVER"], SYSTEM_CONFIG["SMTP_PORT"])
        server.starttls()
        server.login(sender_user, sender_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as smtp_err:
        st.error(f"📧 Email Dispatch Failure: {smtp_err}")
        return False

# ------------------------------------------------------------------------------
# SECTION 7: OAUTH HANDLERS
# ------------------------------------------------------------------------------

def handle_google_callback():
    params = st.query_params
    if "code" in params:
        st.session_state.logged_in = True
        st.query_params.clear()
        st.rerun()

def render_google_sign_in():
    if st.button("Continue with Google Counsel Access", use_container_width=True):
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
# SECTION 9: MAIN INTERFACE
# ------------------------------------------------------------------------------

def render_main_interface():
    apply_enhanced_shaders()
    
    # Menu Toggle Button - Top Left (ALWAYS VISIBLE)
    menu_col1, menu_col2, menu_col3 = st.columns([1, 5, 1])
    
    with menu_col1:
        menu_button_text = "✕ Close" if st.session_state.sidebar_visible else "☰ Menu"
        if st.button(menu_button_text, key="menu_toggle_btn", use_container_width=True):
            st.session_state.sidebar_visible = not st.session_state.sidebar_visible
            st.rerun()
    
    with menu_col3:
        if st.session_state.theme_mode == "dark":
            if st.button("☀️ Light", key="theme_toggle"):
                st.session_state.theme_mode = "light"
                st.rerun()
        else:
            if st.button("🌙 Dark", key="theme_toggle"):
                st.session_state.theme_mode = "dark"
                st.rerun()
    
    lexicon = {
        "English": "en-US", 
        "Urdu": "ur-PK", 
        "Sindhi": "sd-PK", 
        "Punjabi": "pa-PK"
    }

    # --- SIDEBAR (controlled by session state) ---
    if st.session_state.sidebar_visible:
        with st.sidebar:
            st.markdown("<div class='logo-text'>⚖️ ALPHA APEX</div>", unsafe_allow_html=True)
            st.markdown("<div class='sub-logo-text'>Leviathan Suite v38.1</div>", unsafe_allow_html=True)
            
            st.markdown("**Sovereign Navigation Hub**")
            nav_mode = st.radio(
                "Navigation", 
                ["Chambers", "Law Library", "System Admin"], 
                label_visibility="collapsed"
            )
            st.session_state.nav_mode = nav_mode  # Store for use when sidebar is hidden
            
            st.divider()
            
            if nav_mode == "Chambers":
                st.markdown("**Active Case Files**")
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT chamber_name FROM chambers WHERE owner_email=?", (st.session_state.user_email,))
                user_chambers = [r[0] for r in cursor.fetchall()]
                conn.close()
                
                if not user_chambers:
                    user_chambers = ["General Litigation Chamber"]
                    
                st.session_state.active_ch = st.radio(
                    "Select Case", 
                    user_chambers, 
                    label_visibility="collapsed"
                )
                
                # Action Buttons
                col_add, col_del = st.columns(2)
                with col_add:
                    if st.button("➕ New Case"):
                        st.session_state.show_new_case_modal = True
                with col_del:
                    if st.button("🗑️ Delete Case"):
                        if st.session_state.active_ch != "General Litigation Chamber":
                            st.session_state.show_delete_modal = True
                        else:
                            st.warning("Cannot delete default chamber")
                
                # New Case Modal
                if st.session_state.get('show_new_case_modal', False):
                    new_case_name = st.text_input("Enter New Case Name:", key="new_case_input")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Create", key="create_case_btn"):
                            if new_case_name:
                                if db_create_new_chamber(st.session_state.user_email, new_case_name):
                                    st.success(f"✓ Created: {new_case_name}")
                                    st.session_state.show_new_case_modal = False
                                    st.session_state.active_ch = new_case_name
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error("Case already exists or error occurred")
                    with col2:
                        if st.button("Cancel", key="cancel_case_btn"):
                            st.session_state.show_new_case_modal = False
                            st.rerun()
                
                # Delete Case Modal
                if st.session_state.get('show_delete_modal', False):
                    st.warning(f"⚠️ Delete '{st.session_state.active_ch}'?")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Yes, Delete", key="confirm_delete_btn"):
                            if db_delete_chamber(st.session_state.user_email, st.session_state.active_ch):
                                st.success("✓ Case Deleted")
                                st.session_state.active_ch = "General Litigation Chamber"
                                st.session_state.show_delete_modal = False
                                time.sleep(1)
                                st.rerun()
                    with col2:
                        if st.button("Cancel", key="cancel_delete_btn"):
                            st.session_state.show_delete_modal = False
                            st.rerun()
                
                st.divider()
                
                # Email Brief Button
                if st.button("📧 Email Brief", use_container_width=True):
                    hist = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
                    if hist:
                        with st.spinner("Sending email..."):
                            if dispatch_legal_brief(st.session_state.user_email, st.session_state.active_ch, hist):
                                st.success("✓ Brief sent to your email!")
                                db_log_event(st.session_state.user_email, "EMAIL_BRIEF", f"Sent brief for {st.session_state.active_ch}")
                            else:
                                st.error("Failed to send email")
                    else:
                        st.warning("No conversation to send")

            st.divider()
            
            with st.expander("⚙️ Advanced Settings"):
                st.caption("AI Configuration")
                sys_persona = st.text_input("Assistant Persona", value="Senior High Court Advocate")
                sys_lang = st.selectbox("Response Language", list(lexicon.keys()))
                
                st.caption("Response Format")
                st.info("📋 IRAC Format Enabled")
                
                st.divider()
                if st.button("🚪 Secure Logout", use_container_width=True):
                    st.session_state.logged_in = False
                    st.rerun()
    else:
        # Default values when sidebar is hidden
        nav_mode = st.session_state.get('nav_mode', 'Chambers')
        sys_persona = "Senior High Court Advocate"
        sys_lang = "English"

    # --- MAIN CONTENT ---
    if nav_mode == "Chambers":
        st.header(f"💼 CASE: {st.session_state.active_ch}")
        st.caption("Strategic Litigation Environment | IRAC Format Analysis")
        
        # History Canvas
        history_canvas = st.container()
        with history_canvas:
            chat_history = db_fetch_chamber_history(st.session_state.user_email, st.session_state.active_ch)
            for msg in chat_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
        
        # Input Area with Mic Button
        input_container = st.container()
        with input_container:
            # Create a column layout for prompt and mic
            prompt_col, mic_col = st.columns([20, 1])
            
            with prompt_col:
                input_text = st.chat_input("Enter your legal query for IRAC analysis...")
            
            with mic_col:
                st.markdown('<div class="mic-in-prompt">', unsafe_allow_html=True)
                input_voice = speech_to_text(
                    language=lexicon[sys_lang], 
                    start_prompt="🎙️", 
                    stop_prompt="🛑", 
                    key='leviathan_mic', 
                    just_once=True
                )
                st.markdown('</div>', unsafe_allow_html=True)
        
        active_query = input_text or input_voice
        
        if active_query:
            db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "user", active_query)
            
            with history_canvas:
                with st.chat_message("user"): 
                    st.markdown(active_query)
            
            with st.chat_message("assistant"):
                with st.spinner("⚖️ Conducting Legal Analysis..."):
                    engine = get_analytical_engine()
                    if engine:
                        ai_response = get_enhanced_legal_response(engine, active_query, sys_persona, sys_lang)
                        st.markdown(ai_response)
                        db_log_consultation(st.session_state.user_email, st.session_state.active_ch, "assistant", ai_response)
            st.rerun()

    elif nav_mode == "Law Library":
        st.header("📚 Sovereign Law Library")
        st.subheader("Asset Synchronization Vault")
        
        if not os.path.exists("data"):
            os.makedirs("data")
        
        local_files = [f for f in os.listdir("data") if f.endswith('.pdf')]
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Local Assets", len(local_files))
        with col2:
            if st.button("🔄 Force Re-Sync Repository"):
                st.rerun()

        st.divider()
        st.markdown("**Available Jurisprudence Assets**")

        if local_files:
            asset_data = []
            for file in local_files:
                file_path = os.path.join("data", file)
                stats = os.stat(file_path)
                asset_data.append({
                    "Filename": file,
                    "Size (KB)": round(stats.st_size / 1024, 2),
                    "Last Modified": datetime.datetime.fromtimestamp(stats.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
            
            st.table(asset_data)
        else:
            st.warning("⚠️ No PDF documents found in 'data' directory.")

    elif nav_mode == "System Admin":
        st.header("🛡️ System Administration Console")
        
        # Tabs for different admin sections
        admin_tabs = st.tabs(["👥 Counsels", "📊 Interaction Logs", "👨‍💼 Our Team"])
        
        with admin_tabs[0]:
            st.subheader("Registered Counsels")
            counsels = db_get_all_counsels()
            
            if counsels:
                df = pd.DataFrame(counsels)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"Total Counsels: {len(counsels)}")
            else:
                st.info("No counsels registered yet")
        
        with admin_tabs[1]:
            st.subheader("System Interaction Logs")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption("Recent system events and user interactions")
            with col2:
                log_limit = st.selectbox("Show logs:", [50, 100, 200, 500], index=1)
            
            logs = db_get_interaction_logs(log_limit)
            
            if logs:
                df = pd.DataFrame(logs)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"Showing {len(logs)} most recent logs")
            else:
                st.info("No interaction logs available")
        
        with admin_tabs[2]:
            st.subheader("🏗️ Architectural Board")
            architects = [
                {"Name": "Saim Ahmed", "Designation": "Lead Architect", "Domain": "System Logic"},
                {"Name": "Huzaifa Khan", "Designation": "AI Lead", "Domain": "LLM Tuning"},
                {"Name": "Mustafa Khan", "Designation": "DBA", "Domain": "SQL Security"},
                {"Name": "Ibrahim Sohail", "Designation": "UI Lead", "Domain": "Shaders"},
                {"Name": "Daniyal Faraz", "Designation": "QA Lead", "Domain": "Integration"}
            ]
            df = pd.DataFrame(architects)
            st.table(df)

# ------------------------------------------------------------------------------
# SECTION 10: AUTHENTICATION PORTAL
# ------------------------------------------------------------------------------

def render_sovereign_portal():
    apply_enhanced_shaders()
    
    # Theme toggle on login page
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.session_state.theme_mode == "dark":
            if st.button("☀️ Light"):
                st.session_state.theme_mode = "light"
                st.rerun()
        else:
            if st.button("🌙 Dark"):
                st.session_state.theme_mode = "dark"
                st.rerun()
    
    col_l, col_c, col_r = st.columns([1, 1.6, 1])
    
    with col_c:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.title("⚖️ ALPHA APEX PORTAL")
        st.markdown("#### Strategic Litigation and Legal Intelligence")
        st.write("---")
        
        auth_tabs = st.tabs(["🔐 Secure Login", "📝 Counsel Registry"])
        
        with auth_tabs[0]:
            login_e = st.text_input("Vault Email", key="log_e")
            login_p = st.text_input("Security Key", type="password", key="log_p")
            
            if st.button("Authorize Access", use_container_width=True):
                user_name = db_verify_vault_access(login_e, login_p)
                if user_name:
                    st.session_state.logged_in = True
                    st.session_state.user_email = login_e
                    st.session_state.username = user_name
                    st.rerun()
                else:
                    st.error("❌ CREDENTIALS INVALID: Access denied.")
            
            st.divider()
            render_google_sign_in()
            
        with auth_tabs[1]:
            reg_e = st.text_input("Counsel Email", key="reg_e")
            reg_n = st.text_input("Counsel Full Name", key="reg_n")
            reg_p = st.text_input("Vault Key", type="password", key="reg_p")
            
            if st.button("Initialize Registry", use_container_width=True):
                if db_create_vault_user(reg_e, reg_n, reg_p):
                    st.success("✓ Account created successfully!")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Email already exists or invalid input.")

# ------------------------------------------------------------------------------
# SECTION 11: MASTER EXECUTION
# ------------------------------------------------------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "active_ch" not in st.session_state:
    st.session_state.active_ch = "General Litigation Chamber"

handle_google_callback()

if not st.session_state.logged_in:
    render_sovereign_portal()
else:
    render_main_interface()

# ==============================================================================
# END OF ALPHA APEX v38.1 - UPGRADED VERSION
# ==============================================================================
