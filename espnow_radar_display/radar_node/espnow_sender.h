#pragma once
#include "esphome.h"
#include "esp_now.h"
#include "esp_wifi.h"
#include "radar_packet.h"
#include "target_analytics.h"
#include <cstring>
#include <cmath>

// ESP-NOW sender for radar data
// Broadcasts RadarPacket at ~30Hz to the display node

static RadarPacket tx_packet;
static bool espnow_ready = false;
static uint32_t packets_sent = 0;
static uint32_t last_update_ts[3] = {0, 0, 0};

// Persistence filter: target must be seen for N consecutive frames
static const int PERSIST_MIN = 3;  // ~100ms at 30Hz
static int persist_count[3] = {0, 0, 0};

static void on_send_cb(const wifi_tx_info_t *tx_info, esp_now_send_status_t status) {
  if (status == ESP_NOW_SEND_SUCCESS) packets_sent++;
}

void espnow_init_sender() {
  esp_err_t err = esp_now_init();
  if (err != ESP_OK) {
    ESP_LOGE("espnow", "esp_now_init failed: %d", err);
    return;
  }
  esp_now_register_send_cb(on_send_cb);

  // Channel already set by AP mode config (channel 1)

  // Add broadcast peer
  esp_now_peer_info_t peer = {};
  memset(peer.peer_addr, 0xFF, 6);
  peer.channel = 0;  // Use current channel (set by AP config)
  peer.encrypt = false;
  peer.ifidx = WIFI_IF_AP;
  esp_now_add_peer(&peer);

  espnow_ready = true;
  ESP_LOGI("espnow", "ESP-NOW sender initialized (broadcast mode)");

  uint8_t mac_addr[6];
  esp_wifi_get_mac(WIFI_IF_AP, mac_addr);
  ESP_LOGI("espnow", "Radar MAC: %02X:%02X:%02X:%02X:%02X:%02X",
    mac_addr[0], mac_addr[1], mac_addr[2],
    mac_addr[3], mac_addr[4], mac_addr[5]);
}

// Parse LD2450 UART frame and send via ESP-NOW
void parse_ld2450_and_send(const std::vector<uint8_t> &bytes) {
  if (!espnow_ready || bytes.size() < 28) return;

  uint32_t now = millis();
  int count = 0;
  float sys_thr = 0;
  int b = 0;

  for (int i = 0; i < 3; i++) {
    // Parse X (signed 16-bit, LD2450 format)
    int16_t raw_x = (int16_t)((bytes[b+5] << 8) | bytes[b+4]);
    if (bytes[b+5] & 0x80) raw_x -= 32768; else raw_x = -raw_x;
    raw_x = -raw_x;

    // Parse Y (always positive for targets in front of sensor)
    int16_t raw_y = (int16_t)((bytes[b+7] << 8) | bytes[b+6]);
    if (bytes[b+7] & 0x80) raw_y -= 32768; else raw_y = -raw_y;

    // Parse Speed
    int16_t raw_speed = (int16_t)((bytes[b+9] << 8) | bytes[b+8]);
    if (bytes[b+9] & 0x80) raw_speed -= 32768; else raw_speed = -raw_speed;

    // Basic validation: target must be in front of sensor (y > 0), within 6m
    bool raw_valid = (raw_x != 0 || raw_y > 0) && (raw_y > 0);
    if (raw_valid) {
      float dist = sqrtf((float)(raw_x*raw_x) + (float)(raw_y*raw_y));
      if (dist > 6000) raw_valid = false;
    }

    // Persistence filter: suppress ghost targets (must be seen 3 consecutive frames)
    if (raw_valid) {
      if (persist_count[i] < PERSIST_MIN) persist_count[i]++;
    } else {
      persist_count[i] = 0;
    }

    bool confirmed = (persist_count[i] >= PERSIST_MIN);

    if (confirmed) {
      count++;
      uint32_t dt = (last_update_ts[i] > 0) ? (now - last_update_ts[i]) : 200;
      last_update_ts[i] = now;

      target_analytics[i].update((float)raw_x, (float)raw_y, dt, now);

      tx_packet.targets[i].x = target_analytics[i].x;
      tx_packet.targets[i].y = target_analytics[i].y;
      tx_packet.targets[i].speed = target_analytics[i].fil_spd;
      tx_packet.targets[i].threat = target_analytics[i].threat_score;

      if (target_analytics[i].threat_score > sys_thr)
        sys_thr = target_analytics[i].threat_score;
    } else {
      if (persist_count[i] == 0) {
        target_analytics[i].reset();
        last_update_ts[i] = 0;
      }
      tx_packet.targets[i].x = 0;
      tx_packet.targets[i].y = 0;
      tx_packet.targets[i].speed = 0;
      tx_packet.targets[i].threat = 0;
    }
    b += 8;
  }

  tx_packet.target_count = count;
  tx_packet.system_threat = sys_thr;

  // Broadcast packet via ESP-NOW
  uint8_t broadcast[6] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
  esp_now_send(broadcast, (uint8_t *)&tx_packet, sizeof(RadarPacket));
}
