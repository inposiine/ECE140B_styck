# Styck Smart Walking Stick

A Python-based suggestion generator and end-to-end firmware + dashboard system that turns an ordinary cane into a real-time gait analysis and rehabilitation aid. Styck measures force, speed, and posture on each step, streams data over Wi-Fi, and uses Google’s Gemini LLM to deliver human-friendly walking tips.

---

## 📘 Table of Contents

1. [Product Overview](#product-overview)  
2. [Hardware Components](#hardware-components)  
3. [Network & Firmware Setup](#network-&-firmware-setup)  
4. [Software Architecture](#software-architecture)  
5. [Prerequisites & Installation](#prerequisites--installation)  
6. [Calibration & Normalization](#calibration--normalization)  
7. [How It Works](#how-it-works)  
8. [Usage](#usage)  
9. [Extending Styck](#extending-styck)  
10. [License & Acknowledgements](#license--acknowledgements)

---

## Product Overview

Styck is a next-generation smart cane that:

- Captures **cane-tip force** via an FSR sensor  
- Tracks **cane orientation** and **gait speed** with an MPU6050 IMU  
- Streams data over Wi-Fi (ESP32 hotspot or local network) to a multilingual dashboard  
- Provides instant LED alerts for posture deviations  
- Uses Gemini LLM to generate personalized walking tips based on normalized gait parameters

---

## Hardware Components

- **ESP32** development board (Wi-Fi + MCU)  
- **Force-Sensing Resistor (FSR)** at the cane tip for load measurement  
- **MPU6050 IMU** in the handle for acceleration & tilt  
- **LED indicator** for real-time posture alerts  
- **Pushbutton** for session start/stop  
- **Li-Ion battery + charger module** for portable power  
- **3D-printed enclosures** for tip and handle modules

---

## Network & Firmware Setup

1. **ESP32 Hotspot Mode**  
   - On power-up, Styck creates an open Wi-Fi SSID `Styck-Setup`  
   - Connect your laptop or phone to `Styck-Setup`  
2. **Accessing the Dashboard**  
   - Point your browser to `http://192.168.4.1` (ESP32’s default IP)  
   - Use the built-in web UI to configure your local Wi-Fi SSID and password  
3. **Local Network Mode**  
   - After setup, Styck joins your home/clinic Wi-Fi  
   - It obtains a LAN IP (check your router’s DHCP list)  
   - Dashboards and mobile apps connect to `http://<styck-ip>/dashboard`

---

## Software Architecture

- **Firmware (`device_switch.ino`)**  
  - Reads FSR via `analogRead()` and IMU via I²C  
  - Packages JSON `{type, user_id, force, accel, gyro, timestamp}`  
  - Streams over WebSocket to the FastAPI backend  

- **Backend (`main.py`)**  
  - FastAPI routes for `/api/...` and WebSocket `/ws`  
  - Stores sessions, force_measurements, steps, alerts in MySQL  

- **Dashboard (`dashboard.js` + `style.css`)**  
  - Real-time charts (Chart.js) for force vs. time & gait metrics  
  - Session start/stop, threshold adjustment, multi-language support via i18next  

---

## Prerequisites & Installation

1. **Python 3.8+**  
2. **ESP32 toolchain** (Arduino IDE or PlatformIO)  
3. **MySQL database** access for backend storage  
4. **Google Gemini API key** stored in `GEMINI_API_KEY` environment variable  

