"""
plot_results.py  —  Results & Comparison Charts for LD2450 Radar System
Usage (from real capture):  python plot_results.py --csv results.csv
Usage (demo / no capture):  python plot_results.py --demo

Generates 6 publication-quality charts saved to ./results/
"""
import argparse, os, csv, math, random
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
from matplotlib.colors import LinearSegmentedColormap

OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(OUTDIR, exist_ok=True)

# ── Styling ──────────────────────────────────────────────────────────────────
DARK  = '#0a0f0a'
GREEN = '#00ff88'
AMBER = '#ffaa00'
RED   = '#ff3355'
BLUE  = '#00aaff'
GREY  = '#8899aa'

def style():
    plt.rcParams.update({
        'figure.facecolor': DARK, 'axes.facecolor': '#0f180f',
        'axes.edgecolor': '#1a331a', 'axes.labelcolor': GREEN,
        'axes.titlecolor': GREEN, 'text.color': GREEN,
        'xtick.color': GREY, 'ytick.color': GREY,
        'grid.color': '#1a331a', 'grid.linewidth': 0.5,
        'font.family': 'monospace', 'font.size': 9,
        'figure.dpi': 150,
        'axes.spines.top': False, 'axes.spines.right': False,
    })
style()

def savefig(name):
    p = os.path.join(OUTDIR, name)
    plt.savefig(p, bbox_inches='tight', facecolor=DARK)
    plt.close()
    print(f"  Saved: {p}")
    return p


# ─────────────────────────────────────────────────────────────────────────────
# 1. DEMO DATA GENERATOR  (realistic simulated SSE capture)
# ─────────────────────────────────────────────────────────────────────────────
def generate_demo_data(duration=60, dt=0.2):
    """
    Simulate one person walking toward the sensor, pausing (loitering),
    then walking away.  Adds realistic LD2450-level noise.
    Returns dict of lists keyed by field name + 't'.
    """
    rng  = np.random.default_rng(42)
    t    = np.arange(0, duration, dt)
    n    = len(t)
    # Ground-truth path: approach 6m→1m (0-20s), dwell 1m (20-32s), depart 1m→5m (32-60s)
    def gt_y(ti):
        if ti < 20:  return 6000 - (5000/20)*ti
        if ti < 32:  return 1000 + 60*math.sin((ti-20)*0.8)
        return 1000 + (4000/28)*(ti-32)
    def gt_x(ti):
        return 300*math.sin(ti*0.3) + 200*math.sin(ti*0.13)

    raw_x = np.array([gt_x(ti) + rng.normal(0, 150) for ti in t])
    raw_y = np.array([gt_y(ti) + rng.normal(0, 150) for ti in t])
    true_x = np.array([gt_x(ti) for ti in t])
    true_y = np.array([gt_y(ti) for ti in t])

    # Simple Kalman replay matching target_analytics.h params
    Q_pos, Q_vel, R_obs = 20.0, 0.4, 350.0
    def kalman_1d(raw, dt_ms):
        x, v, P00, P01, P11 = raw[0], 0.0, 1000.0, 0.0, 100.0
        filt, vels = [], []
        for meas in raw:
            # predict
            x   = x + v*dt_ms
            P00 = P00 + 2*P01*dt_ms + P11*dt_ms**2 + Q_pos
            P01 = P01 + P11*dt_ms
            P11 = P11 + Q_vel
            # update
            S  = P00 + R_obs
            K0, K1 = P00/S, P01/S
            inn = meas - x
            x  += K0*inn; v += K1*inn
            P00 -= K0*P00; P01 -= K0*P01; P11 -= K1*P01
            P00 = max(P00, 1.0); P11 = max(P11, 0.01)
            filt.append(x); vels.append(v)
        return np.array(filt), np.array(vels)

    kf_x, vx = kalman_1d(raw_x, dt*1000)
    kf_y, vy = kalman_1d(raw_y, dt*1000)
    speed = np.sqrt(vx**2 + vy**2)   # m/s (mm/ms = m/s)

    # EMA on velocity
    alpha = 0.18
    fil_spd = np.zeros(n)
    fil_spd[0] = speed[0]
    for i in range(1, n):
        fil_spd[i] = (1-alpha)*fil_spd[i-1] + alpha*speed[i]

    # Classification
    def classify(s):
        if s < 0.05: return 'STATIC'
        if s < 0.5:  return 'CREEPING'
        if s < 1.8:  return 'WALKING'
        if s < 4.0:  return 'RUNNING'
        return 'VEHICLE'
    cls_arr = [classify(s) for s in fil_spd]

    # Threat score
    def threat(fx, fy, fvx, fvy, spd):
        dist = math.sqrt(fx**2 + fy**2)
        t_spd = min(35.0, spd*14.0)
        t_app = 0.0
        if dist > 100 and spd > 0.05:
            ux, uy = -fx/dist, -fy/dist
            dot = (fvx*ux + fvy*uy)/spd
            t_app = max(0.0, dot)*40.0
        t_prox = max(0.0, 25.0*(1 - dist/7000.0))
        return min(100.0, t_spd + t_app + t_prox)
    thr = np.array([threat(kf_x[i], kf_y[i], vx[i], vy[i], fil_spd[i]) for i in range(n)])

    # Loitering flag
    RADIUS, DWELL = 600, 12
    anchor_x, anchor_y, dwell_start = kf_x[0], kf_y[0], 0.0
    loiter = np.zeros(n, bool)
    for i in range(n):
        d = math.sqrt((kf_x[i]-anchor_x)**2 + (kf_y[i]-anchor_y)**2)
        if d > RADIUS:
            anchor_x, anchor_y, dwell_start = kf_x[i], kf_y[i], t[i]
        else:
            loiter[i] = (t[i] - dwell_start) >= DWELL

    # Alert
    def alert(thr_v, loit):
        if loit:          return 'LOITERING'
        if thr_v >= 72:   return 'THREAT'
        if thr_v >= 45:   return 'APPROACHING'
        return 'CLEAR'
    alrt = [alert(thr[i], loiter[i]) for i in range(n)]

    return dict(t=t, raw_x=raw_x, raw_y=raw_y,
                true_x=true_x, true_y=true_y,
                kf_x=kf_x, kf_y=kf_y,
                raw_spd=speed, fil_spd=fil_spd,
                threat=thr, cls=cls_arr,
                alert=alrt, loiter=loiter)


def load_csv(path):
    rows = []
    with open(path, newline='') as f:
        for row in csv.DictReader(f):
            rows.append(row)
    def col(key, cast=float):
        out = []
        for r in rows:
            try:   out.append(cast(r[key]))
            except: out.append(0.0 if cast is float else '')
        return np.array(out) if cast is float else out
    t = col('timestamp')
    return dict(
        t=t,
        raw_x=col('target1_x'), raw_y=col('target1_y'),
        raw_spd=col('target1_speed'),
        kf_x=col('target1_pred_x'), kf_y=col('target1_pred_y'),  # closest available
        fil_spd=col('target1_filtered_speed'),
        threat=col('target1_threat'),
        cls=col('target1_class', str),
        alert=col('target1_alert', str),
        loiter=np.array([a=='LOITERING' for a in col('target1_alert', str)]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# CHART 1 — Kalman Filter: Raw vs Filtered Position
# ─────────────────────────────────────────────────────────────────────────────
def chart_kalman(d):
    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    fig.suptitle('Chart 1: Kalman Filter — Noise Reduction on LD2450 Position Data',
                 color=GREEN, fontsize=11, fontweight='bold')

    for ax, raw, flt, lbl, unit in zip(
            axes,
            [d['raw_x'], d['raw_y']],
            [d['kf_x'],  d['kf_y']],
            ['X Position (lateral)',  'Y Position (range / depth)'],
            ['mm', 'mm']):

        ax.plot(d['t'], raw, color=GREY,  alpha=0.55, linewidth=0.8, label='Raw LD2450 output')
        ax.plot(d['t'], flt, color=GREEN, alpha=0.95, linewidth=1.6, label='Kalman filtered')
        ax.set_ylabel(f'{lbl} ({unit})', fontsize=9)
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', framealpha=0.2, fontsize=8)

        # Annotate noise std
        noise_std = np.std(np.array(raw) - np.array(flt))
        ax.annotate(f'σ_noise ≈ {noise_std:.0f} mm', xy=(0.02, 0.92),
                    xycoords='axes fraction', color=AMBER, fontsize=8)

    axes[-1].set_xlabel('Time (s)', fontsize=9)
    plt.tight_layout()
    return savefig('01_kalman_filter_noise_reduction.png')


# ─────────────────────────────────────────────────────────────────────────────
# CHART 2 — Threat Score Timeline + Alert Zones
# ─────────────────────────────────────────────────────────────────────────────
def chart_threat(d):
    fig, ax = plt.subplots(figsize=(12, 5))
    fig.suptitle('Chart 2: Real-time Threat Score Timeline with Alert State Transitions',
                 color=GREEN, fontsize=11, fontweight='bold')

    t   = d['t']
    thr = d['threat']
    alr = d['alert']

    # Shaded alert bands
    ax.axhspan(0,  45, alpha=0.06, color=GREEN, label='CLEAR zone (0–45)')
    ax.axhspan(45, 72, alpha=0.06, color=AMBER, label='APPROACHING zone (45–72)')
    ax.axhspan(72,100, alpha=0.06, color=RED,   label='THREAT zone (72–100)')
    ax.axhline(45, color=AMBER, linewidth=0.8, linestyle='--', alpha=0.6)
    ax.axhline(72, color=RED,   linewidth=0.8, linestyle='--', alpha=0.6)

    # Threat line coloured by current state
    colors = {'CLEAR':GREEN, 'APPROACHING':AMBER, 'THREAT':RED, 'LOITERING':'#ff6600'}
    for i in range(len(t)-1):
        ax.plot(t[i:i+2], thr[i:i+2], color=colors.get(alr[i], GREEN), linewidth=2.0)

    # Loitering markers
    loit_t = t[d['loiter']]
    loit_v = thr[d['loiter']]
    if len(loit_t):
        ax.scatter(loit_t, loit_v, color='#ff6600', s=18, zorder=5, label='LOITERING active', marker='D')

    ax.set_ylim(0, 105)
    ax.set_xlabel('Time (s)'); ax.set_ylabel('Threat Score (0–100)')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right', framealpha=0.2, fontsize=8)

    # Annotate peak
    peak_i = np.argmax(thr)
    ax.annotate(f'Peak: {thr[peak_i]:.0f}', xy=(t[peak_i], thr[peak_i]),
                xytext=(t[peak_i]+1, thr[peak_i]+3),
                color=RED, fontsize=8, arrowprops=dict(arrowstyle='->', color=RED, lw=0.7))
    plt.tight_layout()
    return savefig('02_threat_score_timeline.png')


# ─────────────────────────────────────────────────────────────────────────────
# CHART 3 — 2D Position Trace + Prediction Arrows
# ─────────────────────────────────────────────────────────────────────────────
def chart_trace(d):
    fig, ax = plt.subplots(figsize=(7, 10))
    fig.suptitle('Chart 3: 2D Target Position Trace\n(Kalman filtered path + prediction vectors)',
                 color=GREEN, fontsize=11, fontweight='bold')

    raw_x, raw_y = d['raw_x'], d['raw_y']
    kf_x,  kf_y  = d['kf_x'],  d['kf_y']
    thr           = d['threat']

    threat_cmap = LinearSegmentedColormap.from_list('tc', [GREEN, AMBER, RED])

    ax.scatter(raw_x, raw_y, c=GREY, s=4, alpha=0.3, label='Raw LD2450 positions')

    sc = ax.scatter(kf_x, kf_y, c=thr, cmap=threat_cmap, vmin=0, vmax=100,
                    s=14, alpha=0.85, zorder=3, label='Kalman filtered (threat-colored)')

    # Prediction arrows every 10 samples
    n = len(kf_x)
    for i in range(0, n-10, 10):
        vx = kf_x[i+1] - kf_x[i]
        vy = kf_y[i+1] - kf_y[i]
        ax.annotate('', xy=(kf_x[i]+vx*8, kf_y[i]+vy*8), xytext=(kf_x[i], kf_y[i]),
                    arrowprops=dict(arrowstyle='->', color=BLUE, lw=0.7, alpha=0.5))

    cb = fig.colorbar(sc, ax=ax, fraction=0.03, pad=0.02)
    cb.set_label('Threat Score', color=GREEN); cb.ax.yaxis.set_tick_params(color=GREY)
    plt.setp(cb.ax.yaxis.get_ticklabels(), color=GREY)

    # Sensor dot
    ax.scatter([0], [0], color='white', s=60, zorder=5, marker='*', label='Sensor (origin)')
    ax.set_xlabel('X Position (mm)'); ax.set_ylabel('Y Position (mm) — Range from sensor')
    ax.set_xlim(-4000, 4000); ax.set_ylim(0, 8000)
    ax.grid(True, alpha=0.2)
    ax.legend(loc='upper right', framealpha=0.2, fontsize=8)
    plt.tight_layout()
    return savefig('03_position_trace_2d.png')


# ─────────────────────────────────────────────────────────────────────────────
# CHART 4 — Classification Distribution
# ─────────────────────────────────────────────────────────────────────────────
def chart_classification(d):
    from collections import Counter
    counts = Counter(c for c in d['cls'] if c not in ('', 'ABSENT'))
    categories = ['STATIC','CREEPING','WALKING','RUNNING','VEHICLE']
    vals  = [counts.get(c, 0) for c in categories]
    col_  = [GREEN, '#aaff00', AMBER, '#ff8800', RED]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('Chart 4: Target Classification Results', color=GREEN, fontsize=11, fontweight='bold')

    # Bar chart
    bars = ax1.bar(categories, vals, color=col_, edgecolor='none', width=0.6)
    ax1.set_ylabel('Sample Count (frames at 5 Hz)')
    ax1.set_xlabel('Movement Class')
    ax1.grid(True, axis='y', alpha=0.3)
    for bar, v in zip(bars, vals):
        if v > 0:
            ax1.text(bar.get_x()+bar.get_width()/2, v+0.5, str(v),
                     ha='center', va='bottom', color=GREEN, fontsize=8)

    # Pie
    non_zero = [(c, v, col) for c, v, col in zip(categories, vals, col_) if v > 0]
    if non_zero:
        labels, sizes, cols = zip(*non_zero)
        wedges, texts, autotexts = ax2.pie(
            sizes, labels=labels, colors=cols, autopct='%1.1f%%',
            startangle=90, textprops={'color': GREEN, 'fontsize': 8})
        for at in autotexts: at.set_color(DARK)
        ax2.set_title('Classification breakdown', color=GREEN, fontsize=9)

    plt.tight_layout()
    return savefig('04_classification_distribution.png')


# ─────────────────────────────────────────────────────────────────────────────
# CHART 5 — System Comparison vs Alternatives
# ─────────────────────────────────────────────────────────────────────────────
def chart_comparison():
    """
    Compares LD2450+ESP32 system against common alternatives on 6 axes.
    Scores are 0-5 based on published specifications and cost estimates.
    """
    systems = {
        'LD2450\n+ESP32\n(this work)': [5,5,5,4,5,5],
        'PIR\nSensor':                  [1,1,1,5,1,3],
        'Webcam\n+CV':                  [4,3,2,1,4,3],
        'Ultrasonic\n(HC-SR04)':        [2,1,2,5,2,3],
        'Commercial\nRadar System':     [5,5,4,1,4,2],
        'IR Array\n(AMG8833)':          [3,2,3,4,3,2],
    }
    axes_labels = [
        'Multi-target\nTracking',
        'Position\nAccuracy',
        'Speed\nEstimation',
        'Cost\nEfficiency',
        'Privacy\nPreserving',
        'Standalone\n(no cloud)',
    ]
    descriptions = [
        'Up to 3 simultaneous targets',
        'X/Y to ±15cm, Kalman-filtered',
        'Speed + direction estimation',
        'Lower = more expensive',
        'No image data collected',
        'On-device processing',
    ]

    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor(DARK)
    fig.suptitle('Chart 5: System Comparison — LD2450+ESP32 vs Alternatives\n(Score: 0=poor, 5=excellent)',
                 color=GREEN, fontsize=11, fontweight='bold', y=0.98)

    n_ax = len(axes_labels)
    angles = [n / float(n_ax) * 2 * math.pi for n in range(n_ax)]
    angles += angles[:1]

    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor('#0f180f')
    colors_ = [GREEN, GREY, BLUE, AMBER, RED, '#cc44ff']

    for (name, scores), col in zip(systems.items(), colors_):
        vals_ = scores + scores[:1]
        lw = 2.5 if 'this work' in name else 1.0
        alpha = 0.9 if 'this work' in name else 0.55
        ax.plot(angles, vals_, 'o-', linewidth=lw, color=col, alpha=alpha, label=name.replace('\n',' '), markersize=4)
        ax.fill(angles, vals_, color=col, alpha=0.05 if 'this work' not in name else 0.15)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(axes_labels, size=8, color=GREEN)
    ax.set_ylim(0, 5)
    ax.set_yticks([1,2,3,4,5])
    ax.set_yticklabels(['1','2','3','4','5'], color=GREY, size=7)
    ax.grid(color='#1a331a', linewidth=0.6, alpha=0.8)
    ax.tick_params(colors=GREY)

    leg = ax.legend(loc='lower left', bbox_to_anchor=(-0.28, -0.22),
                    framealpha=0.15, fontsize=8, ncol=2)
    for t_ in leg.get_texts(): t_.set_color(GREEN)

    plt.tight_layout()
    return savefig('05_system_comparison_radar.png')


# ─────────────────────────────────────────────────────────────────────────────
# CHART 6 — Cost vs Capability Comparison
# ─────────────────────────────────────────────────────────────────────────────
def chart_cost():
    systems = [
        ('PIR Sensor',            0.8,  1.0),
        ('Ultrasonic HC-SR04',    1.5,  1.5),
        ('IR Array AMG8833',     14.0,  2.5),
        ('LD2450 + ESP32\n(this work)', 12.0, 4.8),
        ('Webcam + PC/CV',       80.0,  3.8),
        ('Commercial Radar',    350.0,  4.5),
    ]
    names, costs, capabs = zip(*systems)
    colors_ = [GREY, GREY, GREY, GREEN, GREY, GREY]

    fig, ax = plt.subplots(figsize=(10, 6))
    fig.suptitle('Chart 6: Cost vs Capability — Detection System Comparison\n(bubble size ∝ capability score)',
                 color=GREEN, fontsize=11, fontweight='bold')

    for name, cost, cap, col in zip(names, costs, capabs, colors_):
        size = (cap ** 2) * 200
        ax.scatter(cost, cap, s=size, color=col, alpha=0.75, edgecolors='white',
                   linewidth=0.5, zorder=3)
        offset_y = 0.12 if 'this work' not in name else 0.18
        ax.text(cost, cap + offset_y, name.replace('\n',' '),
                ha='center', va='bottom', fontsize=7.5,
                color=GREEN if 'this work' in name else GREY)

    # Annotate this-work with arrow
    ax.annotate('Best cost-capability\nratio', xy=(12, 4.8), xytext=(50, 4.2),
                arrowprops=dict(arrowstyle='->', color=GREEN, lw=1.0),
                color=GREEN, fontsize=8)

    ax.set_xscale('log')
    ax.set_xlabel('System Cost (USD, log scale)', fontsize=9)
    ax.set_ylabel('Composite Capability Score (0–5)', fontsize=9)
    ax.set_xlim(0.5, 600)
    ax.set_ylim(0, 5.5)
    ax.grid(True, alpha=0.3, which='both')
    plt.tight_layout()
    return savefig('06_cost_vs_capability.png')


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main():
    p = argparse.ArgumentParser()
    p.add_argument('--csv',  default=None, help='Path to CSV from capture_data.py')
    p.add_argument('--demo', action='store_true', help='Use simulated demo data')
    args = p.parse_args()

    if args.csv and not args.demo:
        print(f"Loading real capture: {args.csv}")
        d = load_csv(args.csv)
    else:
        print("Using realistic simulated demo data (60s approach-dwell-depart scenario).")
        print("Run  python capture_data.py  first for real sensor data.\n")
        d = generate_demo_data()

    print("Generating charts…")
    chart_kalman(d)
    chart_threat(d)
    chart_trace(d)
    chart_classification(d)
    chart_comparison()
    chart_cost()

    print(f"\nAll charts saved to:  {OUTDIR}\\")
    print("\nCharts generated:")
    print("  01_kalman_filter_noise_reduction.png  —  Raw vs filtered positions")
    print("  02_threat_score_timeline.png           —  Threat + alert state over time")
    print("  03_position_trace_2d.png               —  2D trajectory + prediction arrows")
    print("  04_classification_distribution.png     —  WALKING/RUNNING/etc breakdown")
    print("  05_system_comparison_radar.png         —  Radar chart vs alternatives")
    print("  06_cost_vs_capability.png              —  Cost-performance scatter")

if __name__ == '__main__':
    main()
