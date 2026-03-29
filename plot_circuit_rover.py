import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- Theme Configuration ---
BG_COLOR = '#ffffff'
BOX_FACE = '#fdfbf7'          
BOX_EDGE = '#343a40'          
TEXT_COLOR = '#000000'

COLOR_5V   = '#c0392b'   # Red for 5V
COLOR_3V3  = '#e67e22'   # Orange for 3.3V
COLOR_7V   = '#8e44ad'   # Purple for 7.4V (Battery)
COLOR_GND  = '#2c3e50'   # Dark Blue for GND
COLOR_SIG  = '#27ae60'   # Green for Signal (RX/TX, PWM)
COLOR_VID  = '#f39c12'   # Yellow/Orange for Video

fig, ax = plt.subplots(figsize=(16, 11), dpi=200)
ax.set_xlim(0, 160)
ax.set_ylim(0, 120)
ax.axis('off')

# --- Helper Functions ---
def draw_component(x, y, w, h, title, pins=[], is_wireless=False, bg=BOX_FACE):
    ls = '--' if is_wireless else '-'
    box = patches.Rectangle((x, y), w, h, facecolor=bg, edgecolor=BOX_EDGE, linewidth=1.5, linestyle=ls, zorder=3)
    ax.add_patch(box)
    
    # Title
    ax.text(x + w/2, y + h - 2, title, ha='center', va='top', fontweight='bold', fontsize=9, color=TEXT_COLOR, zorder=4)
    
    # Draw Pins
    pin_coords = {}
    for (name, px, py, align) in pins:
        abs_x, abs_y = x + px, y + py
        ha = 'left' if align == 'L' else ('right' if align == 'R' else 'center')
        ax.text(abs_x, abs_y, name, ha=ha, va='center', fontsize=7, color='#333333', zorder=4, fontfamily='monospace', fontweight='bold')
        
        # Tiny pin indicator
        circle_x = x if align == 'L' else (x+w if align == 'R' else abs_x)
        circle_y = abs_y if align in ['L','R'] else (y if align == 'B' else y+h)
        circ = patches.Circle((circle_x, circle_y), 0.6, facecolor='#ffffff', edgecolor=BOX_EDGE, lw=1, zorder=5)
        ax.add_patch(circ)
        pin_coords[name] = (circle_x, circle_y)
        
    return pin_coords

def draw_wire(pts, color='#000', label="", lw=1.5):
    x, y = zip(*pts)
    ax.plot(x, y, color=color, linewidth=lw, zorder=2)
    if label:
        idx = len(pts)//2 - 1
        if idx < 0: idx = 0
        mx, my = (pts[idx][0]+pts[idx+1][0])/2, (pts[idx][1]+pts[idx+1][1])/2
        ax.text(mx, my+1.5, label, ha='center', va='center', fontsize=8, color=color, fontweight='bold',
                bbox=dict(facecolor=BG_COLOR, edgecolor='none', pad=0.5), zorder=4)

def plot_route(start, end, via_x=None, via_y=None, color='#000', label="", lw=1.5):
    pts = [start]
    if via_x is not None:
        pts.append((via_x, start[1]))
        pts.append((via_x, end[1]))
    elif via_y is not None:
        pts.append((start[0], via_y))
        pts.append((end[0], via_y))
    pts.append(end)
    draw_wire(pts, color, label, lw=lw)

# --- Define Components & Pins ---

# 1. Power System (Left)
batt_pins = [("7.4V (+)", 20, 16, 'R'), ("GND (-)", 20, 12, 'R')]
p_bat = draw_component(5, 95, 20, 20, "2S LiPo\nBATTERY", batt_pins, bg='#f9ebea')

buck_pins = [("VIN+", 0, 12, 'L'), ("VIN-", 0, 4, 'L'), ("VOUT+ (5V)", 20, 12, 'R'), ("VOUT- (GND)", 20, 4, 'R')]
p_buck = draw_component(5, 60, 20, 16, "DC-DC BUCK\n(5V Step Down)", buck_pins, bg='#f9ebea')

# 2. Main Logic (Center Top)
nodemcu_pins = [
    ("VIN (5V)", 0, 26, 'L'), ("GND", 0, 22, 'L'),
    ("RX (D5)", 0, 8, 'L'), ("TX (D6)", 0, 4, 'L'),
    ("D1 (IN1)", 24, 26, 'R'), ("D2 (IN2)", 24, 22, 'R'), 
    ("D3 (IN3)", 24, 18, 'R'), ("D4 (IN4)", 24, 14, 'R')
]
p_node = draw_component(50, 80, 24, 30, "ESP8266 NodeMCU\n(Rover Controller)", nodemcu_pins, bg='#eaf2f8')

# 3. RC Receiver (Center)
rx_pins = [("5V", 0, 12, 'L'), ("GND", 0, 8, 'L'), ("TX", 20, 12, 'R'), ("RX", 20, 8, 'R')]
p_rx = draw_component(50, 50, 20, 16, "ES900X\nReceiver", rx_pins, bg='#eaf2f8')

# 4. Motor Driver (Center Bottom)
md_pins = [
    ("12V (VIN)", 0, 26, 'L'), ("GND", 0, 22, 'L'), ("5V", 0, 18, 'L'),
    ("IN1", 0, 12, 'L'), ("IN2", 0, 8, 'L'), ("IN3", 30, 26, 'R'), ("IN4", 30, 22, 'R'),
    ("OUT1", 10, 0, 'B'), ("OUT2", 14, 0, 'B'), ("OUT3", 18, 0, 'B'), ("OUT4", 22, 0, 'B')
]
p_md = draw_component(85, 75, 30, 30, "DUAL H-BRIDGE\n(L298N/MX1508)", md_pins, bg='#fef9e7')

# 5. DC Motors
m1_p = [("M+", 10, 8, 'C')]
p_m_left = draw_component(85, 45, 12, 12, "L-Motors", m1_p)
p_m_right = draw_component(103, 45, 12, 12, "R-Motors", m1_p)

# 6. Radar Node (Top Right)
esp32_pins = [("VIN (5V)", 0, 26, 'L'), ("GND", 0, 22, 'L'), ("RX2", 24, 12, 'R'), ("TX2", 24, 8, 'R')]
p_esp32 = draw_component(100, 10, 24, 30, "ESP32 DevKit\n(Radar Node)", esp32_pins, bg='#eaf2f8')

ld_pins = [("VCC", 0, 12, 'L'), ("GND", 0, 8, 'L'), ("TX", 0, 4, 'L'), ("RX", 0, 0, 'L')] # Actually LD2450 pins are bottom usually, let's just make them Left
p_ld = draw_component(140, 10, 16, 20, "LD2450\nRadar", ld_pins, bg='#eaeded')

# 7. FPV System (Bottom Right)
cam_pins = [("5V", 0, 12, 'L'), ("GND", 0, 8, 'L'), ("VIDEO", 20, 10, 'R')]
p_cam = draw_component(10, 10, 20, 16, "ANALOG FPV\nCAMERA", cam_pins, bg='#eaeded')

vtx_pins = [("7-26V(VIN)", 0, 14, 'L'), ("GND", 0, 10, 'L'), ("VIDEO IN", 0, 6, 'L')]
p_vtx = draw_component(50, 10, 20, 20, "5.8GHz VTX", vtx_pins, bg='#eaeded')


# --- DRAW WIRING ---

# Power Rails (Battery to Buck & Driver)
plot_route(p_bat["7.4V (+)"], p_buck["VIN+"], via_x=32, color=COLOR_7V, label="7.4V BAT")
plot_route(p_bat["GND (-)"], p_buck["VIN-"], via_x=30, color=COLOR_GND, label="GND")

# Battery directly to Motor Driver 12V and VTX
plot_route(p_bat["7.4V (+)"], p_md["12V (VIN)"], via_y=112, color=COLOR_7V, lw=2.0)
plot_route(p_bat["7.4V (+)"], p_vtx["7-26V(VIN)"], via_x=38, color=COLOR_7V)
plot_route(p_bat["GND (-)"], p_md["GND"], via_y=108, color=COLOR_GND, lw=2.0)
plot_route(p_bat["GND (-)"], p_vtx["GND"], via_x=36, color=COLOR_GND)

# 5V Rails from Buck Converter
V5_X = 40
plot_route(p_buck["VOUT+ (5V)"], p_node["VIN (5V)"], via_x=V5_X, color=COLOR_5V, label="5V Rail")
plot_route(p_buck["VOUT+ (5V)"], p_rx["5V"], via_x=V5_X, color=COLOR_5V)
plot_route(p_buck["VOUT+ (5V)"], p_esp32["VIN (5V)"], via_x=V5_X, color=COLOR_5V)
plot_route((V5_X, p_buck["VOUT+ (5V)"][1]), p_cam["5V"], via_y=22, color=COLOR_5V)

# GND Rails from Buck Converter
GND_X = 42
plot_route(p_buck["VOUT- (GND)"], p_node["GND"], via_x=GND_X, color=COLOR_GND, label="Common GND")
plot_route(p_buck["VOUT- (GND)"], p_rx["GND"], via_x=GND_X, color=COLOR_GND)
plot_route(p_buck["VOUT- (GND)"], p_esp32["GND"], via_x=GND_X, color=COLOR_GND)
plot_route((GND_X, p_buck["VOUT- (GND)"][1]), p_cam["GND"], via_y=18, color=COLOR_GND)

# Signal: RC Receiver to NodeMCU
plot_route(p_rx["TX"], p_node["RX (D5)"], via_x=75, color=COLOR_SIG, label="CRSF/SBUS RX")
plot_route(p_rx["RX"], p_node["TX (D6)"], via_x=73, color=COLOR_SIG)

# Signal: NodeMCU to Motor Driver
plot_route(p_node["D1 (IN1)"], p_md["IN1"], via_x=78, color=COLOR_SIG, label="PWM/DIR")
plot_route(p_node["D2 (IN2)"], p_md["IN2"], via_x=80, color=COLOR_SIG)
plot_route(p_node["D3 (IN3)"], p_md["IN3"], via_y=108, color=COLOR_SIG)
plot_route(p_node["D4 (IN4)"], p_md["IN4"], via_y=106, color=COLOR_SIG)

# Motor Outputs
plot_route(p_md["OUT1"], (85+6, 57), color=COLOR_7V, lw=2.0)
plot_route(p_md["OUT2"], (85+6, 57), color=COLOR_GND, lw=2.0)
plot_route(p_md["OUT3"], (103+6, 57), color=COLOR_7V, lw=2.0)
plot_route(p_md["OUT4"], (103+6, 57), color=COLOR_GND, lw=2.0)

# Signal: ESP32 to LD2450
plot_route(p_esp32["TX2"], p_ld["RX"], via_x=132, color=COLOR_SIG, label="UART")
plot_route(p_esp32["RX2"], p_ld["TX"], via_x=134, color=COLOR_SIG)
plot_route(p_esp32["VIN (5V)"], p_ld["VCC"], via_y=42, color=COLOR_5V)
plot_route(p_esp32["GND"], p_ld["GND"], via_y=38, color=COLOR_GND)

# FPV Signal
plot_route(p_cam["VIDEO"], p_vtx["VIDEO IN"], via_x=45, color=COLOR_VID, label="Analog Video")


# --- Title & Legend ---
plt.suptitle('Rover Mobile Base — Pin-to-Pin Circuit & Wiring Diagram', fontsize=16, fontweight='bold', y=0.96)
ax.text(5, 115, "Red = 5V / 3.3V Power | Purple = 7.4V Battery | Dark Blue = GND | Green = Signal (PWM/UART/RC)", fontsize=9, color='#333333', style='italic')

plt.savefig('circuit_diagram_rover.png', bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
