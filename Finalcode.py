# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# ==============================================================================
# SYSTEM VERSION: 36.5 (ULTRA-DECOMPRESSED ARCHITECTURE - NO DELETIONS)
# DEPLOYMENT TARGET: STREAMLIT CLOUD / LOCALHOST / ENTERPRISE SERVER
# DATABASE PERSISTENCE: advocate_ai_v2.db
# SECURITY PROTOCOL: OAUTH 2.0 FEDERATED IDENTITY + LOCAL VAULT
#
# ------------------------------------------------------------------------------
# ARCHITECTURAL BOARD & SENIOR SYSTEM CONTRIBUTORS:
# ------------------------------------------------------------------------------
# 1. SAIM AHMED       - CHIEF SYSTEM ARCHITECT & LOGIC CONTROLLER
# 2. HUZAIFA KHAN     - LEAD AI RESEARCHER & PROMPT ENGINEER
# 3. MUSTAFA KHAN     - SENIOR DATABASE ADMINISTRATOR & SECURITY LEAD
# 4. IBRAHIM SOHAIL   - PRINCIPAL UI/UX DESIGNER & SHADER ARCHITECT
# 5. DANIYAL FARAZ    - CORE INTEGRATION SPECIALIST & QA LEAD
# ==============================================================================

# ------------------------------------------------------------------------------
# SECTION 1: SYSTEM DEPENDENCIES & ENVIRONMENT STABILIZATION
# ------------------------------------------------------------------------------

try:
    # High-performance SQLite3 wrapper for Linux-based Cloud deployments
    import pysqlite3
    import sys
    sys.modules['sqlite3'] = pysqlite3
    # Log: Pysqlite3 successfully injected into sys.modules
except ImportError:
    # Fallback to standard library for local development (Windows/macOS)
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
from langchain_google_genai import ChatGoogleGenerativeAI, HarmBlockThreshold, HarmCategory
from streamlit_mic_recorder import speech_to_text
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# ------------------------------------------------------------------------------
# SECTION 2: GLOBAL CONFIGURATION & SYSTEM CONSTANTS
# ------------------------------------------------------------------------------

# Master Configuration Dictionary for System-wide Reference
SYSTEM_CONFIG = {
    "APP_NAME": "Alpha Apex - Leviathan Law AI",
    "APP_ICON": "⚖️",
    "LAYOUT": "wide",
    "THEME_PRIMARY": "#0b1120",
    "DB_FILENAME": "advocate_ai_v2.db",
    "DATA_REPOSITORY": "data",
    "VERSION_ID": "36.5.0-ALPHA",
    "LOG_LEVEL": "STRICT",
    "SMTP_SERVER": "smtp.gmail.com",
    "SMTP_PORT": 587
}

# Apply Streamlit Runtime Configuration
st.set_page_config(
    page_title=SYSTEM_CONFIG["APP_NAME"], 
    page_icon=SYSTEM_CONFIG["APP_ICON"], 
    layout=SYSTEM_CONFIG["LAYOUT"],
    initial_sidebar_state="expanded"
)

# ------------------------------------------------------------------------------
# SECTION 3: PERMANENT SOVEREIGN SHADER ARCHITECTURE (CSS)
# ------------------------------------------------------------------------------

def apply_leviathan_shaders():
    """
    Injects a high-density Dark Mode CSS architecture into the Streamlit DOM.
    Refined for the 'Sovereign Dark Blue/Navy' aesthetic.
    Line count expanded for granular control over every UI component.
    """
    shader_css = """
    <style>
        /* ------------------------------------------------------- */
        /* 1. GLOBAL RESET & BASE STYLING                          */
        /* ------------------------------------------------------- */
        * { 
            transition: background-color 0.8s ease, color 0.8s ease !important; 
            font-family: 'Inter', 'Segoe UI', 'Helvetica', sans-serif;
            -webkit-font-smoothing: antialiased;
        }
        
        /* ------------------------------------------------------- */
        /* 2. MAIN APPLICATION CANVAS                              */
        /* ------------------------------------------------------- */
        .stApp { 
            background-color: #0b1120 !important; 
            color: #e2e8f0 !important; 
        }

        /* ------------------------------------------------------- */
        /* 3. SIDEBAR GLASSMORPHISM DESIGN                         */
        /* ------------------------------------------------------- */
        [data-testid="stSidebar"] {
            background-color: #020617 !important; 
            border-right: 1px solid #1e293b !important;
            box-shadow: 12px 0 30px rgba(0, 0, 0, 0.7) !important;
        }
        
        [data-testid="stSidebarNav"] {
            padding-top: 2rem !important;
        }

        /* ------------------------------------------------------- */
        /* 4. RADIO & NAVIGATION BUTTONS (RED ACCENT)              */
        /* ------------------------------------------------------- */
        .stRadio > div[role="radiogroup"] > label > div:first-child {
            background-color: #ef4444 !important; 
            border-color: #ef4444 !important;
            box-shadow: 0 0 10px rgba(239, 68, 68, 0.4) !important;
        }
        
        .stRadio > div[role="radiogroup"] {
            gap: 14px;
            padding: 12px 0px;
        }
        
        .stRadio label {
            color: #cbd5e1 !important;
            font-weight: 600 !important;
            font-size: 14px !important;
        }

        /* ------------------------------------------------------- */
        /* 5. HIGH-FIDELITY CHAT WORKSPACE                         */
        /* ------------------------------------------------------- */
        .stChatMessage {
            border-radius: 14px !important;
            padding: 1.8rem !important;
            margin-bottom: 1.8rem !important;
            border: 1px solid rgba(56, 189, 248, 0.12) !important;
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
            background-color: rgba(30, 41, 59, 0.35) !important;
        }

        /* User Message Specifics */
        [data-testid="stChatMessageUser"] {
            border-left: 4px solid #38bdf8 !important;
            background-color: rgba(56, 189, 248, 0.07) !important;
        }
        
        /* Assistant Message Specifics */
        [data-testid="stChatMessageAvatarAssistant"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
        }

        /* ------------------------------------------------------- */
        /* 6. TYPOGRAPHY ENGINE                                    */
        /* ------------------------------------------------------- */
        h1, h2, h3, h4 { 
            color: #f8fafc !important; 
            font-weight: 800 !important; 
            letter-spacing: -0.02em !important;
        }
        
        .logo-text {
            color: #f8fafc;
            font-size: 28px;
            font-weight: 900;
            text-shadow: 0 4px 8px rgba(0,0,0,0.5);
            margin-bottom: 2px;
        }
        
        .sub-logo-text {
            color: #94a3b8;
            font-size: 11px;
            margin-top: -8px;
            margin-bottom: 25px;
            text-transform: uppercase;
            letter-spacing: 2px;
            font-weight: 700;
        }

        /* ------------------------------------------------------- */
        /* 7. PRECISION BUTTON ARCHITECTURE                        */
        /* ------------------------------------------------------- */
        .stButton>button {
            border-radius: 10px !important;
            font-weight: 700 !important;
            background: #1e293b !important;
            color: #f1f5f9 !important;
            border: 1px solid #334155 !important;
            height: 3.5rem !important;
            width: 100% !important;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
        }
        
        .stButton>button:hover {
            background-color: #334155 !important;
            border-color: #38bdf8 !important;
            box-shadow: 0 0 20px rgba(56, 189, 248, 0.3) !important;
            transform: translateY(-2px);
        }
        
        .stButton>button:active {
            transform: scale(0.98);
        }

        /* ------------------------------------------------------- */
        /* 8. GOOGLE OAUTH IDENTITY INTERFACE                      */
        /* ------------------------------------------------------- */
        .google-btn {
            display: flex;
            align-items: center;
            justify-content: center;
            background-color: #ffffff;
            color: #0f172a;
            font-weight: 700;
            padding: 0.9rem;
            border-radius: 12px;
            cursor: pointer;
            border: 1px solid #e2e8f0;
            text-decoration: none !important;
            transition: all 0.3s ease;
            margin-top: 20px;
            width: 100%;
            font-size: 1rem;
        }

        .google-btn:hover {
            background-color: #f8fafc;
            box-shadow: 0 10px 20px rgba(0,0,0,0.2);
            transform: translateY(-3px);
        }

        .google-icon {
            width: 24px;
            height: 24px;
            margin-right: 18px;
        }

        /* ------------------------------------------------------- */
        /* 9. INPUT FIELD OPTIMIZATION                             */
        /* ------------------------------------------------------- */
        .stTextInput>div>div>input {
            background-color: #1e293b !important;
            color: #f8fafc !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            padding: 12px 16px !important;
        }
        
        .stTextInput>div>div>input:focus {
            border-color: #38bdf8 !important;
            box-shadow: 0 0 0 2px rgba(56, 189, 248, 0.2) !important;
        }

        /* ------------------------------------------------------- */
        /* 10. SYSTEM UTILITIES & OVERRIDES                        */
        /* ------------------------------------------------------- */
        footer {visibility: hidden;}
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom Scrollbar for Leviathan */
        ::-webkit-scrollbar { width: 10px; height: 10px; }
        ::-webkit-scrollbar-track { background: #020617; }
        ::-webkit-scrollbar-thumb { background: #1e293b; border-radius: 5px; }
        ::-webkit-scrollbar-thumb:hover { background: #334155; }
    </style>
    """
    st.markdown(shader_css, unsafe_allow_html=True)


# ------------------------------------------------------------------------------
# SECTION 4: RELATIONAL DATABASE PERSISTENCE ENGINE (SQLITE3)
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
        
        # REQUIRED COLUMN INJECTION (Repair Loop)
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
        
        # Existing Table Structures
        cursor.execute("CREATE TABLE IF NOT EXISTS chambers (id INTEGER PRIMARY KEY AUTOINCREMENT, owner_email TEXT, chamber_name TEXT, init_date TEXT, chamber_type TEXT DEFAULT 'General Litigation', case_status TEXT DEFAULT 'Active', is_archived INTEGER DEFAULT 0, FOREIGN KEY(owner_email) REFERENCES users(email))")
        cursor.execute("CREATE TABLE IF NOT EXISTS message_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, chamber_id INTEGER, sender_role TEXT, message_body TEXT, ts_created TEXT, token_count INTEGER DEFAULT 0, FOREIGN KEY(chamber_id) REFERENCES chambers(id))")
        cursor.execute("CREATE TABLE IF NOT EXISTS law_assets (id INTEGER PRIMARY KEY AUTOINCREMENT, filename TEXT, filesize_kb REAL, page_count INTEGER, sync_timestamp TEXT, asset_status TEXT DEFAULT 'Verified')")
        cursor.execute("CREATE TABLE IF NOT EXISTS system_telemetry (event_id INTEGER PRIMARY KEY AUTOINCREMENT, user_email TEXT, event_type TEXT, description TEXT, event_timestamp TEXT)")
        connection.commit()
    except sqlite3.Error as e:
        st.error(f"DATABASE SCHEMA INITIALIZATION FAILED: {e}")
    finally:
        connection.close()

init_leviathan_db()
#-------------------------------------------------------------------------------
# SECTION 5: DATABASE TRANSACTIONAL OPERATIONS (CRUD)
# ------------------------------------------------------------------------------

def db_log_event(email, event_type, desc):
    """Logs system events to the telemetry table for administrative audit."""
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
    """ Registers a new identity in the sovereign vault. """
    if not email or not password or not name:
        return False
        
    conn = get_db_connection()
    if not conn:
        return False
        
    try:
        cursor = conn.cursor()
        
        # Duplicate Prevention
        cursor.execute("SELECT email FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return False
            
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Atomic Transaction 1: User Profile
        cursor.execute('''
            INSERT INTO users (email, full_name, vault_key, registration_date, last_login, provider) 
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, name, password, ts, ts, provider))
        
        # Atomic Transaction 2: Initial Chamber Allocation
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
    """
    Verifies user credentials against the advocate_ai_v2.db store.
    Returns: Full Name (str) or None.
    """
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
    """Persistently records every AI/User interaction."""
    conn = get_db_connection()
    if not conn:
        return
        
    try:
        cursor = conn.cursor()
        
        # Find Chamber Identity
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
    """Retrieves full litigation transcript for a specific chamber."""
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

# Initialize the Sovereign Database on Load
init_leviathan_db()

# ------------------------------------------------------------------------------
# SECTION 6: CORE ANALYTICAL SERVICES (AI ENGINE & SMTP GATEWAY)
# ------------------------------------------------------------------------------

@st.cache_resource
def get_analytical_engine():
    """Configures the Gemini 1.5 High-Context Model for Legal Analysis with Safety Bypass."""
    try:
        # Check if key exists to prevent silent failure
        if "GOOGLE_API_KEY" not in
