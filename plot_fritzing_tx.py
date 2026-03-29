import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Canvas Setup ---
BG_COLOR = '#ffffff'
fig, ax = plt.subplots(figsize=(16, 12), dpi=200)
ax.set_facecolor(BG_COLOR)
ax.set_xlim(0, 180)
ax.set_ylim(0, 120)
ax.axis('off')

# --- Grid Background ---
for x in range(0, 180, 2): ax.plot([x, x], [0, 120], color='#f9f9f9', lw=0.8, zorder=0)
for y in range(0, 120, 2): ax.plot([0, 180], [y, y], color='#f9f9f9', lw=0.8, zorder=0)

# --- 90-DEGREE ORTHOGONAL WIRE ROUTING ---
def draw_poly(pts, color, lw=2.5, label=""):
    x, y = zip(*pts)
    # White background stroke prevents visual overlaps
    ax.plot(x, y, color='#ffffff', linewidth=lw+3.5, zorder=1, solid_capstyle='round', solid_joinstyle='round')
    # Colored Wire
    ax.plot(x, y, color=color, linewidth=lw, zorder=2, solid_capstyle='round', solid_joinstyle='round')
    
    # Solder pads at ends
    ax.add_patch(patches.Circle(pts[0], 0.7, facecolor=color, edgecolor='#333', lw=0.5, zorder=4))
    ax.add_patch(patches.Circle(pts[-1], 0.7, facecolor=color, edgecolor='#333', lw=0.5, zorder=4))

# --- WIRELESS LINKS ---
def draw_wireless(p1, p2, label=""):
    x, y = [p1[0], p2[0]], [p1[1], p2[1]]
    ax.plot(x, y, color='#7f8c8d', lw=2.5, linestyle='--', zorder=2)
    ax.text((p1[0]+p2[0])/2, (p1[1]+p2[1])/2, label, ha='center', va='center', fontsize=8, color='#fff', fontweight='bold',
            bbox=dict(facecolor='#95a5a6', edgecolor='none', pad=0.8), zorder=3, style='italic')


# --- Components ---
def draw_power_bank(x, y):
    w, h = 32, 20
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.5", facecolor='#ecf0f1', edgecolor='#bdc3c7', lw=2, zorder=3))
    ax.add_patch(patches.Rectangle((x+w-2, y+h/2-5), 3, 10, facecolor='#2c3e50', zorder=3)) # Ports
    ax.text(x+w/2, y+h/2, "5V USB\nPower Bank", ha='center', va='center', fontsize=9, fontweight='bold', color='#2c3e50', zorder=4)
    # Output pins (USB-C abstract)
    return {"+": (x+w+1, y+h/2+3), "-": (x+w+1, y+h/2-3)}

def draw_taranis(x, y):
    w, h = 38, 28
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.5", facecolor='#626567', edgecolor='#424949', lw=2, zorder=3))
    ax.add_patch(patches.Rectangle((x+12, y+h/2-4), 14, 12, facecolor='#212F3C', zorder=3)) # Screen
    ax.add_patch(patches.Circle((x+7, y+6), 5, facecolor='#D5DBDB', edgecolor='#839192', lw=2, zorder=4)) # Gimbal Left
    ax.add_patch(patches.Circle((x+w-7, y+6), 5, facecolor='#D5DBDB', edgecolor='#839192', lw=2, zorder=4)) # Gimbal Right
    ax.add_patch(patches.Rectangle((x+w/2-2, y+h+1.5), 4, 12, facecolor='#000', zorder=2)) # Antenna
    ax.text(x+w/2, y+h-7, "FrSky\nTaranis Q X7", color='white', ha='center', va='center', fontsize=7, fontweight='bold', zorder=4)
    return {"TX": (x+w/2, y+h+14)}

def draw_goggles(x, y):
    w, h = 34, 18
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.5", facecolor='#17202A', edgecolor='#111', lw=2, zorder=3))
    ax.add_patch(patches.Circle((x+w/2-7, y+h/2), 5, facecolor='#2C3E50', zorder=4)) # Left Eye
    ax.add_patch(patches.Circle((x+w/2+7, y+h/2), 5, facecolor='#2C3E50', zorder=4)) # Right Eye
    ax.add_patch(patches.Rectangle((x+2, y+h+1.5), 2, 10, facecolor='#000', zorder=2)) # Antenna 1
    ax.add_patch(patches.Rectangle((x+w-6, y+h+1.5), 8, 8, facecolor='#c0392b', zorder=2)) # Patch Antenna
    ax.text(x+w/2, y-3, "FPV Goggles (Analog 5.8GHz)", ha='center', va='center', fontsize=8, fontweight='bold', color='#17202A', zorder=4)
    return {"RX": (x+w/2, y+h+12)}

def draw_elecrow_display(x, y):
    w, h = 56, 36
    # Outer Bezel
    ax.add_patch(patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.0", facecolor='#2C3E50', edgecolor='#1A5276', lw=2, zorder=3))
    # Inner LCD Array
    ax.add_patch(patches.Rectangle((x+2, y+2), w-4, h-4, facecolor='#111', zorder=4))
    # Render simulated radar target graphics on screen
    ax.add_patch(patches.Arc((x+w/2, y+6), 36, 36, theta1=0, theta2=180, edgecolor='#2ecc71', lw=1.5, zorder=5))
    ax.add_patch(patches.Arc((x+w/2, y+6), 24, 24, theta1=0, theta2=180, edgecolor='#2ecc71', lw=1.5, zorder=5))
    ax.plot([x+w/2, x+w/2-10], [y+6, y+21], color='#2ecc71', lw=2, zorder=5) # Sweep line
    ax.add_patch(patches.Circle((x+w/2-5, y+18), 1.5, facecolor='#e74c3c', zorder=5)) # Target
    
    ax.text(x+w/2, y+h/2+2, "ELECROW 7\" ESP32-S3", color='white', ha='center', va='center', fontweight='bold', fontsize=10, zorder=5)
    ax.text(x+w/2, y+h/2-2, "(Radar Dashboard)", color='#bdc3c7', ha='center', va='center', fontsize=8, zorder=5)
    
    # Bottom Pins (Assume USB-C equivalent)
    px = x + w/2
    return {"5V": (px-3, y), "GND": (px+3, y), "WIFI": (x+w, y+h/2)}

# --- Place Real Components ---
pin_pb = draw_power_bank(20, 65)     # Top left
pin_disp = draw_elecrow_display(85, 65) # Top center
pin_tx = draw_taranis(25, 10)        # Bottom left
pin_gog = draw_goggles(125, 10)      # Bottom right

# --- 90-Degree Collision-Free Array Routing ---
C_VCC = '#e74c3c'
C_GND = '#2c3e50'

V_PWR = 45   # Y channel for 5V
V_GND = 40   # Y channel for GND

pb_vcc = pin_pb["+"]
pb_gnd = pin_pb["-"]
disp_5v = pin_disp["5V"]
disp_gnd = pin_disp["GND"]

# Route cleanly under the display directly to the bottom terminal pad
draw_poly([pb_vcc, (60, pb_vcc[1]), (60, V_PWR), (disp_5v[0], V_PWR), disp_5v], C_VCC)
draw_poly([pb_gnd, (65, pb_gnd[1]), (65, V_GND), (disp_gnd[0], V_GND), disp_gnd], C_GND)

# Static Text Label safely plotted off-line
ax.text(80, V_PWR-1.5, "5V USB-C Power", color='#c0392b', ha='center', fontsize=7, fontweight='bold')

# --- Wireless Links (Upward orthogonal to simulate boundary) ---
T_LNK = 110 # Top Y bound for wireless link exits

w_tx = pin_tx["TX"]
draw_wireless(w_tx, (w_tx[0], T_LNK), "CRSF/868MHz Command Out ->")

w_rx = pin_gog["RX"]
draw_wireless(w_rx, (w_rx[0], T_LNK), "Analog 5.8GHz Video In <-")

w_wifi = pin_disp["WIFI"]
draw_wireless(w_wifi, (170, w_wifi[1]), "ESP-NOW Radar Data In <-")


# Render Final
plt.suptitle("Orthogonal Realistic Wiring Schematic (Operator Station)", fontsize=20, fontweight='bold', y=0.96)
plt.savefig('circuit_diagram_tx_monitor_realistic.png', bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
