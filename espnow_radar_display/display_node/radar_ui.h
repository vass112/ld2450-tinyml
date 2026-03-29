#pragma once
#include "esphome.h"
#include <lvgl.h>
#include <cmath>
#include <cstring>

// ============================================================================
// RADAR UI — High-Performance Rendering Pipeline
// Canvas-only renderer with EMA smoothing, prediction arrows, motion trails
// Target: 30-40 FPS on CrowPanel 7" ESP32-S3
// ============================================================================

// --- Trig Lookup Tables ---
static float sin_lut[360];
static float cos_lut[360];

// --- Layout Constants ---
static const int CX = 240;          // Radar center X on screen
static const int CY = 440;          // Radar center Y on screen
static const int RADAR_R = 210;     // Pixel radius of radar
static const float SC = 210.0f / 6000.0f;  // mm-to-pixel scale (6m range fits screen)

// --- Canvas (dynamic layer for sweep, targets, trails, arrows) ---
static lv_color_t * canvas_buf = nullptr;
static lv_obj_t * radar_canvas = nullptr;
static const int C_WIDTH = 480;
static const int C_HEIGHT = 460;

// --- Colors ---
static lv_color_t bg_col, gd_col, gf_col, grn_col, amb_col, wht_col, red_col, blu_col;
static lv_color_t pred_col;  // Prediction arrow color

// --- LVGL Screen ---
static lv_obj_t * scr = nullptr;

// ============================================================================
// Target State — Smoothing, Velocity, Prediction, Trails
// ============================================================================
static const int TRAIL_LEN = 5;
static const float EMA_ALPHA = 0.3f;     // Position smoothing factor
static const float PRED_TIME = 2000.0f;  // Prediction horizon in ms

struct TargetState {
  // Smoothed position (display coordinates: mm)
  float sx, sy;
  // Velocity (mm/ms)
  float vx, vy;
  // Previous raw for velocity computation
  float prev_x, prev_y;
  uint32_t prev_ms;
  // Trail history (screen pixel coords)
  int trail_x[TRAIL_LEN], trail_y[TRAIL_LEN];
  int trail_head;  // Ring buffer index
  int trail_count;
  // Previous canvas pixels for erase
  int old_px, old_py;        // Target dot
  int old_pred_px, old_pred_py;  // Prediction endpoint
  int old_trail_x[TRAIL_LEN], old_trail_y[TRAIL_LEN];
  int old_trail_count;
  // Active tracking
  bool was_active;
  bool initialized;

  void reset() {
    sx = sy = vx = vy = prev_x = prev_y = 0;
    prev_ms = 0;
    trail_head = trail_count = 0;
    old_px = old_py = -1;
    old_pred_px = old_pred_py = -1;
    old_trail_count = 0;
    was_active = false;
    initialized = false;
    memset(trail_x, -1, sizeof(trail_x));
    memset(trail_y, -1, sizeof(trail_y));
    memset(old_trail_x, -1, sizeof(old_trail_x));
    memset(old_trail_y, -1, sizeof(old_trail_y));
  }

  void update(float raw_x, float raw_y, uint32_t now_ms) {
    if (!initialized) {
      sx = raw_x; sy = raw_y;
      prev_x = raw_x; prev_y = raw_y;
      prev_ms = now_ms;
      vx = vy = 0;
      initialized = true;
      return;
    }
    // EMA smoothing
    sx = EMA_ALPHA * raw_x + (1.0f - EMA_ALPHA) * sx;
    sy = EMA_ALPHA * raw_y + (1.0f - EMA_ALPHA) * sy;

    // Velocity from position delta
    uint32_t dt = now_ms - prev_ms;
    if (dt > 10 && dt < 1000) {
      float new_vx = (sx - prev_x) / (float)dt;
      float new_vy = (sy - prev_y) / (float)dt;
      // Smooth velocity too
      vx = 0.4f * new_vx + 0.6f * vx;
      vy = 0.4f * new_vy + 0.6f * vy;
    }
    prev_x = sx; prev_y = sy;
    prev_ms = now_ms;
  }

  void push_trail(int px, int py) {
    trail_x[trail_head] = px;
    trail_y[trail_head] = py;
    trail_head = (trail_head + 1) % TRAIL_LEN;
    if (trail_count < TRAIL_LEN) trail_count++;
  }
};

static TargetState tgt_state[3];

// --- Sweep State ---
static lv_point_t old_sweep[2] = {{0,0},{0,0}};
static int sw_angle = 0;  // Sweep 0-179 degrees (top semicircle)

// --- LVGL UI Objects (right panel, reused) ---
static lv_obj_t * t_lbl[3];
static lv_obj_t * sig_lost_lbl;
static lv_obj_t * conn_dot;
static lv_obj_t * threat_bar;
static lv_obj_t * threat_lbl;
static lv_obj_t * p_box[3];
static lv_obj_t * p_stat[3][3];  // [target][line]
static lv_obj_t * tgt_cnt_lbl;

// --- State tracking for conditional UI updates ---
static bool was_connected = false;
static float last_systhr = -1;
static int last_tgtcnt = -1;

// ============================================================================
// Canvas Draw Helpers — Minimal overhead primitives
// ============================================================================

static void canvas_erase_rect(int x, int y, int w, int h) {
  if (!radar_canvas || x < 0) return;
  lv_draw_rect_dsc_t d;
  lv_draw_rect_dsc_init(&d);
  d.bg_color = LV_COLOR_CHROMA_KEY;
  d.bg_opa = LV_OPA_COVER;
  d.border_width = 0;
  lv_canvas_draw_rect(radar_canvas, x, y, w, h, &d);
}

static void canvas_draw_dot(int cx, int cy, int r, lv_color_t color) {
  if (!radar_canvas || cx < 0) return;
  lv_draw_rect_dsc_t d;
  lv_draw_rect_dsc_init(&d);
  d.bg_color = color;
  d.bg_opa = LV_OPA_COVER;
  d.radius = LV_RADIUS_CIRCLE;
  d.border_width = 0;
  lv_canvas_draw_rect(radar_canvas, cx - r, cy - r, r * 2, r * 2, &d);
}

static void canvas_draw_line_seg(lv_point_t p0, lv_point_t p1, lv_color_t color, int width) {
  if (!radar_canvas) return;
  lv_draw_line_dsc_t d;
  lv_draw_line_dsc_init(&d);
  d.color = color;
  d.width = width;
  lv_point_t pts[2] = {p0, p1};
  lv_canvas_draw_line(radar_canvas, pts, 2, &d);
}

static void canvas_erase_line_seg(lv_point_t p0, lv_point_t p1, int width) {
  if (!radar_canvas) return;
  lv_draw_line_dsc_t d;
  lv_draw_line_dsc_init(&d);
  d.color = LV_COLOR_CHROMA_KEY;
  d.width = width + 4;  // Extra margin to clear antialiasing
  lv_point_t pts[2] = {p0, p1};
  lv_canvas_draw_line(radar_canvas, pts, 2, &d);
}

// ============================================================================
// Right Panel UI Builder
// ============================================================================

static void create_panel_box(int y, lv_color_t color, const char* title, int idx) {
  p_box[idx] = lv_obj_create(scr);
  lv_obj_set_size(p_box[idx], 300, 90);
  lv_obj_set_pos(p_box[idx], 488, y);
  lv_obj_set_style_bg_color(p_box[idx], bg_col, 0);
  lv_obj_set_style_bg_opa(p_box[idx], 255, 0);
  lv_obj_set_style_border_width(p_box[idx], 1, 0);
  lv_obj_set_style_border_color(p_box[idx], gd_col, 0);
  lv_obj_set_style_radius(p_box[idx], 0, 0);
  lv_obj_set_style_pad_all(p_box[idx], 0, 0);  // CRITICAL: Remove default padding
  lv_obj_clear_flag(p_box[idx], LV_OBJ_FLAG_SCROLLABLE);

  lv_obj_t* tl = lv_label_create(p_box[idx]);
  lv_label_set_text(tl, title);
  lv_obj_set_style_text_color(tl, color, 0);
  lv_obj_set_pos(tl, 5, 2);

  const char* init_text[3] = {"--", "--", "--"};
  int y_pos[3] = {18, 36, 54};
  for (int j = 0; j < 3; j++) {
    p_stat[idx][j] = lv_label_create(p_box[idx]);
    lv_label_set_text(p_stat[idx][j], init_text[j]);
    lv_obj_set_style_text_color(p_stat[idx][j], wht_col, 0);
    lv_obj_set_pos(p_stat[idx][j], 5, y_pos[j]);
  }
}

// ============================================================================
// INIT — Called once on boot
// ============================================================================

void radar_ui_init() {
  // Precompute trig
  for (int i = 0; i < 360; i++) {
    float rad = i * 0.0174533f;
    sin_lut[i] = sinf(rad);
    cos_lut[i] = cosf(rad);
  }

  // Colors
  bg_col  = lv_color_hex(0x030A06);
  gd_col  = lv_color_hex(0x005028);
  gf_col  = lv_color_hex(0x002814);
  grn_col = lv_color_hex(0x00FF88);
  amb_col = lv_color_hex(0xFFAA00);
  wht_col = lv_color_hex(0xFFFFFF);
  red_col = lv_color_hex(0xFF3366);
  blu_col = lv_color_hex(0x00AAFF);
  pred_col = lv_color_hex(0x66FFCC);  // Cyan-green for prediction

  scr = lv_scr_act();
  lv_obj_set_style_bg_color(scr, bg_col, 0);

  // --- Static Grid (LVGL objects, drawn once, never redrawn) ---

  // Vertical divider
  lv_obj_t * div = lv_obj_create(scr);
  lv_obj_set_size(div, 1, 480);
  lv_obj_set_pos(div, 480, 0);
  lv_obj_set_style_bg_color(div, gd_col, 0);
  lv_obj_set_style_border_width(div, 0, 0);
  lv_obj_set_style_pad_all(div, 0, 0);

  // Range rings (4 rings at 2m intervals)
  for (int i = 1; i <= 4; i++) {
    int r = i * 50;
    lv_obj_t * ring = lv_obj_create(scr);
    lv_obj_set_size(ring, r * 2, r * 2);
    lv_obj_set_pos(ring, CX - r, CY - r);
    lv_obj_set_style_bg_opa(ring, 0, 0);
    lv_obj_set_style_border_width(ring, 1, 0);
    lv_obj_set_style_border_color(ring, gd_col, 0);
    lv_obj_set_style_radius(ring, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_pad_all(ring, 0, 0);
    lv_obj_clear_flag(ring, LV_OBJ_FLAG_SCROLLABLE);

    lv_obj_t * lbl = lv_label_create(scr);
    lv_label_set_text_fmt(lbl, "%dm", i * 2);
    lv_obj_set_style_text_color(lbl, gd_col, 0);
    lv_obj_set_pos(lbl, CX + 4, CY - r + 2);
  }

  // Vertical crosshair
  lv_obj_t * vert = lv_obj_create(scr);
  lv_obj_set_size(vert, 1, RADAR_R);
  lv_obj_set_pos(vert, CX, CY - RADAR_R);
  lv_obj_set_style_bg_color(vert, gf_col, 0);
  lv_obj_set_style_border_width(vert, 0, 0);
  lv_obj_set_style_pad_all(vert, 0, 0);

  // --- Dynamic Canvas ---
  size_t buf_size = C_WIDTH * C_HEIGHT * sizeof(lv_color_t);
  canvas_buf = (lv_color_t *)heap_caps_malloc(buf_size, MALLOC_CAP_SPIRAM);
  if (canvas_buf) {
    radar_canvas = lv_canvas_create(scr);
    lv_canvas_set_buffer(radar_canvas, canvas_buf, C_WIDTH, C_HEIGHT, LV_IMG_CF_TRUE_COLOR_CHROMA_KEYED);
    lv_obj_set_pos(radar_canvas, 0, 0);
    lv_canvas_fill_bg(radar_canvas, LV_COLOR_CHROMA_KEY, LV_OPA_COVER);

    // Draw static radian lines on canvas (one-time, won't be erased by sweep)
    lv_draw_line_dsc_t cr;
    lv_draw_line_dsc_init(&cr);
    cr.color = gf_col;
    cr.width = 1;
    // 60° left
    lv_point_t pl[2] = {{CX, CY}, {(lv_coord_t)(CX - 100), (lv_coord_t)(CY - 173)}};
    lv_canvas_draw_line(radar_canvas, pl, 2, &cr);
    // 60° right
    lv_point_t pr[2] = {{CX, CY}, {(lv_coord_t)(CX + 100), (lv_coord_t)(CY - 173)}};
    lv_canvas_draw_line(radar_canvas, pr, 2, &cr);
  } else {
    ESP_LOGE("radar_ui", "PSRAM canvas alloc failed! (%d bytes)", buf_size);
  }

  // --- Target Labels (floating over canvas, reused) ---
  lv_color_t t_colors[3] = {grn_col, amb_col, blu_col};
  for (int i = 0; i < 3; i++) {
    t_lbl[i] = lv_label_create(scr);
    lv_obj_set_style_text_color(t_lbl[i], t_colors[i], 0);
    lv_obj_add_flag(t_lbl[i], LV_OBJ_FLAG_HIDDEN);
  }

  // Signal lost label
  sig_lost_lbl = lv_label_create(scr);
  lv_label_set_text(sig_lost_lbl, "SIGNAL LOST");
  lv_obj_set_style_text_color(sig_lost_lbl, red_col, 0);
  lv_obj_set_pos(sig_lost_lbl, CX - 40, CY - 220);

  // --- Right Panel ---
  lv_obj_t* title = lv_label_create(scr);
  lv_label_set_text(title, "LD2450 RADAR");
  lv_obj_set_style_text_color(title, grn_col, 0);
  lv_obj_set_pos(title, 490, 8);

  conn_dot = lv_obj_create(scr);
  lv_obj_set_size(conn_dot, 10, 10);
  lv_obj_set_pos(conn_dot, 770, 18);
  lv_obj_set_style_radius(conn_dot, LV_RADIUS_CIRCLE, 0);
  lv_obj_set_style_bg_color(conn_dot, red_col, 0);
  lv_obj_set_style_border_width(conn_dot, 0, 0);
  lv_obj_set_style_pad_all(conn_dot, 0, 0);

  lv_obj_t* threat_t = lv_label_create(scr);
  lv_label_set_text(threat_t, "SYSTEM THREAT");
  lv_obj_set_style_text_color(threat_t, amb_col, 0);
  lv_obj_set_pos(threat_t, 490, 42);

  lv_obj_t* threat_bg = lv_obj_create(scr);
  lv_obj_set_size(threat_bg, 280, 14);
  lv_obj_set_pos(threat_bg, 490, 60);
  lv_obj_set_style_bg_opa(threat_bg, 0, 0);
  lv_obj_set_style_border_width(threat_bg, 1, 0);
  lv_obj_set_style_border_color(threat_bg, gd_col, 0);

  threat_bar = lv_obj_create(scr);
  lv_obj_set_size(threat_bar, 0, 12);
  lv_obj_set_pos(threat_bar, 491, 61);
  lv_obj_set_style_bg_color(threat_bar, grn_col, 0);
  lv_obj_set_style_border_width(threat_bar, 0, 0);
  lv_obj_set_style_radius(threat_bar, 0, 0);
  lv_obj_set_style_pad_all(threat_bar, 0, 0);

  threat_lbl = lv_label_create(scr);
  lv_label_set_text(threat_lbl, "0%");
  lv_obj_set_style_text_color(threat_lbl, grn_col, 0);
  lv_obj_set_pos(threat_lbl, 630, 78);

  create_panel_box(100, grn_col, "TARGET 1", 0);
  create_panel_box(196, amb_col, "TARGET 2", 1);
  create_panel_box(292, blu_col, "TARGET 3", 2);

  tgt_cnt_lbl = lv_label_create(scr);
  lv_label_set_text(tgt_cnt_lbl, "TARGETS: 0  RANGE: 8m");
  lv_obj_set_style_text_color(tgt_cnt_lbl, gd_col, 0);
  lv_obj_set_pos(tgt_cnt_lbl, 490, 446);

  // Init target state
  for (int i = 0; i < 3; i++) tgt_state[i].reset();

  ESP_LOGI("radar_ui", "Radar UI initialized (canvas %dx%d, %d KB PSRAM)", C_WIDTH, C_HEIGHT, (int)(buf_size/1024));
}

// ============================================================================
// RENDER — Single unified function called every 33ms
// ============================================================================

void radar_ui_update(
    float t1x, float t1y, float t1s, float t1th, bool t1a,
    float t2x, float t2y, float t2s, float t2th, bool t2a,
    float t3x, float t3y, float t3s, float t3th, bool t3a,
    float systhr, int tgtcnt, bool connected) {

  uint32_t frame_start = millis();
  if (!radar_canvas) return;

  // Pack into arrays for loop processing
  float raw_x[3] = {t1x, t2x, t3x};
  float raw_y[3] = {t1y, t2y, t3y};
  float raw_s[3] = {t1s, t2s, t3s};
  float raw_th[3] = {t1th, t2th, t3th};
  bool active[3] = {t1a, t2a, t3a};
  lv_color_t t_colors[3] = {grn_col, amb_col, blu_col};

  // ============================
  // Phase 1: ERASE previous frame
  // ============================

  // Erase old sweep line
  if (old_sweep[1].x != 0 || old_sweep[1].y != 0) {
    canvas_erase_line_seg(old_sweep[0], old_sweep[1], 2);
  }

  // Erase old targets, trails, and prediction arrows
  for (int i = 0; i < 3; i++) {
    TargetState &ts = tgt_state[i];
    // Erase old prediction arrow
    if (ts.old_pred_px >= 0 && ts.old_px >= 0) {
      lv_point_t from = {(lv_coord_t)ts.old_px, (lv_coord_t)ts.old_py};
      lv_point_t to = {(lv_coord_t)ts.old_pred_px, (lv_coord_t)ts.old_pred_py};
      canvas_erase_line_seg(from, to, 1);
      canvas_erase_rect(ts.old_pred_px - 4, ts.old_pred_py - 4, 8, 8);
    }
    // Erase old trails
    for (int j = 0; j < ts.old_trail_count; j++) {
      if (ts.old_trail_x[j] >= 0) {
        canvas_erase_rect(ts.old_trail_x[j] - 4, ts.old_trail_y[j] - 4, 8, 8);
      }
    }
    // Erase old target dot
    if (ts.old_px >= 0) {
      canvas_erase_rect(ts.old_px - 7, ts.old_py - 7, 14, 14);
    }
  }

  // ============================
  // Phase 2: UPDATE state
  // ============================

  uint32_t now = millis();
  for (int i = 0; i < 3; i++) {
    TargetState &ts = tgt_state[i];
    if (active[i]) {
      ts.update(raw_x[i], raw_y[i], now);
    } else if (ts.was_active) {
      ts.reset();
    }
    ts.was_active = active[i];
  }

  // ============================
  // Phase 3: DRAW new frame
  // ============================

  // --- Sweep Line (top semicircle: 0° to 180° in math coords = upper screen) ---
  sw_angle += 2;
  if (sw_angle >= 180) sw_angle = 0;

  int idx = (180 + sw_angle) % 360;  // Map 0-180 → 180-360 in LUT (cos goes from -1 to +1)
  int sx = CX + (int)(RADAR_R * cos_lut[idx]);
  int sy = CY - (int)(RADAR_R * sin_lut[sw_angle]);  // Negative Y = up on screen

  lv_point_t sw_from = {CX, CY};
  lv_point_t sw_to = {(lv_coord_t)sx, (lv_coord_t)sy};

  lv_color_t sw_color = (systhr > 70) ? red_col : (systhr > 40) ? amb_col : grn_col;
  canvas_draw_line_seg(sw_from, sw_to, sw_color, 2);

  old_sweep[0] = sw_from;
  old_sweep[1] = sw_to;

  // --- Targets, Trails, Predictions ---
  for (int i = 0; i < 3; i++) {
    TargetState &ts = tgt_state[i];

    if (!active[i]) {
      ts.old_px = ts.old_py = -1;
      ts.old_pred_px = ts.old_pred_py = -1;
      ts.old_trail_count = 0;
      lv_obj_add_flag(t_lbl[i], LV_OBJ_FLAG_HIDDEN);
      continue;
    }

    // Convert smoothed mm to screen pixels
    int px = CX + (int)(ts.sx * SC);
    int py = CY - (int)(ts.sy * SC);

    // Clamp to canvas
    if (px < 6) px = 6;
    if (px > C_WIDTH - 6) px = C_WIDTH - 6;
    if (py < 6) py = 6;
    if (py > C_HEIGHT - 6) py = C_HEIGHT - 6;

    // --- Draw Trails (oldest first, smaller and dimmer) ---
    int drawn_trails = 0;
    for (int j = 0; j < ts.trail_count; j++) {
      int ti = (ts.trail_head - ts.trail_count + j + TRAIL_LEN) % TRAIL_LEN;
      int tx = ts.trail_x[ti];
      int ty = ts.trail_y[ti];
      if (tx < 0) continue;
      // Fade: oldest = smallest, newest = bigger
      int dot_r = 1 + (j * 2) / TRAIL_LEN;
      lv_color_t fade = gd_col;  // Dim green for trails
      canvas_draw_dot(tx, ty, dot_r, fade);

      ts.old_trail_x[drawn_trails] = tx;
      ts.old_trail_y[drawn_trails] = ty;
      drawn_trails++;
    }
    ts.old_trail_count = drawn_trails;

    // --- Draw Target Dot ---
    lv_color_t dot_color = (raw_th[i] > 60) ? red_col : t_colors[i];
    canvas_draw_dot(px, py, 5, dot_color);

    // --- Draw Prediction Arrow ---
    float pred_x = ts.sx + ts.vx * PRED_TIME;
    float pred_y = ts.sy + ts.vy * PRED_TIME;
    int ppx = CX + (int)(pred_x * SC);
    int ppy = CY - (int)(pred_y * SC);

    // Only draw if prediction is meaningfully different from current
    int dx = ppx - px;
    int dy = ppy - py;
    if (dx * dx + dy * dy > 100) {  // More than ~10px away
      // Clamp prediction to canvas
      if (ppx < 4) ppx = 4;
      if (ppx > C_WIDTH - 4) ppx = C_WIDTH - 4;
      if (ppy < 4) ppy = 4;
      if (ppy > C_HEIGHT - 4) ppy = C_HEIGHT - 4;

      lv_point_t arrow_from = {(lv_coord_t)px, (lv_coord_t)py};
      lv_point_t arrow_to = {(lv_coord_t)ppx, (lv_coord_t)ppy};
      canvas_draw_line_seg(arrow_from, arrow_to, pred_col, 1);
      canvas_draw_dot(ppx, ppy, 3, pred_col);

      ts.old_pred_px = ppx;
      ts.old_pred_py = ppy;
    } else {
      ts.old_pred_px = ts.old_pred_py = -1;
    }

    // Push current position to trail ring buffer
    ts.push_trail(px, py);

    // Store for next frame erase
    ts.old_px = px;
    ts.old_py = py;

    // --- Update floating label ---
    int dist_i = (int)(sqrtf(ts.sx * ts.sx + ts.sy * ts.sy) / 100.0f);  // decimeters
    lv_label_set_text_fmt(t_lbl[i], "T%d %d.%dm", i + 1, dist_i / 10, dist_i % 10);
    lv_obj_set_pos(t_lbl[i], px + 10, py - 8);
    lv_obj_clear_flag(t_lbl[i], LV_OBJ_FLAG_HIDDEN);
  }

  // ============================
  // Phase 4: Right Panel Updates (always refresh)
  // ============================

  // Connection status
  if (connected) {
    lv_obj_add_flag(sig_lost_lbl, LV_OBJ_FLAG_HIDDEN);
    lv_obj_set_style_bg_color(conn_dot, grn_col, 0);
  } else {
    lv_obj_clear_flag(sig_lost_lbl, LV_OBJ_FLAG_HIDDEN);
    lv_obj_set_style_bg_color(conn_dot, red_col, 0);
  }

  // Threat bar — always update
  int bar_w = (int)(systhr * 2.78f);
  if (bar_w < 0) bar_w = 0;
  if (bar_w > 278) bar_w = 278;
  lv_obj_set_size(threat_bar, bar_w, 12);
  lv_color_t bc = (systhr > 70) ? red_col : (systhr > 40) ? amb_col : grn_col;
  lv_obj_set_style_bg_color(threat_bar, bc, 0);
  lv_label_set_text_fmt(threat_lbl, "%d%%", (int)systhr);
  lv_obj_set_style_text_color(threat_lbl, bc, 0);

  // Target count
  lv_label_set_text_fmt(tgt_cnt_lbl, "TARGETS: %d  RANGE: 8m", tgtcnt);

  // Target info panels — always update
  for (int i = 0; i < 3; i++) {
    if (active[i]) {
      lv_obj_set_style_border_color(p_box[i], t_colors[i], 0);
      lv_label_set_text_fmt(p_stat[i][0], "X %d  Y %d mm", (int)raw_x[i], (int)raw_y[i]);
      int dist_dm = (int)(sqrtf(raw_x[i] * raw_x[i] + raw_y[i] * raw_y[i]) / 100.0f);
      int spd_100 = (int)(raw_s[i] * 100.0f);
      lv_label_set_text_fmt(p_stat[i][1], "SPD %d.%02d  DIST %d.%dm", spd_100/100, spd_100%100, dist_dm/10, dist_dm%10);
      lv_label_set_text_fmt(p_stat[i][2], "THREAT %d%%", (int)raw_th[i]);
    } else {
      lv_obj_set_style_border_color(p_box[i], gd_col, 0);
      lv_label_set_text(p_stat[i][0], "NO TARGET");
      lv_label_set_text(p_stat[i][1], "");
      lv_label_set_text(p_stat[i][2], "");
    }
  }

  // ============================
  // Profiling + Diagnostics (every ~1 second)
  // ============================
  static int prof_ctr = 0;
  if (++prof_ctr >= 30) {
    ESP_LOGI("radar_ui", "Frame: %dms | thr=%d cnt=%d conn=%d",
      (int)(millis() - frame_start), (int)systhr, tgtcnt, (int)connected);
    ESP_LOGI("radar_ui", "T1[%s] x=%d y=%d s=%d th=%d",
      active[0]?"ON":"--", (int)raw_x[0], (int)raw_y[0], (int)(raw_s[0]*100), (int)raw_th[0]);
    ESP_LOGI("radar_ui", "T2[%s] x=%d y=%d | T3[%s] x=%d y=%d",
      active[1]?"ON":"--", (int)raw_x[1], (int)raw_y[1],
      active[2]?"ON":"--", (int)raw_x[2], (int)raw_y[2]);
    prof_ctr = 0;
  }
}
