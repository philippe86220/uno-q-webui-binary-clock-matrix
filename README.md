# UNO Q Binary Clock (WebUI + LED Matrix)

A minimal end-to-end UNO Q example showing Linux ↔ Bridge ↔ STM32 ↔ WebUI integration.
A simple and educational project for the Arduino UNO Q platform demonstrating :

- Linux system time as the single time source
- STM32 LED matrix display via Bridge RPC
- A WebUI binary clock rendered in HTML (BCD format)
- Clean separation between Linux and MCU responsibilities

## System Diagram

```
Linux (Python)
   │
   ├── Bridge RPC ──► STM32 LED Matrix
   │
   └── REST API ──► WebUI Binary Clock
```

This project is designed for beginners learning the UNO Q architecture.

---

## Architecture Overview

The project shows the dual-core nature of UNO Q:

Linux (Python) -> Bridge -> STM32 -> LED Matrix  
               -> WebUI (HTML Binary Clock)

### Linux side (Python)

- Retrieves system time using `datetime`
- Sends HH:MM:SS to STM32 every second
- Serves a WebUI using the WebUI brick
- Provides REST API endpoints

### STM32 side

- Receives time via Bridge RPC
- Displays digital clock on LED matrix

### WebUI side

- Displays a binary clock in BCD format
- Uses the same Linux system time
- Allows starting/stopping matrix updates

---

## ✨ Features

- Real-time clock synchronized with Linux system time
- Automatic summer/winter time handling (Europe/Paris)
- Binary clock display (BCD format)
- LED-style glowing WebUI interface
- Simple REST API control
- Very low complexity (ideal for learning)

---

## Design Choices

Separate Bridge commands are used:

- updateTime() for periodic clock updates
- clearMatrix() for one-shot actions

This keeps the system simple, readable, and easy to extend.

---

## 📁 Project Structure
```
/
├── assets/
│   └── index.html      → Interface 13×8 en JavaScript
│
├── python/
│   └── main.py         → WebUI API + Bridge RPC
│
├── sketch/
│   └── sketch.ino      → Réception des frames + matrixWrite()
│   └── sketch.yaml
│ 
├── LICENSE
│
├── README.md
│
└── app.yaml
```


**Important:**  
The `assets` folder must be lowercase and located at the project root.

---

## 🚀 How It Works

### Time Flow

1. Linux reads current time every second
2. Python sends time via Bridge:

Bridge.call("updateTime", h, m, s)


3. STM32 updates LED matrix display
4. WebUI fetches `/api/time` and updates binary clock

---

## 🌐 Web API Endpoints

### Get current time

GET /api/time


Response:

```
{
  "h": 14,
  "m": 32,
  "s": 10,
  "running": true
}
```

**Start LED matrix updates**

```
POST /api/start
```
**Stop LED matrix updates**

```
POST /api/stop
```
---

## Access WebUI

```cpp
http://localhost:7000/
```
or

```cpp
http://UNOQ_IP:7000/
```

---

## Educational Goals

- Learn UNO Q Linux/STM32 architecture
- Understand Bridge RPC communication
- Build simple WebUI interfaces
- Work with system time and threading

---

## Requirements

- Arduino UNO Q board
- Arduino App Lab environment
- LED Matrix enabled on STM32 side
- Network access to the UNO Q device

--- 

License

```
MIT License.
```

---

## Acknowledgments

This project was developed with guidance and technical support from ChatGPT.
