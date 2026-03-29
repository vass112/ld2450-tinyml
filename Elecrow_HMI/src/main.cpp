#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>

#include "LGFX_Elecrow70.hpp"
#include <lvgl.h>
#include "ui.h"

// Hardware Configuration
LGFX lcd;

// LVGL Display Buffer
static const uint32_t screenWidth  = 800;
static const uint32_t screenHeight = 480;
static lv_disp_draw_buf_t draw_buf;
static lv_color_t *buf1;
static lv_color_t *buf2;

// Display Flushing function for LVGL
void my_disp_flush(lv_disp_drv_t *disp_drv, const lv_area_t *area, lv_color_t *color_p) {
  if (lcd.getStartCount() == 0) {
    lcd.endWrite();
  }
  lcd.pushImageDMA(area->x1, area->y1, area->x2 - area->x1 + 1, area->y2 - area->y1 + 1, (lgfx::swap565_t *)&color_p->full);
  lv_disp_flush_ready(disp_drv);
}

// Touch Read function for LVGL
void my_touchpad_read(lv_indev_drv_t *indev_drv, lv_indev_data_t *data) {
  uint16_t touchX, touchY;
  bool touched = lcd.getTouch(&touchX, &touchY);
  if (!touched) {
    data->state = LV_INDEV_STATE_REL;
  } else {
    data->state = LV_INDEV_STATE_PR;
    data->point.x = touchX;
    data->point.y = touchY;
  }
}

// Network Configuration
const char* ssid = "arjuns23fe";
const char* password = "12121212";
String radarIP = "10.174.224.33/radar"; // Default Radar IP

TaskHandle_t NetworkTaskHandle;
void networkTask(void *pvParameters);

void setup() {
  Serial.begin(115200);

  // Initialize LCD
  lcd.init();
  lcd.setRotation(0);
  lcd.setBrightness(255);
  lcd.fillScreen(TFT_BLACK);

  // Initialize LVGL
  lv_init();

  // Allocate memory for display buffers directly in PSRAM
  buf1 = (lv_color_t *)heap_caps_malloc(screenWidth * 40 * sizeof(lv_color_t), MALLOC_CAP_SPIRAM);
  buf2 = (lv_color_t *)heap_caps_malloc(screenWidth * 40 * sizeof(lv_color_t), MALLOC_CAP_SPIRAM);
  lv_disp_draw_buf_init(&draw_buf, buf1, buf2, screenWidth * 40);

  // Initialize the display driver
  static lv_disp_drv_t disp_drv;
  lv_disp_drv_init(&disp_drv);
  disp_drv.hor_res = screenWidth;
  disp_drv.ver_res = screenHeight;
  disp_drv.flush_cb = my_disp_flush;
  disp_drv.draw_buf = &draw_buf;
  lv_disp_drv_register(&disp_drv);

  // Initialize the input device driver
  static lv_indev_drv_t indev_drv;
  lv_indev_drv_init(&indev_drv);
  indev_drv.type = LV_INDEV_TYPE_POINTER;
  indev_drv.read_cb = my_touchpad_read;
  lv_indev_drv_register(&indev_drv);

  // Initialize Custom UI
  ui_init();

  // Start Network Task
  xTaskCreatePinnedToCore(
    networkTask,
    "NetworkTask",
    8192,
    NULL,
    1,
    &NetworkTaskHandle,
    0
  );
}

void loop() {
  ui_tick();
  lv_timer_handler();
  delay(5);
}

// Network and SSE Parsing Task
void networkTask(void *pvParameters) {
  WiFi.begin(ssid, password);
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected.");
  
  // Update UI with IP
  ui_update_radar_ip(radarIP.c_str());

  HTTPClient http;
  String url = "http://" + radarIP + "/events";
  
  while(true) {
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("Connecting to SSE...");
      http.begin(url);
      http.addHeader("Accept", "text/event-stream");
      int httpCode = http.GET();
      
      if (httpCode == 200) {
        WiFiClient* stream = http.getStreamPtr();
        while (http.connected()) {
          if (stream->available()) {
            String line = stream->readStringUntil('\n');
            line.trim();
            if (line.startsWith("data: ")) {
              String jsonData = line.substring(6);
              ui_process_sse_data(jsonData.c_str());
            }
          }
          delay(1);
        }
      } else {
        Serial.printf("HTTP GET failed, error: %s\n", http.errorToString(httpCode).c_str());
      }
      http.end();
    }
    delay(5000); // Reconnect delay
  }
}
