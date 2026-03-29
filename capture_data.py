"""
capture_data.py  —  Live SSE data logger for LD2450 Radar
Usage:  python capture_data.py --ip 10.174.224.33 --duration 60 --out results.csv
Captures raw + Kalman-filtered target data from the ESP32 SSE stream.
"""
import socket, json, time, csv, argparse, sys
from datetime import datetime

def parse_args():
    p = argparse.ArgumentParser(description='LD2450 SSE data capture')
    p.add_argument('--ip',       default='10.174.224.33', help='ESP32 IP address')
    p.add_argument('--duration', type=int, default=60,    help='Capture duration (seconds)')
    p.add_argument('--out',      default='results.csv',   help='Output CSV filename')
    return p.parse_args()

def connect(ip, port=80):
    sock = socket.create_connection((ip, port), timeout=5)
    sock.sendall((
        f'GET /events HTTP/1.1\r\n'
        f'Host: {ip}\r\n'
        f'Accept: text/event-stream\r\n'
        f'Connection: keep-alive\r\n\r\n'
    ).encode())
    return sock

def parse_sse(buf):
    events = []
    buf = buf.replace(b'\r\n', b'\n')   # normalize CRLF → LF (ESPHome uses CRLF)
    while b'\n\n' in buf:
        block, buf = buf.split(b'\n\n', 1)
        event = {}
        for line in block.split(b'\n'):
            line = line.decode(errors='ignore').strip()
            if line.startswith('event:'):
                event['event'] = line[6:].strip()
            elif line.startswith('data:'):
                try:
                    event['data'] = json.loads(line[5:].strip())
                except:
                    pass
        if 'data' in event:
            events.append(event['data'])
    return events, buf

def main():
    args = parse_args()
    print(f"Connecting to {args.ip}:80 …")
    try:
        sock = connect(args.ip)
    except Exception as e:
        print(f"Cannot connect: {e}"); sys.exit(1)
    sock.settimeout(3)

    # State buckets
    state = {}
    rows  = []
    start = time.time()
    buf   = b''

    FIELDS = [
        # raw
        'target1_x','target1_y','target1_speed',
        'target2_x','target2_y','target2_speed',
        'target3_x','target3_y','target3_speed',
        # analytics
        'target1_threat','target2_threat','target3_threat','system_threat',
        'target1_pred_x','target1_pred_y',
        'target2_pred_x','target2_pred_y',
        'target3_pred_x','target3_pred_y',
        'target1_filtered_speed','target2_filtered_speed','target3_filtered_speed',
        'target1_class','target2_class','target3_class',
        'target1_alert','target2_alert','target3_alert',
    ]

    print(f"Capturing for {args.duration}s  →  {args.out}")
    print("Move in front of the sensor now!\n")

    snap_interval = 0.2           # snapshot every 200ms (matches analytics update rate)
    last_snap = time.time()
    snap_count = 0

    try:
        while time.time() - start < args.duration:
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                buf += chunk
            except socket.timeout:
                pass

            events, buf = parse_sse(buf)
            for d in events:
                eid = d.get('id','')
                val = d.get('value', d.get('state',''))
                # strip domain prefix  e.g. "sensor-_target1_x" → key "target1_x"
                key = eid.replace('sensor-_','').replace('text_sensor-_','')
                key = key.replace('_ml_class', '_class')
                state[key] = val

            # Snapshot at 5 Hz
            if time.time() - last_snap >= snap_interval:
                row = {'timestamp': round(time.time() - start, 3)}
                for f in FIELDS:
                    row[f] = state.get(f, '')
                rows.append(row)
                snap_count += 1
                last_snap = time.time()
                elapsed = time.time() - start
                pct = int(elapsed / args.duration * 40)
                bar = '█'*pct + '░'*(40-pct)
                sys.stdout.write(f"\r[{bar}] {elapsed:.0f}s / {args.duration}s  ({snap_count} samples)")
                sys.stdout.flush()

    except KeyboardInterrupt:
        print("\nInterrupted early.")
    finally:
        sock.close()

    print(f"\n\nWriting {len(rows)} rows to {args.out} …")
    with open(args.out, 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['timestamp'] + FIELDS)
        w.writeheader()
        w.writerows(rows)

    print(f"Done!  Now run:  python plot_results.py --csv {args.out}")

if __name__ == '__main__':
    main()
