import time 
import os
import json
import requests 
from sgp4.api import Satrec, WGS72
from sgp4.api import jday
from typing import Iterable, Dict, List
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from .database import SessionLocal 
from .models import Objects,StateVector,TleSet
from datetime import timezone,datetime

SPACE_TRACK_USERNAME = os.getenv("SPACE_TRACK_USERNAME")
SPACE_TRACK_PASSWORD = os.getenv("SPACE_TRACK_PASSWORD")
if not SPACE_TRACK_USERNAME or not SPACE_TRACK_PASSWORD:
    raise RuntimeError ("SPACE_TRACK_USERNAME and SPACE_TRACK_PASSWORD must be set as environment variables.")



SPACE_TRACK_LOGIN_URL = "https://www.space-track.org/ajaxauth/login"

SPACE_TRACK_URL = (
    "https://www.space-track.org/basicspacedata/query/"
    "class/gp/"
    "decay_date/null-val/"
    "epoch/%3Enow-30/"
    "orderby/norad_cat_id/"
    "format/json"
)

FETCH_INTERVAL = 240 * 60   #4 hours wait on data fetch

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
    
def createStateVectors(sats):
    stateVectorOutput = []
    for entry in sats:
        try:
            norad_id = entry.get("NORAD_CAT_ID")
            l1 = entry.get("TLE_LINE1") 
            l2 = entry.get("TLE_LINE2") 
            target = datetime.now(timezone.utc)
            
            try:
                state_vector = propogate_tle(norad_id,l1,l2,target)
                flat = {
                    "norad_id": state_vector["norad_id"],
                    "timestamp": state_vector["timestamp"],
            
                    "x": state_vector["position_vector"][0],
                    "y": state_vector["position_vector"][1],
                    "z": state_vector["position_vector"][2],
                    "vx": state_vector["velocity_vector"][0],
                    "vy": state_vector["velocity_vector"][1],
                    "vz": state_vector["velocity_vector"][2],
                }
                stateVectorOutput.append(flat)
            except:
                print("")
        except:
              print("")
    return stateVectorOutput

def insertToDatabase(state_vectors,sats):
    db = SessionLocal()
    try: 
        for state_vector,sat in zip(state_vectors,sats):
            try:
                norad_id = int(sat["NORAD_CAT_ID"])
            except Exception:
                print("Skipping message without norad_id:", sat)
                continue
            try:
                obj = db.get(Objects, norad_id)
                if not obj:
                    obj = Objects(
                        norad_id=norad_id,
                        name=sat.get("OBJECT_NAME"),
                        cospar_id=sat.get("OBJECT_ID"),
                        object_type=sat.get("OBJECT_TYPE"),
                        country_code=sat.get("COUNTRY_CODE"),
                        launch_date=(sat.get("LAUNCH_DATE")),
                        decay_date=(sat.get("DECAY_DATE")),
                        rcs_size=sat.get("RCS_SIZE"),
                    )
                    db.add(obj)
                
            
                tle = TleSet(
                    norad_id=norad_id,
                    epoch=sat.get("EPOCH"),
                    line1=sat.get("TLE_LINE1"),
                    line2=sat.get("TLE_LINE2"),
                    bstar=sat.get("BSTAR"),
                    element_set_no=sat.get("ELEMENT_SET_NO"),
                    mean_motion=sat.get("MEAN_MOTION"),
                    eccentricity=sat.get("ECCENTRICITY"),
                    inclination=sat.get("INCLINATION"),
                    ra_of_asc_node=sat.get("RA_OF_ASC_NODE"),
                    arg_of_pericenter=sat.get("ARG_OF_PERICENTER"),
                    mean_anomaly=sat.get("MEAN_ANOMALY"),
                    mm_dot=sat.get("MEAN_MOTION_DOT"),
                    mm_ddot=sat.get("MEAN_MOTION_DDOT"),
                    classification_type=sat.get("CLASSIFICATION_TYPE"),
                    ephemeris_type=sat.get("EPHEMERIS_TYPE"),
                    rev_at_epoch=sat.get("REV_AT_EPOCH"),
                )
                db.add(tle)
            
                
                    
                sv = StateVector(
                    norad_id = state_vector['norad_id'],
                    timestamp = datetime.fromisoformat(state_vector["timestamp"]),
                    x = state_vector['x'],
                    y = state_vector['y'],
                    z = state_vector['z'],
                    vx = state_vector['vx'],
                    vy = state_vector['vy'],
                    vz = state_vector['vz'],
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



def handler(event,context):
    try:
        session = create_spacetrack_session()
        print(f"Logged into Space-Track sucessfully")
    except Exception as e:
        print(f"Space Track Login Failed, {e}")
        return {"ok": False, "error": "login_failed", "detail": str(e)}
  
    try:
        tle_list = fetch_TLE(session)
        print(f"Fetched {len(tle_list)} raw TLE entries")
    except Exception as e:
        print("Error fetching/publishing TLEs:", e)
        if isinstance(e, requests.HTTPError) and e.response.status_code == 401:
            try:
                session = create_spacetrack_session()
                print("Re-authenticated to Space-Track.")
                return {"ok": False, "error": "refetch_failed"}
            except Exception as login_err:
                print("Re-login to Space-Track failed:", login_err)
                return {"ok": False, "error": "fetch_failed", "detail": str(e)}

    stateVectorList = createStateVectors(tle_list)
    insertToDatabase(state_vectors=stateVectorList,sats=tle_list)
     
    return {
        "ok": True,
        "tle_count": len(tle_list),
        "state_vectors_generated": len(stateVectorList),
    }



if __name__ == "__main__":
     handler({}, None)