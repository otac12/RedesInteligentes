import network, socket, json, time
import urequests
from machine import Pin

class LCD:
    def __init__(self, rs, e, d4, d5, d6, d7):
        self.rs = Pin(rs, Pin.OUT)
        self.e = Pin(e, Pin.OUT)
        self.d = [Pin(d4, Pin.OUT), Pin(d5, Pin.OUT),
                  Pin(d6, Pin.OUT), Pin(d7, Pin.OUT)]
        self._init()

    def _pulse(self):
        self.e.value(1)
        time.sleep_us(50)
        self.e.value(0)
        time.sleep_us(50)

    def _write4(self, val, rs=0):
        self.rs.value(rs)
        for i, d in enumerate(self.d):
            d.value((val >> (4 + i)) & 1)
        self._pulse()
        for i, d in enumerate(self.d):
            d.value((val >> i) & 1)
        self._pulse()

    def _init(self):
        time.sleep_ms(50)
        for _ in range(3):
            for i, d in enumerate(self.d):
                d.value((0x30 >> (4 + i)) & 1)
            self._pulse()
            time.sleep_ms(5)
        for i, d in enumerate(self.d):
            d.value((0x20 >> (4 + i)) & 1)
        self._pulse()
        self._write4(0x28)
        self._write4(0x0C)
        self._write4(0x01)
        time.sleep_ms(5)
        self._write4(0x06)

    def clear(self):
        self._write4(0x01)
        time.sleep_ms(5)

    def move(self, row, col):
        addr = 0x80 + col + (0x40 if row else 0)
        self._write4(addr)

    def write(self, text):
        for c in text:
            self._write4(ord(c), rs=1)

# --- WiFi AP ---
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid="ESP32-SDN", password="12345678")
print("AP listo:", ap.ifconfig())

# --- LCD ---
lcd = LCD(rs=19, e=23, d4=18, d5=17, d6=16, d7=15)
lcd.clear()
lcd.move(0, 0)
lcd.write("ESP32-SDN listo")
lcd.move(1, 0)
lcd.write("Esperando JSON..")

# --- UDP server ---
udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
udp.bind(("0.0.0.0", 5005))

# IP de tu PC en la red del ESP32
NODE_URL = "http://192.168.4.2:3000/datos"

keys = ["temperatura", "humedad", "latitud", "longitud", "gas_lp", "co2"]
idx = 0

print("Esperando JSON...")
while True:
    udp.settimeout(0.1)
    try:
        data_raw, addr = udp.recvfrom(1024)
        data = json.loads(data_raw)
        print("Recibido:", data)

        # Muestra en LCD
        k1 = keys[idx % len(keys)]
        k2 = keys[(idx + 1) % len(keys)]
        idx += 2
        lcd.clear()
        lcd.move(0, 0)
        lcd.write(f"{k1}:{data.get(k1,'?')}"[:16])
        lcd.move(1, 0)
        lcd.write(f"{k2}:{data.get(k2,'?')}"[:16])

        # Reenvía a Node.js por HTTP POST
        try:
            r = urequests.post(NODE_URL, json=data,
                headers={"Content-Type": "application/json"})
            r.close()
        except Exception as e:
            print("Error HTTP:", e)

    except OSError:
        pass