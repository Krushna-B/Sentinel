from kafka import KafkaConsumer, errors
import json
import threading
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime
from ..models import StateVector,Objects,TleSet
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

    
    try: 
        for msg in consumer:
            data = msg.value
        
            try:
                norad_id = int(data["norad_id"])
            except Exception:
                print("Skipping message without norad_id:", data)
                continue
            try:
                obj = db.get(Objects, norad_id)
                if not obj:
                    obj = Objects(
                        norad_id=norad_id,
                        name=data.get("object_name"),
                        cospar_id=data.get("object_id"),
                        object_type=data.get("object_type"),
                        country_code=data.get("country_code"),
                        launch_date=(data.get("launch_date")),
                        decay_date=(data.get("decay_date")),
                        rcs_size=data.get("rcs_size"),
                    )
                    db.add(obj)
                
            
                tle = TleSet(
                    norad_id=norad_id,
                    epoch=data.get("epoch"),
                    line1=data.get("line1"),
                    line2=data.get("line2"),
                    bstar=data.get("bstar"),
                    element_set_no=data.get("element_set_no"),
                    mean_motion=data.get("mean_motion"),
                    eccentricity=data.get("eccentricity"),
                    inclination=data.get("inclination"),
                    ra_of_asc_node=data.get("ra_of_asc_node"),
                    arg_of_pericenter=data.get("arg_of_pericenter"),
                    mean_anomaly=data.get("mean_anomaly"),
                    mm_dot=data.get("mm_dot"),
                    mm_ddot=data.get("mm_ddot"),
                    classification_type=data.get("classification_type"),
                    ephemeris_type=data.get("ephemeris_type"),
                    rev_at_epoch=data.get("rev_at_epoch"),
                )
                db.add(tle)
            
                
                    
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
      
                db.add(sv)
                db.commit()
                print(f"✔︎ inserted state-vector id={sv.id}")
            except IntegrityError as e:
                db.rollback()
                # likely duplicate on (norad_id,timestamp) or (norad_id,epoch)
                print("IntegrityError; skipping:", repr(e))
            
            except SQLAlchemyError as e:
                db.rollback()
                print("SQLAlchemyError; skipping:", repr(e))
            except Exception as e:
                db.rollback()
                print("Unhandled error; skipping:", repr(e))
    
    finally:
        db.close()

   
def start_consumer():
    thread = threading.Thread(target=consume, daemon=True)
    thread.start()