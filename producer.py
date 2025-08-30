from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',
    retries=5
)

def send_to_kafka(event):
    producer.send("mkt.web.clickstream.v1", value=event)
    producer.flush()