#include "ui.h"
#include <lvgl.h>
#include <ArduinoJson.h>

LV_FONT_DECLARE(lv_font_montserrat_10);
LV_FONT_DECLARE(lv_font_montserrat_12);
LV_FONT_DECLARE(lv_font_montserrat_14);


#define COLOR_BG lv_color_hex(0x030a06)
#define COLOR_PANEL lv_color_hex(0x001209)
#define COLOR_GREEN lv_color_hex(0x00ff88)
#define COLOR_RED lv_color_hex(0xff3366)
#define COLOR_ORANGE lv_color_hex(0xffaa00)
#define COLOR_BLUE lv_color_hex(0x00aaff)
#define COLOR_WHITE lv_color_hex(0xffffff)
#define COLOR_BORDER lv_color_hex(0x002e1c) // rgba(0,255,136,0.18)

static lv_obj_t *main_scr;
static lv_obj_t *radar_cont;
static lv_obj_t *sidebar;

// Labels for targets
static lv_obj_t *t_data[3], *t_threat_bar[3], *t_cls[3], *t_alert[3];

// Stats
static lv_obj_t *lbl_sys_threat_val, *bar_sys_threat;
static uint8_t sys_threat = 0;

// Target points on radar
static lv_obj_t *target_dots[3];
static lv_obj_t *target_labels[3];

struct TargetConfig {
    float x = 0, y = 0, speed = 0;
    String dir = "—";
    uint32_t ts = 0;
    int threat = 0;
    String cls = "ABSENT", alert = "CLEAR";
};

static TargetConfig T[3];

void create_header() {
    lv_obj_t *header = lv_obj_create(main_scr);
    lv_obj_set_size(header, 800, 30);
    lv_obj_set_pos(header, 0, 0);
    lv_obj_set_style_bg_color(header, COLOR_PANEL, 0);
    lv_obj_set_style_border_color(header, COLOR_BORDER, 0);
    lv_obj_set_style_border_width(header, 1, 0);
    lv_obj_set_style_border_side(header, LV_BORDER_SIDE_BOTTOM, 0);
    lv_obj_set_style_pad_all(header, 5, 0);
    lv_obj_set_style_radius(header, 0, 0);

    lv_obj_t *logo = lv_label_create(header);
    lv_label_set_text(logo, "LD2450 RADAR");
    lv_obj_set_style_text_color(logo, COLOR_GREEN, 0);
    lv_obj_set_style_text_font(logo, &lv_font_montserrat_14, 0);
    lv_obj_align(logo, LV_ALIGN_LEFT_MID, 5, 0);

    lv_obj_t *sdot = lv_obj_create(header);
    lv_obj_set_size(sdot, 8, 8);
    lv_obj_set_style_radius(sdot, LV_RADIUS_CIRCLE, 0);
    lv_obj_set_style_bg_color(sdot, COLOR_RED, 0);
    lv_obj_align(sdot, LV_ALIGN_RIGHT_MID, -120, 0);
}

void draw_radar_base() {
    radar_cont = lv_obj_create(main_scr);
    lv_obj_set_size(radar_cont, 585, 430);
    lv_obj_set_pos(radar_cont, 0, 30);
    lv_obj_set_style_bg_color(radar_cont, COLOR_BG, 0);
    lv_obj_set_style_border_width(radar_cont, 0, 0);
    lv_obj_set_style_radius(radar_cont, 0, 0);

    int max_radius = 420;

    for (int d = 1000; d <= 8000; d += 1000) {
        int r = (d / 8000.0) * max_radius;
        lv_obj_t *arc = lv_arc_create(radar_cont);
        lv_obj_set_size(arc, r * 2, r * 2);
        lv_obj_align(arc, LV_ALIGN_BOTTOM_MID, 0, r);
        lv_arc_set_angles(arc, 180, 360);
        lv_arc_set_bg_angles(arc, 180, 360);
        lv_obj_set_style_arc_width(arc, d % 2000 == 0 ? 2 : 1, 0);
        lv_obj_set_style_arc_color(arc, COLOR_GREEN, 0);
        lv_obj_set_style_arc_opa(arc, d % 2000 == 0 ? 50 : 20, 0);
        lv_obj_remove_style(arc, NULL, LV_PART_KNOB);
        lv_obj_clear_flag(arc, LV_OBJ_FLAG_CLICKABLE);

        if (d % 2000 == 0) {
            lv_obj_t *lbl = lv_label_create(radar_cont);
            lv_label_set_text_fmt(lbl, "%dm", d / 1000);
            lv_obj_set_style_text_color(lbl, COLOR_GREEN, 0);
            lv_obj_set_style_text_opa(lbl, 100, 0);
            lv_obj_align(lbl, LV_ALIGN_BOTTOM_MID, 0, -r - 10);
        }
    }

    for(int i=0; i<3; i++) {
        target_dots[i] = lv_obj_create(radar_cont);
        lv_obj_set_size(target_dots[i], 14, 14);
        lv_obj_set_style_radius(target_dots[i], LV_RADIUS_CIRCLE, 0);
        lv_obj_set_style_bg_color(target_dots[i], i==0 ? COLOR_GREEN : (i==1 ? COLOR_ORANGE : COLOR_BLUE), 0);
        lv_obj_add_flag(target_dots[i], LV_OBJ_FLAG_HIDDEN);
        
        target_labels[i] = lv_label_create(radar_cont);
        lv_label_set_text_fmt(target_labels[i], "T%d", i+1);
        lv_obj_set_style_text_color(target_labels[i], i==0 ? COLOR_GREEN : (i==1 ? COLOR_ORANGE : COLOR_BLUE), 0);
        lv_obj_add_flag(target_labels[i], LV_OBJ_FLAG_HIDDEN);
    }
}

void create_target_card(lv_obj_t *parent, int i) {
    lv_obj_t *card = lv_obj_create(parent);
    lv_obj_set_width(card, 195);
    lv_obj_set_height(card, LV_SIZE_CONTENT);
    lv_obj_set_style_bg_color(card, lv_color_hex(0x001a0d), 0);
    lv_obj_set_style_border_color(card, COLOR_BORDER, 0);
    lv_obj_set_style_border_width(card, 1, 0);
    lv_obj_set_style_pad_all(card, 8, 0);

    lv_color_t tc = i == 0 ? COLOR_GREEN : (i == 1 ? COLOR_ORANGE : COLOR_BLUE);

    lv_obj_t *header = lv_label_create(card);
    lv_label_set_text_fmt(header, "TARGET %d", i+1);
    lv_obj_set_style_text_color(header, tc, 0);
    lv_obj_set_style_text_font(header, &lv_font_montserrat_12, 0);

    t_cls[i] = lv_label_create(card);
    lv_label_set_text(t_cls[i], "ABSENT");
    lv_obj_set_style_text_color(t_cls[i], tc, 0);
    lv_obj_align(t_cls[i], LV_ALIGN_TOP_RIGHT, 0, 0);

    t_data[i] = lv_label_create(card);
    lv_label_set_text(t_data[i], "X: — mm  Y: — mm\nSPD: —   DIR: —");
    lv_obj_set_style_text_color(t_data[i], COLOR_GREEN, 0);
    lv_obj_set_style_text_font(t_data[i], &lv_font_montserrat_10, 0);
    lv_obj_align(t_data[i], LV_ALIGN_TOP_LEFT, 0, 20);

    t_threat_bar[i] = lv_bar_create(card);
    lv_obj_set_size(t_threat_bar[i], 180, 6);
    lv_bar_set_range(t_threat_bar[i], 0, 100);
    lv_bar_set_value(t_threat_bar[i], 0, LV_ANIM_OFF);
    lv_obj_set_style_bg_color(t_threat_bar[i], tc, LV_PART_INDICATOR);
    lv_obj_align(t_threat_bar[i], LV_ALIGN_TOP_LEFT, 0, 50);

    t_alert[i] = lv_label_create(card);
    lv_label_set_text(t_alert[i], "ALERT: CLEAR");
    lv_obj_set_style_text_color(t_alert[i], COLOR_GREEN, 0);
    lv_obj_set_style_text_font(t_alert[i], &lv_font_montserrat_10, 0);
    lv_obj_align(t_alert[i], LV_ALIGN_TOP_LEFT, 0, 65);
}

void create_sidebar() {
    sidebar = lv_obj_create(main_scr);
    lv_obj_set_size(sidebar, 215, 430);
    lv_obj_set_pos(sidebar, 585, 30);
    lv_obj_set_style_bg_color(sidebar, COLOR_PANEL, 0);
    lv_obj_set_style_border_color(sidebar, COLOR_BORDER, 0);
    lv_obj_set_style_border_width(sidebar, 1, 0);
    lv_obj_set_style_border_side(sidebar, LV_BORDER_SIDE_LEFT, 0);
    lv_obj_set_style_pad_all(sidebar, 5, 0);
    lv_obj_set_style_radius(sidebar, 0, 0);
    lv_obj_set_flex_flow(sidebar, LV_FLEX_FLOW_COLUMN);
    lv_obj_set_flex_align(sidebar, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER, LV_FLEX_ALIGN_CENTER);

    lv_obj_t *t_title = lv_label_create(sidebar);
    lv_label_set_text(t_title, "SYSTEM THREAT");
    lv_obj_set_style_text_color(t_title, COLOR_ORANGE, 0);
    lv_obj_set_style_text_font(t_title, &lv_font_montserrat_10, 0);

    bar_sys_threat = lv_bar_create(sidebar);
    lv_obj_set_size(bar_sys_threat, 190, 14);
    lv_bar_set_range(bar_sys_threat, 0, 100);
    lv_bar_set_value(bar_sys_threat, 0, LV_ANIM_OFF);
    lv_obj_set_style_bg_color(bar_sys_threat, COLOR_GREEN, LV_PART_INDICATOR);

    lbl_sys_threat_val = lv_label_create(sidebar);
    lv_label_set_text(lbl_sys_threat_val, "0%");
    lv_obj_set_style_text_color(lbl_sys_threat_val, COLOR_GREEN, 0);

    lv_obj_t *tar_title = lv_label_create(sidebar);
    lv_label_set_text(tar_title, "TARGETS");
    lv_obj_set_style_text_color(tar_title, COLOR_ORANGE, 0);
    lv_obj_set_style_text_font(tar_title, &lv_font_montserrat_10, 0);
    lv_obj_set_style_pad_top(tar_title, 10, 0);

    for(int i=0; i<3; i++) {
        create_target_card(sidebar, i);
    }
}

void create_footer() {
    lv_obj_t *footer = lv_obj_create(main_scr);
    lv_obj_set_size(footer, 800, 20);
    lv_obj_set_pos(footer, 0, 460);
    lv_obj_set_style_bg_color(footer, COLOR_PANEL, 0);
    lv_obj_set_style_border_color(footer, COLOR_BORDER, 0);
    lv_obj_set_style_border_width(footer, 1, 0);
    lv_obj_set_style_border_side(footer, LV_BORDER_SIDE_TOP, 0);
    lv_obj_set_style_pad_all(footer, 2, 0);
    lv_obj_set_style_radius(footer, 0, 0);

    lv_obj_t *lbl = lv_label_create(footer);
    lv_label_set_text(lbl, "LD2450 RADAR + ANALYTICS  |  RANGE ±4m × 8m");
    lv_obj_set_style_text_color(lbl, COLOR_GREEN, 0);
    lv_obj_set_style_text_opa(lbl, 150, 0);
    lv_obj_set_style_text_font(lbl, &lv_font_montserrat_10, 0);
    lv_obj_align(lbl, LV_ALIGN_LEFT_MID, 5, 0);
}

extern "C" void ui_init(void) {
    main_scr = lv_obj_create(NULL);
    lv_obj_set_style_bg_color(main_scr, COLOR_BG, 0);
    lv_scr_load(main_scr);

    create_header();
    draw_radar_base();
    create_sidebar();
    create_footer();
}

extern "C" void ui_tick(void) {
    uint32_t now = lv_tick_get();

    for(int i=0; i<3; i++) {
        bool active = (now - T[i].ts < 3500) && (T[i].ts != 0) && (T[i].x != 0 || T[i].y != 0) && T[i].cls != "OFF";
        
        if (!active) {
            lv_obj_add_flag(target_dots[i], LV_OBJ_FLAG_HIDDEN);
            lv_obj_add_flag(target_labels[i], LV_OBJ_FLAG_HIDDEN);
            lv_label_set_text(t_cls[i], "ABSENT");
            lv_label_set_text(t_data[i], "X: — mm  Y: — mm\nSPD: —   DIR: —");
            lv_label_set_text(t_alert[i], "ALERT: CLEAR");
            lv_bar_set_value(t_threat_bar[i], 0, LV_ANIM_OFF);
        } else {
            lv_obj_clear_flag(target_dots[i], LV_OBJ_FLAG_HIDDEN);
            lv_obj_clear_flag(target_labels[i], LV_OBJ_FLAG_HIDDEN);
            
            lv_label_set_text(t_cls[i], T[i].cls.c_str());
            lv_label_set_text_fmt(t_data[i], "X: %d mm  Y: %d mm\nSPD: %.1f m/s", (int)T[i].x, (int)T[i].y, T[i].speed);
            lv_label_set_text_fmt(t_alert[i], "ALERT: %s", T[i].alert.c_str());
            lv_bar_set_value(t_threat_bar[i], T[i].threat, LV_ANIM_OFF);
            
            int center_x = 585 / 2;
            int center_y = 430;
            int max_radius = 420;

            int px = center_x + (T[i].x / 4000.0) * (max_radius/2);
            int py = center_y - (T[i].y / 8000.0) * max_radius;

            lv_obj_set_pos(target_dots[i], px - 7, py - 7);
            lv_obj_set_pos(target_labels[i], px + 10, py - 10);
        }
    }
}

extern "C" void ui_update_radar_ip(const char* ip) {
    // 
}

extern "C" void ui_process_sse_data(const char* json_str) {
    DynamicJsonDocument doc(512);
    DeserializationError error = deserializeJson(doc, json_str);
    if (error) return;

    String id = doc["id"].as<String>();
    float val = doc["value"].as<float>();
    String str = doc["state"].as<String>();
    uint32_t now = lv_tick_get();

    int idx = -1;
    if (id.indexOf("target1") >= 0 || id.indexOf("target_1") >= 0) idx = 0;
    else if (id.indexOf("target2") >= 0 || id.indexOf("target_2") >= 0) idx = 1;
    else if (id.indexOf("target3") >= 0 || id.indexOf("target_3") >= 0) idx = 2;

    if (idx >= 0) {
        if (id.endsWith("_x")) T[idx].x = val;
        else if (id.endsWith("_y")) T[idx].y = val;
        else if (id.endsWith("_speed")) T[idx].speed = val;
        else if (id.endsWith("_direction")) T[idx].dir = str.length() > 0 ? str : "—";
        else if (id.endsWith("_threat")) T[idx].threat = (int)val;
        else if (id.endsWith("_ml_class")) T[idx].cls = str;
        else if (id.endsWith("_alert")) T[idx].alert = str;
        
        T[idx].ts = now;
    } 
    else if (id.indexOf("system_threat") >= 0) {
        sys_threat = (uint8_t)val;
        lv_bar_set_value(bar_sys_threat, sys_threat, LV_ANIM_ON);
        lv_label_set_text_fmt(lbl_sys_threat_val, "%d%%", sys_threat);
        lv_color_t color = sys_threat > 70 ? COLOR_RED : (sys_threat > 40 ? COLOR_ORANGE : COLOR_GREEN);
        lv_obj_set_style_bg_color(bar_sys_threat, color, LV_PART_INDICATOR);
        lv_obj_set_style_text_color(lbl_sys_threat_val, color, 0);
    }
}
