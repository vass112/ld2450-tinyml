import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# --- Theme Configuration (Light & Clean) ---
BG_COLOR = '#ffffff'          # Pure white background
BOX_FACE = '#dbeacc'          # Classic pale green
BOX_EDGE = '#38761d'          # Classic dark green border
TEXT_COLOR = '#000000'        # Black text
LINE_COLOR = '#000000'        # Black lines for arrows

fig, ax = plt.subplots(figsize=(12, 10), dpi=200)
ax.set_xlim(0, 120)
ax.set_ylim(0, 105)
ax.axis('off')

# --- Helper Functions ---
def draw_box(x, y, w, h, label, is_main=False):
    # Sharp rectangular boxes
    lw = 2.0 if is_main else 1.5
    box = patches.Rectangle((x - w/2, y - h/2), w, h,
                            facecolor=BOX_FACE, edgecolor=BOX_EDGE, linewidth=lw, zorder=3)
    ax.add_patch(box)
    
    # Text formatting
    fs = 14 if is_main else 13
    fw = 'bold' if is_main else 'normal'
    ax.text(x, y, label, ha='center', va='center', color=TEXT_COLOR, 
            fontweight=fw, fontsize=fs, zorder=4, family='sans-serif')

def draw_arrow(x1, y1, x2, y2):
    # Use standard solid triangle arrows directly on line endpoints
    dx = x2 - x1
    dy = y2 - y1
    head_len = 3.0
    head_wid = 2.0
    # Shorten the target coordinate slightly so edge covers exactly
    if dx > 0: x2 -= 0.5
    if dx < 0: x2 += 0.5
    if dy > 0: y2 -= 0.5
    if dy < 0: y2 += 0.5
        
    ax.arrow(x1, y1, x2-x1, y2-y1, width=0.4, head_width=head_wid, head_length=head_len,
             fc=LINE_COLOR, ec=LINE_COLOR, length_includes_head=True, zorder=4)

# --- Component Sizes & Spacing (Massively scaled up for text space) ---
W, H = 24, 11
W_M, H_M = 48, 30
C_X, C_Y = 60, 52  # Center position shifted slightly up for bottom space

# Bounding coordinates for arrows
C_LEFT = C_X - W_M/2
C_RIGHT = C_X + W_M/2
C_TOP = C_Y + H_M/2
C_BOT = C_Y - H_M/2

# Sub-component Centers
X_L_INNER = 46     # Center X for top/bottom left blocks
X_R_INNER = 74     # Center X for top/bottom right blocks
X_L_OUTER = 16     # Center X for far left blocks
X_R_OUTER = 104    # Center X for far right blocks

Y_TOP = 86
Y_MID_HI = 61
Y_MID_LO = 43
Y_BOT_HI = 23
Y_BOT_LO = 6

# --- Central Block ---
draw_box(C_X, C_Y, W_M, H_M, "MAIN CONTROLLERS\n(NodeMCU & ESP32)", is_main=True)

# --- Top Inputs ---
draw_box(X_L_INNER, Y_TOP, W, H, "ANALOG FPV\nCAMERA & VTX")
draw_box(X_R_INNER, Y_TOP, W, H, "LD2450 RADAR\nSENSOR")

# --- Left Inputs ---
draw_box(X_L_OUTER, Y_MID_HI, W, H, "RC RECEIVER\n(ES900X)")
draw_box(X_L_OUTER, Y_MID_LO, W, H, "RC TRANSMITTER\n(FrSky)")

# --- Right Output ---
draw_box(X_R_OUTER, C_Y, W, H, "DASHBOARD\nDISPLAY")

# --- Bottom Left (Power Flow) ---
draw_box(X_L_INNER, Y_BOT_HI, W, H, "POWER\nDISTRIBUTION")
draw_box(X_L_INNER, Y_BOT_LO, W, H, "2S LiPo\nBATTERY PACK")

# --- Bottom Right (Motor Flow) ---
draw_box(X_R_INNER, Y_BOT_HI, W, H, "DUAL H-BRIDGE\nMOTOR DRIVER")
draw_box(X_R_INNER, Y_BOT_LO, W, H, "4x DC\nMOTORS")


# --- Draw Interconnecting Arrows (Exact matching paths of reference image) ---

# Top inputs down to Central
draw_arrow(X_L_INNER, Y_TOP - H/2, X_L_INNER, C_TOP)  # Camera to Center
draw_arrow(X_R_INNER, Y_TOP - H/2, X_R_INNER, C_TOP)  # Radar to Center

# Left inputs right to Central
draw_arrow(X_L_OUTER + W/2, Y_MID_HI, C_LEFT, Y_MID_HI)  # Receiver to Center
draw_arrow(X_L_OUTER + W/2, Y_MID_LO, C_LEFT, Y_MID_LO)  # Transmitter to Center

# Central right to Display
draw_arrow(C_RIGHT, C_Y, X_R_OUTER - W/2, C_Y)  # Center to Display

# Power (Bottom-Up to Center)
draw_arrow(X_L_INNER, Y_BOT_LO + H/2, X_L_INNER, Y_BOT_HI - H/2)  # Battery to Power Dist
draw_arrow(X_L_INNER, Y_BOT_HI + H/2, X_L_INNER, C_BOT)           # Power Dist to Center

# Motors (Center Down-to-Bottom)
draw_arrow(X_R_INNER, C_BOT, X_R_INNER, Y_BOT_HI + H/2)           # Center to Motor Driver
draw_arrow(X_R_INNER, Y_BOT_HI - H/2, X_R_INNER, Y_BOT_LO + H/2)  # Motor Driver to Motors


# --- Title & Spacing ---
plt.suptitle('3.1 SYSTEM BLOCK DIAGRAM', fontsize=18, fontweight='bold', color=TEXT_COLOR, y=0.96, ha='left', x=0.08)

plt.savefig('rover_block_diagram_python.png', bbox_inches='tight', facecolor=BG_COLOR)
plt.close()
