import streamlit as st
import os
import shutil
import time
import glob
import pandas as pd
import json
from io import BytesIO
from gtts import gTTS
from dotenv import load_dotenv
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. BACKEND INITIALIZATION & SECRETS
# ==============================================================================

# Load environment variables from .env file
load_dotenv()

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
# ------------------------------------------------------------------------------
# SYSTEM CONSTANTS
# ------------------------------------------------------------------------------
API_KEY = os.getenv("GEMINI_API_KEY")
DATA_FOLDER = "DATA"
DB_PATH = "./chroma_db"
BRAIN_FILE = "brain.json"

# Load brain responses
try:
    with open(BRAIN_FILE, 'r') as f:
        brain_responses = json.load(f)
except FileNotFoundError:
    brain_responses = {}
    st.warning("brain.json not found. Instant responses disabled.")

# Safety Check: Stop the app if the key is missing from .env
if not API_KEY:
    st.error("⚠️ Missing API Key! Please ensure your .env file contains GEMINI_API_KEY.")
    st.stop()

# ==============================================================================
# 2. CORE MODELS & VOICE ENGINE
# ==============================================================================

@st.cache_resource
def init_ai_models():
    # Using Gemini 1.5 Flash (stable) or 2.0 Flash
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2, google_api_key=API_KEY)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, embeddings

ai_engine, vector_embedder = init_ai_models()

def speak_text(text):
    """Generates MP3 audio from text and plays it automatically."""
    try:
        sound_file = BytesIO()
        tts = gTTS(text=text, lang='en')
        tts.write_to_fp(sound_file)
        st.audio(sound_file, format='audio/mp3', autoplay=True)
    except Exception as e:
        st.error(f"Audio Error: {e}")

# ==============================================================================
# 3. UI STYLING & AUTH
# ==============================================================================

st.set_page_config(page_title="Advocate AI - Sindh Legal Intelligence", page_icon="⚖️", layout="wide")

st.markdown("""
    <style>
    .stChatMessage { border-radius: 15px; padding: 20px; margin-bottom: 15px; box-shadow: 0px 4px 6px rgba(0,0,0,0.05); }
    .stChatMessage.user { background-color: #f1f3f4; border-right: 8px solid #0056b3; }
    .stChatMessage.assistant { background-color: #ffffff; border-left: 8px solid #2e7d32; border: 1px solid #eee; }
    </style>
""", unsafe_allow_html=True)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "username" not in st.session_state: st.session_state.username = None
if "case_files" not in st.session_state: st.session_state.case_files = {"General Consultation": {"history": []}}
if "active_case_name" not in st.session_state: st.session_state.active_case_name = "General Consultation"
if "prev_v_input" not in st.session_state: st.session_state.prev_v_input = ""

def check_login(u, p):
    team = ["saim", "mustafa", "ibrahim", "huzaifa", "daniyal", "admin"]
    return u.lower() in team and p == "12345"

# ==============================================================================
# 4. DATA LOGIC (RAG)
# ==============================================================================

def sync_knowledge_base():
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        return None, "System Error: 'DATA' folder not found."
    
    pdfs = glob.glob(f"{DATA_FOLDER}/*.pdf")
    if not pdfs: return None, "Warning: No PDFs found in DATA folder."
    
    if os.path.exists(DB_PATH):
        return Chroma(persist_directory=DB_PATH, embedding_function=vector_embedder), "Legal archives connected."
    else:
        chunks = []
        for p in pdfs:
            loader = PyPDFLoader(p)
            splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=300)
            chunks.extend(loader.load_and_split(splitter))
        db = Chroma.from_documents(documents=chunks, embedding=vector_embedder, persist_directory=DB_PATH)
        return db, f"Success: Indexed {len(chunks)} sections."

# ==============================================================================
# 5. LOGIN SCREEN
# ==============================================================================

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
                else:
                    st.error("Invalid Credentials")
    st.stop()

if "law_db" not in st.session_state:
    db_obj, msg = sync_knowledge_base()
    st.session_state.law_db = db_obj
    st.toast(msg)

# ==============================================================================
# 6. SIDEBAR
# ==============================================================================

with st.sidebar:
    st.header(f"⚖️ Advocate {st.session_state.username.upper()}")
    view_mode = st.radio("System Menu", ["🏢 Chambers", "📚 Legal Library", "ℹ️ About Project"])

    st.divider()
    st.subheader("📁 Case Management")

    all_case_names = list(st.session_state.case_files.keys())
    try:
        current_idx = all_case_names.index(st.session_state.active_case_name)
    except ValueError:
        current_idx = 0

    current_sel = st.selectbox("Select Active Case", all_case_names, index=current_idx)

    if current_sel != st.session_state.active_case_name:
        st.session_state.active_case_name = current_sel
        st.rerun()

    with st.expander("➕ New Consultation"):
        new_case_input = st.text_input("Case Name", key="new_case_input")
        if st.button("Create Case", use_container_width=True):
            if new_case_input and new_case_input not in st.session_state.case_files:
                st.session_state.case_files[new_case_input] = {"history": []}
                st.session_state.active_case_name = new_case_input
                st.rerun()

    st.divider()
    if st.button("🚪 Log Out", type="primary", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()
# ==============================================================================
# 7. VIEW: CHAMBERS (UPDATED WITH WRITING STATUS & 2-SEC DELAY)
# ==============================================================================

if view_mode == "🏢 Chambers":
    active_data = st.session_state.case_files[st.session_state.active_case_name]
    st.title(f"📂 {st.session_state.active_case_name}")

    # --- 1. SYSTEM INSTRUCTIONS ---
    legal_instructions = """
    You are 'Advocate AI', a senior legal consultant for Sindh Laws.
    If the user asks a legal question, you MUST start your response with:
    'Here is my judgement in IRAC format'

    Then, follow this template with bold headings:
    ### **ISSUE**
    ### **RULE**
    ### **ANALYSIS**
    ### **CONCLUSION**

    Note: This is an AI legal analysis. Consult a High Court Advocate for official filings.
    """

    # --- 2. AUDIO PERSISTENCE ---
    if st.session_state.current_audio:
        st.info("🔊 Listen to latest response:")
        st.audio(st.session_state.current_audio, format='audio/mp3', autoplay=True)

    # --- 3. CHAT HISTORY ---
    for m in active_data["history"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    # --- 4. INPUTS ---
    v_input = speech_to_text(
        language='en', 
        start_prompt="🎤 Click & Speak", 
        key=f"mic_{st.session_state.mic_key}"
    )
    u_prompt = st.chat_input("Continue the conversation...")

    current_input = None
    if u_prompt:
        current_input = u_prompt
    elif v_input and v_input != st.session_state.get('prev_v_input', ''):
        current_input = v_input
        st.session_state.prev_v_input = v_input

    # --- 5. LOGIC PROCESSING ---
    if current_input:
        active_data["history"].append({"role": "user", "content": current_input})
        with st.chat_message("user"):
            st.markdown(current_input)

        input_lower = current_input.lower().strip().strip('?.!')
        
        # --- DECISION POINT: BRAIN VS AI ---
        if input_lower in brain_responses:
            # INSTANT RESPONSE LOGIC (With 2s delay and 'WRITING' status)
            with st.chat_message("assistant"):
                with st.status("WRITING...") as status:
                    time.sleep(1) # The 2-second gap you requested
                    full_text = brain_responses[input_lower]
                    status.update(label="Response Ready", state="complete")
                st.markdown(full_text)
        else:
            # DEEP LEGAL ANALYSIS (AI Engine)
            with st.chat_message("assistant"):
                with st.status("Analyzing Laws...") as status:
                    # RAG Retrieval
                    retrieved_context = ""
                    if st.session_state.law_db:
                        hits = st.session_state.law_db.as_retriever(search_kwargs={"k": 5}).invoke(current_input)
                        retrieved_context = "\n\n".join([h.page_content for h in hits])

                    # Build History & Prompt
                    hist_text = "\n".join([f"{m['role']}: {m['content']}" for m in active_data["history"][-5:]])
                    sys_prompt = f"{legal_instructions}\n\nCONTEXT: {retrieved_context}\n\nHISTORY: {hist_text}\n\nQUERY: {current_input}"

                    response = ai_engine.invoke(sys_prompt)
                    full_text = response.content
                    st.markdown(full_text)
                    status.update(label="Judgement Complete", state="complete")

        # --- 6. SHARED POST-PROCESSING (Audio & History) ---
        active_data["history"].append({"role": "assistant", "content": full_text})
        try:
            sound_file = BytesIO()
            tts = gTTS(text=full_text, lang='en')
            tts.write_to_fp(sound_file)
            st.session_state.current_audio = sound_file.getvalue()
        except Exception:
            st.session_state.current_audio = None
        
        # Increment mic_key and rerun to play audio/clear mic
        st.session_state.mic_key += 1
        st.rerun()