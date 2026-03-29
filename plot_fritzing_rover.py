import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Canvas Setup ---
fig, ax = plt.subplots(figsize=(24, 16), dpi=200)
ax.set_facecolor('#ffffff')
ax.set_xlim(0, 200)
ax.set_ylim(0, 150)
ax.axis('off')

# --- Grid Background ---
for x in range(0, 200, 2): ax.plot([x, x], [0, 150], color='#fcfcfc', lw=0.8, zorder=0)
for y in range(0, 150, 2): ax.plot([0, 200], [y, y], color='#fcfcfc', lw=0.8, zorder=0)

# --- 90-DEGREE ORTHOGONAL WIRE ROUTING ---
def draw_poly(pts, color, lw=2.5):
    # White background stroke prevents visual overlaps
    x, y = zip(*pts)
    ax.plot(x, y, color='#ffffff', linewidth=lw+3.5, zorder=1, solid_capstyle='round', solid_joinstyle='round')
    # Colored Wire
    ax.plot(x, y, color=color, linewidth=lw, zorder=2, solid_capstyle='round', solid_joinstyle='round')
    # Solder pads at ends
    ax.add_patch(patches.Circle(pts[0], 0.7, facecolor=color, edgecolor='#333', lw=0.5, zorder=4))
    ax.add_patch(patches.Circle(pts[-1], 0.7, facecolor=color, edgecolor='#333', lw=0.5, zorder=4))

# --- Components ---
def draw_nodemcu(x, y):
    w, h = 34, 22
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5", facecolor='#196F3D', edgecolor='#0F4525', lw=2, zorder=3))
    ax.add_patch(patches.Rectangle((x+w/2-3, y+h-4), 6, 5, facecolor='#ecf0f1', edgecolor='#999', zorder=3))
    ax.add_patch(patches.Rectangle((x+4, y+6), w-8, 10, facecolor='#111', zorder=3))
    ax.text(x+w/2, y+h/2, "ESP8266 NodeMCU\n(Rover Control)", color='#eee', ha='center', va='center', fontweight='bold', fontsize=8, zorder=4)
    pins = {}
    for i, p in enumerate(["D0","D1","D2","D3","D4","3V","GND","D5","D6","RX","TX","VIN"]):
        px = x + 2 + (i * 2.5); py = y + 1
        ax.add_patch(patches.Circle((px, py), 0.6, color='gold', zorder=4))
        ax.text(px, py+2, p, color='white', ha='center', fontsize=5, rotation=90, zorder=4); pins[p] = (px, py)
    for i, p in enumerate(["A0","RSV","SD3","CMD","CLK","EN","RST"]):
        px = x + 2 + (i * 2.5); py = y + h - 1
        ax.add_patch(patches.Circle((px, py), 0.6, color='gold', zorder=4))
        ax.text(px, py-2, p, color='white', ha='center', fontsize=5, rotation=90, zorder=4)
    return pins

def draw_esp32(x, y):
    w, h = 36, 24
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5", facecolor='#151515', edgecolor='#000', lw=2, zorder=3))
    ax.add_patch(patches.Rectangle((x+w/2-3, y+h-4), 6, 5, facecolor='#ecf0f1', edgecolor='#999', zorder=3))
    ax.add_patch(patches.Rectangle((x+5, y+6), w-10, 12, facecolor='#d5dbdb', edgecolor='#b2babb', lw=1, zorder=3))
    ax.text(x+w/2, y+h/2, "ESP32 Node\n(Radar Logic)", color='#111', ha='center', va='center', fontweight='bold', fontsize=8, zorder=4)
    pins = {}
    for i, p in enumerate(["3V3","EN","VP","VN","34","35","32","33","25","26","27","14","12","13","GND","VIN"]): # left
        px = x + 1.5 + (i * 2.2); py = y + 1
        ax.add_patch(patches.Circle((px, py), 0.6, color='gold', zorder=4))
        ax.text(px, py+2, p, color='white', ha='center', fontsize=5, rotation=90, zorder=4); pins[p] = (px, py)
    for i, p in enumerate(["D23","D22","TX0","RX0","D21","D19","D18","D5","TX2","RX2","D4","D2","D15","GND_R","3V3_R"]): # right
        px = x + 1.5 + (i * 2.2); py = y + h - 1
        ax.add_patch(patches.Circle((px, py), 0.6, color='gold', zorder=4))
        ax.text(px, py-2, p, color='white', ha='center', fontsize=5, rotation=90, zorder=4); pins[p] = (px, py)
    return pins

def draw_hw354(x, y):
    w, h = 30, 30
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5", facecolor='#c0392b', edgecolor='#922b21', lw=2, zorder=3))
    ax.add_patch(patches.Rectangle((x+4, y+6), w-8, 14, facecolor='#212f3c', zorder=3))
    ax.text(x+w/2, y+h/2, "HW-354\nH-BRIDGE", color='#f1c40f', ha='center', va='center', fontsize=8, fontweight='bold', zorder=4)
    ax.add_patch(patches.Rectangle((x+8, y), 14, 4, facecolor='#2980b9', zorder=3))
    ax.add_patch(patches.Rectangle((x, y+18), 4, 10, facecolor='#2980b9', zorder=3))
    ax.add_patch(patches.Rectangle((x+w-4, y+18), 4, 10, facecolor='#2980b9', zorder=3))
    ax.text(x+10, y+2, "12V", color='white', fontsize=6, zorder=4)
    ax.text(x+15, y+2, "GND", color='white', fontsize=6, zorder=4)
    ax.text(x+20, y+2, "5V", color='white', fontsize=6, zorder=4)
    ax.add_patch(patches.Rectangle((x+16, y+5), 10, 2, facecolor='#111', zorder=3))
    return {
        "12V": (x+10, y+2), "GND": (x+15, y+2), "5V_OUT": (x+20, y+2),
        "OUT1": (x+2, y+26), "OUT2": (x+2, y+20), "OUT3": (x+w-2, y+26), "OUT4": (x+w-2, y+20),
        "IN1": (x+17, y+6), "IN2": (x+19.5, y+6), "IN3": (x+22, y+6), "IN4": (x+24.5, y+6)
    }

def draw_12v_motor(x, y, flip=False):
    w, h = 22, 12
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2", facecolor='#95a5a6', edgecolor='#7f8c8d', lw=2, zorder=3))
    ax.add_patch(patches.Rectangle((x+w/2-2, y-2), 4, h+4, facecolor='#34495e', zorder=2))
    ax.add_patch(patches.Rectangle((x+w if not flip else x-4, y+5), 4, 2, facecolor='#ecf0f1', edgecolor='#bdc3c7', lw=1, zorder=3))
    ax.text(x+w/2, y+h/2, "12V Geared", ha='center', va='center', fontsize=6, fontweight='bold', color='white', zorder=4)
    return {"+": (x, y+9) if not flip else (x+w, y+9), "-": (x, y+3) if not flip else (x+w, y+3)}

def draw_sensor(x, y, name, pins_list):
    w, h = 18, 14
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2", facecolor='#111', edgecolor='#333', zorder=3))
    ax.text(x+w/2, y+h/2, name, color='white', ha='center', va='center', fontsize=7, fontweight='bold', zorder=4)
    pins = {}
    for i, p in enumerate(pins_list):
        px = x + 3 + (i * 4); py = y + 1
        ax.add_patch(patches.Circle((px, py), 0.6, color='gold', zorder=4))
        pins[p] = (px, py)
        ax.text(px, py+2, p, color='white', ha='center', fontsize=5, zorder=4)
    return pins

def draw_camera(x, y):
    w, h = 16, 16
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2", facecolor='#1E8449', edgecolor='#145A32', lw=2, zorder=3))
    ax.add_patch(patches.Circle((x+w/2, y+h/2), 5, facecolor='#111', edgecolor='#444', lw=2, zorder=4))
    ax.text(x+w/2, y+h+3, "Analog FPV", ha='center', fontsize=7, fontweight='bold', zorder=4)
    return {"VCC": (x+4, y-1), "GND": (x+8, y-1), "VID": (x+12, y-1)}

def draw_vtx(x, y):
    w, h = 16, 12
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2", facecolor='#c0392b', edgecolor='#922b21', lw=2, zorder=3))
    ax.plot([x+8, x+8], [y+12, y+24], color='#e67e22', lw=2.5, zorder=2) # Antenna
    ax.add_patch(patches.Circle((x+8, y+24), 1.5, facecolor='#111', zorder=3))
    ax.text(x+w/2, y+h/2, "5.8GHz VTX", color='white', ha='center', va='center', fontsize=6, fontweight='bold', zorder=4)
    return {"VCC": (x+4, y-1), "GND": (x+8, y-1), "VID": (x+12, y-1)}

def draw_battery(x, y):
    w, h = 30, 20
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2", facecolor='#34495E', edgecolor='#2C3E50', zorder=3))
    ax.add_patch(patches.Rectangle((x, y+4), 3, h-8, facecolor='#F1C40F', zorder=4))
    ax.text(x+w/2+2, y+h/2, "2S LiPo\n(7.4V)", ha='center', va='center', fontsize=9, color='white', fontweight='bold', zorder=4)
    return {"+": (x+w, y+13), "-": (x+w, y+7)}

# --- 1. PLACE COMPONENTS EXTREMELY FAR APART ---
# Left 
pin_m_tl = draw_12v_motor(10, 60, flip=False)
pin_m_bl = draw_12v_motor(10, 20, flip=False)
pin_bat  = draw_battery(12, 100)

# Top 
pin_cam  = draw_camera(50, 130)
pin_node = draw_nodemcu(50, 95)
pin_rx   = draw_sensor(15, 130, "ES900X", ["5V","GND","RX","TX"])

# Right 
pin_m_tr = draw_12v_motor(168, 60, flip=True)
pin_m_br = draw_12v_motor(168, 20, flip=True)
pin_vtx  = draw_vtx(145, 130)
pin_ld   = draw_sensor(175, 130, "LD2450", ["VCC","GND","TX","RX"])
pin_esp32= draw_esp32(130, 95)

# Center 
pin_drv  = draw_hw354(85, 30)

# --- 2. EXACT RIGID ORTHOGONAL WIRING TRACES ---
C_VCC = '#e74c3c'  
C_3V3 = '#f39c12'  
C_GND = '#2c3e50'  
C_TX  = '#27ae60'  
C_PWM = '#8e44ad'  

# A. Power Network (Battery -> HW-354 12V, NodeMCU VIN, ESP32 VIN, CAM/VTX)
b_vcc = pin_bat["+"]  # (42, 113)
b_gnd = pin_bat["-"]  # (42, 107)

# Power Buses
BUS_VCC_Y = 16
BUS_GND_Y = 12

draw_poly([b_vcc, (46, b_vcc[1]), (46, BUS_VCC_Y), (pin_drv["12V"][0], BUS_VCC_Y), pin_drv["12V"]], C_VCC)
draw_poly([b_gnd, (48, b_gnd[1]), (48, BUS_GND_Y), (pin_drv["GND"][0], BUS_GND_Y), pin_drv["GND"]], C_GND)

vin_node = pin_node["VIN"] # (50+2+11*2.5=79.5, 96)
draw_poly([vin_node, (vin_node[0], 25), (46, 25), (46, BUS_VCC_Y)], C_VCC)  # Drops down safely below M_TL
gnd_node = pin_node["GND"] # (50+2+6*2.5=67, 96)
draw_poly([gnd_node, (gnd_node[0], 23), (48, 23), (48, BUS_GND_Y)], C_GND)

vin_esp = pin_esp32["VIN"] # (130+1.5+15*2.2=164.5, 96)
draw_poly([vin_esp, (vin_esp[0], 25), (46, 25)], C_VCC)  
gnd_esp = pin_esp32["GND"] # (130+1.5+14*2.2=162.3, 96)
draw_poly([gnd_esp, (gnd_esp[0], 23), (48, 23)], C_GND)

# FPV power tapped from Battery explicitly UP
draw_poly([b_vcc, (42, 126), (pin_cam["VCC"][0], 126), pin_cam["VCC"]], C_VCC)
draw_poly([b_gnd, (44, 124), (pin_cam["GND"][0], 124), pin_cam["GND"]], C_GND)
draw_poly([(pin_cam["VCC"][0], 126), (pin_vtx["VCC"][0], 126), pin_vtx["VCC"]], C_VCC)
draw_poly([(pin_cam["GND"][0], 124), (pin_vtx["GND"][0], 124), pin_vtx["GND"]], C_GND)
draw_poly([pin_cam["VID"], (pin_cam["VID"][0], 122), (pin_vtx["VID"][0], 122), pin_vtx["VID"]], '#f1c40f')

# B. Internal 3.3V Logic 
v3_node = pin_node["3V"] # (50+2+5*2.5=64.5, 96)
draw_poly([v3_node, (v3_node[0], 118), (pin_rx["5V"][0], 118), pin_rx["5V"]], C_3V3)
draw_poly([(gnd_node[0], 96), (gnd_node[0], 116), (pin_rx["GND"][0], 116), pin_rx["GND"]], C_GND)
draw_poly([pin_rx["TX"], (pin_rx["TX"][0], 115), (pin_node["RX"][0], 115), pin_node["RX"]], C_TX)

v3_esp = pin_esp32["3V3_R"] # (130+1.5+14*2.2=162.3, 118)
draw_poly([v3_esp, (v3_esp[0], 126), (pin_ld["VCC"][0], 126), pin_ld["VCC"]], C_3V3)
g_esp_r = pin_esp32["GND_R"]
draw_poly([g_esp_r, (g_esp_r[0], 124), (pin_ld["GND"][0], 124), pin_ld["GND"]], C_GND)
draw_poly([pin_esp32["TX2"], (pin_esp32["TX2"][0], 120), (pin_ld["RX"][0], 120), pin_ld["RX"]], '#3498db')
draw_poly([pin_esp32["RX2"], (pin_esp32["RX2"][0], 118), (pin_ld["TX"][0], 118), pin_ld["TX"]], '#3498db')


# C. Engine Control Lines (PWM from NodeMCU to HW354)
draw_poly([pin_node["D1"], (pin_node["D1"][0], 85), (102, 85), (102, 36), pin_drv["IN1"]], C_PWM)
draw_poly([pin_node["D2"], (pin_node["D2"][0], 83), (104.5, 83), (104.5, 36), pin_drv["IN2"]], C_PWM)
draw_poly([pin_node["D3"], (pin_node["D3"][0], 81), (107, 81), (107, 36), pin_drv["IN3"]], C_PWM)
draw_poly([pin_node["D4"], (pin_node["D4"][0], 79), (109.5, 79), (109.5, 36), pin_drv["IN4"]], C_PWM)


# D. High Power Drive Rails (Motors)
# L motors
draw_poly([pin_drv["OUT1"], (77, 56), (40, 56), (40, pin_m_tl["+"][1]), pin_m_tl["+"]], C_VCC)
draw_poly([(40, 56), (40, pin_m_bl["+"][1]), pin_m_bl["+"]], C_VCC)
draw_poly([pin_drv["OUT2"], (75, 50), (38, 50), (38, pin_m_tl["-"][1]), pin_m_tl["-"]], '#2c3e50')
draw_poly([(38, 50), (38, pin_m_bl["-"][1]), pin_m_bl["-"]], '#2c3e50')

# R motors
draw_poly([pin_drv["OUT3"], (113, 56), (150, 56), (150, pin_m_tr["+"][1]), pin_m_tr["+"]], C_VCC)
draw_poly([(150, 56), (150, pin_m_br["+"][1]), pin_m_br["+"]], C_VCC)
draw_poly([pin_drv["OUT4"], (115, 50), (152, 50), (152, pin_m_tr["-"][1]), pin_m_tr["-"]], '#2c3e50')
draw_poly([(152, 50), (152, pin_m_br["-"][1]), pin_m_br["-"]], '#2c3e50')

# Clear Manual Helper Text Flags 
ax.text(20, 25, "7.4V Power\n& GND Rail", color=C_VCC, ha='center', fontsize=6, fontweight='bold', bbox=dict(facecolor='#fff', edgecolor='none'))
ax.text(113, 85, "D1-D4 Motor PWM Logic", color=C_PWM, ha='left', fontsize=6, fontweight='bold')

plt.suptitle("Orthogonal Pin-to-Pin Realistic Wiring Schematic (Strict Collision-Free Routing)", fontsize=18, fontweight='bold', y=0.96)
plt.savefig('rover_fritzing_diagram.png', bbox_inches='tight', facecolor='#ffffff')
plt.close()
