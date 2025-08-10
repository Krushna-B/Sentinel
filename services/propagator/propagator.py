import os 
import json 
from datetime import datetime, timezone
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable
from sgp4.api import Satrec, WGS72
from sgp4.api import jday
import time
from kafka.vendor import six
import sys

# if sys.version_info >= (3, 12, 0):
#     sys.modules['kafka.vendor.six.moves'] = six.moves

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
RAW_TOPIC = "TLE.raw"
PROP_TOPIC = "state_vectors"

def wait_for_kafka(timeout=60, interval=5):
    """Block until Kafka is accepting connections, or raise after timeout (sec)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            p = KafkaProducer(bootstrap_servers=[KAFKA_BROKER])
            if p.bootstrap_connected():
                p.close()
                return
        except NoBrokersAvailable:
            pass
        print(f"[{datetime.now(timezone.utc).isoformat()}] Kafka not ready, retrying in {interval}s…")
        time.sleep(interval)
    raise RuntimeError("Timeout waiting for Kafka broker")

def create_producer():
    return KafkaProducer(
        bootstrap_servers=KAFKA_BROKER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def create_consumer():
    return KafkaConsumer(
        RAW_TOPIC,
        bootstrap_servers=[KAFKA_BROKER],
        group_id="propagator-group",
        auto_offset_reset="earliest",
        value_deserializer=lambda m: json.loads(m.decode('utf-8'))
    )


def propogate_tle(norad_id, line1, line2, target_time):
    sat = Satrec.twoline2rv(line1, line2, whichconst = WGS72)
    jd, fr = jday(target_time.year,target_time.month, target_time.day,
                  target_time.hour, target_time.minute,target_time.second + target_time.microsecond * 1e-6)
    
    e,r,v,= sat.sgp4(jd,fr)

    if e != 0:
        raise RuntimeError(f"SGP4 error code {e} for NORAD {norad_id}")
    else:
        return {
            "norad_id": norad_id,
            "timestamp": target_time.isoformat(),
            "position_vector": list(r),      # [ x ,y ,z ]
            "velocity_vector": list(v),
        }

def main():
    print("Waiting for Kafka broker to come up…")
    wait_for_kafka()

    consumer = create_consumer()
    consumer.subscribe(["TLE.raw"])

    producer = create_producer()

    print("PROPAGATOR SERVICE STARTED")
    
    try:
        for msg in consumer:
            tle = msg.value
            norad_id = tle["norad_id"]
            l1, l2 = tle["line1"], tle["line2"]
            target = datetime.now(timezone.utc)

            try:
                state_vector = propogate_tle(norad_id,l1,l2,target)
                flat = {
                    "norad_id": state_vector["norad_id"],
                    "timestamp": state_vector["timestamp"],
                    "object_name": tle.get["object_name"],
                    "object_id": tle.get["object_id"],
                    "object_type": tle.get["object_type"],
                    "country_code": tle.get["country_code"],
                    "launch_date": tle.get["launch_date"],
                    "classification_type": tle.get["classification_type"],

                    "x": state_vector["position_vector"][0],
                    "y": state_vector["position_vector"][1],
                    "z": state_vector["position_vector"][2],
                    "vx": state_vector["velocity_vector"][0],
                    "vy": state_vector["velocity_vector"][1],
                    "vz": state_vector["velocity_vector"][2],

                     "mean_motion":        tle.get("mean_motion"),
                    "eccentricity":       tle.get("eccentricity"),
                    "inclination":        tle.get("inclination"),
                    "ra_of_asc_node":     tle.get("ra_of_asc_node"),
                    "arg_of_pericenter":  tle.get("arg_of_pericenter"),
                    "mean_anomaly":       tle.get("mean_anomaly"),
                    "mm_dot":             tle.get("mm_dot"),
                    "mm_ddot":            tle.get("mm_ddot"),
                    "ephemeris_type":     tle.get("ephemeris_type"),
                    "rev_at_epoch":       tle.get("rev_at_epoch"),
                }
                producer.send(PROP_TOPIC, flat)
                producer.flush()
                print(f"Propagated NORAD {norad_id} at {state_vector['timestamp']} with Position {state_vector['position_vector']} ")
            except Exception as e:
                print(f"Error in propogating NORAD {norad_id}: {e}")

    except KeyboardInterrupt:
        print("Shutting down propagator…")
    finally:
        consumer.close()

if __name__ == "__main__":
    main()
