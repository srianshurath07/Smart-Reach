from flask import Flask, request, jsonify
from jsonschema import validate
import json
from datetime import datetime, timezone
from producer import send_to_kafka

app = Flask(__name__)

with open("schema.json") as f:
    schema = json.load(f)

@app.route("/", methods=["POST"])
def ingest():
    event = request.get_json()
    event["ingested_at"] = datetime.now(timezone.utc).isoformat()
    try:
        validate(instance=event, schema=schema)
        send_to_kafka(event)
        return jsonify({"status": "Event validated and sent to Kafka"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(port=5000)