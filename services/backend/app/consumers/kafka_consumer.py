from kafka import KafkaConsumer, errors
import json
import threading
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from ..models import StateVector
from ..database import SessionLocal
import os
import time

KAFKA_TOPIC  = os.getenv("KAFKA_TOPIC",  "state_vectors")
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:9092")

def create_consumer():
    return KafkaConsumer(
        KAFKA_TOPIC,
        bootstrap_servers = [KAFKA_BROKER],
        value_deserializer = lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset = "earliest",
        enable_auto_commit = True,
        group_id = "state_vectors_consumers"
    )

def consume():
    while True:
        try:
            consumer = create_consumer()
            print("✅ Kafka connected")
            break
        except errors.NoBrokersAvailable:
            print("Kafka not ready, retrying in 5 s …")
            time.sleep(5)

    db = SessionLocal()

    required = {"timestamp", "x", "y", "z", "vx", "vy", "vz"}

    for msg in consumer:
        data = msg.value
        # print("💬 got msg:", data)
        
        
                  
        sv = StateVector(
            norad_id = data['norad_id'],
            timestamp = datetime.fromisoformat(data["timestamp"]),
            x = data['x'],
            y = data['y'],
            z = data['z'],
            vx = data['vx'],
            vy = data['vy'],
            vz = data['vz'],
        )
        try:
            db.add(sv)
            db.commit()
            print(f"✔︎ inserted state-vector id={sv.id}")
        except SQLAlchemyError as e:
            db.rollback()
            print(f"{e}")
        finally:
             db.close()

   
def start_consumer():
    thread = threading.Thread(target=consume, daemon=True)
    thread.start()