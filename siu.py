import sys
import streamlit as st
import os
import time
import json
from io import BytesIO
from gtts import gTTS
from streamlit_mic_recorder import speech_to_text

# 1. DATABASE FIX (REQUIRED FOR STREAMLIT CLOUD)
try:
    __import__('pysqlite3')
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# ==============================================================================
# 2. SESSION STATE (Advanced Multi-Case Management)
# ==============================================================================
if "logged_in" not in st.session_state: st.session_state.logged_in = False
if "cases" not in st.session_state: 
    st.session_state.cases = {"General Consultation": {"history": []}}
if "active_case" not in st.session_state: 
    st.session_state.active_case = "General Consultation"
if "mic_key" not in st.session_state: st.session_state.mic_key = 0

API_KEY = st.secrets.get("GEMINI_API_KEY")

@st.cache_resource
def init_ai():
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=API_KEY, max_output_tokens=8192)
    emb = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=API_KEY)
    return llm, emb

ai_llm, ai_emb = init_ai()

# ==============================================================================
# 3. SIDEBAR (Case Control Center)
# ==============================================================================
with st.sidebar:
    st.title("📂 Legal Chambers")
    
    # Create New Case
    new_case_name = st.text_input("New Case Name", placeholder="e.g. Property Dispute")
    if st.button("➕ Create Case") and new_case_name:
        if new_case_name not in st.session_state.cases:
            st.session_state.cases[new_case_name] = {"history": []}
            st.session_state.active_case = new_case_name
            st.rerun()

    st.divider()
    
    # Case Selection
    st.session_state.active_case = st.selectbox("Select Case", list(st.session_state.cases.keys()))
    
    # Rename Case
    rename_val = st.text_input("Rename Current Case")
    if st.button("📝 Rename") and rename_val:
        old_name = st.session_state.active_case
        st.session_state.cases[rename_val] = st.session_state.cases.pop(old_name)
        st.session_state.active_case = rename_val
        st.rerun()

    st.divider()
    if st.button("🗑️ Delete Case", type="secondary"):
        if len(st.session_state.cases) > 1:
            del st.session_state.cases[st.session_state.active_case]
            st.session_state.active_case = list(st.session_state.cases.keys())[0]
            st.rerun()

# ==============================================================================
# 4. MAIN INTERFACE & INSTANT ACTIONS
# ==============================================================================
st.title(f"⚖️ {st.session_state.active_case}")
case_data = st.session_state.cases[st.session_state.active_case]

# Instant Action Buttons
cols = st.columns(3)
with cols[0]:
    if st.button("📝 Summarize Case", use_container_width=True):
        prompt = "Summarize the key legal points of this conversation so far."
        # Call AI logic here (Simplified for space)
with cols[1]:
    if st.button("🔍 Infer Intent", use_container_width=True):
        prompt = "Analyze the user's messages and infer the hidden legal intent or risk."
with cols[2]:
    if st.button("⚖️ Final Ruling", use_container_width=True):
        prompt = "Based on Sindh Law, provide a theoretical final ruling for this case."

# Display Chat History
for chat in case_data["history"]:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])

# User Input
u_input = st.chat_input("Enter legal query...")
v_input = speech_to_text(language='en', key=f"mic_{st.session_state.mic_key}")

final_q = u_input or v_input

if final_q:
    case_data["history"].append({"role": "user", "content": final_q})
    with st.chat_message("user"): st.markdown(final_q)
    
    with st.chat_message("assistant"):
        with st.status("Reviewing Sindh Law...") as status:
            try:
                # Add RAG logic here
                res = ai_llm.invoke(f"Expert Sindh Lawyer. History: {case_data['history'][-5:]}\nQuery: {final_q}")
                ans = res.content
                status.update(label="Analysis Done", state="complete")
            except Exception as e:
                ans = f"⚠️ API Error: {str(e)}"
                status.update(label="Failed", state="error")
        
        st.markdown(ans)
        case_data["history"].append({"role": "assistant", "content": ans})
        st.session_state.mic_key += 1
        st.rerun()

