import streamlit as st

def show():
    st.title("User 360 Profile & Next Best Action")
    st.subheader("User Details")
    st.write("Display user info like demographics, recent transactions, engagement history.")
    
    st.subheader("Next Best Action (NBA)")
    st.metric("Recommended Offer", "Credit Card Upgrade")
    st.metric("Channel", "Email")
    st.metric("Confidence", "92%")
