import xml.etree.ElementTree as ET
from xml.dom import minidom

class DrawIO:
    def __init__(self):
        self.root = ET.Element("mxfile", version="14.6.13", type="device")
        self.diagram = ET.SubElement(self.root, "diagram", name="Page-1")
        self.model = ET.SubElement(self.diagram, "mxGraphModel", dx="1422", dy="794", grid="1", gridSize="10", guides="1", tooltips="1", connect="1", arrows="1", fold="1", page="1", pageScale="1", pageWidth="827", pageHeight="1169", math="0", shadow="0")
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
        id_str = f"edge_{self.edge_idx}"
        full_style = f"edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;{style_str}"
        cell = ET.SubElement(self.root_cell, "mxCell", id=id_str, value=label, style=full_style, edge="1", parent="1", source=src_id, target=tgt_id)
        # Add labels to edge if exists
        geo = ET.SubElement(cell, "mxGeometry", relative="1")
        geo.set("as", "geometry")

    def save(self, filename):
        xml_str = ET.tostring(self.root, encoding='utf-8')
        parsed = minidom.parseString(xml_str)
        with open(filename, "w", encoding='utf-8') as f:
            f.write(parsed.toprettyxml(indent="  "))


# ==========================================
# 1. GENERATE ROVER DIAGRAM
# ==========================================
doc = DrawIO()

# Styles
S_CHIP = "rounded=1;whiteSpace=wrap;html=1;fillColor=#239B56;strokeColor=#186A3B;fontColor=#ffffff;strokeWidth=2;"
S_DRV  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#CB4335;strokeColor=#922B21;fontColor=#ffffff;strokeWidth=2;"
S_BAT  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#34495E;strokeColor=#273746;fontColor=#F1C40F;strokeWidth=2;"
S_MOT  = "shape=cylinder3;whiteSpace=wrap;html=1;boundedLbl=1;backgroundOutline=1;size=15;fillColor=#95A5A6;strokeColor=#7F8C8D;fontColor=#ffffff;strokeWidth=2;"
S_SEN  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#17202A;strokeColor=#000000;fontColor=#ffffff;strokeWidth=2;"
S_CAM  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#2874A6;strokeColor=#1B4F72;fontColor=#ffffff;strokeWidth=2;"

# Components (Spaced out optimally to prevent wire tangles)
doc.add_node("c_bat", "<b>2S LiPo Battery</b><br>7.4V Power", 50, 250, 120, 60, S_BAT)

doc.add_node("c_rx", "<b>ES900X RX</b><br>(Telemetry/Control)", 150, 100, 120, 60, S_SEN)
doc.add_node("c_node", "<b>ESP8266 NodeMCU</b><br>(Rover Controller)", 350, 100, 140, 80, S_CHIP)
doc.add_node("c_esp", "<b>ESP32 Node</b><br>(Radar Processor)", 550, 100, 140, 80, S_SEN)
doc.add_node("c_ld", "<b>LD2450</b><br>(Radar Sensor)", 750, 100, 100, 60, S_SEN)

doc.add_node("c_cam", "<b>FPV Camera</b>", 250, 250, 100, 60, S_CAM)
doc.add_node("c_vtx", "<b>5.8GHz VTX</b>", 450, 250, 100, 60, S_CAM)

doc.add_node("c_drv", "<b>HW-354 L298N</b><br>Dual H-Bridge Motor Driver", 350, 450, 140, 80, S_DRV)

doc.add_node("c_mtl", "<b>12V Geared</b><br>Motor (L-Top)", 100, 400, 80, 80, S_MOT)
doc.add_node("c_mbl", "<b>12V Geared</b><br>Motor (L-Bot)", 100, 550, 80, 80, S_MOT)
doc.add_node("c_mtr", "<b>12V Geared</b><br>Motor (R-Top)", 650, 400, 80, 80, S_MOT)
doc.add_node("c_mbr", "<b>12V Geared</b><br>Motor (R-Bot)", 650, 550, 80, 80, S_MOT)


# Edges (Auto-routed by Draw.io)
E_VCC = "strokeColor=#E74C3C;strokeWidth=3;"
E_GND = "strokeColor=#2C3E50;strokeWidth=3;"
E_3V3 = "strokeColor=#F39C12;strokeWidth=2.5;"
E_PWM = "strokeColor=#8E44AD;strokeWidth=2.5;"
E_SIG = "strokeColor=#27AE60;strokeWidth=2;"
E_VID = "strokeColor=#F1C40F;strokeWidth=2;"

# Precise connection point routing (exit/entry flags) to stop messy tangle rendering
P_RL = "exitX=1;exitY=0.5;entryX=0;entryY=0.5;"
P_LR = "exitX=0;exitY=0.5;entryX=1;entryY=0.5;"
P_DT = "exitX=0.5;exitY=1;entryX=0.5;entryY=0;"
P_BT = "exitX=0.5;exitY=1;entryX=0.5;entryY=0;" # bottom to top

# Power Routing (from battery right side to various points)
doc.add_edge("c_bat", "c_node", E_VCC + "exitX=1;exitY=0.25;entryX=0;entryY=0.75;", "7.4V")
doc.add_edge("c_bat", "c_drv", E_VCC + "exitX=1;exitY=0.75;entryX=0;entryY=0.25;", "7.4V (to VMOT)")
doc.add_edge("c_bat", "c_esp", E_VCC + "exitX=1;exitY=0.5;entryX=0;entryY=0.75;", "7.4V")
doc.add_edge("c_bat", "c_cam", E_VCC + P_RL, "7.4V")
doc.add_edge("c_bat", "c_vtx", E_VCC + "exitX=1;exitY=0.5;entryX=0;entryY=1;", "7.4V")

# Common GND
doc.add_edge("c_bat", "c_drv", E_GND + "exitX=1;exitY=0.8;entryX=0;entryY=0.5;", "GND")
doc.add_edge("c_bat", "c_node", E_GND + "exitX=1;exitY=0.2;entryX=0;entryY=0.8;", "GND")

# Logic Power Route
doc.add_edge("c_node", "c_rx", E_3V3 + P_LR, "3.3V Power")
doc.add_edge("c_esp", "c_ld", E_3V3 + P_RL, "3.3V Power")

# Logic Signal Route
doc.add_edge("c_rx", "c_node", E_SIG + "exitX=1;exitY=0.2;entryX=0;entryY=0.2;", "UART TX -> RX")
doc.add_edge("c_esp", "c_ld", E_SIG + "exitX=1;exitY=0.2;entryX=0;entryY=0.2;", "UART TX2->RX")
doc.add_edge("c_ld", "c_esp", E_SIG + "exitX=0;exitY=0.8;entryX=1;entryY=0.8;", "UART TX->RX2")

# Motor Control (PWM)
doc.add_edge("c_node", "c_drv", E_PWM + P_DT, "D1-D4 -> IN1-IN4")

# Motor Output Route
doc.add_edge("c_drv", "c_mtl", E_VCC + P_LR, "OUT1/2")
doc.add_edge("c_drv", "c_mbl", E_VCC + "exitX=0;exitY=0.75;entryX=1;entryY=0.5;", "OUT1/2")
doc.add_edge("c_drv", "c_mtr", E_VCC + P_RL, "OUT3/4")
doc.add_edge("c_drv", "c_mbr", E_VCC + "exitX=1;exitY=0.75;entryX=0;entryY=0.5;", "OUT3/4")

# FPV
doc.add_edge("c_cam", "c_vtx", E_VID + P_RL, "Video Out")

doc.save("rover_wiring_diagram_editable.drawio")


# ==========================================
# 2. GENERATE TX DIAGRAM
# ==========================================
dtx = DrawIO()

S_DISP = "rounded=1;whiteSpace=wrap;html=1;fillColor=#2C3E50;strokeColor=#1A5276;fontColor=#ffffff;strokeWidth=3;"
S_TAR  = "rounded=1;whiteSpace=wrap;html=1;fillColor=#7F8C8D;strokeColor=#616A6B;fontColor=#ffffff;strokeWidth=2;"
S_PW   = "rounded=1;whiteSpace=wrap;html=1;fillColor=#ECF0F1;strokeColor=#BDC3C7;fontColor=#2C3E50;strokeWidth=2;"

dtx.add_node("t_pb", "<b>5V USB Bank</b><br>Power Source", 50, 130, 120, 60, S_PW)
dtx.add_node("t_disp", "<b>ELECROW 7\" Display</b><br>(ESP32-S3 Radar Interface)", 300, 100, 200, 120, S_DISP)
dtx.add_node("t_tar", "<b>FrSky Taranis QX7</b><br>(RC Controller)", 50, 300, 160, 100, S_TAR)
dtx.add_node("t_gog", "<b>Analog FPV Goggles</b><br>5.8GHz Receiver", 500, 300, 160, 80, S_SEN)
dtx.add_node("t_rov", "<b>ROVER MOBILE BASE</b>", 300, 500, 200, 60, S_CHIP) # Destination stub

dtx.add_edge("t_pb", "t_disp", E_VCC + P_RL, "5V USB-C")
dtx.add_edge("t_disp", "t_pb", E_GND + "exitX=0;exitY=0.75;entryX=1;entryY=0.75;", "GND")

W_LNK = "strokeColor=#7F8C8D;strokeWidth=3;dashed=1;dashPattern=1 2;"
dtx.add_edge("t_tar", "t_rov", W_LNK + P_DT, "CRSF/868MHz Command Downlink")
dtx.add_edge("t_rov", "t_disp", W_LNK + P_BT, "ESP-NOW (2.4GHz) Radar Target Data")
dtx.add_edge("t_rov", "t_gog", W_LNK + "exitX=1;exitY=0;entryX=0.5;entryY=1;", "Analog 5.8GHz FPV Video Stream")

dtx.save("operator_station_editable.drawio")
