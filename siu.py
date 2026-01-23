import sys

# 1. DATABASE FIX (MUST BE AT THE VERY TOP)
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import os
import time
import glob
import json
from io import BytesIO
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 2. SESSION STATE INITIALIZATION (FIXES ATTRIBUTE ERROR)
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = None
if "case_files" not in st.session_state: st.session_state.case_files = {"General Consultation": {"history": []}}
if "active_case_name" not in st.session_state: st.session_state.active_case_name = "General Consultation"
if "prev_v_input" not in st.session_state: st.session_state.prev_v_input = ""
if "current_audio" not in st.session_state: st.session_state.current_audio = None
if "mic_key" not in st.session_state: st.session_state.mic_key = 0

# ==============================================================================
# 3. SECRETS & AI MODELS
# ==============================================================================
# Using st.secrets is more stable on Streamlit Cloud than os.getenv
API_KEY = st.secrets.get("GEMINI_API_KEY")

if not API_KEY:
    st.error("⚠️ Missing API Key! Go to Settings > Secrets and add GEMINI_API_KEY")
    st.stop()

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

@st.cache_resource
def init_ai_models():
    # Corrected model to gemini-1.5-flash
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2, google_api_key=API_KEY)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, embeddings

ai_engine, vector_embedder = init_ai_models()

# ==============================================================================
# 4. LOGIN SYSTEM (THE GATEKEEPER)
# ==============================================================================
def check_login(u, p):
    team = ["saim", "mustafa", "ibrahim", "huzaifa", "daniyal", "admin"]
    return u.lower() in team and p == "12345"

if not st.session_state.logged_in:
    st.title("⚖️ ADVOCATE AI - SINDH LEGAL INTELLIGENCE")
    with st.container(border=True):
        user_in = st.text_input("Username")
        pass_in = st.text_input("Password", type="password")
        if st.button("LOG IN", use_container_width=True):
            if check_login(user_in, pass_in):
                st.session_state.logged_in = True
                st.session_state.username = user_in
                st.rerun()
            else:
                st.error("Invalid Credentials")
    st.stop() # Stops the code here if not logged in

# ==============================================================================
# 5. MAIN APP UI (ONLY RUNS AFTER LOGIN)
# ==============================================================================
st.set_page_config(page_title="Advocate AI", page_icon="⚖️", layout="wide")

# Sidebar Logic
with st.sidebar:
    st.header(f"⚖️ Advocate {st.session_state.username.upper()}")
    view_mode = st.radio("System Menu", ["🏢 Chambers", "📚 Legal Library"])
    
    st.divider()
    if st.button("🚪 Log Out", type="primary"):
        st.session_state.logged_in = False
        st.rerun()

# RAG Knowledge Base Sync
def sync_kb():
    if not os.path.exists("DATA"): os.makedirs("DATA")
    pdfs = glob.glob("DATA/*.pdf")
    if not pdfs: return None, "No PDFs found."
    if os.path.exists("./chroma_db"):
        return Chroma(persist_directory="./chroma_db", embedding_function=vector_embedder), "Connected."
    return None, "Database not indexed."

if "law_db" not in st.session_state:
    db, msg = sync_kb()
    st.session_state.law_db = db

# ==============================================================================
# 6. CHAMBERS VIEW
# ==============================================================================
if view_mode == "🏢 Chambers":
    active_data = st.session_state.case_files[st.session_state.active_case_name]
    st.title(f"📂 Case: {st.session_state.active_case_name}")

    # Audio Playback
    if st.session_state.current_audio:
        st.audio(st.session_state.current_audio, format='audio/mp3', autoplay=True)

    # History
    for m in active_data["history"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # Inputs
    v_input = speech_to_text(language='en', start_prompt="🎤 Speak", key=f"mic_{st.session_state.mic_key}")
    u_prompt = st.chat_input("Enter legal query...")

    current_input = u_prompt if u_prompt else (v_input if v_input != st.session_state.prev_v_input else None)

    if current_input:
        st.session_state.prev_v_input = v_input if v_input else ""
        active_data["history"].append({"role": "user", "content": current_input})
        
        with st.chat_message("assistant"):
            with st.status("Analyzing Sindh Laws..."):
                # RAG Logic
                context = ""
                if st.session_state.law_db:
                    hits = st.session_state.law_db.similarity_search(current_input, k=3)
                    context = "\n".join([h.page_content for h in hits])
                
                prompt = f"You are a Sindh Legal Expert. Context: {context}\nQuery: {current_input}"
                response = ai_engine.invoke(prompt).content
                st.markdown(response)
                
                # TTS
                tts = gTTS(text=response, lang='en')
                sound_file = BytesIO()
                tts.write_to_fp(sound_file)
                st.session_state.current_audio = sound_file.getvalue()
        
        active_data["history"].append({"role": "assistant", "content": response})
        st.session_state.mic_key += 1
        st.rerun()
