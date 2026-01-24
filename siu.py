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
SQL_DB_FILE = "advocate_ai_v6.db"

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
# 2. STRICT ENGLISH TTS UTILITY
# ==============================================================================
def play_voice_js(english_text):
    """Strictly filters for English voices only"""
    safe_text = english_text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <div style="background: #f1f5f9; padding: 10px; border-radius: 8px; border: 1px solid #cbd5e1; margin: 10px 0;">
        <span style="font-size: 0.8rem; font-weight: bold; color: #1e293b;">🔊 Audio Brief (English):</span>
        <button onclick="window.speakEnglish()">▶ Play</button>
        <button onclick="window.speechSynthesis.pause()">⏸ Pause</button>
        <button onclick="window.speechSynthesis.cancel()" style="background:#fca5a5; border:none; border-radius:3px;">⏹ Stop</button>
    </div>
    <script>
        window.speakEnglish = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            
            // Force English Voice
            var voices = window.speechSynthesis.getVoices();
            var enVoice = voices.find(v => v.lang.startsWith('en-US')) || voices.find(v => v.lang.startsWith('en'));
            
            if(enVoice) {{
                msg.voice = enVoice;
                msg.lang = 'en-US';
            }}
            msg.rate = 1.0;
            window.speechSynthesis.speak(msg);
        }};
        // Ensure voices are loaded
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
    
    # Quick Actions
    st.write("### Quick Actions")
    q1, q2, q3 = st.columns(3)
    quick_query = None
    if q1.button("🔍 Infer Context"): quick_query = "Summarize the legal context of this case in English."
    if q2.button("⚖️ Give Ruling"): quick_query = "What is the legal opinion on this under Pakistan Law? Explain in English."
    if q3.button("📝 Summarize"): quick_query = "Give me a brief summary of the case facts in English."

    st.divider()
    m_col, i_col = st.columns([1, 8])
    with m_col: voice_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)
    with i_col: text_in = st.chat_input("Enter your query...")

    history = db_load_history(st.session_state.user_email, active_case)
    with chat_container:
        for m in history:
            with st.chat_message(m["role"]):
                # Only show the script part to the user
                st.write(m["content"].split("|||")[0])

    final_query = voice_in or text_in or quick_query
    if final_query:
        db_save_message(st.session_state.user_email, active_case, "user", final_query)
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=API_KEY)
            
            # MANDATORY FORMATTING INSTRUCTION
            prompt = f"""
            SYSTEM: You are a Pakistani Legal Expert.
            USER REQUEST: {final_query}
            
            INSTRUCTIONS:
            1. Respond in TWO DISTINCT PARTS separated by '|||'.
            2. PART 1 (VISUAL): Write the full legal response in {target_lang} native script. Do NOT include English here.
            3. PART 2 (AUDIO): Provide a concise English translation of that response. Do NOT include {target_lang} script here.
            
            FORMAT: [Part 1 Script] ||| [Part 2 English]
            """
            
            response = llm.invoke(prompt).content
            db_save_message(st.session_state.user_email, active_case, "assistant", response)
            st.rerun() 
        except Exception as e: st.error(f"Error: {e}")

    if history and history[-1]["role"] == "assistant":
        if "|||" in history[-1]["content"]:
            # Extract ONLY the English part for TTS
            parts = history[-1]["content"].split("|||")
            english_tts_content = parts[1].strip()
            
            if st.session_state.get("last_spoken") != english_tts_content:
                play_voice_js(english_tts_content)
                st.session_state.last_spoken = english_tts_content

# ==============================================================================
# 4. ABOUT SECTION (Updated with your request)
# ==============================================================================
def render_about():
    st.header("ℹ️ About Advocate AI")
    st.markdown("""
    ### 🏛️ The Advocate AI: A Digital Bridge to Law
    Alpha Apex is a specialized legal intelligence platform designed to make Pakistani law accessible to everyone. 
    It translates complex statutes into conversational advice, acting as a 24/7 digital consultant.
    
    ### ⚠️ The Problem: The Justice Gap
    The primary problem in Pakistan’s legal landscape is the "justice gap" caused by high consultation costs, 
    dense legal jargon, and severe language barriers.
    
    ### ✨ The Solution: Democratizing Legal Power
    This AI creates value by offering instant analysis in native scripts (Sindhi, Pashto, Balochi) 
    while providing English audio summaries to ensure clarity and confidence.
    """)

# Main Navigation logic (Fixed Syntax)
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
