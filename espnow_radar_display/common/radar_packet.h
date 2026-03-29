#pragma once
#include <stdint.h>

// Shared binary packet for ESP-NOW radar data (53 bytes)
// Well under the 250-byte ESP-NOW limit
typedef struct __attribute__((packed)) {
  uint8_t target_count;       // 0-3 active targets
  struct {
    float x;                  // mm, Kalman-filtered
    float y;                  // mm, Kalman-filtered
    float speed;              // m/s, EMA-filtered
    float threat;             // 0-100%
  } targets[3];
  float system_threat;        // max threat across all targets
} RadarPacket;
// sizeof(RadarPacket) = 1 + 3*16 + 4 = 53 bytes
