#pragma once
#include "esphome.h"
#include "esp_http_client.h"
#include "esp_wifi.h"
#include <cstring>
#include <cstdlib>

// Safe HTTP polling client for LD2450 radar node
// Uses a slower polling rate and ensures connections are properly closed
// to avoid exhausting the radar node's limited sockets.

static char http_buf[1024];
static int http_buf_len = 0;
static unsigned long last_poll_ms = 0;
static unsigned long last_ok_ms = 0;
static bool radar_reachable = false;
static int fail_count = 0;

static esp_err_t _http_evt(esp_http_client_event_t *evt) {
  if (evt->event_id == HTTP_EVENT_ON_DATA) {
    int room = sizeof(http_buf) - http_buf_len - 1;
    if (room > 0) {
      int cp = (evt->data_len < room) ? evt->data_len : room;
      memcpy(http_buf + http_buf_len, evt->data, cp);
      http_buf_len += cp;
      http_buf[http_buf_len] = '\0';
    }
  }
  return ESP_OK;
}

// Parse a single value from ESPHome web server JSON response
static float parse_value(const char* json) {
  const char* vp = strstr(json, "\"value\":");
  if (!vp) return 0;
  vp += 8;
  while (*vp == ' ') vp++;
  if (*vp == '"') vp++;
  return strtof(vp, NULL);
}

// Fetch a single sensor value via HTTP GET
static float fetch_sensor(const char* object_id) {
  char url[128];
  snprintf(url, sizeof(url), "http://10.109.204.33/sensor/%s", object_id);
  http_buf_len = 0;
  http_buf[0] = '\0';
  
  esp_http_client_config_t cfg = {};
  cfg.url = url;
  cfg.event_handler = _http_evt;
  cfg.timeout_ms = 800; // Increased timeout for stability
  cfg.disable_auto_redirect = true;
  cfg.keep_alive_enable = false; // MUST BE FALSE to prevent TIME_WAIT exhaustion
  
  esp_http_client_handle_t c = esp_http_client_init(&cfg);
  if (!c) return 0;
  
  // Force Connection: close
  esp_http_client_set_header(c, "Connection", "close");
  
  float val = 0;
  esp_err_t err = esp_http_client_perform(c);
  int status = esp_http_client_get_status_code(c);
  
  if (err == ESP_OK && status == 200) {
    val = parse_value(http_buf);
    last_ok_ms = millis();
    fail_count = 0;
    radar_reachable = true;
  } else {
    fail_count++;
    if (fail_count > 3) radar_reachable = false;
  }
  
  // Clean up socket
  esp_http_client_cleanup(c);
  return val;
}

// We only poll essential sensors to reduce load
static const char* sensor_ids[] = {
  "_target1_x", "_target1_y", "_target1_speed", "_target1_threat",
  "_target2_x", "_target2_y", "_target2_speed", "_target2_threat",
  "_target3_x", "_target3_y", "_target3_speed", "_target3_threat",
  "_system_threat", "_all_target_count"
};

static int poll_step = 0;

void radar_poll() {
  unsigned long now = millis();
  
  // Extremely slow polling: 1 target property every 1000ms (1 second)
  // This completely guarantees the ESP32 web server will not exhaust sockets.
  if (now - last_poll_ms < 1000) return; 
  last_poll_ms = now;
  
  // Check WiFi
  wifi_ap_record_t ap;
  if (esp_wifi_sta_get_ap_info(&ap) != ESP_OK) {
    id(radar_connected) = false;
    return;
  }
  
  // If unreachable, retry very slowly (every 10 seconds)
  if (!radar_reachable && fail_count > 3) {
    if (now - last_ok_ms < 10000) return;
    fail_count = 0;
  }
  
  float val = fetch_sensor(sensor_ids[poll_step]);
  
  if (!radar_reachable) {
    id(radar_connected) = false;
    return;
  }
  
  // Store fetched value
  switch (poll_step) {
    case 0: id(t1_x) = val; break;
    case 1: id(t1_y) = val; id(t1_active) = (id(t1_x)!=0 || val!=0); break;
    case 2: id(t1_speed) = val; break;
    case 3: id(t1_threat) = val; break;
    case 4: id(t2_x) = val; break;
    case 5: id(t2_y) = val; id(t2_active) = (id(t2_x)!=0 || val!=0); break;
    case 6: id(t2_speed) = val; break;
    case 7: id(t2_threat) = val; break;
    case 8: id(t3_x) = val; break;
    case 9: id(t3_y) = val; id(t3_active) = (id(t3_x)!=0 || val!=0); break;
    case 10: id(t3_speed) = val; break;
    case 11: id(t3_threat) = val; break;
    case 12: id(sys_threat) = val; break;
    case 13: id(target_count) = (int)val; break;
  }
  
  poll_step++;
  if (poll_step > 13) poll_step = 0;
  
  id(radar_connected) = (now - last_ok_ms < 5000);
}
