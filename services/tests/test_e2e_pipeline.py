import os
import subprocess
import time
import json
import threading
import pytest
from kafka import KafkaConsumer

# Adjust these to match your setup
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:29092")
RAW_TOPIC      = "TLE.raw"
PROP_TOPIC     = "TLE.prop"

# Paths to your entry-point scripts:
INGEST_CMD     = ["python3", "-u", "services/acquisition/main.py"]
PROPAGATOR_CMD = ["python3", "-u", "services/propogator/propogator.py"]

def run_subprocess(cmd, ready_marker, timeout=30):
    """
    Launches cmd as subprocess, reads stdout lines until we see ready_marker.
    Returns the subprocess.Popen object.
    """
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    deadline = time.time() + timeout
    for line in proc.stdout:
        if ready_marker in line:
            return proc
        if time.time() > deadline:
            proc.kill()
            raise RuntimeError(f"Service failed to start: did not see '{ready_marker}' in time.")
    raise RuntimeError("Unexpected EOF while waiting for service start.")

@pytest.fixture(scope="module")
def pipeline_services():
    # 1. Start ingest service
    ingest = run_subprocess(INGEST_CMD, ready_marker="Logged into Space-Track sucessfully")
    # 2. Start propagator service
    propagator = run_subprocess(PROPAGATOR_CMD, ready_marker="Propagated NORAD")
    yield
    # Teardown
    ingest.terminate()
    propagator.terminate()

def test_end_to_end(pipeline_services):
    """
    Wait for a few propagated messages, then assert properties.
    """
    consumer = KafkaConsumer(
        PROP_TOPIC,
        bootstrap_servers=[KAFKA_BOOTSTRAP],
        auto_offset_reset="earliest",
        consumer_timeout_ms=20_000,  # stop after 20s if no messages
        value_deserializer=lambda m: json.loads(m.decode("utf-8"))
    )

    received = []
    for msg in consumer:
        received.append(msg.value)
        if len(received) >= 3:  # wait for 3 messages
            break

    assert len(received) >= 1, "No propagated messages received"
    for state in received:
        # Basic sanity checks:
        assert "norad_id" in state and isinstance(state["norad_id"], int)
        assert "position_km" in state and len(state["position_km"]) == 3
        assert "velocity_km_s" in state and len(state["velocity_km_s"]) == 3
