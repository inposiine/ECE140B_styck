# Styck

A Python-based suggestion generator and end-to-end firmware + dashboard system that turns an ordinary cane experience into a real-time gait analysis and rehabilitation aid. Styck measures force, gait speed, and posture on each step, streams data over Wi-Fi, and uses customize threshold and Google’s Gemini LLM to deliver human-friendly walking tips.

---

##  Table of Contents

1. [Product Overview](#product-overview)  
2. [Hardware Components](#hardware-components)  
3. [Network & Firmware Setup](#network-&-firmware-setup)  
4. [Software Architecture](#software-architecture)  
5. [Prerequisites & Installation](#prerequisites--installation)  
6. [How It Works](#how-it-works)  
7. [Usage](#usage)  


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
2. **ESP32 toolchain** 
3. **MySQL database** access for backend storage  
4. **Google Gemini API key** stored in `GEMINI_API_KEY` environment variable



##  How It Works

1. **Session Control**  
   - **Start:** Press and release the cane’s pushbutton once. The LED will blink to confirm the session is active.  
   - **Stop:** Press and release the button again. The LED will then turn off, marking the session end.  

2. **Sensor Sampling**  
   - During an active session, the ESP32 reads the FSR at the tip and the IMU in the handle at ~50 Hz.  

3. **On-Device Processing & Alerts**  
   - Styck computes normalized force and gait speed in real time.  
   - If either metric exceeds your personalized threshold, the LED flashes once every second until you correct your posture or slow down.  

4. **Data Streaming & Storage**  
   - Each reading (`force`, `gait speed`, `steps`, `timestamp`) is sent via Wi-Fi (WebSocket) to the FastAPI backend.  
   - FastAPI tags data by session and stores it in MySQL for later review.

5. **Dashboard Visualization**  
   - The web dashboard displays live force vs. time and gait-speed charts.  
   - When your session ends, Styck groups that data into a named session entry for easy comparison.

---

##  Usage

1. **Power On & Connect**  
   - Battery replacement on Styck. It broadcasts `Styck-Setup` as an open Wi-Fi SSID.  
   - Connect your phone or laptop to `Styck-Setup` and open `http://192.168.4.1`.  
   - Enter your local Wi-Fi credentials to join your network.  

2. **Run a Walking Session**  
   - Press the cane button once to start. The LED will flash slowly.  
   - Walk as usual. LED alerts will indicate when to adjust.  
   - Press the button again to end. The LED wii turn off indicating the session if off.  

3. **Review Your Data**  
   - In your browser, navigate to `http://<styck-ip>/dashboard`.  
   - Click **Session History**, select your latest session, and view interactive graphs for force, gait symmetry, and speed.  
   - Adjust your alert thresholds or export the session report for your therapist.

4. **Generate AI Suggestions**  
- **Data Collection:**  
  Each walking session is logged with detailed metrics (force, acceleration, steps, and timestamps) through the FastAPI backend into a secure MySQL database.

- **Continuous Model Training:**  
  Over time, aggregated session data is used to periodically fine-tune the AI model. By learning from historical trends and individual variations in gait, the system enhances its accuracy, delivering more personalized and context-aware walking tips.

- **Real-Time Analysis & Suggestions:**  
  - When you run the suggestion generator script, the system:
     1. Retrieves your most recent session data.  
     2. Analyzes the data against historical trends and personalized parameters.  
     3. Uses the refined model to generate actionable and human-friendly suggestions tailored to your current performance and improvement areas.



