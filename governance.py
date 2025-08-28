import streamlit as st
import pandas as pd

def show():
    st.title("Governance & Compliance Logs")
    
    data = {
        'Timestamp': ['2025-08-28 10:00', '2025-08-28 12:30'],
        'Action': ['Content Approved', 'NBA Delivered'],
        'User': ['Admin', 'System'],
        'Compliance Check': ['Passed', 'Passed']
    }
    
    df = pd.DataFrame(data)
    st.dataframe(df)
