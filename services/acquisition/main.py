import time 
import os
import json
import requests 
from kafka import KafkaProducer


SPACE_TRACK_USERNAME = os.getenv("SPACE_TRACK_USERNAME")
SPACE_TRACK_PASSWORD = os.getenv("SPACE_TRACK_PASSWORD")
if not SPACE_TRACK_USERNAME or not SPACE_TRACK_PASSWORD:
    raise RuntimeError ("SPACE_TRACK_USERNAME and SPACE_TRACK_PASSWORD must be set as environment variables.")

KAFKA_BROKER = "localhost:29092"
TOPIC = "TLE.raw"

SPACE_TRACK_LOGIN_URL = "https://www.space-track.org/ajaxauth/login"
SPACE_TRACK_URL = "https://www.space-track.org/basicspacedata/query/class/gp/decay_date/null-val/epoch/>now-30/orderby/norad_cat_id/limit/10/format/json"

FETCH_INTERVAL = 30 * 60   #30 minute wait on data fetch

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
        line1 = entry.get("TLE_LINE1") 
        line2 = entry.get("TLE_LINE2") 
        epoch = entry.get("EPOCH")

        if not (norad and line1 and line2 and epoch):
            continue
        
        payload = {
            "norad_id" : norad,
            "line1" : line1,
            "line2" : line2,
            "epoch" : epoch
        }
        producer.send(TOPIC,json.dumps(payload).encode("utf-8"))
        count +=1
    producer.flush()
    return count


def main():
    prodcuer = KafkaProducer(bootstrap_servers = [KAFKA_BROKER],
                             linger_ms = 10,
                             retries = 5,
                             request_timeout_ms = 20000
                             )


    try:
        session = create_spacetrack_session()
        print(f"Logged into Space-Track sucessfully")
    except Exception as e:
        print(f"Space Track Login Failed, {e}")

    while True:
        try:
            tle_list = fetch_TLE(session)
            print(f"🔍 Fetched {len(tle_list)} raw TLE entries")
            num_published = post_to_kafka(prodcuer,tle_list)
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