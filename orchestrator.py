from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import sqlite3
from datetime import datetime
import random
from fastapi import Query

app = FastAPI()




conn = sqlite3.connect("delivery.db", check_same_thread=False)
cursor = conn.cursor()

# attempts table stores sent items
cursor.execute("""CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT,
    channel TEXT,
    to_email TEXT,
    subject TEXT,
    body TEXT,
    status TEXT,
    ts TEXT
)""")

# feedback table stores user feedback events (clicked/opened/ignored/etc)
cursor.execute("""CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT,
    user_id TEXT,
    feedback TEXT,
    ts TEXT
)""")

conn.commit()


#external service endpoints

NBA_API = "http://127.0.0.1:8001/decision"
CONTENT_API = "http://127.0.0.1:8002/content"


#helpers

def send_email_simulated(to_email: str, subject: str, body: str) -> str:
    """Simulate sending an email (prints to console) and returns status string."""
    print("\n=== SIMULATED EMAIL ===")
    print(f"To: {to_email}")
    print(f"Subject: {subject}")
    print("Body:")
    print(body)
    print("======================\n")
    return "DELIVERED (simulated)"


#orchestration endpoint

@app.get("/orchestrate")
def orchestrate( user_id: str = Query(..., description="User ID for decision logic"),
    to_email: str = Query(..., description="Email address to simulate delivery")):
    """
    Triggers a decision -> content -> simulated delivery flow.
    Query params:
      - user_id
      - to_email
    """
    try:
        # 1) Get decision
        r = requests.get(NBA_API, params={"user_id": user_id}, timeout=5)
        r.raise_for_status()
        decision = r.json()

        # 2) Get content for the decision
        r2 = requests.get(f"{CONTENT_API}/{decision['decision_id']}", params={"channel": decision["channel"]}, timeout=5)
        r2.raise_for_status()
        content = r2.json()

        # 3) Simulate delivery (only for email channel here)
        status = "NOT_SENT"
        subject = ""
        body = ""
        if decision.get("channel") == "email":
            subject = content.get("subject", "")
            body = content.get("body", "")
            status = send_email_simulated(to_email, subject, body)
        else:
            # simulate other channels generically
            status = "DELIVERED (simulated - non-email)"

        # 4) Persist attempt
        cursor.execute(
            "INSERT INTO attempts (decision_id, channel, to_email, subject, body, status, ts) VALUES (?,?,?,?,?,?,?)",
            (decision.get("decision_id"), decision.get("channel"), to_email, subject, body, status, datetime.utcnow().isoformat())
        )
        conn.commit()

        return {"decision": decision, "content": content, "delivery_status": status}

    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Upstream error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

# -----------------------------
# List sent emails (for UI)
# -----------------------------
@app.get("/emails")
def get_emails(limit: int = 50, offset: int = 0):
    """
    Returns recent sent attempts (email + other channels).
    Params:
      - limit (default 50)
      - offset (default 0)
    """
    cursor.execute(
        "SELECT id, decision_id, channel, to_email, subject, body, status, ts FROM attempts ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    rows = cursor.fetchall()
    emails = []
    for r in rows:
        emails.append({
            "id": r[0],
            "decision_id": r[1],
            "channel": r[2],
            "to_email": r[3],
            "subject": r[4],
            "body": r[5],
            "status": r[6],
            "ts": r[7]
        })
    return emails

# -----------------------------
# Feedback model + endpoint
# -----------------------------
class FeedbackIn(BaseModel):
    decision_id: str
    user_id: str
    feedback: str  # e.g., "clicked", "opened", "ignored"

@app.post("/feedback")
def submit_feedback(f: FeedbackIn):
    """
    Record feedback for a decision.
    Body JSON: { "decision_id": "...", "user_id": "...", "feedback": "clicked" }
    """
    try:
        cursor.execute(
            "INSERT INTO feedback (decision_id, user_id, feedback, ts) VALUES (?,?,?,?)",
            (f.decision_id, f.user_id, f.feedback, datetime.utcnow().isoformat())
        )
        conn.commit()
        return {"message": "Feedback recorded", "decision_id": f.decision_id, "feedback": f.feedback}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simulate feedback (hackathon helper)

@app.post("/simulate_feedback")
def simulate_feedback(decision_id: str, user_id: str):
    """
    Generates a random feedback event for demo (clicked/opened/ignored).
    Query params: decision_id, user_id
    """
    choice = random.choices(["clicked", "opened", "ignored"], weights=[0.3, 0.4, 0.3], k=1)[0]
    cursor.execute(
        "INSERT INTO feedback (decision_id, user_id, feedback, ts) VALUES (?,?,?,?)",
        (decision_id, user_id, choice, datetime.utcnow().isoformat())
    )
    conn.commit()
    return {"simulated_feedback": choice, "decision_id": decision_id, "user_id": user_id}

# -----------------------------
# Metrics endpoint
# -----------------------------
@app.get("/metrics")
def get_metrics():
    """
    Returns aggregated feedback metrics:
      - counts per feedback type
      - total emails sent
      - click_through_rate (clicks / total_sent)
      - open_rate (opens / total_sent)
    """
    # counts per feedback type
    cursor.execute("SELECT feedback, COUNT(*) FROM feedback GROUP BY feedback")
    rows = cursor.fetchall()
    feedback_counts = {r[0]: r[1] for r in rows}

    # total emails sent (attempts where channel=email)
    cursor.execute("SELECT COUNT(*) FROM attempts WHERE channel = 'email'")
    total_sent = cursor.fetchone()[0] or 0

    clicks = feedback_counts.get("clicked", 0)
    opens = feedback_counts.get("opened", 0)
    ignored = feedback_counts.get("ignored", 0)

    ctr = (clicks / total_sent) if total_sent > 0 else 0.0
    open_rate = (opens / total_sent) if total_sent > 0 else 0.0

    return {
        "feedback_counts": feedback_counts,
        "total_email_sent": total_sent,
        "clicks": clicks,
        "opens": opens,
        "ignored": ignored,
        "click_through_rate": round(ctr, 4),
        "open_rate": round(open_rate, 4)
    }
@app.get("/")
def root():
    return {"message": "Orchestrator is running", "status": "ready"}

