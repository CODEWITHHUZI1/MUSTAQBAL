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
# 2. SETUP & BRAIN LOADING
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "current_audio" not in st.session_state: st.session_state.current_audio = None
if "mic_key" not in st.session_state: st.session_state.mic_key = 0
if "case_files" not in st.session_state: st.session_state.case_files = {"General Consultation": {"history": []}}
if "active_case_name" not in st.session_state: st.session_state.active_case_name = "General Consultation"

# Load your brain.json
try:
    with open("brain.json", "r") as f:
        brain_responses = json.load(f)
except:
    brain_responses = {}

# Get API Key from Secrets
API_KEY = st.secrets.get("GEMINI_API_KEY")

# ==============================================================================
# 3. AI ENGINE
# ==============================================================================
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

@st.cache_resource
def init_ai():
    # Using 'latest' to ensure we don't hit a retired model error
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest", google_api_key=API_KEY)
    emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, emb

# ==============================================================================
# 4. LOGIN SCREEN (The "Gatekeeper")
# ==============================================================================
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
# 5. MAIN APP UI
# ==============================================================================
st.set_page_config(page_title="Advocate AI", layout="wide")
ai_llm, ai_emb = init_ai()

with st.sidebar:
    st.header("MENU")
    view = st.radio("Go to", ["🏢 Chambers", "📚 Library"])
    st.divider()
    # Case Switching
    cases = list(st.session_state.case_files.keys())
    sel = st.selectbox("Active Case", cases, index=cases.index(st.session_state.active_case_name))
    if sel != st.session_state.active_case_name:
        st.session_state.active_case_name = sel
        st.rerun()

# --- CHAMBERS VIEW ---
if view == "🏢 Chambers":
    active_case = st.session_state.case_files[st.session_state.active_case_name]
    st.title(f"📂 {st.session_state.active_case_name}")

    # Audio Player
    if st.session_state.current_audio:
        st.audio(st.session_state.current_audio, autoplay=True)

    # Chat History
    for m in active_case["history"]:
        with st.chat_message(m["role"]): st.markdown(m["content"])

    # Input
    v_in = speech_to_text(language='en', start_prompt="🎤 Speak", key=f"mic_{st.session_state.mic_key}")
    u_in = st.chat_input("Ask about Sindh Law...")

    user_query = u_in or v_in

    if user_query:
        active_case["history"].append({"role": "user", "content": user_query})
        with st.chat_message("user"): st.markdown(user_query)

        clean_q = user_query.lower().strip().strip("?!.")

        with st.chat_message("assistant"):
            # --- CHECK BRAIN FIRST ---
            if clean_q in brain_responses:
                with st.status("WAIT...", state="running") as status:
                    time.sleep(2) # 2 Second Gap
                    ans = brain_responses[clean_q]
                    status.update(label="Verified Answer Found", state="complete")
            
            # --- OTHERWISE USE AI ---
            else:
                with st.status("Analyzing Sindh Laws...") as status:
                    try:
                        # RAG Context
                        context = ""
                        if os.path.exists("./chroma_db"):
                            db = Chroma(persist_directory="./chroma_db", embedding_function=ai_emb)
                            docs = db.similarity_search(user_query, k=3)
                            context = "\n".join([d.page_content for d in docs])
                        
                        prompt = f"Expert Sindh Lawyer. Context: {context}\n\nUser: {user_query}"
                        res = ai_llm.invoke(prompt)
                        ans = res.content
                        status.update(label="Analysis Done", state="complete")
                    except Exception as e:
                        ans = f"⚠️ API Error: {str(e)}"
                        status.update(label="Failed", state="error")

            st.markdown(ans)
            active_case["history"].append({"role": "assistant", "content": ans})
            
            # Voice
            try:
                tts = gTTS(text=ans, lang='en')
                buf = BytesIO()
                tts.write_to_fp(buf)
                st.session_state.current_audio = buf.getvalue()
            except: pass
            
            st.session_state.mic_key += 1
            st.rerun()
