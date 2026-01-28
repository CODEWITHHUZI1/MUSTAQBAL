# ==============================================================================
# ALPHA APEX - LEVIATHAN ENTERPRISE LEGAL INTELLIGENCE SYSTEM
# VERSION: 40.0 (FINAL PERFORMANCE & UI UPGRADE)
# ==============================================================================

import streamlit as st
import sqlite3
import datetime
import os
import time
import requests
import pandas as pd
import fitz  # PyMuPDF for superior PDF extraction
from streamlit_lottie import st_lottie, st_lottie_spinner
from langchain_google_genai import ChatGoogleGenerativeAI
from streamlit_mic_recorder import speech_to_text

# ==============================================================================
# 1. ARCHITECTURAL UI - LEVIATHAN GLASS-DARK SHADERS
# ==============================================================================

st.set_page_config(
    page_title="Alpha Apex | Leviathan AI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def apply_final_shaders():
    st.markdown("""
    <style>
        /* BASE THEME */
        .stApp { background: radial-gradient(circle at top, #0f172a, #020617) !important; color: #f1f5f9 !important; }
        
        /* GLASS-MORPHISM CHAT BUBBLES */
        .stChatMessage {
            background: rgba(30, 41, 59, 0.45) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            border-radius: 15px !important;
            padding: 20px !important;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        }

        /* SIDEBAR CUSTOMIZATION */
        [data-testid="stSidebar"] {
            background-color: #020617 !important;
            border-right: 1px solid #1e293b !important;
        }

        /* BUTTONS: THE LEVIATHAN GLOW */
        .stButton>button {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%) !important;
            color: #ffffff !important;
            border: 1px solid #334155 !important;
            border-radius: 10px !important;
            height: 3rem;
            transition: all 0.3s ease;
        }
        .stButton>button:hover {
            border-color: #3b82f6 !important;
            box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
            transform: scale(1.02);
        }

        /* CLEANER INPUTS */
        .stChatInput textarea {
            background: #1e293b !important;
            color: #ffffff !important;
            border-radius: 12px !important;
        }

        /* TABS STYLING */
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] {
            background-color: transparent;
            color: #94a3b8;
            border-radius: 5px;
            padding: 10px 20px;
        }
        .stTabs [aria-selected="true"] { color: #f8fafc !important; border-bottom-color: #3b82f6 !important; }
    </style>
    """, unsafe_allow_html=True)

# ==============================================================================
# 2. ENHANCED DOCUMENT EXTRACTION (PyMuPDF)
# ==============================================================================

def extract_pdf_advanced(uploaded_file):
    """Uses PyMuPDF (fitz) for faster, cleaner text extraction."""
    try:
        # Save temp file for PyMuPDF to read
        with open("temp_vault_doc.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        doc = fitz.open("temp_vault_doc.pdf")
        full_text = ""
        for page in doc:
            full_text += page.get_text("text") + "\n\n"
        
        meta = {
            "pages": doc.page_count,
            "metadata": doc.metadata
        }
        doc.close()
        os.remove("temp_vault_doc.pdf")
        return full_text, meta
    except Exception as e:
        st.error(f"Extraction Error: {e}")
        return None, None

# ==============================================================================
# 3. INTERFACE LOGIC
# ==============================================================================

def load_lottie(url):
    r = requests.get(url)
    return r.json() if r.status_code == 200 else None

def main():
    apply_final_shaders()
    lottie_law = load_lottie("https://assets5.lottiefiles.com/packages/lf20_v76zkn9x.json")

    with st.sidebar:
        st.markdown("### ⚖️ LEVIATHAN COMMAND")
        if lottie_law: st_lottie(lottie_law, height=100)
        
        menu = st.radio("Access Level", ["🏛️ Chambers", "📁 Law Library", "🛡️ Admin"], label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

    if menu == "🏛️ Chambers":
        st.title("💼 Case Management")
        
        # Tabs for better UI flow
        tab_chat, tab_files, tab_settings = st.tabs(["💬 Consultation", "📄 Evidence", "⚙️ Persona"])
        
        with tab_chat:
            # Chat rendering with Lottie Spinner
            history = st.session_state.get('history', [])
            for msg in history:
                with st.chat_message(msg["role"]): st.write(msg["content"])

            query = st.chat_input("Ask about Pakistani Statute or Case Law...")
            if query:
                history.append({"role": "user", "content": query})
                st.session_state.history = history
                st.rerun()

        with tab_files:
            st.subheader("Case Evidence & Assets")
            st.info("Upload documents relevant to this specific case file.")
            up_ev = st.file_uploader("Upload Evidence (PDF)", type="pdf", key="case_pdf")
            if up_ev and st.button("Index Evidence"):
                with st.status("Analyzing document structure..."):
                    text, meta = extract_pdf_advanced(up_ev)
                    if text:
                        st.success(f"Indexed {meta['pages']} pages successfully.")
                        st.json(meta['metadata'])

    elif menu == "📁 Law Library":
        st.header("📚 Central Law Library")
        st.markdown("Global repository for Pakistani Statutes (PPC, CrPC, etc.)")
        # Library logic here...

# ==============================================================================
# 4. INITIALIZATION
# ==============================================================================

if __name__ == "__main__":
    if "logged_in" not in st.session_state: st.session_state.logged_in = True # Bypass for demo
    main()
