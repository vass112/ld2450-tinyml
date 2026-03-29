import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Theme Configuration ---
BG_COLOR = '#ffffff'
BOX_FACE = '#f1f8fc'          # Very light blue for base station
BOX_EDGE = '#1a5276'          # Navy blue borders
DASH_EDGE = '#707b7c'         # Gray for wireless boundaries
TEXT_COLOR = '#000000'

fig, ax = plt.subplots(figsize=(12, 8), dpi=200)
ax.set_xlim(0, 120)
ax.set_ylim(0, 80)
ax.axis('off')

# --- Helper Functions ---
def draw_component(x, y, w, h, title, pins=[], is_wireless=False):
    ls = '--' if is_wireless else '-'
    ec = DASH_EDGE if is_wireless else BOX_EDGE
    # Draw Component Body
    box = patches.Rectangle((x, y), w, h, facecolor=BOX_FACE, edgecolor=ec, linewidth=1.8, linestyle=ls, zorder=3)
    ax.add_patch(box)
    
    # Title
    ax.text(x + w/2, y + h - 2, title, ha='center', va='top', fontweight='bold', fontsize=11, color=TEXT_COLOR, zorder=4)
    
    # Draw Pins
    pin_locs = {}
    for (name, px, py, align) in pins:
        abs_x, abs_y = x + px, y + py
        ha = 'left' if align == 'L' else ('right' if align == 'R' else 'center')
        ax.text(abs_x, abs_y, name, ha=ha, va='center', fontsize=8, color='#333333', zorder=4, fontfamily='monospace')
        # Tiny pin indicator
        circle_x = x if align == 'L' else (x+w if align == 'R' else abs_x)
        circle_y = abs_y if align in ['L','R'] else (y if align == 'B' else y+h)
        circ = patches.Circle((circle_x, circle_y), 0.5, facecolor='#ffffff', edgecolor=BOX_EDGE, zorder=5)
        ax.add_patch(circ)
        pin_locs[name] = (circle_x, circle_y)
    return pin_locs

def draw_wire(x_pts, y_pts, color='#000', label="", lbl_pos='center'):
    ax.plot(x_pts, y_pts, color=color, linewidth=2.0, zorder=2)
    if label:
        idx = max(0, len(x_pts)//2 - 1)
        mx, my = (x_pts[idx]+x_pts[idx+1])/2, (y_pts[idx]+y_pts[idx+1])/2
        ax.text(mx, my+1.5, label, ha='center', va='center', fontsize=9, color=color, fontweight='bold',
                bbox=dict(facecolor=BG_COLOR, edgecolor='none', pad=1), zorder=4)

def draw_wireless(p1, p2, label):
    ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#999999', linewidth=2.0, linestyle=':', zorder=2)
    ax.text((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, label, ha='center', va='center', fontsize=9, color='#666666',
            bbox=dict(facecolor=BG_COLOR, edgecolor='none', pad=1), zorder=4, style='italic')

# --- Draw Components ---
# 1. ESP32-S3 CrowPanel (Dashboard)
crow_pins = [
    ("VIN (5V)", 2, 8, 'L'),
    ("GND", 2, 4, 'L'),
]
p_crow = draw_component(50, 45, 30, 16, "ELECROW 7\" ESP32-S3\n(Radar Dashboard)", crow_pins)

# 2. USB Power Bank
pb_pins = [
    ("5V OUT", 18, 8, 'R'),
    ("GND", 18, 4, 'R'),
]
p_pb = draw_component(10, 45, 20, 16, "5V USB POWER BANK", pb_pins)

# 3. FrSky Taranis
tx_pins = [
    ("Internal 2S", 10, 4, 'C')
]
p_tx = draw_component(30, 10, 24, 18, "FrSky Taranis Q X7\n(RC Controller)", tx_pins, is_wireless=True)

# 4. FPV Goggles
gog_pins = []
p_gog = draw_component(70, 10, 24, 18, "FPV GOGGLES\n(Analog 5.8GHz)", gog_pins, is_wireless=True)


# --- WIRING ---
# Power Bank to CrowPanel
draw_wire([p_pb["5V OUT"][0], p_crow["VIN (5V)"][0]], [p_pb["5V OUT"][1], p_crow["VIN (5V)"][1]], color='#c0392b', label='5V USB-C')
draw_wire([p_pb["GND"][0], p_crow["GND"][0]], [p_pb["GND"][1], p_crow["GND"][1]], color='#2c3e50', label='GND')

# Abstract Wireless boundaries
draw_wireless((42, 28), (42, 45), "ESP-NOW (2.4GHz) Input")
draw_wireless((82, 35), (82, 28), "5.8GHz Analog Video In")
draw_wireless((30, 35), (30, 28), "CRSF/868MHz RC Out")

# Title
plt.suptitle('Operator Station (TX + Monitor) — Power & Signal Wiring', fontsize=16, fontweight='bold', y=0.92)
plt.savefig('circuit_diagram_tx_monitor.png', bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
