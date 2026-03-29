# LD2450 TinyML Radar Rover: Current Phase Specification (v1.0)

This document serves as the absolute technical source of truth for the current state of the "ld2450-tinyml" project. It is designed to provide full context for future AI agents or developers.

---

## 1. System Architecture Overview
The system is a distributed radar-sensing platform mounted on a teleoperated rover.

### 1.1 Hardware Components
| Component | Model | Role |
| :--- | :--- | :--- |
| **Rover Controller** | ESP8266 NodeMCU | Motor control and RC link handling. |
| **Radar Processor** | ESP32 DevKit V1 | Radar UART parsing, Analytics, ESP-NOW broadcast. |
| **Radar Sensor** | HLK-LD2450 | 24GHz mmWave radar (3-target tracking). |
| **HMI Dashboard** | Elecrow 7" ESP32-S3 | Display node, GUI rendering (LVGL). |
| **RC Link** | ES900X + Taranis Q X7 | Long-range LoRa control (CRSF/SBUS). |
| **FPV System** | 5.8GHz Analog | Low-latency visual feed. |
| **Motor Driver** | L298N (HW-354) | Dual H-Bridge for 4x geared DC motors. |

### 1.2 Physical Wiring (Pinout)
#### Radar Node (ESP32)
*   **LD2450 UART**: TX (GPIO17) -> ESP32 RX2 (GPIO16), RX (GPIO16) -> ESP32 TX2 (GPIO17).
*   **Baud Rate**: 256,000 bps.
*   **Power**: 5V/VIN from 2S LiPo regulator.

#### Rover Node (ESP8266)
*   **Motor Driver**: D1 (IN1), D2 (IN2), D3 (IN3), D4 (IN4).
*   **RC Receiver**: UART TX -> ESP8266 RX.

---

## 2. Firmware & Logic Details

### 2.1 Radar Analysis Pipeline (ESP32)
1.  **UART Parsing**: Reads 30-byte frames from LD2450.
2.  **Persistence Filter**: Targets must be detected for ≥ 3 consecutive frames (~100ms) to be "confirmed".
3.  **Kalman Filtering**:
    *   **Process Noise (Q)**: `pos = 20.0`, `vel = 0.4`.
    *   **Observation Noise (R)**: `350.0`.
4.  **Threat Analytics**:
    *   `Threat = Speed_Score + Approach_Score + Proximity_Score` (Max 100).
    *   `Speed_Score`: `min(35, m/s * 14)`.
    *   `Approach_Score`: Derived from velocity vector dot-product toward center (Max 40).
    *   `Proximity_Score`: `25 * (1 - dist_mm/7000)`.

### 2.2 ESP-NOW Protocol (Comms)
*   **Mode**: Broadcast (`FF:FF:FF:FF:FF:FF`).
*   **WiFi Channel**: Locked to **Channel 1**.
*   **Packet Structure (`RadarPacket`)**:
    ```cpp
    struct RadarPacket {
      uint8_t target_count; // 0-3
      struct {
        float x, y;         // mm (Kalman-filtered)
        float speed;        // m/s
        float threat;       // 0-100%
      } targets[3];
      float system_threat;  // Max threat
    }; // Total: 53 bytes
    ```
*   **Frequency**: ~30Hz (broadcast every 33ms).

---

## 3. TinyML implementation

### 3.1 Model Architecture (MLP)
*   **Framework**: TensorFlow/Keras (exported to `tinyml_weights.h`).
*   **Input**: 70 features (10-frame window × 7 features/frame).
*   **Layers**:
    1.  Input (70)
    2.  Dense (32, ReLU)
    3.  Dropout (0.2)
    4.  Dense (16, ReLU)
    5.  Dense (5, Softmax) - Classes: `STATIC`, `CREEPING`, `WALKING`, `RUNNING`, `PACING`.

### 3.2 Feature Engineering (Normalization)
Normalization is critical for model inference on-device:
*   **X Position**: `x / 4000.0`
*   **Y Position**: `y / 8000.0`
*   **Speed**: `speed / 4.0`
*   **Distance**: `sqrt(x^2 + y^2) / 8000.0`
*   **Threat**: `threat / 100.0`
*   **Delta X/Y**: `clip(dx / 300.0, -1, 1)`

---

## 4. HMI Dashboard (Elecrow ESP32-S3)

### 4.1 Rendering Logic (LVGL)
*   **Layering**: Static grid (circles/lines) drawn once; Dynamic targets/arcs drawn on a **PSRAM Canvas**.
*   **Canvas Details**: 480x460 buffer allocated in `SPIRAM`.
*   **Coordinate system**:
    *   Origin (0,0) at the bottom-center of the radar area.
    *   Scaling: `210 pixels / 6000 mm`.
*   **Visual FX**:
    *   **Motion Trails**: 5-point ring buffer of past coordinates.
    *   **Trajectory Prediction**: Draws arrow to `pos + velocity * 2000ms`.

### 4.2 GUI Features
*   **System Threat Bar**: Dynamic color (Green < 40 < Amber < 60 < Red).
*   **Target Info Panels**: Real-time X/Y (mm), Speed (m/s), and Threat (%) for each target.
*   **Connection Monitor**: Signal dot turns Red if no ESP-NOW packet received for > 2 seconds.

---

## 5. Development Workflow
*   **Data Capture**: `capture_data.py` (Logs SSE/HTTP stream to CSV).
*   **Training**: `train_classifier.py` (Produces `motion_classifier.h5`).
*   **Export**: `export_weights.h` (Converts H5 to C++ headers).
*   **Build**: ESPHome with custom C++ includes (`espnow_sender.h`, `radar_ui.h`).

---
*End of Specification - Created for future Agent context.*
