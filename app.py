import streamlit as st
import requests


st.set_page_config(page_title="Marketing Dashboard", layout="wide")

# Sidebar for navigation
page = st.sidebar.radio("Navigation", ["Dashboard", "Profile", "Content", "Governance"])


# --- DASHBOARD PAGE ---
if page == "Dashboard":
    # Your existing dashboard code here (metrics, cards, etc.)
    st.markdown("## KEY METRICS")

    metrics = [
        {"label": "Total Campaigns", "value": "12", "desc": "Active"},
        {"label": "Total Spend", "value": "$5400", "desc": "This Month"},
        {"label": "Total Revenue", "value": "$12000", "desc": "This Month"},
        {"label": "ROI", "value": "50%", "desc": "This Month"},
    ]

    cols = st.columns(3)
    for i, metric in enumerate(metrics):
        col = cols[i % 3]
        with col:
            st.markdown(
                f"""
                <div class="card">
                    <div class="metric-label">{metric['label']}</div>
                    <div class="metric-value">{metric['value']}</div>
                    <div style="font-size:12px; color:black;">{metric['desc']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

# --- PROFILE PAGE ---
elif page == "Profile":
    st.title("User Profile & Recommendations")

    user_id = st.text_input("Enter User ID:")
    if st.button("Get Recommendations"):
        if user_id:
            try:
                response = requests.get(
                    "https://smart-reach-6.onrender.com/recommend?user_id=123",  # Replace with your actual FastAPI URL
                    params={"user_id": 123}
                )
                if response.status_code == 200:
                    data = response.json()
                    st.subheader("Recommended Action")
                    st.success(data.get("action", "No recommendation available"))
                else:
                    st.error(f"API Error: {response.status_code}")
            except Exception as e:
                st.error(f"Request failed: {e}")
        else:
            st.warning("Please enter a User ID")

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
        color: white;
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
        font-color: #000000
    }
    .metric-value {
        font-size: 24px;
        margin-top: 0.5rem;
        font-color: #000000
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
