import urllib.request
import json
import time

url = "http://10.174.224.33/events"
print("Connecting...")
req = urllib.request.Request(url, headers={'Accept': 'text/event-stream'})
with urllib.request.urlopen(req, timeout=5) as response:
    start = time.time()
    for line in response:
        line = line.decode('utf-8', errors='ignore').strip()
        if line.startswith('data:'):
            try:
                d = json.loads(line[5:].strip())
                id_val = d.get('id', '')
                if 'class' in id_val or 'alert' in id_val:
                    print(d)
            except:
                pass
        if time.time() - start > 3:
            break
