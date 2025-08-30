# main.py
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

import pandas as pd
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Optional: OpenAI integration
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

try:
    if OPENAI_KEY:
        import openai
        openai.api_key = OPENAI_KEY
except Exception:
    openai = None

APP_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(APP_DIR, "data")
ENGAGEMENT_CSV = os.path.join(DATA_DIR, "engagement.csv")
USERS_JSON = os.path.join(DATA_DIR, "users.json")
SQLITE_DB = os.path.join(APP_DIR, "governance.db")

app = FastAPI(title="Marketing Dashboard API")

# CORS - allow your frontend during hackathon
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://smart-reach-4wxm4qpxz3buk7paivptbw.streamlit.app/",
        "http://localhost:8501"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


# ✅ Add this root route here
@app.get("/")
def root():
    return {"message": "Backend is running. Use /recommend?user_id=123"}


# ---------- Data loaders ----------
def load_engagement_df() -> pd.DataFrame:
    if not os.path.exists(ENGAGEMENT_CSV):
        return pd.DataFrame(columns=["user_id", "step", "timestamp"])
    df = pd.read_csv(ENGAGEMENT_CSV, parse_dates=["timestamp"])
    return df

def compute_engagement_payload(df: pd.DataFrame) -> Dict:
    # funnel counts
    funnel_counts = df['step'].value_counts().to_dict()
    funnel = [
        {"step": "email_open", "count": int(funnel_counts.get("email_open", 0))},
        {"step": "click", "count": int(funnel_counts.get("click", 0))},
        {"step": "purchase", "count": int(funnel_counts.get("purchase", 0))}
    ]
    # heatmap by hour-slot (simple)
    if df.empty:
        heatmap = []
    else:
        df['hour'] = df['timestamp'].dt.hour
        bins = [(0,6),(6,9),(9,12),(12,15),(15,18),(18,21),(21,24)]
        heatmap = []
        for start,end in bins:
            label = f"{start:02d}:00-{end:02d}:00"
            count = int(df[(df['hour'] >= start) & (df['hour'] < end)].shape[0])
            heatmap.append({"time_slot": label, "engagement": count})
    return {"funnel": funnel, "heatmap": heatmap}

def load_users() -> Dict:
    if not os.path.exists(USERS_JSON):
        return {}
    with open(USERS_JSON, 'r') as f:
        return json.load(f)

# ---------- SQLite for governance ----------
def init_db():
    conn = sqlite3.connect(SQLITE_DB, check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        content TEXT,
        approved_by TEXT
    )
    """)
    conn.commit()
    return conn

db_conn = init_db()

def insert_approval(content: str, approved_by: str) -> Dict:
    ts = datetime.utcnow().isoformat() + "Z"
    cur = db_conn.cursor()
    cur.execute("INSERT INTO approvals (timestamp, content, approved_by) VALUES (?, ?, ?)", (ts, content, approved_by))
    db_conn.commit()
    return {"timestamp": ts, "content": content, "approved_by": approved_by}

def read_approvals(limit: int = 100) -> List[Dict]:
    cur = db_conn.cursor()
    cur.execute("SELECT timestamp, content, approved_by FROM approvals ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    return [{"timestamp": r[0], "content": r[1], "approved_by": r[2]} for r in rows]

# ---------- request models ----------
class ContentRequest(BaseModel):
    prompt: str

class ApprovalRequest(BaseModel):
    content: str
    approved_by: str

# ---------- endpoints ----------
@app.get("/api/engagement")
def get_engagement():
    df = load_engagement_df()
    payload = compute_engagement_payload(df)
    return payload

@app.get("/api/user/{user_id}")
def get_user(user_id: int):
    users = load_users()
    user = users.get(str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Simple NBA logic
    score = user.get("engagement_score", 0)
    if score >= 80:
        rec = "Upgrade to Platinum Card"
    elif score >= 50:
        rec = "Offer Cashback Promotion"
    else:
        rec = "Offer 10% Discount"
    explanation = [
        {"factor": "Engagement Score", "weight": min(80, score)},
        {"factor": "Purchase History", "weight": 30},
        {"factor": "Loyalty Tier", "weight": 20}
    ]
    return {"user": {"id": user_id, **user}, "nba": {"recommendation": rec, "explanation": explanation}}

@app.post("/api/generate-content")
def generate_content(request: ContentRequest):
    prompt = request.prompt
    # If OPENAI_KEY present, call OpenAI; otherwise return mock variations
    if OPENAI_KEY and openai:
        system = {"role":"system", "content":"You are a marketing copywriter that generates short subject lines."}
        user_msg = {"role":"user", "content": f"Generate 3 concise email subject lines for: {prompt}. Return as newline separated lines."}
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[system, user_msg],
                temperature=0.7,
                max_tokens=150
            )
            text = resp.choices[0].message['content']
            # split into non-empty lines
            variations = [line.strip() for line in text.splitlines() if line.strip()]
            if not variations:
                variations = [text.strip()]
        except Exception as e:
            # fallback to mock on failure
            variations = [
                f"{prompt} — Exclusive Offer",
                f"Limited Time: {prompt}",
                f"Don’t Miss Out on {prompt}"
            ]
    else:
        # mock variants
        variations = [
            f"{prompt} — Exclusive Offer",
            f"Limited Time: {prompt}",
            f"Don’t Miss Out on {prompt}"
        ]
    return {"variations": variations}

@app.post("/api/log-approval")
def log_approval(req: ApprovalRequest):
    entry = insert_approval(req.content, req.approved_by)
    return {"status": "success", **entry}

@app.get("/api/governance")
def get_governance(limit: Optional[int] = 100):
    logs = read_approvals(limit)
    return {"logs": logs}

# Reload endpoints for development convenience
@app.post("/api/reload-data")
def reload_data():
    # intentionally simple: checks files exist
    exist_eng = os.path.exists(ENGAGEMENT_CSV)
    exist_users = os.path.exists(USERS_JSON)
    return {"engagement_csv": exist_eng, "users_json": exist_users}

