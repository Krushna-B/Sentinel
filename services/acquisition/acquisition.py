import time 
import os
import json
import requests 
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

SPACE_TRACK_USERNAME = os.getenv("SPACE_TRACK_USERNAME")
SPACE_TRACK_PASSWORD = os.getenv("SPACE_TRACK_PASSWORD")
if not SPACE_TRACK_USERNAME or not SPACE_TRACK_PASSWORD:
    raise RuntimeError ("SPACE_TRACK_USERNAME and SPACE_TRACK_PASSWORD must be set as environment variables.")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "localhost:9092")
TOPIC = "TLE.raw"

SPACE_TRACK_LOGIN_URL = "https://www.space-track.org/ajaxauth/login"

SPACE_TRACK_URL = (
    "https://www.space-track.org/basicspacedata/query/"
    "class/gp/"
    "decay_date/null-val/"
    "epoch/%3Enow-30/"
    "orderby/norad_cat_id/"
    "format/json"
)

FETCH_INTERVAL = 60 * 60   #10 minute wait on data fetch

def create_spacetrack_session():
    session = requests.Session()
    payload = { "identity": SPACE_TRACK_USERNAME,
                "password": SPACE_TRACK_PASSWORD,
    }
    resp = session.post(SPACE_TRACK_LOGIN_URL,data=payload,timeout=10)
    if resp.status_code != 200 or "Login Failed" in resp.text:
        raise RuntimeError("Space-Track login failed")
    return session

def fetch_TLE(session):
    resp = session.get(SPACE_TRACK_URL, timeout=15)
    resp.raise_for_status()
    tle_list = resp.json()
    return tle_list

def post_to_kafka(producer, tle_list):
    count = 0
    for entry in tle_list:
        norad = entry.get("NORAD_CAT_ID")
        object_name = entry.get("OBJECT_NAME")
        object_id = entry.get("OBJECT_ID")
        object_type = entry.get("OBJECT_TYPE")
        country_code = entry.get("COUNTRY_CODE")
        launch_date = entry.get("LAUNCH_DATE")
        classification_type = entry.get("CLASSIFICATION_TYPE")
        line1 = entry.get("TLE_LINE1") 
        line2 = entry.get("TLE_LINE2") 
        epoch = entry.get("EPOCH")

        mean_motion       = entry.get("MEAN_MOTION")
        eccentricity      = entry.get("ECCENTRICITY")
        inclination       = entry.get("INCLINATION")
        ra_of_asc_node    = entry.get("RA_OF_ASC_NODE")
        arg_of_pericenter = entry.get("ARG_OF_PERICENTER")
        mean_anomaly      = entry.get("MEAN_ANOMALY")
        mm_dot            = entry.get("MEAN_MOTION_DOT")
        mm_ddot           = entry.get("MEAN_MOTION_DDOT")
        ephemeris_type    = entry.get("EPHEMERIS_TYPE")
        rev_at_epoch      = entry.get("REV_AT_EPOCH")

        if not (norad and line1 and line2 and epoch):
            continue
        
        payload = {
            "norad_id" : norad,
            "line1" : line1,
            "line2" : line2,
            "epoch" : epoch,
            "object_name": object_name,
            "object_id": object_id,
            "object_type": object_type,
            "country_code": country_code,
            "launch_date": launch_date,
            "classification_type": classification_type,

            "mean_motion": mean_motion,
            "eccentricity": eccentricity,
            "inclination": inclination,
            "ra_of_asc_node": ra_of_asc_node,
            "arg_of_pericenter": arg_of_pericenter,
            "mean_anomaly": mean_anomaly,
            "mm_dot": mm_dot,
            "mm_ddot": mm_ddot,
            "ephemeris_type": ephemeris_type,
            "rev_at_epoch": rev_at_epoch
        }
        
        producer.send(TOPIC,json.dumps(payload).encode("utf-8"))
        count +=1
    producer.flush()
    return count

def create_producer():
    for i in range(10):  # try for ~10 seconds
        try:
            return KafkaProducer(bootstrap_servers=[KAFKA_BROKER],
                                 linger_ms = 10,
                                retries = 5,
                                request_timeout_ms = 20000
                                )
        except NoBrokersAvailable:
            time.sleep(1)
    raise RuntimeError("Kafka broker not available after multiple retries")

def main():
    producer = create_producer()
    try:
        session = create_spacetrack_session()
        print(f"Logged into Space-Track sucessfully")
    except Exception as e:
        print(f"Space Track Login Failed, {e}")

    while True:
        try:
            tle_list = fetch_TLE(session)
            print(f"🔍 Fetched {len(tle_list)} raw TLE entries")
            num_published = post_to_kafka(producer,tle_list)
            print(f"Published {num_published} TLEs to Kafka topic {TOPIC}")
        except Exception as e:
            print("Error fetching/publishing TLEs:", e)
            if isinstance(e, requests.HTTPError) and e.response.status_code == 401:
                try:
                    session = create_spacetrack_session()
                    print("Re-authenticated to Space-Track.")
                except Exception as login_err:
                    print("Re-login to Space-Track failed:", login_err)


        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main()