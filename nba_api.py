from fastapi import FastAPI
import sqlite3
import random

app = FastAPI()


conn = sqlite3.connect("delivery.db", check_same_thread=False)
cursor = conn.cursor()

@app.get("/decision")
def get_decision(user_id: str):
    """
    returns a decision for the given user_id.
    uses feedback history to bias future decisions.
    """

    #check past feedback for this user
    cursor.execute(
        "SELECT feedback FROM feedback WHERE user_id=? ORDER BY id DESC LIMIT 5",
        (user_id,)
    )
    rows = cursor.fetchall()
    feedbacks = [r[0] for r in rows]

   
    if "clicked" in feedbacks:
        channel = "email"   #user responds well to emails
    elif "ignored" in feedbacks:
        channel = "push"    #user ignores email, try push
    else:
        channel = random.choice(["email", "push"])

 
    decision = {
        "user_id": user_id,
        "decision_id": f"dec-{random.randint(1000,9999)}",
        "offer": "20% OFF on your next purchase!",
        "channel": channel
    }

    return decision


