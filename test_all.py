import urllib.request, json, time

req = urllib.request.Request("http://10.174.224.33/events", headers={'Accept': 'text/event-stream'})
with urllib.request.urlopen(req, timeout=5) as r:
    start = time.time()
    for _ in range(500):
        try:
            line = r.readline().decode('utf-8', 'ignore').strip()
            if line.startswith('data:'):
                try: 
                    d = json.loads(line[5:])
                    if 'ml_class' in d.get('id', ''):
                        import sys
                        sys.stdout.write(str(d) + "\n")
                        sys.stdout.flush()
                except: pass
        except: break
