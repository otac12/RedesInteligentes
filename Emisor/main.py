import struct, time
from machine import Pin, SPI, UART, ADC
from nrf24l01 import NRF24L01
import dht

# =============================================
#  PINES DEL EMISOR (ESP32)
# =============================================
#  NRF24L01:  SCK=18, MOSI=23, MISO=19, CSN=5, CE=4
#  DHT11:     GPIO 15
#  GPS NEO6M: UART2 → TX=17, RX=16
#  MQ2:       GPIO 34 (ADC)
# =============================================

# --- NRF24L01 ---
spi = SPI(1, baudrate=4000000, polarity=0, phase=0,
          sck=Pin(18), mosi=Pin(23), miso=Pin(19))
csn = Pin(5, Pin.OUT)
ce  = Pin(4, Pin.OUT)

nrf = NRF24L01(spi, csn, ce, payload_size=20)
nrf.open_tx_pipe(b"sens1")
nrf.set_power_speed(NRF24L01.POWER_3, NRF24L01.SPEED_250K)
nrf.stop_listening()

# --- DHT11 (temperatura + humedad) ---
sensor_dht = dht.DHT11(Pin(15))

# --- GPS NEO-6M (UART2) ---
gps_uart = UART(2, baudrate=9600, tx=17, rx=16)

# --- MQ2 (gas LP - lectura analógica) ---
sensor_mq2 = ADC(Pin(34))
sensor_mq2.atten(ADC.ATTN_11DB)   # rango 0-3.3V
sensor_mq2.width(ADC.WIDTH_12BIT)  # 0-4095

# =============================================
#  FUNCIONES
# =============================================

def leer_dht():
    try:
        sensor_dht.measure()
        return sensor_dht.temperature(), sensor_dht.humidity()
    except Exception:
        print("Error DHT11")
        return 0.0, 0.0

def leer_gps():
    """Parsea sentencia NMEA $GPGGA para obtener lat/lon"""
    lat, lon = 0.0, 0.0
    timeout = time.ticks_ms() + 2000
    while time.ticks_ms() < timeout:
        if gps_uart.any():
            line = gps_uart.readline()
            if line is None:
                continue
            try:
                line = line.decode("ascii", "ignore").strip()
            except:
                continue
            if line.startswith("$GPGGA") or line.startswith("$GNGGA"):
                parts = line.split(",")
                if len(parts) >= 6 and parts[2] and parts[4]:
                    # Latitud: ddmm.mmmm → grados decimales
                    raw_lat = float(parts[2])
                    lat = int(raw_lat / 100) + (raw_lat % 100) / 60
                    if parts[3] == "S":
                        lat = -lat
                    # Longitud: dddmm.mmmm → grados decimales
                    raw_lon = float(parts[4])
                    lon = int(raw_lon / 100) + (raw_lon % 100) / 60
                    if parts[5] == "W":
                        lon = -lon
                    return lat, lon
    return lat, lon

def leer_mq2():
    """Lectura analógica del MQ2, valor crudo 0-4095"""
    return sensor_mq2.read()

# =============================================
#  LOOP PRINCIPAL
# =============================================
print("Emisor NRF24L01 listo")
print("Sensores: DHT11(15) GPS(16,17) MQ2(34)")

while True:
    temperatura, humedad = leer_dht()
    latitud, longitud = leer_gps()
    gas_lp = float(leer_mq2())

    payload = struct.pack("fffff", temperatura, humedad, latitud, longitud, gas_lp)

    try:
        nrf.send(payload)
        print(f"Enviado: t={temperatura} h={humedad} lat={latitud} lon={longitud} gas={gas_lp}")
    except OSError:
        print("Error al enviar")

    time.sleep(2)
