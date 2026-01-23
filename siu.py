import sys
# 1. DATABASE FIX
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import os
import time
import json
from io import BytesIO
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 2. SETUP & SECRETS
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "case_files" not in st.session_state: st.session_state.case_files = {"General Consultation": {"history": []}}
if "active_case_name" not in st.session_state: st.session_state.active_case_name = "General Consultation"
if "current_audio" not in st.session_state: st.session_state.current_audio = None
if "mic_key" not in st.session_state: st.session_state.mic_key = 0

API_KEY = st.secrets.get("GEMINI_API_KEY")

# ==============================================================================
# 3. AI ENGINE (Optimized for 1.5 Flash)
# ==============================================================================
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

@st.cache_resource
def init_ai():
    # max_output_tokens=8192 is the physical limit of the model
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=API_KEY,
        temperature=0.3,
        max_output_tokens=8192, 
        max_retries=3
    )
    emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, emb

# Load brain.json
try:
    with open("brain.json", "r") as f:
        brain_responses = json.load(f)
except:
    brain_responses = {}

# ==============================================================================
# 4. UI CONFIG & LOGIN
# ==============================================================================
st.set_page_config(page_title="Advocate AI", layout="wide", page_icon="⚖️")

if not st.session_state.logged_in:
    st.title("⚖️ ADVOCATE AI - LOGIN")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("LOG IN"):
        if u.lower() in ["admin", "saim", "mustafa"] and p == "12345":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# ==============================================================================
# 5. MAIN APPLICATION
# ==============================================================================
ai_llm, ai_emb = init_ai()

with st.sidebar:
    st.header("🏢 CHAMBERS")
    view = st.radio("Menu", ["Chambers", "Library"])
    st.divider()
    cases = list(st.session_state.case_files.keys())
    sel = st.selectbox("Active Case", cases)
    st.session_state.active_case_name = sel

if view == "Chambers":
    active_case = st.session_state.case_files[st.session_state.active_case_name]
    st.title(f"📂 {st.session_state.active_case_name}")

    # Audio Player
    if st.session_state.current_audio:
        st.audio(st.session_state.current_audio, autoplay=True)

    # Scannable Chat History
    for m in active_case["history"]:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Voice & Text Inputs
    v_in = speech_to_text(language='en', start_prompt="🎤 Speak", key=f"mic_{st.session_state.mic_key}")
    u_in = st.chat_input("Ask about Sindh Law...")

    query = u_in or v_in

    if query:
        active_case["history"].append({"role": "user", "content": query})
        with st.chat_message("user"): st.markdown(query)

        clean_q = query.lower().strip().strip("?!.")

        with st.chat_message("assistant"):
            # --- BRAIN MATCH ---
            if clean_q in brain_responses:
                with st.status("WAIT...", state="running") as status:
                    time.sleep(2) # Your 2-second gap
                    ans = brain_responses[clean_q]
                    status.update(label="Verified Found", state="complete")
            
            # --- AI RAG ENGINE ---
            else:
                with st.status("Analyzing Archives...") as status:
                    try:
                        # RAG Search
                        context = ""
                        if os.path.exists("./chroma_db"):
                            db = Chroma(persist_directory="./chroma_db", embedding_function=ai_emb)
                            docs = db.similarity_search(query, k=3)
                            context = "\n".join([d.page_content for d in docs])
                        
                        # Memory Cleanup: Only send last 5 exchanges to save tokens
                        history_snippet = active_case["history"][-5:]
                        
                        full_prompt = f"Expert Sindh Lawyer. History: {history_snippet}\nContext: {context}\nQuery: {query}"
                        res = ai_llm.invoke(full_prompt)
                        ans = res.content
                        status.update(label="Analysis Done", state="complete")
                    except Exception as e:
                        ans = f"⚖️ Legal Library Busy. Using general logic: {str(e)}"
                        status.update(label="Quota Note", state="error")

            st.markdown(ans)
            active_case["history"].append({"role": "assistant", "content": ans})
            
            # Text to Speech
            try:
                tts = gTTS(text=ans[:300], lang='en') # Limit TTS to first 300 chars to avoid lag
                buf = BytesIO()
                tts.write_to_fp(buf)
                st.session_state.current_audio = buf.getvalue()
            except: pass
            
            st.session_state.mic_key += 1
            st.rerun()
