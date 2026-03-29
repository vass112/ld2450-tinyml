import gzip

with open('radar_gui.html', 'rb') as f:
    html_data = f.read()

gzipped = gzip.compress(html_data)

with open('ESP32_LD2450/radar_html.h', 'w') as f:
    f.write('#pragma once\n')
    f.write('#include <Arduino.h>\n') # include stdint
    f.write('#include <stddef.h>\n')
    f.write('const uint8_t RADAR_HTML[] __attribute__((aligned(4))) = {\n')
    f.write(','.join(f"0x{b:02x}" for b in gzipped))
    f.write('\n};\n')
    f.write('const size_t RADAR_HTML_SIZE = sizeof(RADAR_HTML);\n')

print(f"Generated radar_html.h ({len(gzipped)} bytes)")
