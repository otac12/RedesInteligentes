from machine import Pin, SoftI2C
import time

# LCD en modo 4 bits sin I2C
from machine import Pin
import time

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
        self._write4(0x28)  # 4 bits, 2 líneas
        self._write4(0x0C)  # display on
        self._write4(0x01)  # clear
        time.sleep_ms(5)
        self._write4(0x06)  # entry mode

    def clear(self):
        self._write4(0x01)
        time.sleep_ms(5)

    def move(self, row, col):
        addr = 0x80 + col + (0x40 if row else 0)
        self._write4(addr)

    def write(self, text):
        for c in text:
            self._write4(ord(c), rs=1)

# Pines según tu conexión
lcd = LCD(rs=19, e=23, d4=18, d5=17, d6=16, d7=15)
lcd.clear()
lcd.move(0, 0)
lcd.write("Hola ESP32!")
lcd.move(1, 0)
lcd.write("LCD funcionando")