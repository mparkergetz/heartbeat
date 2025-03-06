import paho.mqtt.client as mqtt
import time
from datetime import datetime
import logging

HUB_IP = "192.168.2.1"  # Change to your hub Pi’s IP
TOPIC = "heartbeat"
SENSOR_NAME = "sensor_1"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        logging.info("Connected to MQTT broker")
    else:
        logging.error(f"Connection failed with error code {rc}")

def on_disconnect(client, userdata, rc, properties=None):
    logging.warning("Disconnected from MQTT broker")

client.on_connect = on_connect
client.on_disconnect = on_disconnect

try:
    client.connect(HUB_IP, 1883, 60)
    client.loop_start()  # Starts a background thread to handle MQTT communication
except Exception as e:
    logging.error(f"Failed to connect to MQTT broker: {e}")
    exit(1)

while True:
    timestamp = datetime.now()
    message = f"{SENSOR_NAME},{timestamp}"

    try:
        client.publish(TOPIC, message)
        logging.info(f"Heartbeat sent: {message}")
    except Exception as e:
        logging.error(f"Failed to send heartbeat: {e}")

    time.sleep(1)
