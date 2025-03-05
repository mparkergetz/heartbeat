import paho.mqtt.client as mqtt
import time
from datetime import datetime
import logging

HUB_IP = "192.168.2.1"  # Change to your hub Pi’s IP
TOPIC = "sensor/heartbeat"
SENSOR_NAME = "sensor_1"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

while True:
    timestamp = datetime.now()
    message = f"{SENSOR_NAME},{timestamp}"
    
    try:
        client.connect(HUB_IP, 1883, 60)
        client.publish(TOPIC, message)
        client.disconnect()
        #print(f"Heartbeat sent: {message}")
        logging.info(f"Heartbeat sent: {message}")
    except Exception as e:
        #print("Failed to send heartbeat:", e)
        logging.error(f"Failed to send heartbeat: {e}")

    time.sleep(10)
