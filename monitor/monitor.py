import paho.mqtt.client as mqtt
from datetime import datetime, timedelta
import time
import threading
import sys
import logging

HUB_IP = "192.168.2.1"
TOPIC = "sensor/heartbeat"

TIMEOUT_THRESHOLD = 600  
TIME_DRIFT_THRESHOLD = 600 

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s", stream=sys.stdout)
logging.info("Heartbeat monitor started")
logging.debug("Debugging mode active")

sensor_status = {}
sensor_history = {}

def on_message(client, userdata, msg):
    message = msg.payload.decode()
    sensor_name, timestamp_str = message.split(',')
    sensor_time = datetime.fromisoformat(timestamp_str)
    if sensor_name in sensor_history:
        sensor_history[sensor_name].append(sensor_time)
        if len(sensor_history[sensor_name]) > 2:
            sensor_history[sensor_name].pop(0)
    else:
        sensor_history[sensor_name] = [sensor_time]
    sensor_status[sensor_name] = sensor_time
    #print(f"Received heartbeat from {sensor_name} at {sensor_time}")
    logging.info(f"{sensor_name} heartbeat: {sensor_time}")
    hub_time = datetime.now()
    if abs((hub_time - sensor_time).total_seconds()) > TIME_DRIFT_THRESHOLD:
        #print(f"⚠ WARNING: {sensor_name} clock is out of sync! Time difference: {abs((hub_time - sensor_time).total_seconds())} seconds")
        logging.warning(f"⚠ WARNING: {sensor_name} clock is out of sync! Time difference: {abs((hub_time - sensor_time).total_seconds())} seconds")

def check_sensor_status():
    while True:
        for sensor, timestamps in list(sensor_history.items()):
            if len(timestamps) < 2:
                continue
            delta = (timestamps[-1] - timestamps[-2]).total_seconds()
            if delta > TIMEOUT_THRESHOLD:
                #print(f"⚠ WARNING: {sensor} is DOWN! Gap between heartbeats: {delta} seconds")
                logging.warning(f"⚠ WARNING: {sensor} is DOWN! Gap between heartbeats: {delta} seconds")
        time.sleep(10)

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(HUB_IP, 1883, 60)
client.subscribe(TOPIC)

from threading import Thread
Thread(target=check_sensor_status, daemon=True).start()

client.loop_forever()
