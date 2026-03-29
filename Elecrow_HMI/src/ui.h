#ifndef UI_H
#define UI_H

#ifdef __cplusplus
extern "C" {
#endif

void ui_init(void);
void ui_tick(void); // Call this frequently to update the sweep animation
void ui_update_radar_ip(const char* ip);
void ui_process_sse_data(const char* json_str);

#ifdef __cplusplus
} /*extern "C"*/
#endif

#endif
