import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

# --- Configuration ---
BG_COLOR = '#ffffff'
fig, ax = plt.subplots(figsize=(16, 12), dpi=200)
ax.set_xlim(0, 160)
ax.set_ylim(0, 120)
ax.axis('off')

# --- Wire Routing Helper ---
def draw_wire(pts, color, lw=2.5, label=""):
    x, y = zip(*pts)
    # Background outline for contrast
    ax.plot(x, y, color='#ffffff', linewidth=lw+2.5, zorder=1, solid_capstyle='round', solid_joinstyle='round')
    # Main wire
    ax.plot(x, y, color=color, linewidth=lw, zorder=2, solid_capstyle='round', solid_joinstyle='round')
    if label:
        idx = max(0, len(pts)//2 - 1)
        mx, my = (pts[idx][0]+pts[idx+1][0])/2, (pts[idx][1]+pts[idx+1][1])/2
        ax.text(mx, my+1.5, label, ha='center', va='center', fontsize=9, color=color, fontweight='bold',
                bbox=dict(facecolor=BG_COLOR, edgecolor='none', pad=0.5), zorder=4)

# --- Define Vector Graph Components ---

def draw_lipo(x, y, w=20, h=12):
    # Blue battery pack
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, facecolor='#2980b9', edgecolor='#1a5276', lw=2, zorder=5, boxstyle="round,pad=0.5"))
    ax.text(x+w/2, y+h/2+1.5, "2S LiPo", color='white', fontweight='bold', ha='center', va='center', zorder=6)
    ax.text(x+w/2, y+h/2-1.5, "7.4V", color='#f1c40f', fontweight='bold', ha='center', va='center', zorder=6)
    # Terminals
    tx, ty = x+w, y+h/2
    ax.add_patch(patches.Rectangle((tx, ty+1), 3, 2, facecolor='#c0392b', zorder=5)) # Red
    ax.add_patch(patches.Rectangle((tx, ty-3), 3, 2, facecolor='#2c3e50', zorder=5)) # Black
    return (tx+3, ty+2), (tx+3, ty-2) # Power, GND pins

def draw_nodemcu(x, y, w=22, h=30):
    # Black PCB
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, facecolor='#1c1c1c', edgecolor='#000', lw=2, zorder=5, boxstyle="round,pad=0.2"))
    # USB port
    ax.add_patch(patches.Rectangle((x+w/2-3, y+h-1), 6, 2, facecolor='#bdc3c7', edgecolor='#7f8c8d', lw=1, zorder=6))
    # WiFi Module
    ax.add_patch(patches.Rectangle((x+3, y+h-10), w-6, 8, facecolor='#e6e6e6', edgecolor='#999', lw=1, zorder=6))
    ax.add_patch(patches.Rectangle((x+6, y+h-4), 8, 1, facecolor='#d4af37', edgecolor='none', zorder=7)) # Antenna trace
    # ESP8266 Text
    ax.text(x+w/2, y+8, "NodeMCU\nESP8266", color='white', ha='center', va='center', fontsize=9, fontweight='bold', zorder=6)
    
    # Generate Pins
    pins = {}
    pin_labels_left = ['A0','RSV','RSV','SD3','SD2','SD1','CMD','SD0','CLK','GND','3V','EN','RST']
    pin_labels_right= ['D0','D1','D2','D3','D4','3V','GND','D5','D6','D7','D8','RX','TX']
    
    for i, p in enumerate(pin_labels_left):
        py = y + h - 12 - (i * 1.3)
        ax.add_patch(patches.Rectangle((x-1, py), 2, 0.8, facecolor='#f1c40f', zorder=6)) # Gold pin
        ax.text(x+2, py+0.4, p, color='white', ha='left', va='center', fontsize=6, zorder=6, fontfamily='monospace')
        pins[p+"_L"] = (x-1, py+0.4)
        if p == 'VIN': pins['VIN'] = (x-1, py+0.4)
    for i, p in enumerate(pin_labels_right):
        py = y + h - 12 - (i * 1.3)
        ax.add_patch(patches.Rectangle((x+w-1, py), 2, 0.8, facecolor='#f1c40f', zorder=6))
        ax.text(x+w-2, py+0.4, p, color='white', ha='right', va='center', fontsize=6, zorder=6, fontfamily='monospace')
        pins[p+"_R"] = (x+w+1, py+0.4)
    
    # Assume VIN is at bottom left (often it is next to GND at the bottom)
    pins['VIN']  = (x-1, y+h-12-(13*1.3)) 
    ax.add_patch(patches.Rectangle((x-1, pins['VIN'][1]-0.4), 2, 0.8, facecolor='#f1c40f', zorder=6))
    ax.text(x+2, pins['VIN'][1], "VIN", color='white', ha='left', va='center', fontsize=6, zorder=6, fontfamily='monospace')

    return pins

def draw_l298n(x, y, w=26, h=26):
    # Red PCB
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, facecolor='#c0392b', edgecolor='#922b21', lw=2, zorder=5, boxstyle="round,pad=0.2"))
    # Huge Heatsink
    ax.add_patch(patches.Rectangle((x+4, y+6), w-8, 14, facecolor='#212f3c', edgecolor='#17202a', lw=1.5, zorder=6))
    ax.text(x+w/2, y+h/2, "L298N/HW-354\nH-BRIDGE", color='#7f8c8d', ha='center', va='center', fontsize=8, fontweight='bold', zorder=7)
    
    # Power Terminals (Bottom)
    ax.add_patch(patches.Rectangle((x+6, y-2), 14, 4, facecolor='#2980b9', edgecolor='#154360', zorder=6))
    ax.text(x+8, y+3, "12V", color='white', ha='center', fontsize=6, zorder=7)
    ax.text(x+13, y+3, "GND", color='white', ha='center', fontsize=6, zorder=7)
    ax.text(x+18, y+3, "5V", color='white', ha='center', fontsize=6, zorder=7)
    
    # Motor Terminals (Left/Right)
    ax.add_patch(patches.Rectangle((x-2, y+18), 4, 6, facecolor='#2980b9', edgecolor='#154360', zorder=6)) # Motor A
    ax.text(x+4, y+21, "OUT1\nOUT2", color='white', ha='left', va='center', fontsize=5, zorder=7)
    
    ax.add_patch(patches.Rectangle((x+w-2, y+18), 4, 6, facecolor='#2980b9', edgecolor='#154360', zorder=6)) # Motor B
    ax.text(x+w-4, y+21, "OUT3\nOUT4", color='white', ha='right', va='center', fontsize=5, zorder=7)
    
    # Logic Pins (Bottom Right)
    ax.add_patch(patches.Rectangle((x+16, y+5), 8, 2, facecolor='#111', zorder=6))
    ax.text(x+17, y+6, " INs", color='white', ha='center', va='center', fontsize=5, zorder=7)

    return {
        "VCC": (x+8, y-2), "GND": (x+13, y-2), "5V_OUT": (x+18, y-2),
        "OUT1": (x-2, y+22), "OUT2": (x-2, y+19),
        "OUT3": (x+w+2, y+22), "OUT4": (x+w+2, y+19),
        "IN1": (x+17, y+4), "IN2": (x+19, y+4), "IN3": (x+21, y+4), "IN4": (x+23, y+4)
    }

def draw_tt_motor(x, y, label="Motor"):
    # Yellow Gearbox
    ax.add_patch(patches.FancyBboxPatch((x, y), 14, 6, facecolor='#f1c40f', edgecolor='#b7950b', lw=1.5, zorder=5, boxstyle="round,pad=0.2"))
    # White Axis
    ax.add_patch(patches.Rectangle((x+4, y-2), 6, 2, facecolor='#ecf0f1', edgecolor='#bdc3c7', lw=1, zorder=4))
    ax.add_patch(patches.Rectangle((x+4, y+6), 6, 2, facecolor='#ecf0f1', edgecolor='#bdc3c7', lw=1, zorder=4))
    ax.text(x+7, y+3, label, ha='center', va='center', fontsize=7, fontweight='bold', zorder=6)
    return {"+": (x+14, y+4), "-": (x+14, y+2)}

def draw_receiver(x, y):
    # ES900X is a tiny black square with antenna and wires
    ax.add_patch(patches.FancyBboxPatch((x, y), 10, 10, facecolor='#1a1a1a', edgecolor='#000', lw=1.5, zorder=5, boxstyle="round,pad=0.2"))
    ax.text(x+5, y+5, "ES900X\nRX", color='white', ha='center', va='center', fontsize=6, fontweight='bold', zorder=6)
    # T-Antenna
    ax.plot([x+5, x+5], [y+10, y+16], color='#111', lw=1.5, zorder=4)
    ax.plot([x+1, x+9], [y+16, y+16], color='#111', lw=2, zorder=4)
    # Pins at bottom
    ax.add_patch(patches.Rectangle((x+2, y-1), 6, 1, facecolor='#d4af37', zorder=4))
    return {"RX": (x+3, y-1), "TX": (x+5, y-1), "5V": (x+7, y-1), "GND": (x+9, y-1)}

def draw_fpv(x, y):
    # Tiny box
    ax.add_patch(patches.Rectangle((x, y), 12, 12, facecolor='#000', edgecolor='#333', lw=1.5, zorder=5))
    # Lens
    ax.add_patch(patches.Circle((x+6, y+6), 4, facecolor='#111', edgecolor='#555', lw=1, zorder=6))
    ax.add_patch(patches.Circle((x+7, y+7), 1, facecolor='#fff', alpha=0.5, zorder=7)) # Glare
    ax.text(x+6, y-2, "FPV CAM", ha='center', va='top', fontsize=7, fontweight='bold', zorder=6)
    return {"VCC": (x+12, y+8), "GND": (x+12, y+6), "VID": (x+12, y+4)}

def draw_vtx(x, y):
    ax.add_patch(patches.Rectangle((x, y), 12, 8, facecolor='#c0392b', edgecolor='#922b21', lw=1.5, zorder=5))
    ax.text(x+6, y+4, "VTX", color='white', ha='center', va='center', fontsize=7, fontweight='bold', zorder=6)
    # Antenna
    ax.plot([x+6, x+6], [y+8, y+14], color='#d35400', lw=2, zorder=4)
    ax.add_patch(patches.Circle((x+6, y+15), 1.5, facecolor='#111', zorder=5))
    return {"VCC": (x, y+6), "GND": (x, y+4), "VID": (x, y+2)}


# --- PLOT COMPONENTS ON CANVAS ---

p_batt = draw_lipo(10, 80)
p_node = draw_nodemcu(50, 70)
p_md   = draw_l298n(95, 70)
p_rx   = draw_receiver(25, 50)

p_ml1  = draw_tt_motor(135, 85, "L-Motor 1")
p_ml2  = draw_tt_motor(135, 75, "L-Motor 2")
p_mr1  = draw_tt_motor(135, 60, "R-Motor 1")
p_mr2  = draw_tt_motor(135, 50, "R-Motor 2")

p_cam  = draw_fpv(10, 20)
p_vtx  = draw_vtx(40, 22)


# --- DRAW WIRING ---

# Colors
C_VCC = '#e74c3c'  # Red for VCC
C_GND = '#2c3e50'  # Dark blue/black for GND
C_3V3 = '#e67e22'  # Orange for 3.3V
C_TX  = '#27ae60'  # Green for TX/RX
C_RX  = '#2980b9'  # Blue for RX/TX
C_PWM = '#8e44ad'  # Purple for PWM
C_VID = '#f1c40f'  # Yellow for Video

# 1. Power (Battery to Motor Driver & ESP8266)
# Batt to NodeMCU VIN
draw_wire([p_batt[0], (40, 82), (40, p_node["VIN"][1]), p_node["VIN"]], color=C_VCC, label="Battery + (7.4V) -> VIN")
# Batt to Motor Driver VCC (12V Input pin of HW-354 is used for VMOT)
draw_wire([p_batt[0], (42, 82), (42, 110), (p_md["VCC"][0], 110), p_md["VCC"]], color=C_VCC, label="7.4V -> VMOT")

# Batt GND to NodeMCU GND
gnd_pin_node = p_node["GND_L"] 
draw_wire([p_batt[1], (36, 78), (36, gnd_pin_node[1]), gnd_pin_node], color=C_GND, label="Common GND")
# Batt GND to Motor Driver GND
draw_wire([p_batt[1], (38, 78), (38, 108), (p_md["GND"][0], 108), p_md["GND"]], color=C_GND)


# 2. Receiver to ESP8266
# RX VCC to NodeMCU 3V3
draw_wire([p_rx["5V"], (p_rx["5V"][0], 45), (p_node["3V_L"][0]-8, 45), (p_node["3V_L"][0]-8, p_node["3V_L"][1]), p_node["3V_L"]], color=C_3V3, label="3.3V Power Out")
# RX GND to Common GND (NodeMCU Left GND)
draw_wire([p_rx["GND"], (p_rx["GND"][0], 43), (p_node["GND_L"][0]-6, 43), (p_node["GND_L"][0]-6, p_node["GND_L"][1]-2), (p_node["GND_L"][0], p_node["GND_L"][1]-2)], color=C_GND)
# RX TX to NodeMCU RX (GPIO3 -> RX pin)
draw_wire([p_rx["TX"], (p_rx["TX"][0], p_node["RX_R"][1]), p_node["RX_R"]], color=C_TX, label="ES900X TX -> NodeMCU RX")


# 3. ESP8266 to Motor Driver (D1-D4 to IN1-IN4)
draw_wire([p_node["D1_R"], (p_node["D1_R"][0]+10, p_node["D1_R"][1]), (p_node["D1_R"][0]+10, p_md["IN1"][1]-10), (p_md["IN1"][0], p_md["IN1"][1]-10), p_md["IN1"]], color=C_PWM)
draw_wire([p_node["D2_R"], (p_node["D2_R"][0]+12, p_node["D2_R"][1]), (p_node["D2_R"][0]+12, p_md["IN2"][1]-8), (p_md["IN2"][0], p_md["IN2"][1]-8), p_md["IN2"]], color=C_PWM)
draw_wire([p_node["D3_R"], (p_node["D3_R"][0]+14, p_node["D3_R"][1]), (p_node["D3_R"][0]+14, p_md["IN3"][1]-6), (p_md["IN3"][0], p_md["IN3"][1]-6), p_md["IN3"]], color=C_PWM)
draw_wire([p_node["D4_R"], (p_node["D4_R"][0]+16, p_node["D4_R"][1]), (p_node["D4_R"][0]+16, p_md["IN4"][1]-4), (p_md["IN4"][0], p_md["IN4"][1]-4), p_md["IN4"]], color=C_PWM, label="D1-D4 -> IN1-IN4")


# 4. Motor Driver to Left/Right Motors
draw_wire([p_md["OUT1"], (p_ml1["+"][0]-8, p_md["OUT1"][1]), (p_ml1["+"][0]-8, p_ml1["+"][1]), p_ml1["+"]], color=C_VCC, lw=3)
draw_wire([(p_ml1["+"][0]-8, p_ml1["+"][1]), (p_ml2["+"][0]-8, p_ml2["+"][1]), p_ml2["+"]], color=C_VCC, lw=3)

draw_wire([p_md["OUT2"], (p_ml1["-"][0]-6, p_md["OUT2"][1]), (p_ml1["-"][0]-6, p_ml1["-"][1]), p_ml1["-"]], color=C_GND, lw=3)
draw_wire([(p_ml1["-"][0]-6, p_ml1["-"][1]), (p_ml2["-"][0]-6, p_ml2["-"][1]), p_ml2["-"]], color=C_GND, lw=3)

draw_wire([p_md["OUT3"], (p_mr1["+"][0]-8, p_md["OUT3"][1]), (p_mr1["+"][0]-8, p_mr1["+"][1]), p_mr1["+"]], color=C_VCC, lw=3)
draw_wire([(p_mr1["+"][0]-8, p_mr1["+"][1]), (p_mr2["+"][0]-8, p_mr2["+"][1]), p_mr2["+"]], color=C_VCC, lw=3)

draw_wire([p_md["OUT4"], (p_mr1["-"][0]-6, p_md["OUT4"][1]), (p_mr1["-"][0]-6, p_mr1["-"][1]), p_mr1["-"]], color=C_GND, lw=3)
draw_wire([(p_mr1["-"][0]-6, p_mr1["-"][1]), (p_mr2["-"][0]-6, p_mr2["-"][1]), p_mr2["-"]], color=C_GND, lw=3)


# 5. FPV System
draw_wire([p_batt[0], (p_batt[0][0]-5, p_batt[0][1]), (p_batt[0][0]-5, p_cam["VCC"][1]), p_cam["VCC"]], color=C_VCC)
draw_wire([p_batt[1], (p_batt[1][0]-3, p_batt[1][1]), (p_batt[1][0]-3, p_cam["GND"][1]), p_cam["GND"]], color=C_GND)

draw_wire([(p_batt[0][0]-5, p_vtx["VCC"][1]), p_vtx["VCC"]], color=C_VCC)
draw_wire([(p_batt[1][0]-3, p_vtx["GND"][1]), p_vtx["GND"]], color=C_GND)

draw_wire([p_cam["VID"], p_vtx["VID"]], color=C_VID, label="Analog Video", lw=2)


# --- Titles & Labels ---
plt.suptitle('Pin-to-Pin Circuit Schematic — Mobile Rover Platform', fontsize=18, fontweight='bold', y=0.96)
ax.text(80, 115, "Red = 7.4V Battery | Orange = 3.3V Logic | Dark Blue = Common GND | Green/Purple = Signal", 
        fontsize=10, color='#333333', style='italic', ha='center',
        bbox=dict(facecolor='#f8f9fa', edgecolor='#dee2e6', pad=1))

plt.savefig('circuit_diagram_rover_realistic.png', bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
