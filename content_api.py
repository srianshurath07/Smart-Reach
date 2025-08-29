from fastapi import FastAPI

app = FastAPI()

@app.get("/content/{decision_id}")
def get_content(decision_id: str, channel: str):
    if channel == "email":
        return {
            "decision_id": decision_id,
            "variant_id": "email_v1",
            "subject": "Special Offer Just for You!",
            "body": f"Hello! Here’s your exclusive discount. DecisionID: {decision_id}"
        }
    elif channel == "push":
        return {
            "decision_id": decision_id,
            "variant_id": "push_v1",
            "title": "Limited Time Offer!",
            "message": "Get 20% OFF today only!"
        }
    else:
        return {"error": "unsupported channel"}