"""Quick debug: show what the SSE stream actually sends for target entities"""
import socket, json, time

sock = socket.create_connection(('10.174.224.33', 80), timeout=5)
sock.sendall(b'GET /events HTTP/1.1\r\nHost: 10.174.224.33\r\nAccept: text/event-stream\r\nConnection: keep-alive\r\n\r\n')
sock.settimeout(3)
buf = b''
start = time.time()
print("Listening for 12 seconds — STAND IN FRONT OF SENSOR NOW...")
while time.time() - start < 12:
    try:
        buf += sock.recv(8192)
    except:
        break
sock.close()

text = buf.decode(errors='ignore')
seen = set()
print("\n--- All unique entity state events ---")
for line in text.split('\n'):
    line = line.strip()
    if line.startswith('data:') and '{' in line:
        try:
            d = json.loads(line[5:].strip())
            if 'id' in d and d['id'] not in seen:
                seen.add(d['id'])
                print(f"  id={d['id']!r:50s}  value={d.get('value','?')}")
        except:
            pass

print(f"\nTotal unique entities seen: {len(seen)}")
print("\n--- Non-zero target values ---")
for line in text.split('\n'):
    line = line.strip()
    if line.startswith('data:') and 'target' in line.lower() and '{' in line:
        try:
            d = json.loads(line[5:].strip())
            val = d.get('value', 0)
            if val != 0 and val != '':
                print(f"  {d.get('id')} = {val}")
        except:
            pass
