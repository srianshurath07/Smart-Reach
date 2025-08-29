import streamlit as st

# --- PAGE CONFIG ---
st.set_page_config(page_title="SmartReach Dashboard", layout="wide")

# --- CUSTOM CSS ---
st.markdown(
    """
    <style>
    /* Header styling */
    .css-18ni7ap.e8zbici2 {
        background-color: #000000;
        padding: 1rem;
    }
    .css-18ni7ap .stButton button {
        color: black;
    }
    /* Remove top padding */
    .css-1d391kg {
        padding-top: 1rem;
    }
    /* Card styling */
    .card {
        background-color: #f0f0f5;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .metric-label {
        font-weight: bold;
        font-size: 16px;
    }
    .metric-value {
        font-size: 24px;
        margin-top: 0.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- HEADER ---
st.markdown(
    """
    <div style="display:flex; justify-content: space-between; align-items:center;">
        <h2 style="color:white;">SMART<span style='color:#7F5AF0;'>REACH</span></h2>
        <div>
            <button style='margin-right:10px;'>Dashboard</button>
            <button style='margin-right:10px;'>Campaigns</button>
            <button style='margin-right:10px;'>Audiences</button>
            <button style='margin-right:10px;'>Reports</button>
        </div>
        <div>
            <button>Profile</button>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("## KEY METRICS")

# --- DUMMY DATA (replace with your backend logic) ---
metrics = [ 
    {"label": "Total Campaigns", "value": "12", "desc": "Active"}, 
    {"label": "Total Spend", "value": "$5400", "desc": "This Month"}, 
    {"label": "Total Revenue", "value": "$12000", "desc": "This Month"}, 
    {"label": "ROI", "value": "50%", "desc": "This Month"}, 
    {"label": "Total Campaigns", "value": "12", "desc": "Active"},
]
<div>
        <div style='color:black?
</div>
# --- LAYOUT METRICS CARDS ---
cols = st.columns(3)

for i, metric in enumerate(metrics):
    col = cols[i % 3]
    with col:
        st.markdown(
            f"""
            <div class="card">
                <div class="metric-label">{metric['label']}</div>
                <div class="metric-value">{metric['value']}</div>
                <div style="font-size:12px; color:gray;">{metric['desc']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

# --- ADDITIONAL SPACING ---
st.markdown("<br><br>", unsafe_allow_html=True)
