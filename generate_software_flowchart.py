import xml.etree.ElementTree as ET
from xml.dom import minidom

class DrawIOFlowchart:
    def __init__(self):
        self.root = ET.Element("mxfile", version="14.6.13", type="device")
        self.diagram = ET.SubElement(self.root, "diagram", name="Software Flow")
        self.model = ET.SubElement(self.diagram, "mxGraphModel", dx="1422", dy="794", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="1169", pageHeight="827", math="0", shadow="0")
        self.root_cell = ET.SubElement(self.model, "root")
        ET.SubElement(self.root_cell, "mxCell", id="0")
        ET.SubElement(self.root_cell, "mxCell", id="1", parent="0")
        self.edge_idx = 0
    
    def add_node(self, id_str, label, x, y, w, h, style_str):
        cell = ET.SubElement(self.root_cell, "mxCell", id=id_str, value=label, style=style_str, vertex="1", parent="1")
        geo = ET.SubElement(cell, "mxGeometry", x=str(x), y=str(y), width=str(w), height=str(h))
        geo.set("as", "geometry")
    
    def add_edge(self, src_id, tgt_id, style_str, label=""):
        self.edge_idx += 1
        id_str = f"edge_f_{self.edge_idx}"
        full_style = f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;{style_str}"
        cell = ET.SubElement(self.root_cell, "mxCell", id=id_str, value=label, style=full_style, edge="1", parent="1", source=src_id, target=tgt_id)
        if label:
            geo = ET.SubElement(cell, "mxGeometry", relative="1", x="0", y="0")
            geo.set("as", "geometry")
            ET.SubElement(geo, "mxPoint", {"as": "offset"})
        else:
            geo = ET.SubElement(cell, "mxGeometry", relative="1")
            geo.set("as", "geometry")

    def save(self, filename):
        xml_str = ET.tostring(self.root, encoding='utf-8')
        parsed = minidom.parseString(xml_str)
        with open(filename, "w", encoding='utf-8') as f:
            f.write(parsed.toprettyxml(indent="  "))

# ==========================================
# FLOWCHART GENERATION
# ==========================================
doc = DrawIOFlowchart()

# Standard Flowchart Styles
S_TERM = "rounded=1;whiteSpace=wrap;html=1;arcSize=50;fillColor=#E1F5FE;strokeColor=#03A9F4;fontColor=#01579B;strokeWidth=2;fontStyle=1;"
S_PROC = "rounded=0;whiteSpace=wrap;html=1;fillColor=#F1F8E9;strokeColor=#8BC34A;fontColor=#33691E;strokeWidth=2;"
S_DEC  = "rhombus;whiteSpace=wrap;html=1;fillColor=#FFFDE7;strokeColor=#FBC02D;fontColor=#F57F17;strokeWidth=2;"
S_IO   = "shape=parallelogram;perimeter=parallelogramPerimeter;whiteSpace=wrap;html=1;fixedSize=1;fillColor=#F3E5F5;strokeColor=#9C27B0;fontColor=#4A148C;strokeWidth=2;"
S_LANE = "swimlane;whiteSpace=wrap;html=1;fillColor=#FAFAFA;strokeColor=#CFD8DC;fontColor=#263238;startSize=30;fontStyle=1;fontSize=14;"

# Edges
E_DEF = "strokeColor=#546E7A;strokeWidth=2;fontColor=#263238;"
DOWN  = "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"
LEFT  = "exitX=0;exitY=0.5;entryX=1;entryY=0.5;"
RIGHT = "exitX=1;exitY=0.5;entryX=0;entryY=0.5;"

# --- Swimlanes ---
doc.add_node("lane1", "ESP8266 Firmware (Rover Controller)", 50, 50, 260, 750, S_LANE)
doc.add_node("lane2", "ESP32 Firmware (Radar Node)", 350, 50, 260, 750, S_LANE)
doc.add_node("lane3", "ESP32-S3 Firmware (Radar Display)", 650, 50, 260, 750, S_LANE)

# =====================
# LANE 1: ESP8266 ROVER
# =====================
L1 = 110 # X center
doc.add_node("r_start", "System Power On", L1, 100, 140, 40, S_TERM)
doc.add_node("r_init", "Init PWM Pins,\nSerial RC Port", L1, 180, 140, 50, S_PROC)
doc.add_node("r_read", "Read CRSF/SBUS\nfrom ES900X", L1, 270, 140, 50, S_IO)
doc.add_node("r_dec", "Valid Signal\nReceived?", L1, 360, 140, 70, S_DEC)
doc.add_node("r_fail", "Motor Failsafe\n(Set PWM = 0)", 60, 450, 100, 50, S_PROC)  # Offset left
doc.add_node("r_mix", "Extract Ch1/Ch2\nCompute Diff-Mix", 200, 450, 100, 50, S_PROC) # Offset right
doc.add_node("r_pwm", "Write PWM Limits\nto L298N (IN1-IN4)", L1, 550, 140, 50, S_IO)
doc.add_node("r_delay", "Wait Frame Interval", L1, 640, 140, 50, S_PROC)

doc.add_edge("r_start", "r_init", E_DEF + DOWN)
doc.add_edge("r_init", "r_read", E_DEF + DOWN)
doc.add_edge("r_read", "r_dec", E_DEF + DOWN)
doc.add_edge("r_dec", "r_mix", E_DEF + "exitX=1;exitY=0.5;entryX=0.5;entryY=0;", "Yes")
doc.add_edge("r_dec", "r_fail", E_DEF + "exitX=0;exitY=0.5;entryX=0.5;entryY=0;", "No")
doc.add_edge("r_fail", "r_pwm", E_DEF + "exitX=0.5;exitY=1;entryX=0;entryY=0.5;")
doc.add_edge("r_mix", "r_pwm", E_DEF + "exitX=0.5;exitY=1;entryX=1;entryY=0.5;")
doc.add_edge("r_pwm", "r_delay", E_DEF + DOWN)
doc.add_edge("r_delay", "r_read", E_DEF + "exitX=0;exitY=0.5;entryX=0;entryY=0.5;edgeStyle=orthogonalEdgeStyle;routingCenterX=-40;") # Loop back


# =======================
# LANE 2: ESP32 RADAR
# =======================
L2 = 410 # X center
doc.add_node("ld_start", "System Power On", L2, 100, 140, 40, S_TERM)
doc.add_node("ld_init", "Init ESP-NOW Broadcast\nInit UART2 (256000)", L2, 180, 140, 50, S_PROC)
doc.add_node("ld_read", "Read Buffer from\nLD2450 Radar", L2, 270, 140, 50, S_IO)
doc.add_node("ld_dec", "Valid Target\nHeader Found?", L2, 360, 140, 70, S_DEC)
doc.add_node("ld_filt", "Apply Persistence Filter\nSuppress Ghosts", L2, 470, 140, 50, S_PROC)
doc.add_node("ld_pack", "Pack Data Array\n(Target ID, X, Y)", L2, 550, 140, 50, S_PROC)
doc.add_node("ld_send", "Broadcast via\nESP-NOW", L2, 640, 140, 50, S_IO)

doc.add_edge("ld_start", "ld_init", E_DEF + DOWN)
doc.add_edge("ld_init", "ld_read", E_DEF + DOWN)
doc.add_edge("ld_read", "ld_dec", E_DEF + DOWN)
doc.add_edge("ld_dec", "ld_filt", E_DEF + DOWN, "Yes")
doc.add_edge("ld_dec", "ld_read", E_DEF + "exitX=1;exitY=0.5;entryX=1;entryY=0.5;edgeStyle=orthogonalEdgeStyle;routingCenterX=40;", "No")
doc.add_edge("ld_filt", "ld_pack", E_DEF + DOWN)
doc.add_edge("ld_pack", "ld_send", E_DEF + DOWN)
doc.add_edge("ld_send", "ld_read", E_DEF + "exitX=0;exitY=0.5;entryX=0;entryY=0.5;edgeStyle=orthogonalEdgeStyle;routingCenterX=-40;") # Loop back


# =======================
# LANE 3: ESP32-S3 DISPLAY
# =======================
L3 = 710 # X center
doc.add_node("s_start", "Power On", L3, 100, 140, 40, S_TERM)
doc.add_node("s_init", "Init TFT (LovyanGFX)\nInit ESP-NOW (Recv)", L3, 160, 140, 50, S_PROC)

doc.add_node("s_rx", "ESP-NOW Callback\n(Interrupt Handler)", L3, 240, 140, 50, S_IO)
doc.add_node("s_buf", "Dump Targets\nInto Memory Array", L3, 310, 140, 50, S_PROC)

doc.add_node("s_loop", "Main GUI Loop", L3, 390, 140, 40, S_TERM)
doc.add_node("s_clr", "Fill Screen Black\nDraw Distance Rings", L3, 460, 140, 50, S_PROC)
doc.add_node("s_anim", "Draw Hardware\nSweep Line", L3, 530, 140, 50, S_PROC)
doc.add_node("s_draw", "Map Target X/Y\nto Canvas Pixels", L3, 600, 140, 50, S_PROC)
doc.add_node("s_push", "Update Display", L3, 670, 140, 50, S_IO)

doc.add_edge("s_start", "s_init", E_DEF + DOWN)
doc.add_edge("s_init", "s_rx", E_DEF + DOWN)
doc.add_edge("s_rx", "s_buf", E_DEF + DOWN)
doc.add_edge("s_buf", "s_rx", E_DEF + "exitX=1;exitY=0.5;entryX=1;entryY=0.5;edgeStyle=orthogonalEdgeStyle;", "Await Next")

doc.add_edge("s_loop", "s_clr", E_DEF + DOWN)
doc.add_edge("s_clr", "s_anim", E_DEF + DOWN)
doc.add_edge("s_anim", "s_draw", E_DEF + DOWN)
doc.add_edge("s_draw", "s_push", E_DEF + DOWN)
doc.add_edge("s_push", "s_loop", E_DEF + "exitX=0;exitY=0.5;entryX=0;entryY=0.5;edgeStyle=orthogonalEdgeStyle;routingCenterX=-40;")

# Inter-lane wireless interaction dashed lines
W_LNK = "strokeColor=#8E44AD;strokeWidth=2;dashed=1;dashPattern=1 2;"
doc.add_edge("ld_send", "s_rx", W_LNK + "exitX=1;exitY=0.5;entryX=0;entryY=0.5;", "MAC Broadcast")

doc.save("software_flowchart.drawio")
