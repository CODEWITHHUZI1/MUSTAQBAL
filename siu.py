import sys
# 1. DATABASE FIX (Must be at the top)
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
# 2. SESSION STATE
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "case_files" not in st.session_state: st.session_state.case_files = {"General": {"history": []}}
if "current_audio" not in st.session_state: st.session_state.current_audio = None
if "mic_key" not in st.session_state: st.session_state.mic_key = 0

# ==============================================================================
# 3. THE "HACKATHON" AI SETUP
# ==============================================================================
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def init_ai():
    # SETTING MAX OUTPUT TOKENS TO 8192 (Max for Flash)
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=API_KEY,
        max_output_tokens=8192,
        temperature=0.3
    )
    # EMBEDDING model - This is usually where the '429' error happens
    emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, emb

# Load brain.json (Keep it simple)
try:
    with open("brain.json", "r") as f: brain_responses = json.load(f)
except: brain_responses = {}

# ==============================================================================
# 4. APP UI
# ==============================================================================
st.set_page_config(page_title="Advocate AI", layout="wide")
ai_llm, ai_emb = init_ai()

if not st.session_state.logged_in:
    st.title("⚖️ ADVOCATE AI - LOGIN")
    u = st.text_input("User")
    p = st.text_input("Pass", type="password")
    if st.button("LOG IN"):
        if u.lower() in ["admin", "saim", "mustafa"] and p == "12345":
            st.session_state.logged_in = True
            st.rerun()
    st.stop()

# SIDEBAR
with st.sidebar:
    st.header("🏢 Chambers")
    if st.button("🚪 Logout"): st.session_state.logged_in = False; st.rerun()

# MAIN CHAT
st.title("📂 Case File")
if st.session_state.current_audio:
    st.audio(st.session_state.current_audio, autoplay=True)

# Process Input
query = st.chat_input("Ask Sindh Law...")
v_query = speech_to_text(language='en', start_prompt="🎤 Speak", key=f"m_{st.session_state.mic_key}")
final_q = query or v_query

if final_q:
    with st.chat_message("user"): st.markdown(final_q)
    
    clean_q = final_q.lower().strip().strip("?!.")
    
    with st.chat_message("assistant"):
        # --- 1. BRAIN MATCH (The 2-Second "WAIT") ---
        if clean_q in brain_responses:
            with st.status("WAIT...", state="running") as s:
                time.sleep(2)
                ans = brain_responses[clean_q]
                s.update(label="Verified Found", state="complete")
        
        # --- 2. AI ENGINE WITH EMERGENCY FALLBACK ---
        else:
            with st.status("Analyzing Laws...") as s:
                try:
                    # Try Library search first
                    context = ""
                    if os.path.exists("./chroma_db"):
                        db = Chroma(persist_directory="./chroma_db", embedding_function=ai_emb)
                        docs = db.similarity_search(final_q, k=2)
                        context = "\n".join([d.page_content for d in docs])
                    
                    res = ai_llm.invoke(f"Expert Sindh Lawyer. Context: {context}\n\nQuery: {final_q}")
                    ans = res.content
                    s.update(label="Analysis Done", state="complete")
                
                except Exception as e:
                    # FALLBACK: If embedding quota is dead, just use pure AI knowledge
                    s.update(label="Offline Mode: Using AI Knowledge", state="running")
                    try:
                        res = ai_llm.invoke(f"Expert Sindh Lawyer. Answer this: {final_q}")
                        ans = res.content
                        s.update(label="Complete", state="complete")
                    except:
                        ans = "⚠️ API Limit reached. Please wait 60 seconds."
        
        st.markdown(ans)
        # TTS logic
        try:
            tts = gTTS(text=ans[:300], lang='en')
            b = BytesIO(); tts.write_to_fp(b)
            st.session_state.current_audio = b.getvalue()
        except: pass
        
        st.session_state.mic_key += 1
        st.rerun()
