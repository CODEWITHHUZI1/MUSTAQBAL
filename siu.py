import sys
import streamlit as st
import os
import time
import json
from io import BytesIO
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder, speech_to_text

# 1. DATABASE COMPATIBILITY FIX
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# ==============================================================================
# 2. INITIALIZATION & SESSION STATE
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "cases" not in st.session_state: 
    st.session_state.cases = {"General Consultation": {"history": []}}
if "active_case" not in st.session_state: st.session_state.active_case = "General Consultation"
if "mic_key" not in st.session_state: st.session_state.mic_key = 0

API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def init_ai():
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=API_KEY, max_output_tokens=8192)
    emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, emb

ai_llm, ai_emb = init_ai()

# ==============================================================================
# 3. SIDEBAR: CASE MANAGEMENT & RECORDING
# ==============================================================================
with st.sidebar:
    st.title("📂 Legal Chambers")
    
    # --- VOICE RECORDING ---
    st.subheader("🎤 Voice Assistant")
    v_input = speech_to_text(language='en', start_prompt="Start Recording", key=f"sidebar_mic_{st.session_state.mic_key}")
    if v_input:
        st.success("Voice Captured!")

    st.divider()

    # --- CASE CONTROLS ---
    st.subheader("📁 Case Management")
    
    # 1. Create New Case
    with st.expander("➕ New Case"):
        new_name = st.text_input("Case Name", key="create_input")
        if st.button("Create"):
            if new_name and new_name not in st.session_state.cases:
                st.session_state.cases[new_name] = {"history": []}
                st.session_state.active_case = new_name
                st.rerun()

    # 2. Select Case
    st.session_state.active_case = st.selectbox("Select Case", list(st.session_state.cases.keys()))

    # 3. Rename Case
    with st.expander("📝 Rename Current Case"):
        rename_val = st.text_input("New Name")
        if st.button("Confirm Rename"):
            old = st.session_state.active_case
            st.session_state.cases[rename_val] = st.session_state.cases.pop(old)
            st.session_state.active_case = rename_val
            st.rerun()

    # 4. Delete Case
    if st.button("🗑️ Delete Current Case", type="secondary"):
        if len(st.session_state.cases) > 1:
            del st.session_state.cases[st.session_state.active_case]
            st.session_state.active_case = list(st.session_state.cases.keys())[0]
            st.rerun()

# ==============================================================================
# 4. MAIN INTERFACE
# ==============================================================================
st.title(f"⚖️ {st.session_state.active_case}")
case_data = st.session_state.cases[st.session_state.active_case]

# --- INSTANT ACTIONS BAR ---
cols = st.columns(3)
action_prompt = None

with cols[0]:
    if st.button("📝 Summarize", use_container_width=True):
        action_prompt = "Summarize the key facts of this legal case clearly."
with cols[1]:
    if st.button("🔍 Infer Intent", use_container_width=True):
        action_prompt = "Analyze the intent and potential legal risks in this discussion."
with cols[2]:
    if st.button("🏛️ Legal Ruling", use_container_width=True):
        action_prompt = "Based on Sindh Law, provide a theoretical ruling or conclusion."

# --- CHAT PROCESSING ---
u_input = st.chat_input("Ask a question about Sindh Law...")
final_q = u_input or v_input or action_prompt

# Display History
for chat in case_data["history"]:
    with st.chat_message(chat["role"]): st.markdown(chat["content"])

if final_q:
    case_data["history"].append({"role": "user", "content": final_q})
    with st.chat_message("user"): st.markdown(final_q)
    
    with st.chat_message("assistant"):
        with st.status("Analyzing Archives...") as status:
            try:
                # Context Logic (RAG)
                context = ""
                if os.path.exists("./chroma_db"):
                    db = Chroma(persist_directory="./chroma_db", embedding_function=ai_emb)
                    docs = db.similarity_search(final_q, k=2)
                    context = "\n".join([d.page_content for d in docs])
                
                # Model Invoke
                full_prompt = f"Expert Sindh Lawyer. Context: {context}\nChat History: {case_data['history'][-5:]}\nQuery: {final_q}"
                res = ai_llm.invoke(full_prompt)
                ans = res.content
                status.update(label="Analysis Done", state="complete")
            except Exception as e:
                ans = f"⚖️ Error: {str(e)}"
                status.update(label="API Limit Hit", state="error")
        
        st.markdown(ans)
        case_data["history"].append({"role": "assistant", "content": ans})
        st.session_state.mic_key += 1
        st.rerun()import sys
import streamlit as st
import os
import time
import json
from io import BytesIO
from gtts import gTTS
from streamlit_mic_recorder import mic_recorder, speech_to_text

# 1. DATABASE COMPATIBILITY FIX
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# ==============================================================================
# 2. INITIALIZATION & SESSION STATE
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "cases" not in st.session_state: 
    st.session_state.cases = {"General Consultation": {"history": []}}
if "active_case" not in st.session_state: st.session_state.active_case = "General Consultation"
if "mic_key" not in st.session_state: st.session_state.mic_key = 0

API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def init_ai():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY, max_output_tokens=8192)
    emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, emb

ai_llm, ai_emb = init_ai()

# ==============================================================================
# 3. SIDEBAR: CASE MANAGEMENT & RECORDING
# ==============================================================================
with st.sidebar:
    st.title("📂 Legal Chambers")
    
    # --- VOICE RECORDING ---
    st.subheader("🎤 Voice Assistant")
    v_input = speech_to_text(language='en', start_prompt="Start Recording", key=f"sidebar_mic_{st.session_state.mic_key}")
    if v_input:
        st.success("Voice Captured!")

    st.divider()

    # --- CASE CONTROLS ---
    st.subheader("📁 Case Management")
    
    # 1. Create New Case
    with st.expander("➕ New Case"):
        new_name = st.text_input("Case Name", key="create_input")
        if st.button("Create"):
            if new_name and new_name not in st.session_state.cases:
                st.session_state.cases[new_name] = {"history": []}
                st.session_state.active_case = new_name
                st.rerun()

    # 2. Select Case
    st.session_state.active_case = st.selectbox("Select Case", list(st.session_state.cases.keys()))

    # 3. Rename Case
    with st.expander("📝 Rename Current Case"):
        rename_val = st.text_input("New Name")
        if st.button("Confirm Rename"):
            old = st.session_state.active_case
            st.session_state.cases[rename_val] = st.session_state.cases.pop(old)
            st.session_state.active_case = rename_val
            st.rerun()

    # 4. Delete Case
    if st.button("🗑️ Delete Current Case", type="secondary"):
        if len(st.session_state.cases) > 1:
            del st.session_state.cases[st.session_state.active_case]
            st.session_state.active_case = list(st.session_state.cases.keys())[0]
            st.rerun()

# ==============================================================================
# 4. MAIN INTERFACE
# ==============================================================================
st.title(f"⚖️ {st.session_state.active_case}")
case_data = st.session_state.cases[st.session_state.active_case]

# --- INSTANT ACTIONS BAR ---
cols = st.columns(3)
action_prompt = None

with cols[0]:
    if st.button("📝 Summarize", use_container_width=True):
        action_prompt = "Summarize the key facts of this legal case clearly."
with cols[1]:
    if st.button("🔍 Infer Intent", use_container_width=True):
        action_prompt = "Analyze the intent and potential legal risks in this discussion."
with cols[2]:
    if st.button("🏛️ Legal Ruling", use_container_width=True):
        action_prompt = "Based on Sindh Law, provide a theoretical ruling or conclusion."

# --- CHAT PROCESSING ---
u_input = st.chat_input("Ask a question about Sindh Law...")
final_q = u_input or v_input or action_prompt

# Display History
for chat in case_data["history"]:
    with st.chat_message(chat["role"]): st.markdown(chat["content"])

if final_q:
    case_data["history"].append({"role": "user", "content": final_q})
    with st.chat_message("user"): st.markdown(final_q)
    
    with st.chat_message("assistant"):
        with st.status("Analyzing Archives...") as status:
            try:
                # Context Logic (RAG)
                context = ""
                if os.path.exists("./chroma_db"):
                    db = Chroma(persist_directory="./chroma_db", embedding_function=ai_emb)
                    docs = db.similarity_search(final_q, k=2)
                    context = "\n".join([d.page_content for d in docs])
                
                # Model Invoke
                full_prompt = f"Expert Sindh Lawyer. Context: {context}\nChat History: {case_data['history'][-5:]}\nQuery: {final_q}"
                res = ai_llm.invoke(full_prompt)
                ans = res.content
                status.update(label="Analysis Done", state="complete")
            except Exception as e:
                ans = f"⚖️ Error: {str(e)}"
                status.update(label="API Limit Hit", state="error")
        
        st.markdown(ans)
        case_data["history"].append({"role": "assistant", "content": ans})
        st.session_state.mic_key += 1
        st.rerun()
