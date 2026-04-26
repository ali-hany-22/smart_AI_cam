# 🦾 Roptics AI: Next-Gen Computer Vision Control System
> **An Advanced Human-Machine Interface (HMI) integrating MediaPipe, FastAPI, and ESP32 for Real-Time Automation.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?style=for-the-badge&logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Framework-009688.svg?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer--Vision-5C3EE8.svg?style=for-the-badge&logo=opencv)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/Google-MediaPipe-0070D2.svg?style=for-the-badge&logo=google)](https://mediapipe.dev/)

**Roptics AI** is a sophisticated system that bridges the gap between Computer Vision and Hardware Control. It allows users to interact with their environment through hand gestures, featuring an interactive virtual whiteboard, digital media control (Zoom/Record), and real-time hardware tracking using a single-axis servo mechanism.

---

## 🏗️ System Architecture & File Structure

The project follows a **Modular Architecture**, ensuring high scalability and clean separation of concerns:

```text
SMART_AI_CAM_R/
├── 📂 backend/                  # The AI Core Engine
│   ├── 📂 camera/               # Multi-threaded Video Acquisition
│   │   └── camera.py            # Low-latency V4L2 frame handler
│   ├── 📂 vision/               # Computer Vision Algorithms
│   │   ├── hand_tracking.py     # 21-Landmark Detection & Gesture Recognition
│   │   ├── teaching_mode.py     # Virtual Whiteboard & Air-Keyboard logic
│   │   ├── live_mode.py         # Smooth Pinch-to-Zoom & Media Controller
│   │   ├── gesture_drive.py     # Serial Comm & ESP32 Pan-Servo logic
│   │   └── control_mode.py      # Automated State Machine (Mode Switcher)
│   ├── 📂 assets/               # Local Media Repository
│   │   ├── 📂 photos/           # AI-captured snapshots
│   │   └── 📂 videos/           # H.264 encoded recordings
│   ├── app.py                   # FastAPI Server & Socket.IO Entry Point
│   └── config.py                # Global Constants & Environment Settings
├── 📂 ESP32/                    # Embedded Firmware
│   └── esp32_pan_servo.ino      # C++ Micro-controller Firmware
├── 📂 frontend/                 # Interactive Dashboard
│   ├── index.html               # Main UI Layout (Cyberpunk Theme)
│   ├── style.css                # Futuristic Visual Design
│   └── script.js                # WebSocket & Real-time SVG Hand Visualization
└── 📂 test/                     # Unit Tests & Debugging Tools






🛠️ Installation & Setup
1. Clone the repository
Bash

git clone [https://github.com/ali-hany-22/smart_AI_cam.git]
cd SMART_AI_CAM_R

2. Set up Virtual Environment (Recommended)
Bash

# Create venv
python3 -m venv venv

# Activate venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# .\venv\Scripts\activate

3. Install Dependencies
Bash

pip install --upgrade pip
pip install -r requirements.txt

4. Execution

    Connect the ESP32 via USB.

    Grant Serial permissions (Linux): sudo chmod 666 /dev/ttyUSB0.

    Run the backend: python3 backend/app.py.

    Open frontend/index.html in a modern browser.
