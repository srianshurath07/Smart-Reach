import streamlit as st

def show():
    st.title("Content Workbench")
    
    st.subheader("Generate Content Variations")
    prompt = st.text_area("Enter your prompt", "Generate a personalized email for credit card upgrade.")
    
    if st.button("Generate"):
        st.write("Generated Variation 1: Personalized Email Copy")
        st.write("Generated Variation 2: Push Notification Copy")
        st.write("Generated Variation 3: Social Media Caption")
    
    st.subheader("Approve Content")
    st.checkbox("Variation 1 Approved")
    st.checkbox("Variation 2 Approved")
    st.checkbox("Variation 3 Approved")
