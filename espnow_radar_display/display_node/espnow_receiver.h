#pragma once
#include "esphome.h"
#include "esp_now.h"
#include "esp_wifi.h"
#include "radar_packet.h"
#include <cstring>

// ESP-NOW receiver for radar data
// Receives broadcast RadarPacket and copies to ESPHome globals

static RadarPacket rx_packet;
static volatile bool new_data = false;
static volatile unsigned long last_packet_ms = 0;
static uint32_t packets_received = 0;

// ESP-NOW receive callback (runs in WiFi task context)
static void espnow_recv_cb(const esp_now_recv_info_t *info,
                           const uint8_t *data, int len) {
  if (len == sizeof(RadarPacket)) {
    memcpy((void*)&rx_packet, data, sizeof(RadarPacket));
    new_data = true;
    last_packet_ms = millis();
    packets_received++;
  }
}

void espnow_init_receiver() {
  esp_err_t err = esp_now_init();
  if (err != ESP_OK) {
    ESP_LOGE("espnow", "esp_now_init failed: %d", err);
    return;
  }
  // Channel already set by AP mode config (channel 1)
  // No need to force channel manually

  esp_now_register_recv_cb(espnow_recv_cb);

  ESP_LOGI("espnow", "ESP-NOW receiver initialized");

  // Print own MAC so user can configure sender if needed
  uint8_t mac[6];
  esp_wifi_get_mac(WIFI_IF_AP, mac);
  ESP_LOGI("espnow", "Display MAC: %02X:%02X:%02X:%02X:%02X:%02X",
    mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

// Copy received packet data into ESPHome globals
// Call this from an interval lambda
void espnow_update_globals() {
  if (new_data) {
    new_data = false;

    id(target_count) = rx_packet.target_count;
    id(sys_threat) = rx_packet.system_threat;

    id(t1_x) = rx_packet.targets[0].x;
    id(t1_y) = rx_packet.targets[0].y;
    id(t1_speed) = rx_packet.targets[0].speed;
    id(t1_threat) = rx_packet.targets[0].threat;
    id(t1_active) = (rx_packet.targets[0].x != 0 || rx_packet.targets[0].y != 0);

    id(t2_x) = rx_packet.targets[1].x;
    id(t2_y) = rx_packet.targets[1].y;
    id(t2_speed) = rx_packet.targets[1].speed;
    id(t2_threat) = rx_packet.targets[1].threat;
    id(t2_active) = (rx_packet.targets[1].x != 0 || rx_packet.targets[1].y != 0);

    id(t3_x) = rx_packet.targets[2].x;
    id(t3_y) = rx_packet.targets[2].y;
    id(t3_speed) = rx_packet.targets[2].speed;
    id(t3_threat) = rx_packet.targets[2].threat;
    id(t3_active) = (rx_packet.targets[2].x != 0 || rx_packet.targets[2].y != 0);
  }

  // Connection status: true if packet received in last 2 seconds
  id(radar_connected) = (millis() - last_packet_ms < 2000);
}
