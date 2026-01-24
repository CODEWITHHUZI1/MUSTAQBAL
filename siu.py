import streamlit as st
import os
import sqlite3
import glob
import time
import json
import re
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit.components.v1 as components

# ==============================================================================
# 1. SYSTEM & DATABASE CONFIGURATION
# ==============================================================================

try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass 

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from streamlit_mic_recorder import speech_to_text
from streamlit_google_auth import Authenticate

# Core Configuration
API_KEY = st.secrets["GEMINI_API_KEY"]
DATA_FOLDER = "DATA"
DB_PATH = "./chroma_db"
SQL_DB_FILE = "advocate_ai_v3.db"
MODEL_NAME = "gemini-2.5-flash" 

def send_email_report(receiver_email, case_name, content):
    """Sends the legal timeline to the logged-in user's email"""
    try:
        sender_email = st.secrets["EMAIL_USER"]
        sender_password = st.secrets["EMAIL_PASS"]
        
        msg = MIMEMultipart()
        msg['From'] = f"Alpha Apex Legal AI <{sender_email}>"
        msg['To'] = receiver_email
        msg['Subject'] = f"Case Report: {case_name}"
        
        body = f"Hello,\n\nAlpha Apex has generated a report for '{case_name}':\n\n{content}\n\nRegards,\nAlpha Apex Team"
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
        return True
    except:
        return False

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, username TEXT, joined_date TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

def db_register_user(email, username):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users VALUES (?,?,?)", (email, username, datetime.now().strftime("%Y-%m-%d")))
    c.execute("SELECT count(*) FROM cases WHERE email=?", (email,))
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General Consultation", datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_create_case(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, case_name, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

def db_rename_case(email, old_name, new_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE cases SET case_name = ? WHERE email = ? AND case_name = ?", (new_name, email, old_name))
    conn.commit()
    conn.close()

def db_get_cases(email):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT case_name FROM cases WHERE email=? ORDER BY id DESC", (email,))
    cases = [row[0] for row in c.fetchall()]
    conn.close()
    return cases if cases else ["General Consultation"]

def db_save_message(email, case_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    res = c.fetchone()
    if res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", (res[0], role, content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def db_load_history(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT role, content FROM history JOIN cases ON history.case_id = cases.id WHERE cases.email=? AND cases.case_name=? ORDER BY history.id ASC", (email, case_name))
    data = [{"role": r, "content": t} for r, t in c.fetchall()]
    conn.close()
    return data

init_sql_db()

# ==============================================================================
# 2. AI MODELS & UI STYLING
# ==============================================================================

st.set_page_config(page_title="Alpha Apex | Advocate AI", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #eee; }
    .mic-box { display: flex; align-items: center; justify-content: center; padding-top: 38px; }
    /* This ensures the chat is above the input bar */
    .main .block-container { padding-bottom: 150px; }
    </style>
""", unsafe_allow_html=True)

def play_voice_js(text, lang_code):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            msg.lang = '{lang_code}';
            window.speechSynthesis.speak(msg);
        </script>
    """
    components.html(js_code, height=0)

@st.cache_resource
def load_models():
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.3, google_api_key=API_KEY)
    embed = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, embed

ai_engine, vector_embedder = load_models()

def sync_knowledge_base():
    if not os.path.exists(DATA_FOLDER): os.makedirs(DATA_FOLDER)
    if os.path.exists(DB_PATH): return Chroma(persist_directory=DB_PATH, embedding_function=vector_embedder), "OK"
    pdfs = glob.glob(f"{DATA_FOLDER}/*.pdf")
    if pdfs:
        chunks = []
        for p in pdfs:
            loader = PyPDFLoader(p)
            chunks.extend(loader.load_and_split(RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)))
        return Chroma.from_documents(chunks, vector_embedder, persist_directory=DB_PATH), "Ready"
    return None, "Empty"

if "law_db" not in st.session_state:
    db_inst, _ = sync_knowledge_base()
    st.session_state.law_db = db_inst

# ==============================================================================
# 3. CHAMBERS UI (RESTORED ACTIONS + MANAGEMENT)
# ==============================================================================

def render_chambers_page():
    cases = db_get_cases(st.session_state.user_email)
    if "active_case" not in st.session_state:
        st.session_state.active_case = cases[0]

    languages = {
        "English": {"script": "English", "code": "en-US"},
        "Sindhi": {"script": "Sindhi script", "code": "sd-PK"},
        "Urdu": {"script": "Urdu script", "code": "ur-PK"},
        "Arabic": {"script": "Arabic", "code": "ar-SA"},
        "French": {"script": "French", "code": "fr-FR"},
        "Punjabi": {"script": "Punjabi script", "code": "pa-PK"},
        "Pashto": {"script": "Pashto script", "code": "ps-PK"}
    }

    with st.sidebar:
        st.header(f"👨‍⚖️ {st.session_state.username}")
        target_lang = st.selectbox("🌐 Response Language", options=list(languages.keys()))
        lang_cfg = languages[target_lang]

        st.divider()
        st.subheader("📁 Case Management")
        sel = st.selectbox("Switch Case", cases, index=cases.index(st.session_state.active_case))
        if sel != st.session_state.active_case:
            st.session_state.active_case = sel
            st.rerun()

        with st.expander("✏️ Rename Case"):
            new_name = st.text_input("New Case Name", value=st.session_state.active_case)
            if st.button("Update Name"):
                db_rename_case(st.session_state.user_email, st.session_state.active_case, new_name)
                st.session_state.active_case = new_name
                st.rerun()

        if st.button("➕ New Consultation"):
            db_create_case(st.session_state.user_email, f"Consultation {len(cases)+1}")
            st.rerun()

        st.divider()
        st.subheader("📅 Export Tools")
        history = db_load_history(st.session_state.user_email, st.session_state.active_case)
        
        if st.button("🕒 Extract Case Timeline"):
            if history:
                with st.spinner("Processing..."):
                    t_prompt = f"Create a chronological timeline of dates and legal events from this chat: {' '.join([m['content'] for m in history])}"
                    st.session_state.export_data = ai_engine.invoke(t_prompt).content
                st.info(st.session_state.export_data)
            else: st.warning("No data found.")
        
        if "export_data" in st.session_state:
            if st.button("📧 Email Export to Me"):
                with st.spinner("Mailing..."):
                    if send_email_report(st.session_state.user_email, st.session_state.active_case, st.session_state.export_data):
                        st.success("Report emailed!")
                    else: st.error("Configuration Error. Check Secrets.")

        st.divider()
        if st.button("Log Out"):
            st.session_state.clear()
            st.rerun()

    st.title(f"💼 {st.session_state.active_case}")

    # Chat Display (Above input)
    for msg in history:
        with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Quick Action Buttons
    st.write("---")
    qc1, qc2, qc3 = st.columns(3)
    quick_input = None
    with qc1:
        if st.button("🧠 Infer Legal Path"): quick_input = "Based on our conversation, what is the best legal path forward under Sindh Law?"
    with qc2:
        if st.button("📜 Give Preliminary Ruling"): quick_input = "Act as a Judge of the Sindh High Court and provide a preliminary ruling based on these facts."
    with qc3:
        if st.button("📝 Summarize Facts"): quick_input = "Please provide a concise legal summary of the facts discussed so far."

    # Input area
    c_text, c_mic = st.columns([10, 1])
    with c_text: text_in = st.chat_input(f"Consult Alpha Apex in {target_lang}...")
    with c_mic:
        st.markdown('<div class="mic-box">', unsafe_allow_html=True)
        voice_in = speech_to_text(language=lang_cfg["code"], key='mic', just_once=True)
        st.markdown('</div>', unsafe_allow_html=True)

    final_in = quick_input if quick_input else (voice_in if voice_in else text_in)
    
    if final_in:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_in)
        with st.chat_message("user"): st.markdown(final_in)
        with st.chat_message("assistant"):
            ctx = ""
            if st.session_state.law_db:
                docs = st.session_state.law_db.as_retriever(search_kwargs={"k": 3}).invoke(final_in)
                ctx = "\n\n".join([d.page_content for d in docs])
            
            p = f"Senior Legal Expert on Sindh Law. Respond ONLY in {lang_cfg['script']}.\nContext: {ctx}\nUser: {final_in}"
            res = ai_engine.invoke(p).content
            st.markdown(res)
            db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", res)
            play_voice_js(res, lang_cfg["code"])
            st.rerun() # Refresh to keep chat flow

# ==============================================================================
# 4. AUTHENTICATION & NAVIGATION
# ==============================================================================

config_dict = dict(st.secrets["google_auth"])
secret_data = {"web": config_dict}
with open('client_secret.json', 'w') as f: json.dump(secret_data, f)
authenticator = Authenticate('client_secret.json', config_dict['redirect_uris'][0], 'adv_cookie', 'app_secret', 30)

if "logged_in" not in st.session_state: 
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.write("# ⚖️ Alpha Apex AI")
        with st.container(border=True):
            st.subheader("Secure Access")
            authenticator.login() 
            st.divider()
            st.subheader("Manual Entry")
            e = st.text_input("Professional Email")
            if st.button("Enter Chambers"):
                if "@" in e and "." in e:
                    st.session_state.logged_in = True
                    st.session_state.user_email = e
                    st.session_state.username = e.split("@")[0].capitalize()
                    db_register_user(e, st.session_state.username)
                    st.success("Identity Verified.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Invalid email.")
else:
    with st.sidebar:
        nav = st.radio("System Menu", ["🏢 Chambers", "📚 Library", "ℹ️ Team"])
    
    if nav == "🏢 Chambers":
        render_chambers_page()
    elif nav == "📚 Library":
        st.title("📚 Legal Library")
        pdfs = [os.path.basename(f) for f in glob.glob(f"{DATA_FOLDER}/*.pdf")]
        st.table([{"Document": p, "Status": "Indexed"} for p in pdfs])
    else:
        st.title("ℹ️ Team Alpha Apex")
        st.info("Saim, Mustafa, Ibrahim, Huzaifa, Daniyal")
