import struct, time
from machine import Pin, SPI, UART, ADC
from nrf24l01 import NRF24L01, POWER_3, SPEED_250K

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
nrf.set_power_speed(POWER_3, SPEED_250K)
nrf.stop_listening()

# --- Verificar sensores al inicio ---
print("=" * 40)
print("  EMISOR NRF24L01 - Diagnóstico")
print("=" * 40)
print("[OK] NRF24L01 configurado")

# DHT11
dht_ok = False
try:
    import dht
    sensor_dht = dht.DHT11(Pin(15))
    sensor_dht.measure()
    print("[OK] DHT11 (GPIO 15)")
    dht_ok = True
except Exception:
    print("[NO] DHT11 (GPIO 15) - no conectado")

# GPS NEO-6M
gps_uart = UART(2, baudrate=9600, tx=17, rx=16)
gps_ok = False
time.sleep_ms(500)
if gps_uart.any():
    print("[OK] GPS NEO-6M (UART2)")
    gps_ok = True
else:
    print("[NO] GPS NEO-6M (UART2) - no conectado")

# MQ2
sensor_mq2 = ADC(Pin(34))
sensor_mq2.atten(ADC.ATTN_11DB)
sensor_mq2.width(ADC.WIDTH_12BIT)
mq2_val = sensor_mq2.read()
if mq2_val > 0:
    print(f"[OK] MQ2 (GPIO 34) - valor: {mq2_val}")
else:
    print("[NO] MQ2 (GPIO 34) - no conectado")

print("=" * 40)
print("Enviando datos cada 2s (sensores sin conectar envían 0)")
print("=" * 40)

# =============================================
#  FUNCIONES
# =============================================

def leer_dht():
    if not dht_ok:
        return 0.0, 0.0
    try:
        sensor_dht.measure()
        return sensor_dht.temperature(), sensor_dht.humidity()
    except Exception:
        return 0.0, 0.0

def leer_gps():
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
                    raw_lat = float(parts[2])
                    lat = int(raw_lat / 100) + (raw_lat % 100) / 60
                    if parts[3] == "S":
                        lat = -lat
                    raw_lon = float(parts[4])
                    lon = int(raw_lon / 100) + (raw_lon % 100) / 60
                    if parts[5] == "W":
                        lon = -lon
                    return lat, lon
    return lat, lon

def leer_mq2():
    return sensor_mq2.read()

# =============================================
#  LOOP PRINCIPAL
# =============================================

while True:
    temperatura, humedad = leer_dht()
    latitud, longitud = leer_gps()
    gas_lp = float(leer_mq2())

    payload = struct.pack("fffff", temperatura, humedad, latitud, longitud, gas_lp)

    try:
        nrf.send(payload)
        print(f"TX: t={temperatura} h={humedad} lat={latitud} lon={longitud} gas={gas_lp}")
    except OSError:
        print("TX: sin ACK (receptor apagado?) - datos: t={} h={} lat={} lon={} gas={}".format(
            temperatura, humedad, latitud, longitud, gas_lp))

    time.sleep(2)
