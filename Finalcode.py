# AI Processing Loop (FIXED INDENTATION & LOGIC)
        if final_query:
            db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "user", final_query)
            with chat_container:
                with st.chat_message("user"): 
                    st.write(final_query)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing Statutes and Precedents..."):
                    try:
                        # SOVEREIGN INSTRUCTION PROMPT
                        instruction = f"""
                        SYSTEM PERSONA: {custom_persona}. 

                        CONVERSATIONAL PROTOCOL:
                        1. GREETINGS: If the user greets you (e.g., "Hi", "Hello"), respond with a professional, legal-themed greeting.
                        2. GRATITUDE: If the user says "Thank you", respond politely as a Senior Counsel.
                        3. FAREWELLS: If the user says "Goodbye" or "That is all", respond with a formal professional farewell.

                        STRICT LEGAL BOUNDARY: 
                        For any other query NOT related to Constitutional Law, Civil Law, Criminal Procedure, or Legal Strategy:
                        Strictly state: 'I am authorized only for legal consultation.'

                        RESPONSE LANGUAGE: {lang_choice}.
                        USER QUERY: {final_query}
                        """

                        # AI Inference Call
                        engine = get_analytical_engine()
                        resp = engine.invoke(instruction).content
                        
                        st.markdown(resp)
                        db_log_consultation(st.session_state.user_email, st.session_state.current_chamber, "assistant", resp)
                        
                        # Use a slight delay before rerun to ensure DB write is complete
                        time.sleep(0.5)
                        st.rerun()
                        
                    except Exception as e: 
                        st.error(f"Inference Engine Error: {e}")
