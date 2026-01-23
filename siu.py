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
# 2. SESSION STATE INITIALIZATION
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
    # Use gemini-1.5-flash (STABLE)
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.2, google_api_key=API_KEY)
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, embeddings

ai_engine, vector_embedder = init_ai_models()

# ==============================================================================
# 4. LOGIN SYSTEM
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
    st.stop()

# ==============================================================================
# 5. MAIN UI CONFIG
# ==============================================================================
st.set_page_config(page_title="Advocate AI", page_icon="⚖️", layout="wide")

# ==============================================================================
# 6. SIDEBAR: CASE MANAGEMENT
# ==============================================================================
with st.sidebar:
    st.header(f"⚖️ Advocate {st.session_state.username.upper()}")
    view_mode = st.radio("System Menu", ["🏢 Chambers", "📚 Legal Library", "ℹ️ About Project"])
    
    st.divider()
    st.subheader("📁 Case Management")
    
    all_cases = list(st.session_state.case_files.keys())
    selected_case = st.selectbox("Select Active Case", all_cases, 
                                 index=all_cases.index(st.session_state.active_case_name))
    
    if selected_case != st.session_state.active_case_name:
        st.session_state.active_case_name = selected_case
        st.rerun()

    with st.expander("➕ New Consultation"):
        new_case_name = st.text_input("Case Name")
        if st.button("Create"):
            if new_case_name and new_case_name not in st.session_state.case_files:
                st.session_state.case_files[new_case_name] = {"history": []}
                st.session_state.active_case_name = new_case_name
                st.rerun()

    st.divider()
    if st.button("🚪 Log Out", type="primary", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ==============================================================================
# 7. RAG SYNC
# ==============================================================================
def sync_kb():
    if not os.path.exists("DATA"): os.makedirs("DATA")
    if os.path.exists("./chroma_db"):
        return Chroma(persist_directory="./chroma_db", embedding_function=vector_embedder)
    return None

if "law_db" not in st.session_state:
    st.session_state.law_db = sync_kb()

# ==============================================================================
# 8. VIEW: CHAMBERS
# ==============================================================================
if view_mode == "🏢 Chambers":
    active_data = st.session_state.case_files[st.session_state.active_case_name]
    st.title(f"📂 {st.session_state.active_case_name}")

    # QUICK ACTIONS
    col1, col2, col3 = st.columns(3)
    quick_query = None
    with col1:
        if st.button("📝 Summarize Case"): quick_query = "Provide a concise summary of our discussion."
    with col2:
        if st.button("⚖️ Give Ruling"): quick_query = "Provide a ruling in IRAC format for this case based on Sindh Laws."
    with col3:
        if st.button("🔍 Legal Research"): quick_query = "Search archives for relevant precedents."

    if st.session_state.current_audio:
        st.audio(st.session_state.current_audio, format='audio/mp3', autoplay=True)

    for m in active_data["history"]:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])

    v_input = speech_to_text(language='en', start_prompt="🎤 Click to Speak", key=f"mic_{st.session_state.mic_key}")
    u_prompt = st.chat_input("Ask a legal question...")

    current_input = quick_query or u_prompt or (v_input if v_input != st.session_state.prev_v_input else None)

    if current_input:
        st.session_state.prev_v_input = v_input if v_input else ""
        active_data["history"].append({"role": "user", "content": current_input})
        
        with st.chat_message("assistant"):
            with st.status("Reviewing Sindh Statutes...") as status:
                try:
                    context = ""
                    if st.session_state.law_db:
                        hits = st.session_state.law_db.similarity_search(current_input, k=3)
                        context = "\n".join([h.page_content for h in hits])
                    
                    full_prompt = f"You are Advocate AI, an expert in Sindh Law. Use IRAC format if asked for a ruling.\n\nCONTEXT:\n{context}\n\nQUERY: {current_input}"
                    
                    # Call the AI engine
                    response = ai_engine.invoke(full_prompt)
                    full_text = response.content
                    
                    st.markdown(full_text)
                    
                    # TTS
                    tts = gTTS(text=full_text, lang='en')
                    s_file = BytesIO()
                    tts.write_to_fp(s_file)
                    st.session_state.current_audio = s_file.getvalue()
                    status.update(label="Judgement Ready", state="complete")

                except Exception as e:
                    status.update(label="API Error", state="error")
                    st.error(f"Chat Error: {str(e)}")
                    full_text = "I apologize, but I encountered an error while processing that request."
        
        active_data["history"].append({"role": "assistant", "content": full_text})
        st.session_state.mic_key += 1
        st.rerun()

elif view_mode == "ℹ️ About Project":
    st.title("ℹ️ About Advocate AI")
    st.info("Advocate AI analyzes the Laws of Sindh, Pakistan using RAG technology.")

elif view_mode == "📚 Legal Library":
    st.title("📚 Legal Library")
    pdfs = glob.glob("DATA/*.pdf")
    if pdfs:
        for p in pdfs: st.text(f"📄 {os.path.basename(p)}")
    else:
        st.warning("No documents found in 'DATA' folder.")
