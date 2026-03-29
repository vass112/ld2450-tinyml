# Radar-Assisted FPV Rover Platform

## Overview
The Radar-Assisted FPV Rover Platform is a modular ground vehicle designed for remote observation and inspection. It integrates a traditional RC (Radio Controlled) differential-drive rover chassis with analog First-Person View (FPV) video and an advanced 24GHz Millimeter-Wave (mmWave) radar sensing system.

The system allows an operator to navigate complex environments remotely while receiving two simultaneous streams of data:
1. **Live Analog FPV Video** for visual navigation and identification.
2. **Real-Time ESP-NOW Radar Telemetry** for detecting, tracking, and predicting the movement of objects (even through thin walls, smoke, or darkness) displayed on a dedicated smart dashboard.

---

## 1. Hardware Architecture

The platform consists of three distinct subsystems: the Rover mobility base, the Radar Sensor Node, and the Operator Dashboard.

### 1.1 Rover Mobility Base
The rover chassis provides the physical platform, power, and teleoperation capabilities.
* **Drive System:** 4-wheel differential drive (skid-steer/tank style). Two parallel motors on the left and two parallel motors on the right.
* **Motor Control:** Dual H-Bridge motor driver controlled by a central onboard microcontroller.
* **Power System:** Powered by a centralized 2S Lithium Polymer (LiPo) battery pack (7.4V - 8.4V).
    * Battery provides direct voltage to the motor driver.
    * Regulated down to provide logic voltage (VIN / 3.3V) to the microcontroller and peripherals.
* **RC Receiver:** ES900X receiver, establishing a high-reliability, low-latency control link with the operator's FrSky Taranis Q X7 transmitter.
* **FPV System:** Low-latency analog FPV camera paired with an onboard Video Transmitter (VTX) operating on the 5.8GHz band.

### 1.2 Radar Sensing Node (Mounted on Rover)
The radar node provides the localized sensing capabilities, operating independently of the main rover microcontroller to ensure zero latency impact on motor control.
* **Microcontroller:** ESP32 (e.g., DevKit V1).
* **Sensor:** HLK-LD2450 24GHz mmWave radar module.
* **Function:** Detects up to 3 moving targets simultaneously, calculating their X/Y coordinates, distance, and speed.
* **Communication:** Streams target data at ~30Hz via ESP-NOW to the operator dashboard.

### 1.3 Operator FPV & Radar Dashboard
The remote command station setup consists of the RC transmitter, FPV goggles/monitor, and a digital radar dashboard.
* **Display Hardware:** Elecrow CrowPanel 7-inch ESP32-S3 HMI Touch Display (800x480 resolution).
* **Function:** Receives ESP-NOW telemetry from the rover and renders a real-time, low-latency top-down radar map of the rover's environment.

---

## 2. Software & Firmware Architecture

### 2.1 Teleoperation Control Loop
The movement of the rover operates on a closed manual control loop:
1. Operator inputs movement commands via the FrSky Taranis Q X7 transmitter.
2. The ES900X receiver acts on the radio signals and passes protocols (e.g., CRSF or SBUS) to the microcontroller.
3. The microcontroller translates steering angles/throttle into left/right differential PWM signals.
4. The dual H-Bridge drives the 4 motors.
5. The operator receives visual feedback via the 5.8GHz FPV video link to close the loop.

### 2.2 Radar Data Pipeline (ESP-NOW)
To achieve extreme low-latency and fluid 30+ FPS radar updates, standard Wi-Fi protocols were bypassed in favor of Espressif's ESP-NOW protocol.
* **Sender (Radar Node):**
  * Reads continuous UART data from the LD2450 sensor.
  * Implements a **3-Frame Persistence Filter** to suppress noise and "ghost" targets. A target must be detected for ~100ms consecutively before being broadcast.
  * Packages X/Y coordinates, speed, and threat analytics into a compressed `RadarPacket`.
  * Broadcasts via `WIFI_IF_AP` interface on a locked Channel 1 using ESP-NOW.
* **Receiver (Operator Dashboard):**
  * Listens on Channel 1 (`WIFI_IF_AP`) for ESP-NOW broadcasts.
  * Immediately updates internal target memory arrays upon callback.

### 2.3 Dashboard UI & Rendering Engine (LVGL)
The Elecrow 7-inch display utilizes the **LVGL (Light and Versatile Graphics Library)** for the radar user interface.
The rendering pipeline is highly optimized using a direct canvas drawing approach rather than discrete LVGL widgets for moving targets:
* **EMA Smoothing:** Incoming radar coordinates jitter naturally. An Exponential Moving Average (EMA) algorithm applies temporal smoothing to the X/Y positions to ensure fluid dot movement on screen.
* **Trailing Effects:** Stores a historical ring buffer of previous coordinates to draw a fading 5-point motion trail behind fast-moving targets.
* **Predictive Trajectory:** Calculates a velocity vector (Vx, Vy) and draws a directional arrow projecting where the target will be in X seconds.
* **Threat Assessment:** Analyzes target speed and proximity to generate a 0-100% "Threat Level" warning, dynamically changing target colors (Green -> Amber -> Red).

---

## 3. Future Integration Roadmap

Currently, the rover base and the radar node operate as parallel, independent systems. The next phases of development involve deep integration:

1. **Telemetry Multiplexing:**
   * Feed rover battery voltage and motor telemetry into the ESP32 radar node.
   * Send both radar targets and rover health data in the same ESP-NOW packet to the dashboard.
2. **Semi-Autonomous Obstacle Avoidance:**
   * Connect the LD2450 target coordinates directly to the rover's motor microcontroller.
   * Implement safety overrides: If the radar detects an imminent collision (e.g., an object appearing suddenly in the FPV blindspot), automatically cut forward throttle or initiate evasive steering.
3. **Radar-Guided Tracking:**
   * Develop a "Follow Me" or "Track Target" mode where the rover automatically steers to keep an identified radar target centered in its forward X-axis.
