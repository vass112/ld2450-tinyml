from capture_data import parse_sse, connect
import time

sock = connect("10.174.224.33")
sock.settimeout(2.0)
buf = b""
start = time.time()
state = {}
while time.time() - start < 5:
    try:
        buf += sock.recv(4096)
    except:
        pass
    events, buf = parse_sse(buf)
    for d in events:
        eid = d.get('id','')
        val = d.get('value', d.get('state',''))
        key = eid.replace('sensor-_','').replace('text_sensor-_','')
        key = key.replace('_ml_class', '_class')
        state[key] = val
print("Captured keys:")
for k, v in state.items():
    if "class" in k or "alert" in k:
        print(f"{k}: {v}")
