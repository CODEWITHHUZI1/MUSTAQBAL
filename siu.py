__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import sqlite3
import datetime
import streamlit.components.v1 as components
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. INITIALIZATION & DATABASE
# ==============================================================================
st.set_page_config(page_title="Alpha Apex", page_icon="⚖️", layout="wide")
API_KEY = st.secrets["GEMINI_API_KEY"]
SQL_DB_FILE = "advocate_ai_v7.db"

def init_sql_db():
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS cases (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT, case_name TEXT, created_at TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS history (id INTEGER PRIMARY KEY AUTOINCREMENT, case_id INTEGER, role TEXT, content TEXT, timestamp TEXT)')
    conn.commit()
    conn.close()

def db_save_message(email, case_name, role, content):
    conn = sqlite3.connect(SQL_DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id FROM cases WHERE email=? AND case_name=?", (email, case_name))
    res = c.fetchone()
    if res:
        c.execute("INSERT INTO history (case_id, role, content, timestamp) VALUES (?,?,?,?)", 
                  (res[0], role, content, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
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
# 2. STRICT ENGLISH-ONLY TTS ENGINE
# ==============================================================================
def play_voice_js(english_text):
    safe_text = english_text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f8fafc; padding: 10px; border-radius: 8px; border: 1px solid #e2e8f0; margin: 10px 0; font-family: sans-serif;">
        <span style="font-size: 0.8rem; font-weight: bold; color: #1e293b;">🔊 English Audio Summary:</span>
        <button onclick="window.speakEnglish()" style="margin-left:10px;">Play</button>
        <button onclick="window.speechSynthesis.pause()">Pause</button>
        <button onclick="window.speechSynthesis.cancel()">Stop</button>
    </div>
    <script>
        window.speakEnglish = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            var voices = window.speechSynthesis.getVoices();
            // Strictly select English voice
            var enVoice = voices.find(v => v.lang.startsWith('en-US')) || voices.find(v => v.lang.startsWith('en'));
            if(enVoice) {{
                msg.voice = enVoice;
                msg.lang = 'en-US';
            }}
            msg.rate = 1.0;
            window.speechSynthesis.speak(msg);
        }};
        if (speechSynthesis.onvoiceschanged !== undefined) {{
            speechSynthesis.onvoiceschanged = window.speakEnglish;
        }}
        window.speakEnglish();
    </script>
    """
    components.html(js_code, height=90)

# ==============================================================================
# 3. CHAMBERS
# ==============================================================================
def render_chambers():
    langs = {"Sindhi": "sd-PK", "Pashto": "ps-PK", "Balochi": "bal-PK", "English": "en-US"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Display Language", list(langs.keys()))
        
        st.divider()
        st.subheader("📁 Case Management")
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        active_case = st.selectbox("Active Case", cases if cases else ["General"])
        st.session_state.active_case = active_case

    st.header(f"💼 Case: {active_case}")
    chat_container = st.container()
    
    st.divider()
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Enter your query...")

    history = db_load_history(st.session_state.user_email, active_case)
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]):
                # Display only the first part (Native Script)
                st.write(m["content"].split("|||")[0])

    final_query = voice_in or text_in
    if final_query:
        db_save_message(st.session_state.user_email, active_case, "user", final_query)
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)
            
            # THE STRICT TWO-PART PROMPT
            prompt = f"""
            You are a Pakistani Law Analyst.
            1. Provide a detailed legal answer in {target_lang} script.
            2. Provide a concise summary of that answer in English ONLY.
            
            Format: [Native Script Response] ||| [English Audio Summary]
            
            Query: {final_query}
            """
            
            response = llm.invoke(prompt).content
            db_save_message(st.session_state.user_email, active_case, "assistant", response)
            st.rerun() 
        except Exception as e: st.error(f"Error: {e}")

    if history and history[-1]["role"] == "assistant":
        if "|||" in history[-1]["content"]:
            # Extract only Part 2 (English) for TTS
            english_audio_text = history[-1]["content"].split("|||")[1].strip()
            if st.session_state.get("last_spoken") != english_audio_text:
                play_voice_js(english_audio_text)
                st.session_state.last_spoken = english_audio_text

# ==============================================================================
# 4. ABOUT SECTION
# ==============================================================================
def render_about():
    st.header("ℹ️ About Advocate AI")
    st.markdown("""
    ### 🏛️ Advocate AI: Digital Justice
    Alpha Apex acts as a 24/7 digital consultant for Pakistani Law.
    
    ### ⚠️ Language Barriers Solved
    This tool provides legal analysis in native **Sindhi, Pashto, and Balochi** scripts. 
    To ensure technical clarity, all audio summaries are provided strictly in **English**.
    """)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    email = st.text_input("Email")
    if st.button("Login"):
        st.session_state.logged_in = True
        st.session_state.user_email = email
        st.rerun()
else:
    page = st.sidebar.radio("Nav", ["Chambers", "About"])
    if page == "Chambers": render_chambers()
    else: render_about()
