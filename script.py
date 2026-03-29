import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(5.0)
s.connect(("10.174.224.33", 80))
s.sendall(b"GET /events HTTP/1.1\r\nHost: 10.174.224.33\r\n\r\n")
buf = b""
try:
    for _ in range(50):
        buf += s.recv(4096)
except: pass
for line in buf.decode("utf-8", "ignore").split("\n"):
    if "ml_class" in line or "alert" in line:
        print(line)
