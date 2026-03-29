#pragma once
#include <math.h>
#include <algorithm>

// Standalone Kalman-filtered target analytics
// Adapted from ESP32_LD2450/target_analytics.h (no ESPHome dependencies)

const float Q_pos = 20.0f;
const float Q_vel = 0.4f;
const float R_obs = 350.0f;
const float EMA_alpha = 0.18f;

class TargetAnalytics {
public:
    float x = 0, v_x = 0, P00_x = 1000, P01_x = 0, P11_x = 100;
    float y = 0, v_y = 0, P00_y = 1000, P01_y = 0, P11_y = 100;
    float fil_spd = 0, threat_score = 0;
    bool loitering = false, initialized = false;
    float anchor_x = 0, anchor_y = 0;
    uint32_t dwell_start = 0;

    void reset() {
        initialized = false;
        fil_spd = 0; threat_score = 0; loitering = false;
    }

    void update(float raw_x, float raw_y, uint32_t dt_ms, uint32_t now_ms) {
        if (!initialized || dt_ms > 1000) {
            x = raw_x; y = raw_y; v_x = 0; v_y = 0;
            P00_x = 1000; P01_x = 0; P11_x = 100;
            P00_y = 1000; P01_y = 0; P11_y = 100;
            fil_spd = 0;
            anchor_x = raw_x; anchor_y = raw_y;
            dwell_start = now_ms;
            initialized = true;
            return;
        }
        // Kalman X
        x += v_x * dt_ms;
        P00_x += 2*P01_x*dt_ms + P11_x*dt_ms*dt_ms + Q_pos;
        P01_x += P11_x*dt_ms; P11_x += Q_vel;
        float S = P00_x + R_obs;
        float K0 = P00_x/S, K1 = P01_x/S;
        float inn = raw_x - x;
        x += K0*inn; v_x += K1*inn;
        P00_x -= K0*P00_x; P01_x -= K0*P01_x; P11_x -= K1*P01_x;
        if (P00_x < 1) P00_x = 1; if (P11_x < 0.01f) P11_x = 0.01f;

        // Kalman Y
        y += v_y * dt_ms;
        P00_y += 2*P01_y*dt_ms + P11_y*dt_ms*dt_ms + Q_pos;
        P01_y += P11_y*dt_ms; P11_y += Q_vel;
        S = P00_y + R_obs; K0 = P00_y/S; K1 = P01_y/S;
        inn = raw_y - y;
        y += K0*inn; v_y += K1*inn;
        P00_y -= K0*P00_y; P01_y -= K0*P01_y; P11_y -= K1*P01_y;
        if (P00_y < 1) P00_y = 1; if (P11_y < 0.01f) P11_y = 0.01f;

        // EMA speed (mm/ms = m/s)
        float cur_spd = sqrtf(v_x*v_x + v_y*v_y);
        fil_spd = (1.0f - EMA_alpha)*fil_spd + EMA_alpha*cur_spd;

        // Threat score
        float dist = sqrtf(x*x + y*y);
        float t_spd = std::min(35.0f, fil_spd * 14.0f);
        float t_app = 0;
        if (dist > 100 && fil_spd > 0.05f) {
            float dot = (v_x*(-x/dist) + v_y*(-y/dist)) / fil_spd;
            t_app = std::max(0.0f, dot) * 40.0f;
        }
        float t_prox = std::max(0.0f, 25.0f*(1.0f - dist/7000.0f));
        threat_score = std::min(100.0f, t_spd + t_app + t_prox);

        // Loitering detection
        float d_anc = sqrtf((x-anchor_x)*(x-anchor_x) + (y-anchor_y)*(y-anchor_y));
        if (d_anc > 600) { anchor_x = x; anchor_y = y; dwell_start = now_ms; loitering = false; }
        else { loitering = (now_ms - dwell_start >= 12000); }
    }
};

static TargetAnalytics target_analytics[3];
