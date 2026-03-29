import socket, json
sock = socket.create_connection(('10.174.224.33', 80))
sock.sendall(b'GET /events HTTP/1.1\r\nHost: 10.174.224.33\r\nAccept: text/event-stream\r\n\r\n')
sock.settimeout(2.0)
buf = b''
for _ in range(30):
    try:
        buf += sock.recv(4096)
    except Exception as e:
        break
for line in buf.split(b'\n'):
    if b'data: {' in line:
        line = line.decode('utf-8', errors='ignore')
        try:
            d = json.loads(line[5:])
            print(d.get('id', ''))
        except:
            pass
