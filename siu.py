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

if "show_audio_tools" not in st.session_state: st.session_state.show_audio_tools = False
if "voice_speed" not in st.session_state: st.session_state.voice_speed = 1.0
if "logged_in" not in st.session_state: st.session_state.logged_in = False

API_KEY = st.secrets["GEMINI_API_KEY"]
SQL_DB_FILE = "advocate_ai_master.db"

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
# 2. VOICE ENGINE (STRICT ENGLISH)
# ==============================================================================
def inject_voice_js(text, speed):
    safe_text = text.replace('\\', '\\\\').replace("'", "\\'").replace('"', '\\"').replace("\n", " ").strip()
    js_code = f"""
    <script>
        window.speakNow = function() {{
            window.speechSynthesis.cancel();
            var msg = new SpeechSynthesisUtterance("{safe_text}");
            msg.lang = 'en-US';
            msg.rate = {speed};
            window.speechSynthesis.speak(msg);
        }};
        window.pauseNow = function() {{ window.speechSynthesis.pause(); }};
        window.stopNow = function() {{ window.speechSynthesis.cancel(); }};
        window.speakNow();
    </script>
    """
    components.html(js_code, height=0)

# ==============================================================================
# 3. CHAMBERS
# ==============================================================================
def render_chambers():
    langs = {"English": "en-US", "Urdu": "ur-PK", "Sindhi": "sd-PK", "Punjabi": "pa-PK", "Pashto": "ps-PK", "Balochi": "bal-PK"}
    
    with st.sidebar:
        st.title("⚖️ Alpha Apex")
        target_lang = st.selectbox("🌐 Language", list(langs.keys()))
        sys_persona = st.text_input("AI Persona:", value="You are a Pakistani Law Analyst.")
        use_irac = st.toggle("Enable IRAC Format", value=True)
        
        st.divider()
        conn = sqlite3.connect(SQL_DB_FILE)
        cases = [r[0] for r in conn.execute("SELECT case_name FROM cases WHERE email=?", (st.session_state.user_email,)).fetchall()]
        conn.close()
        active_case = st.selectbox("Select Case", cases if cases else ["General"])
        st.session_state.active_case = active_case

    st.header(f"💼 {active_case}")

    # Display History
    history = db_load_history(st.session_state.user_email, active_case)
    for m in history:
        with st.chat_message(m["role"]): st.write(m["content"])
    
    st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)

    # FIXED BOTTOM BAR
    with st.container():
        st.divider()
        if st.session_state.show_audio_tools and target_lang == "English":
            ac1, ac2 = st.columns([4, 6])
            with ac1:
                b_p, b_pa, b_s = st.columns(3)
                if b_p.button("▶️ Play"): components.html("<script>window.parent.speakNow()</script>", height=0)
                if b_pa.button("⏸️ Pause"): components.html("<script>window.parent.pauseNow()</script>", height=0)
                if b_s.button("⏹️ Stop"): components.html("<script>window.parent.stopNow()</script>", height=0)
            with ac2:
                st.session_state.voice_speed = st.slider("Speed", 0.5, 2.0, st.session_state.voice_speed)

        c_hp, c_txt, c_mic = st.columns([1, 8, 1])
        with c_hp: 
            if st.button("🎧"): 
                st.session_state.show_audio_tools = not st.session_state.show_audio_tools
                st.rerun()
        with c_txt: text_in = st.chat_input("Ask Alpha Apex...")
        with c_mic: mic_in = speech_to_text(language=langs[target_lang], key='mic', just_once=True)

    # RESPONSE LOGIC
    query = text_in or mic_in
    if query:
        # 1. Save and Show User Query
        db_save_message(st.session_state.user_email, active_case, "user", query)
        
        # 2. Generate and Show AI Response
        try:
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY)
            irac = "Structure: Issue, Rule, Analysis, Conclusion." if use_irac else ""
            prompt = f"{sys_persona}\n{irac}\nRespond strictly in {target_lang} script. Query: {query}"
            
            with st.spinner("Analyzing..."):
                response = llm.invoke(prompt).content
                db_save_message(st.session_state.user_email, active_case, "assistant", response)
                st.rerun() # Refresh to show the new exchange
        except Exception as e:
            st.error(f"Error: {e}")

    # TTS Trigger
    if history and history[-1]["role"] == "assistant" and target_lang == "English":
        if st.session_state.show_audio_tools:
            inject_voice_js(history[-1]["content"], st.session_state.voice_speed)

# ==============================================================================
# 4. EXECUTION
# ==============================================================================
if not st.session_state.logged_in:
    st.title("⚖️ Alpha Apex Login")
    email = st.text_input("Email")
    if st.button("Enter"):
        st.session_state.logged_in = True
        st.session_state.user_email = email
        conn = sqlite3.connect(SQL_DB_FILE)
        conn.execute("INSERT OR IGNORE INTO cases (email, case_name, created_at) VALUES (?,?,?)", (email, "General", "2026-01-24"))
        conn.commit(); conn.close()
        st.rerun()
else:
    page = st.sidebar.radio("Navigation", ["Chambers", "About"])
    if page == "Chambers": render_chambers()
    else: st.write("Legal AI platform.")
