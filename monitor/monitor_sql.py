##########
#
# Stores sensor state in dictionary, may want to move to flag files for other scripts to access
#
##########


import paho.mqtt.client as mqtt
import sqlite3
from datetime import datetime, timedelta
import time
from threading import Thread
import sys
import logging

DEBUG_MODE = False

HUB_IP = "192.168.2.1"
TOPIC = "sensor/heartbeat"

TIMEOUT_THRESHOLD = 60
TIME_DRIFT_THRESHOLD = 600 

log_level = logging.DEBUG if DEBUG_MODE else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)
logging.info("Heartbeat monitor started")

DB_PATH = "/home/pi/heartbeat_monitor/heartbeats.db"

sensor_warnings = {}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS heartbeats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sensor_name TEXT NOT NULL,
            receipt_time TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sensor_status (
            sensor_name TEXT PRIMARY KEY,
            last_seen TEXT NOT NULL,
            sync_status TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

def log_heartbeat(sensor_name, receipt_time, sync_status):
    """Log the heartbeat receipt time and update the sensor status."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO heartbeats (sensor_name, receipt_time)
        VALUES (?, ?)
    """, (sensor_name, receipt_time))

    cursor.execute("""
        INSERT INTO sensor_status (sensor_name, last_seen, sync_status)
        VALUES (?, ?, ?)
        ON CONFLICT(sensor_name) DO UPDATE SET 
            last_seen = excluded.last_seen,
            sync_status = excluded.sync_status
    """, (sensor_name, receipt_time, sync_status))
    
    conn.commit()
    conn.close()

    if sensor_name in sensor_warnings and sync_status == "good":
        logging.info(f"✅ {sensor_name} has recovered.")
        sensor_warnings.pop(sensor_name, None)

def on_message(client, userdata, msg):
    """Handles incoming MQTT messages."""
    message = msg.payload.decode()
    sensor_name, timestamp_str = message.split(',')
    sensor_time = datetime.fromisoformat(timestamp_str)
    receipt_time = datetime.now()

    drift = abs((receipt_time - sensor_time).total_seconds())
    sync_status = "good" if drift <= TIME_DRIFT_THRESHOLD else "out of sync"

    if sync_status == "out of sync" and sensor_warnings.get(sensor_name) != "out_of_sync":
        logging.warning(f"⚠ WARNING: {sensor_name} clock is out of sync by {drift} seconds")
        sensor_warnings[sensor_name] = "out_of_sync"

    log_heartbeat(sensor_name, receipt_time.isoformat(), sync_status)

def check_sensor_status():
    while True:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT sensor_name, last_seen, sync_status FROM sensor_status")
        sensors = cursor.fetchall()
        conn.close()

        hub_time = datetime.now()

        for sensor_name, last_seen_str, sync_status in sensors:
            last_seen = datetime.fromisoformat(last_seen_str)
            gap = (hub_time - last_seen).total_seconds()

            if gap > TIMEOUT_THRESHOLD and sync_status == "good" and sensor_warnings.get(sensor_name) != "down":
                logging.warning(f"⚠ WARNING: {sensor_name} is DOWN! Last heartbeat received at {last_seen}.")
                sensor_warnings[sensor_name] = "down"

            elif gap <= TIMEOUT_THRESHOLD and sensor_warnings.get(sensor_name) == "down":
                logging.info(f"✅ {sensor_name} has recovered from being down.")
                sensor_warnings.pop(sensor_name, None)

        time.sleep(10)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(HUB_IP, 1883, 60)
client.subscribe(TOPIC)

Thread(target=check_sensor_status, daemon=True).start()

client.loop_forever()
