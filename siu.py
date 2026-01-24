import streamlit as st
import os
import sqlite3
import glob
import time
import pandas as pd
import streamlit.components.v1 as components
import json
import re
from datetime import datetime
import chromadb
from langchain_chroma import Chroma

# ==============================================================================
# 1. SYSTEM CONFIGURATION
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

# API Key and Model Config
API_KEY = st.secrets["GEMINI_API_KEY"]
DATA_FOLDER = "DATA"
DB_PATH = "./chroma_db"
SQL_DB_FILE = "advocate_ai_v2.db"
MODEL_NAME = "gemini-2.5-flash" # Keeping your specified model

# ==============================================================================
# 2. UI STYLING & VOICE JS
# ==============================================================================

st.set_page_config(page_title="Alpha Apex | Advocate AI", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .main .block-container { padding-bottom: 150px; }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #eee; }
    .mic-box { display: flex; align-items: center; justify-content: center; padding-top: 38px; }
    </style>
""", unsafe_allow_html=True)

def play_voice_js(text, lang_code):
    """Dynamic Browser-Based Voice Synthesis"""
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            function setVoice() {{
                var voices = window.speechSynthesis.getVoices();
                msg.lang = '{lang_code}';
                var v = voices.find(v => v.lang.startsWith('{lang_code.split("-")[0]}'));
                if (v) msg.voice = v;
                window.speechSynthesis.speak(msg);
            }}
            if (window.speechSynthesis.getVoices().length !== 0) {{ setVoice(); }}
            else {{ window.speechSynthesis.onvoiceschanged = setVoice; }}
        </script>
    """
    components.html(js_code, height=0)

def stream_text(text):
    for word in text.split(" "):
        yield word + " "
        time.sleep(0.01)

# ==============================================================================
# 3. DATABASE LOGIC (SQLITE)
# ==============================================================================

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
# 4. AI & VECTOR SEARCH
# ==============================================================================

@st.cache_resource
def load_models():
    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, temperature=0.3, google_api_key=API_KEY)
    embed = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, embed

ai_engine, vector_embedder = load_models()

def sync_knowledge_base():
    if not os.path.exists(DATA_FOLDER): os.makedirs(DATA_FOLDER)
    pdfs = glob.glob(f"{DATA_FOLDER}/*.pdf")
    if not pdfs: return None, "No PDFs."
    if os.path.exists(DB_PATH):
        return Chroma(persist_directory=DB_PATH, embedding_function=vector_embedder), "Connected."
    else:
        chunks = []
        for p in pdfs:
            loader = PyPDFLoader(p)
            chunks.extend(loader.load_and_split(RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=200)))
        return Chroma.from_documents(chunks, vector_embedder, persist_directory=DB_PATH), "Indexed."

if "law_db" not in st.session_state:
    db_inst, _ = sync_knowledge_base()
    st.session_state.law_db = db_inst

# ==============================================================================
# 5. AUTHENTICATION
# ==============================================================================

config_dict = dict(st.secrets["google_auth"])
secret_data = {"web": config_dict}
with open('client_secret.json', 'w') as f: json.dump(secret_data, f)

authenticator = Authenticate('client_secret.json', config_dict['redirect_uris'][0], 'adv_cookie', 'app_secret', 30)

if "logged_in" not in st.session_state: st.session_state.logged_in = False

def login_page():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.write("# ⚖️ Advocate AI")
        authenticator.login()

# ==============================================================================
# 6. CHAMBERS PAGE (TIMELINE + MULTILANG + VOICE)
# ==============================================================================

def render_chambers_page():
    # Comprehensive Language List
    languages = {
        "English": {"script": "English", "code": "en-US"},
        "Sindhi": {"script": "Sindhi (Sindhi script)", "code": "sd-PK"},
        "Urdu": {"script": "Urdu (Urdu script)", "code": "ur-PK"},
        "Punjabi": {"script": "Punjabi (Shahmukhi script)", "code": "pa-PK"},
        "Arabic": {"script": "Arabic", "code": "ar-SA"},
        "French": {"script": "French", "code": "fr-FR"},
        "Spanish": {"script": "Spanish", "code": "es-ES"},
        "Turkish": {"script": "Turkish", "code": "tr-TR"},
        "Chinese": {"script": "Chinese (Simplified)", "code": "zh-CN"},
        "German": {"script": "German", "code": "de-DE"},
        "Russian": {"script": "Russian", "code": "ru-RU"},
        "Hindi": {"script": "Hindi (Devanagari)", "code": "hi-IN"},
        "Bengali": {"script": "Bengali", "code": "bn-BD"},
        "Japanese": {"script": "Japanese", "code": "ja-JP"},
        "Korean": {"script": "Korean", "code": "ko-KR"},
        "Portuguese": {"script": "Portuguese", "code": "pt-PT"},
        "Pashto": {"script": "Pashto", "code": "ps-PK"},
        "Balochi": {"script": "Balochi", "code": "bal-PK"},
        "Persian": {"script": "Persian (Farsi)", "code": "fa-IR"},
        "Italian": {"script": "Italian", "code": "it-IT"}
    }

    with st.sidebar:
        st.header(f"👨‍⚖️ {st.session_state.username}")
        
        # 🌐 Language Settings
        st.divider()
        st.subheader("🌐 Language & Voice")
        target_lang = st.selectbox("AI Response Language", options=list(languages.keys()), index=0)
        
        # 🕒 Timeline Tool
        st.divider()
        st.subheader("📅 Expert Tools")
        history = db_load_history(st.session_state.user_email, st.session_state.active_case)
        if st.button("🕒 Extract Case Timeline"):
            if history:
                with st.status("Analyzing dates..."):
                    t_prompt = f"Extract a bulleted chronological timeline of events/dates from this chat: {' '.join([m['content'] for m in history])}"
                    timeline = ai_engine.invoke(t_prompt).content
                st.info(timeline)
            else: st.warning("No case history yet.")

        # 📂 Case Files
        st.divider()
        cases = db_get_cases(st.session_state.user_email)
        if "active_case" not in st.session_state: st.session_state.active_case = cases[0]
        sel = st.selectbox("Current Case", cases, index=cases.index(st.session_state.active_case))
        if sel != st.session_state.active_case:
            st.session_state.active_case = sel
            st.rerun()
            
        st.divider()
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    st.title(f"💼 {st.session_state.active_case}")

    # Chat UI
    h_cont = st.container()
    with h_cont:
        for msg in history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # Input logic
    c_text, c_mic = st.columns([10, 1])
    with c_text: text_in = st.chat_input(f"Consult Alpha Apex in {target_lang}...")
    with c_mic:
        st.markdown('<div class="mic-box">', unsafe_allow_html=True)
        voice_in = speech_to_text(language=languages[target_lang]["code"], start_prompt="🎤", stop_prompt="⏹️", key='mic', just_once=True)
        st.markdown('</div>', unsafe_allow_html=True)

    final_in = voice_in if voice_in else text_in
    if final_in:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_in)
        with h_cont:
            with st.chat_message("user"): st.markdown(final_in)
            with st.chat_message("assistant"):
                p, res, ctx = st.empty(), "", ""
                if st.session_state.law_db:
                    docs = st.session_state.law_db.as_retriever(search_kwargs={"k": 3}).invoke(final_in)
                    ctx = "\n\n".join([d.page_content for d in docs])
                
                lang_cfg = languages[target_lang]
                prompt = f"You are a Senior Legal Expert. Respond ONLY in {lang_cfg['script']}.\nContext: {ctx}\nUser: {final_in}"
                
                ai_out = ai_engine.invoke(prompt).content
                for chunk in stream_text(ai_out):
                    res += chunk
                    p.markdown(res + "▌")
                p.markdown(res)
                db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", res)
                play_voice_js(res, lang_cfg["code"])

# ==============================================================================
# 7. MAIN APP
# ==============================================================================

if st.session_state.get('connected'):
    if not st.session_state.get('logged_in'):
        user_info = st.session_state.get('user_info', {})
        st.session_state.user_email = user_info.get('email')
        st.session_state.username = user_info.get('name', "Lawyer")
        st.session_state.logged_in = True
        db_register_user(st.session_state.user_email, st.session_state.username)
        st.rerun()

if not st.session_state.get('logged_in'):
    login_page()
else:
    with st.sidebar:
        nav = st.radio("Menu", ["🏢 Chambers", "📚 Library", "ℹ️ Team"])
    
    if nav == "🏢 Chambers": render_chambers_page()
    elif nav == "📚 Library":
        st.title("📚 Law Library")
        st.table([{"Doc": os.path.basename(f), "Status": "Ready"} for f in glob.glob(f"{DATA_FOLDER}/*.pdf")])
    else:
        st.title("ℹ️ Alpha Apex Team")
        st.info("Saim, Mustafa, Ibrahim, Huzaifa, Daniyal")
