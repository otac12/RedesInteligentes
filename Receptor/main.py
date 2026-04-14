import network, json, struct, time
import urequests
from machine import Pin, SPI
from nrf24l01 import NRF24L01

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

# --- LCD (pines reasignados para liberar SPI: 18, 19, 23) ---
lcd = LCD(rs=13, e=12, d4=14, d5=27, d6=26, d7=25)
lcd.clear()
lcd.move(0, 0)
lcd.write("POST destino:")
lcd.move(1, 0)
lcd.write("192.168.4.2:3000")

# --- NRF24L01 Receptor ---
spi = SPI(1, baudrate=4000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))
csn = Pin(5, Pin.OUT)
ce  = Pin(4, Pin.OUT)

nrf = NRF24L01(spi, csn, ce, payload_size=20)
nrf.open_rx_pipe(1, b"sens1")   # mismo canal que el emisor
nrf.set_power_speed(NRF24L01.POWER_3, NRF24L01.SPEED_250K)
nrf.start_listening()

# IP de tu PC en la red del ESP32
NODE_URL = "http://192.168.4.2:3000/datos"

keys = ["temperatura", "humedad", "latitud", "longitud", "gas_lp"]
idx = 0

print("Esperando datos por NRF24L01...")
while True:
    if nrf.any():
        payload = nrf.recv()
        t, h, la, lo, g = struct.unpack("fffff", payload)
        data = {
            "temperatura": round(t, 2),
            "humedad": round(h, 2),
            "latitud": round(la, 6),
            "longitud": round(lo, 6),
            "gas_lp": round(g, 2)
        }
        print("Recibido:", data)

        # Muestra en LCD
        k1 = keys[idx % len(keys)]
        k2 = keys[(idx + 1) % len(keys)]
        idx += 2
        lcd.clear()
        lcd.move(0, 0)
        lcd.write(f"{k1}:{data[k1]}"[:16])
        lcd.move(1, 0)
        lcd.write(f"{k2}:{data[k2]}"[:16])

        # Reenvía a Node.js por HTTP POST
        try:
            r = urequests.post(NODE_URL, json=data,
                headers={"Content-Type": "application/json"})
            r.close()
        except Exception as e:
            print("Error HTTP:", e)

    time.sleep_ms(100)