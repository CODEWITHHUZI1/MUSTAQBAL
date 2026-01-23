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
from dotenv import load_dotenv
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 2. SESSION STATE INITIALIZATION (FIXES ATTRIBUTE ERROR)
# ==============================================================================
# We define these BEFORE the app tries to run any logic
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = None
if "case_files" not in st.session_state: st.session_state.case_files = {"General Consultation": {"history": []}}
if "active_case_name" not in st.session_state: st.session_state.active_case_name = "General Consultation"
if "prev_v_input" not in st.session_state: st.session_state.prev_v_input = ""
if "current_audio" not in st.session_state: st.session_state.current_audio = None
if "mic_key" not in st.session_state: st.session_state.mic_key = 0

# ==============================================================================
# 3. BACKEND & AI SETUP
# ==============================================================================
load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma

API_KEY = os.getenv("GEMINI_API_KEY")
DATA_FOLDER = "DATA"
DB_PATH = "./chroma_db"
BRAIN_FILE = "brain.json"

if not API_KEY:
    st.error("⚠️ Missing API Key! Check your .env or Streamlit Secrets.")
    st.stop()

@st.cache_resource
def init_ai_models():
    # FIXED: Changed from 2.5 (non-existent) to 1.5-flash
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2, google_api_key=API_KEY)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, embeddings

ai_engine, vector_embedder = init_ai_models()

# ==============================================================================
# 4. LOGIN & UI SETUP
# ==============================================================================
st.set_page_config(page_title="Advocate AI - Sindh Legal Intelligence", page_icon="⚖️", layout="wide")

def check_login(u, p):
    team = ["saim", "mustafa", "ibrahim", "huzaifa", "daniyal", "admin"]
    return u.lower() in team and p == "12345"

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.title("ADVOCATE AI")
        with st.container(border=True):
            user_in = st.text_input("Username")
            pass_in = st.text_input("Password", type="password")
            if st.button("LOG IN", use_container_width=True):
                if check_login(user_in, pass_in):
                    st.session_state.logged_in = True
                    st.session_state.username = user_in
                    st.rerun()
    st.stop()

# ==============================================================================
# 5. CHAT & AUDIO LOGIC
# ==============================================================================
# 

# Sidebar logic (Simplified for space - keep your existing view_mode logic)
with st.sidebar:
    st.header(f"⚖️ Advocate {st.session_state.username.upper()}")
    view_mode = st.radio("System Menu", ["🏢 Chambers", "📚 Legal Library"])

if view_mode == "🏢 Chambers":
    active_data = st.session_state.case_files[st.session_state.active_case_name]
    st.title(f"📂 {st.session_state.active_case_name}")

    # FIX: This check no longer fails because we initialized current_audio at the top!
    if st.session_state.current_audio:
        st.info("🔊 Listen to latest response:")
        st.audio(st.session_state.current_audio, format='audio/mp3', autoplay=True)

    # Rest of your chat history and processing logic...
    # (Ensure you use st.session_state.mic_key to reset the mic recorder after each turn)
