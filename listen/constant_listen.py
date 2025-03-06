import sys
import time
import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import board
import atexit

class Display:
    def __init__(self):
        self.width = 128
        self.height = 64
        self.font = ImageFont.load_default()
        self.enabled = True  
        #self.ip = self.get_ip_address()
        i2c = board.I2C()
        try:
            self._disp = adafruit_ssd1306.SSD1306_I2C(self.width, self.height, i2c)
            self._disp.fill(0)
            self._disp.show()
        except RuntimeError as e:
            print(f'Display: {e}', file=sys.stderr)
            self.enabled = False

        atexit.register(self.clear_display)

    def show_message(self, message):
        if self.enabled:
            image = Image.new('1', (self.width, self.height))
            draw = ImageDraw.Draw(image)
            draw.text((0, 0), message, font=self.font, fill=255)
            self._disp.image(image)
            self._disp.show()

    def clear_display(self):
        if self.enabled:
            self._disp.fill(0)
            self._disp.show()

def on_connect(client, userdata, flags, rc, properties):
    if rc == 0:
        if userdata.enabled:
            userdata.show_message("MQTT Active")
    else:
        userdata.show_message(f"MQTT Error {rc}")

def on_message(client, userdata, msg):
    if msg.topic == "heartbeat":
        userdata.show_message("Connected")

def on_disconnect(client, userdata, rc, properties=None):
    userdata.show_message("MQTT Disconnected")

def main():
    display = Display()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, userdata=display)
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.connect("192.168.2.1", 1883, 60)
    client.loop_start()

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
