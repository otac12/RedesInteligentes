# Proyecto Redes - ESP32 SDN con NRF24L01

Sistema de telemetría con dos ESP32 comunicándose por radio NRF24L01 (2.4 GHz).
El emisor lee sensores reales, empaqueta los datos en binario (20 bytes) y los transmite.
El receptor los desempaqueta, los muestra en un LCD 16x2 y los reenvía por HTTP POST a un servidor Node.js.

## Arquitectura

```
ESP32 Emisor                          ESP32 Receptor                        PC
┌──────────────┐   NRF24L01 Radio   ┌──────────────────┐   HTTP POST     ┌──────────┐
│ DHT11        │   2.4 GHz          │ NRF24L01 → JSON  │   WiFi AP      │ Node.js  │
│ GPS NEO-6M   │ ────────────────►  │ LCD 16x2         │ ──────────────► │ SQLite   │
│ MQ2          │   20 bytes/paquete │ WiFi AP           │   :3000/datos  │ WebSocket│
└──────────────┘                    └──────────────────┘                 └──────────┘
```

## Conexiones ESP32 Emisor

### NRF24L01+PA+LNA

| Pin NRF24L01 | GPIO ESP32 | Función       |
|--------------|------------|---------------|
| VCC (V+)     | 3.3V       | Alimentación  |
| GND          | GND        | Tierra        |
| SCK          | GPIO 18    | SPI Clock     |
| MOSI         | GPIO 23    | SPI Data Out  |
| MISO         | GPIO 19    | SPI Data In   |
| CSN          | GPIO 5     | Chip Select   |
| CE           | GPIO 4     | Chip Enable   |

### DHT11 (Temperatura y Humedad)

| Pin DHT11 | GPIO ESP32 | Función  |
|-----------|------------|----------|
| VCC       | 3.3V       | Alimentación |
| GND       | GND        | Tierra   |
| DATA      | GPIO 15    | Datos    |

### GPS NEO-6M (Latitud y Longitud)

| Pin GPS | GPIO ESP32 | Función     |
|---------|------------|-------------|
| VCC     | 3.3V       | Alimentación|
| GND     | GND        | Tierra      |
| TX      | GPIO 16    | UART2 RX    |
| RX      | GPIO 17    | UART2 TX    |

### MQ2 (Gas LP)

| Pin MQ2 | GPIO ESP32 | Función         |
|---------|------------|-----------------|
| VCC     | 5V         | Alimentación    |
| GND     | GND        | Tierra          |
| AOUT    | GPIO 34    | Lectura ADC     |

## Conexiones ESP32 Receptor

### NRF24L01+PA+LNA

| Pin NRF24L01 | GPIO ESP32 | Función       |
|--------------|------------|---------------|
| VCC (V+)     | 3.3V       | Alimentación  |
| GND          | GND        | Tierra        |
| SCK          | GPIO 18    | SPI Clock     |
| MOSI         | GPIO 23    | SPI Data Out  |
| MISO         | GPIO 19    | SPI Data In   |
| CSN          | GPIO 5     | Chip Select   |
| CE           | GPIO 4     | Chip Enable   |

### LCD 16x2 (Modo 4 bits)

| Pin LCD | GPIO ESP32 | Función     |
|---------|------------|-------------|
| VSS     | GND        | Tierra      |
| VDD     | 5V         | Alimentación|
| RS      | GPIO 13    | Register Select |
| E       | GPIO 12    | Enable      |
| D4      | GPIO 14    | Data 4      |
| D5      | GPIO 27    | Data 5      |
| D6      | GPIO 26    | Data 6      |
| D7      | GPIO 25    | Data 7      |
| RW      | GND        | Write mode  |
| V0      | Potenciómetro | Contraste |

## Flashear MicroPython en el ESP32 (paso a paso)

Ambos ESP32 (emisor y receptor) necesitan tener MicroPython instalado.
El firmware incluido es `ESP32_GENERIC-20260406-v1.28.0.bin`.

### Requisitos previos

1. Instalar Python 3 en tu PC (si no lo tienes)
2. Instalar esptool:
   ```bash
   pip install esptool
   ```
   > **Nota Windows:** Si después de instalar `esptool` no se reconoce el comando, usa `python -m esptool` en lugar de `esptool` en todos los pasos siguientes.
3. Instalar Thonny (IDE para subir archivos al ESP32):
   - Descargar desde https://thonny.org

### Paso 1: Conectar el ESP32

- Conecta el ESP32 a tu PC con un cable USB
- Identifica el puerto COM asignado:
  - Windows: Abre **Administrador de dispositivos** → Puertos (COM y LPT) → busca "CP210x" o "CH340" (ej: COM3)
  - Si no aparece, instala el driver CH340 o CP2102 según tu placa

### Paso 2: Borrar la flash del ESP32

```bash
python -m esptool --port COM3 erase_flash
```

> Cambia `COM3` por tu puerto real. Si el ESP32 no responde, mantén presionado el botón **BOOT** mientras ejecutas el comando.

### Paso 3: Flashear el firmware MicroPython

Para el **Emisor**:
```bash
cd Emisor
python -m esptool --port COM3 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-20260406-v1.28.0.bin
```

Para el **Receptor**:
```bash
cd Receptor
python -m esptool --port COM3 --baud 460800 write_flash -z 0x1000 ESP32_GENERIC-20260406-v1.28.0.bin
```

> Espera a que termine (tarda ~30 segundos). Al finalizar verás "Hash of data verified".

### Paso 4: Subir los archivos .py al ESP32

1. Abre **Thonny**
2. Ve a **Herramientas** → **Opciones** → **Intérprete**
3. Selecciona **MicroPython (ESP32)** y el puerto COM correcto
4. Click en **OK** — deberías ver el REPL de MicroPython en la consola
5. Ve a **Archivo** → **Abrir** → selecciona el `main.py` correspondiente (Emisor o Receptor)
6. Ve a **Archivo** → **Guardar como** → selecciona **Dispositivo MicroPython** → guarda como `main.py`
7. Para el emisor, también sube `nrf24l01.py` al dispositivo
8. Para el receptor, sube `nrf24l01.py` al dispositivo
9. Presiona el botón **RST** del ESP32 o haz click en **Stop/Restart** en Thonny

### Paso 5: Verificar

- En la consola de Thonny deberías ver:
  - Emisor: `"Emisor NRF24L01 listo"`
  - Receptor: `"AP listo: ..."` y `"Esperando datos por NRF24L01..."`

### Notas importantes

- El archivo debe llamarse `main.py` en el ESP32 para que se ejecute automáticamente al encender
- El driver `nrf24l01.py` se puede obtener del repositorio oficial: `micropython/micropython-lib` en GitHub
- Si usas un ESP32 con chip CH340, necesitas el driver CH340. Si usa CP2102, necesitas el driver CP210x
- Siempre alimenta el NRF24L01 con **3.3V** (nunca 5V, se quema)

## Estructura del proyecto

```
proyectoredes/
├── Emisor/
│   ├── main.py                          ← Sensores reales → struct.pack → NRF24L01 TX
│   └── ESP32_GENERIC-20260406-v1.28.0.bin  ← Firmware MicroPython
├── Receptor/
│   ├── main.py                          ← NRF24L01 RX → struct.unpack → LCD + HTTP POST
│   └── ESP32_GENERIC-20260406-v1.28.0.bin  ← Firmware MicroPython
├── web/
│   ├── server.js                        ← Node.js + SQLite + WebSocket
│   └── index.html                       ← Dashboard frontend
└── README.md
```

## Datos transmitidos

| Campo       | Sensor   | Tipo  | Bytes |
|-------------|----------|-------|-------|
| temperatura | DHT11    | float | 4     |
| humedad     | DHT11    | float | 4     |
| latitud     | GPS NEO6 | float | 4     |
| longitud    | GPS NEO6 | float | 4     |
| gas_lp      | MQ2      | float | 4     |
| **Total**   |          |       | **20**|

Formato: `struct.pack("fffff", temperatura, humedad, latitud, longitud, gas_lp)`

## Librerías necesarias (MicroPython)

- `nrf24l01.py` — Driver NRF24L01 (ambos ESP32)
- `dht` — Incluido en MicroPython (solo emisor)

## Instalación de dependencias

### Python (herramientas para flashear)

```bash
pip install -r requirements.txt
```

Contenido de `requirements.txt`:
- `esptool` — Para flashear el firmware MicroPython al ESP32

### Node.js (servidor web)

```bash
cd web
npm install
```

Dependencias en `package.json`:
- `express` — Servidor HTTP
- `better-sqlite3` — Base de datos SQLite
- `ws` — WebSocket para tiempo real

## Servidor Web

```bash
cd web
node server.js
```

Escucha en `http://192.168.4.2:3000`. Endpoints:
- `POST /datos` — Recibe JSON de sensores
- `GET /api/lecturas?fecha=YYYY-MM-DD` — Consulta por día
- `GET /` — Dashboard
