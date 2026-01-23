import sys
import os

# 1. DATABASE FIX (MUST BE AT THE VERY TOP)
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

import streamlit as st
import time
import json
from io import BytesIO
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 2. SESSION STATE & PAGE CONFIG
# ==============================================================================
st.set_page_config(
    page_title="Advocate AI", 
    page_icon="⚖️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "cases" not in st.session_state: 
    st.session_state.cases = {"General Consultation": {"history": []}}
if "active_case" not in st.session_state: st.session_state.active_case = "General Consultation"
if "mic_key" not in st.session_state: st.session_state.mic_key = 0

# ==============================================================================
# 3. AI ENGINE SETUP
# ==============================================================================
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def init_ai():
    # Use 1.5 Flash for Hackathon speed
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash", 
        google_api_key=API_KEY, 
        max_output_tokens=8192,
        temperature=0.3
    )
    emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, emb

ai_llm, ai_emb = init_ai()

# ==============================================================================
# 4. SIDEBAR: CASE MANAGEMENT & RECORDING
# ==============================================================================
with st.sidebar:
    st.title("⚖️ Advocate AI")
    st.info("Sindh Legal Intelligence")
    
    # VOICE ASSISTANT
    st.subheader("🎤 Voice Input")
    v_input = speech_to_text(
        language='en', 
        start_prompt="Record Case Note", 
        key=f"sidebar_mic_{st.session_state.mic_key}"
    )

    st.divider()

    # CASE MANAGEMENT
    st.subheader("📁 Case Files")
    
    # 1. New Case
    with st.expander("➕ Create New Case"):
        n_name = st.text_input("Name")
        if st.button("Add Case") and n_name:
            st.session_state.cases[n_name] = {"history": []}
            st.session_state.active_case = n_name
            st.rerun()

    # 2. Select Active
    st.session_state.active_case = st.selectbox("Switch Case", list(st.session_state.cases.keys()))

    # 3. Rename
    with st.expander("📝 Rename Current"):
        r_name = st.text_input("New Title")
        if st.button("Update") and r_name:
            old = st.session_state.active_case
            st.session_state.cases[r_name] = st.session_state.cases.pop(old)
            st.session_state.active_case = r_name
            st.rerun()

# ==============================================================================
# 5. MAIN UI & INSTANT ACTIONS
# ==============================================================================
st.title(f"📂 {st.session_state.active_case}")
case_data = st.session_state.cases[st.session_state.active_case]

# INSTANT BUTTONS
c1, c2, c3 = st.columns(3)
quick_prompt = None
with c1: 
    if st.button("📝 Summarize", use_container_width=True): quick_prompt = "Summarize the case."
with c2: 
    if st.button("🔍 Infer", use_container_width=True): quick_prompt = "Analyze legal intent."
with c3: 
    if st.button("🏛️ Ruling", use_container_width=True): quick_prompt = "Give theoretical Sindh ruling."

# CHAT LOGIC
u_input = st.chat_input("Enter legal query...")
final_q = u_input or v_input or quick_prompt

# Display Chat History
for chat in case_data["history"]:
    with st.chat_message(chat["role"]): st.markdown(chat["content"])

if final_q:
    case_data["history"].append({"role": "user", "content": final_q})
    with st.chat_message("user"): st.markdown(final_q)
    
    with st.chat_message("assistant"):
        with st.status("Analyzing Sindh Law...") as status:
            try:
                # RAG / Database Search
                context = ""
                if os.path.exists("./chroma_db"):
                    db = Chroma(persist_directory="./chroma_db", embedding_function=ai_emb)
                    docs = db.similarity_search(final_q, k=2)
                    context = "\n".join([d.page_content for d in docs])
                
                # History Window (Last 5 messages)
                hist = case_data["history"][-5:]
                
                # AI Response
                prompt = f"Expert Sindh Lawyer. History: {hist}\nContext: {context}\nQuery: {final_q}"
                res = ai_llm.invoke(prompt)
                ans = res.content
                status.update(label="Complete", state="complete")
            except Exception as e:
                ans = f"⚠️ System Busy. Error: {str(e)}"
                status.update(label="Quota Reached", state="error")
        
        st.markdown(ans)
        case_data["history"].append({"role": "assistant", "content": ans})
        
        # Audio Response (gTTS)
        try:
            tts = gTTS(text=ans[:300], lang='en')
            buf = BytesIO()
            tts.write_to_fp(buf)
            st.audio(buf.getvalue(), autoplay=True)
        except: pass
        
        st.session_state.mic_key += 1
        st.rerun()
