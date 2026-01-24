

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

# Secure way to fetch keys on deployment
API_KEY = st.secrets["GOOGLE_API_KEY"]
DATA_FOLDER = "data"
DB_PATH = "./chroma_db"
SQL_DB_FILE = "advocate_ai_v2.db"
MODEL_NAME = "gemini-2.5-flash"

# ==============================================================================
# 2. UI STYLING & JS
# ==============================================================================

st.set_page_config(page_title="Advocate AI", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    /* Ensure the main container has enough bottom padding so input doesn't cover text */
    .main .block-container { padding-bottom: 150px; }
   
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; border: 1px solid #eee; }
   
    /* Mic Alignment Fix */
    .mic-box {
        display: flex;
        align-items: center;
        justify-content: center;
        padding-top: 38px;
    }
   
    /* Urdu Font */
    [data-testid="stMarkdownContainer"] p {
        font-family: 'Segoe UI', 'Tahoma', sans-serif;
        font-size: 1.1rem;
    }
    </style>
""", unsafe_allow_html=True)

def play_voice_js(text):
    safe_text = text.replace("'", "").replace('"', "").replace("\n", " ").strip()
    is_urdu = bool(re.search(r'[\u0600-\u06FF]', safe_text))
    js_code = f"""
        <script>
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance('{safe_text}');
            function setVoice() {{
                var voices = window.speechSynthesis.getVoices();
                if ({str(is_urdu).lower()}) {{
                    msg.lang = 'ur-PK';
                    var v = voices.find(v => v.lang.includes('ur') || v.lang.includes('hi'));
                    if (v) msg.voice = v;
                }} else {{
                    msg.lang = 'en-US';
                }}
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
# 3. DATABASE
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

def db_rename_case(email, old_name, new_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE cases SET case_name = ? WHERE email = ? AND case_name = ?", (new_name, email, old_name))
    conn.commit()
    conn.close()

def db_create_case(email, case_name):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, case_name, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    conn.close()

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
# 4. AI & KNOWLEDGE
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
# 5. AUTH
# ==============================================================================

# 1. Create the physical file on the server from secrets
try:
    config_dict = dict(st.secrets["google_auth"])
    # Wrap in "web" as required by the underlying Google library
    secret_data = {"web": config_dict}
   
    with open('client_secret.json', 'w') as f:
        json.dump(secret_data, f)
       
    my_uri = config_dict['redirect_uris'][0]
except KeyError:
    st.error("Missing 'google_auth' in Streamlit Secrets!")
    st.stop()

# 2. Positional Arguments: (path, uri, cookie_name, key, expiry)
# This format avoids "unexpected keyword argument" errors
authenticator = Authenticate(
    'client_secret.json',
    my_uri,
    'advocate_ai_cookie',
    'legal_app_secret_key',
    30
)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login_page():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.write("# ⚖️ Advocate AI")
        with st.container(border=True):
            t1, t2 = st.tabs(["Google", "Email"])
            with t1:
                authenticator.login()
            with t2:
                e = st.text_input("Email")
                if st.button("Enter"):
                    if "@" in e:
                        st.session_state.logged_in = True
                        st.session_state.user_email = e
                        st.session_state.username = e.split("@")[0].title()
                        db_register_user(e, st.session_state.username)
                        st.rerun()
# ==============================================================================
# 6. CHAMBERS PAGE (FIXED LAYOUT)
# ==============================================================================

def render_chambers_page():
    # 1. Sidebar Logic
    with st.sidebar:
        st.header(f"👨‍⚖️ {st.session_state.username}")
        cases = db_get_cases(st.session_state.user_email)
        if "active_case" not in st.session_state: st.session_state.active_case = cases[0]
        sel = st.selectbox("Case Files", cases, index=cases.index(st.session_state.active_case))
        if sel != st.session_state.active_case:
            st.session_state.active_case = sel
            st.rerun()
       
        with st.expander("Rename Case"):
            nt = st.text_input("New Name", value=st.session_state.active_case)
            if st.button("Confirm"):
                db_rename_case(st.session_state.user_email, st.session_state.active_case, nt)
                st.session_state.active_case = nt
                st.rerun()
       
        if st.button("New Case"):
            db_create_case(st.session_state.user_email, f"Case {len(cases)+1}")
            st.rerun()
       
        st.divider()
        if st.button("Log Out"):
            st.session_state.logged_in = False
            st.rerun()

    st.title(f"⚖️ {st.session_state.active_case}")

    # 2. Chat History Block (ALWAYS ABOVE INPUT)
    history_container = st.container()
    with history_container:
        history = db_load_history(st.session_state.user_email, st.session_state.active_case)
        for msg in history:
            with st.chat_message(msg["role"]): st.markdown(msg["content"])

    # 3. Input Tools Block (STAYS AT THE BOTTOM)
    input_placeholder = st.container()
    with input_placeholder:
        c_text, c_mic = st.columns([10, 1])
        with c_text:
            text_in = st.chat_input("Ask Sindh Law / قانونی سوال...")
        with c_mic:
            st.markdown('<div class="mic-box">', unsafe_allow_html=True)
            voice_in = speech_to_text(language='ur-PK', start_prompt="🎤", stop_prompt="⏹️", key='mic_chambers', just_once=True)
            st.markdown('</div>', unsafe_allow_html=True)

    # 4. Logic Handling
    final_in = voice_in if voice_in else text_in
    is_v = True if voice_in else False

    if final_in:
        db_save_message(st.session_state.user_email, st.session_state.active_case, "user", final_in)
        # Append immediately to history container
        with history_container:
            with st.chat_message("user"): st.markdown(final_in)
            with st.chat_message("assistant"):
                p, res = st.empty(), ""
                ctx = ""
                if st.session_state.law_db:
                    docs = st.session_state.law_db.as_retriever(search_kwargs={"k": 4}).invoke(final_in)
                    ctx = "\n\n".join([d.page_content for d in docs])
               
                prompt = f"Senior Legal Expert Sindh Law. Use same language as user (Urdu script or English).\nContext: {ctx}\nUser: {final_in}"
               
                try:
                    ai_out = ai_engine.invoke(prompt).content
                    for chunk in stream_text(ai_out):
                        res += chunk
                        p.markdown(res + "▌")
                    p.markdown(res)
                    db_save_message(st.session_state.user_email, st.session_state.active_case, "assistant", res)
                    if is_v: play_voice_js(res)
                except Exception as e: st.error(f"Error: {e}")

# ==============================================================================
# 7. MAIN
# ==============================================================================

# ==============================================================================
# 7. MAIN EXECUTION FLOW (FIXED LOGIN & SESSION SYNC)
# ==============================================================================

# Step 1: Handle Google Handshake immediately
if st.session_state.get('connected'):
    # Check if we haven't synced the Google info to our local session yet
    if not st.session_state.get('logged_in'):
        user_info = st.session_state.get('user_info', {})
        st.session_state.user_email = user_info.get('email')
        st.session_state.username = user_info.get('name', "Lawyer")
        st.session_state.logged_in = True
       
        # Register in SQLite database
        db_register_user(st.session_state.user_email, st.session_state.username)
       
        # FORCE RERUN: This breaks the loop and moves the script to the 'else' block
        st.rerun()

# Step 2: Determine which page to show based on finalized state
if not st.session_state.get('logged_in'):
    login_page()
else:
    # Sidebar navigation for logged-in users
    with st.sidebar:
        st.markdown("---")
        nav = st.radio("Navigate", ["🏢 Chambers", "📚 Library", "ℹ️ Team"], label_visibility="collapsed")
   
    if nav == "🏢 Chambers":
        render_chambers_page()
    elif nav == "📚 Library":
        st.title("📚 Legal Library")
        f_list = glob.glob(f"{DATA_FOLDER}/*.pdf")
        if f_list:
            st.table([{"Document": os.path.basename(f), "Status": "✅ Indexed"} for f in f_list])
        else:
            st.warning("No legal documents found in DATA folder.")
    else:
        st.title("ℹ️ Development Team")
        st.info("Advocate AI - Sindh Legal Intelligence System")
        st.markdown("""
        **Project Contributors:**
        * Saim Ahmed
        * Mustafa Khan
        * Ibrahim Sohail
        * Huzaifa Khan
        * Daniyal Faraz

        """)


