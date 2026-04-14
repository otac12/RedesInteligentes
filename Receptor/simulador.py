import socket, json, time

ESP32_IP = "192.168.4.1"

data = {
    "temperatura": 24.5,
    "humedad": 60.2,
    "latitud": 19.432,
    "longitud": -99.133,
    "gas_lp": 0.03,
    "co2": 412
}

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
while True:
    sock.sendto(json.dumps(data).encode(), (ESP32_IP, 5005))
    print("Enviado al ESP32:", data)
    time.sleep(2)