"""
train_classifier.py  —  TinyML Motion Classifier for LD2450 Radar
==================================================================
Trains a lightweight MLP on labeled session CSVs captured by capture_data.py

Classes: STATIC | CREEPING | WALKING | RUNNING | PACING

Usage:
    python train_classifier.py
    (reads all CSVs from ./labeled_data/ folder automatically)
"""

import os, json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
from tensorflow import keras

# ── Config ──────────────────────────────────────────────────────────────────
WINDOW_SIZE = 10          # frames  (10 × 200ms = 2 seconds of context)
N_FEATURES  = 7           # features per frame
CLASSES     = ['STATIC', 'CREEPING', 'WALKING', 'RUNNING', 'PACING']
DATA_DIR    = 'labeled_data'
MODEL_OUT   = 'motion_classifier.h5'
EPOCHS      = 80
BATCH_SIZE  = 32

# Map: filename prefix → class label
FILE_CLASS_MAP = {
    'walking':  'WALKING',
    'static':   'STATIC',
    'creeping': 'CREEPING',
    'running':  'RUNNING',
    'pacing':   'PACING',
}

print("=" * 60)
print("  LD2450 TinyML Motion Classifier — Training Script")
print("=" * 60)

# ── Feature Extraction ──────────────────────────────────────────────────────
def extract_features(df):
    """
    Extract 7 normalized features per frame from a capture CSV.
    Uses pred_x/pred_y (Kalman-filtered positions) and filtered_speed
    — these are the entities actually published in the SSE stream.
    """
    x    = pd.to_numeric(df['target1_pred_x'],         errors='coerce').fillna(0).values
    y    = pd.to_numeric(df['target1_pred_y'],         errors='coerce').fillna(0).values
    spd  = pd.to_numeric(df['target1_filtered_speed'], errors='coerce').fillna(0).values
    thr  = pd.to_numeric(df['target1_threat'],         errors='coerce').fillna(0).values

    dist = np.sqrt(x**2 + y**2)

    # Signed per-frame displacement (velocity proxy, same as what ESP32 computes)
    dx = np.diff(x, prepend=x[0])
    dy = np.diff(y, prepend=y[0])

    # Normalize to [-1, 1] or [0, 1] — MUST match tinyml_classifier.h constants
    x_n    = x    / 4000.0
    y_n    = y    / 8000.0
    spd_n  = spd  / 4.0          # max human speed ~4 m/s
    dist_n = dist / 8000.0
    thr_n  = thr  / 100.0
    dx_n   = np.clip(dx  / 300.0, -1.0, 1.0)
    dy_n   = np.clip(dy  / 300.0, -1.0, 1.0)

    return np.column_stack([x_n, y_n, spd_n, dist_n, thr_n, dx_n, dy_n])



def make_windows(features, label_idx):
    """Slide a window of size WINDOW_SIZE over the feature array."""
    X, y = [], []
    for i in range(len(features) - WINDOW_SIZE):
        window = features[i : i + WINDOW_SIZE]
        if not np.any(np.isnan(window)):
            X.append(window.flatten())   # shape: (WINDOW_SIZE * N_FEATURES,) = (70,)
            y.append(label_idx)
    return X, y


# ── Load & Label Data ───────────────────────────────────────────────────────
print(f"\n📂 Loading CSVs from ./{DATA_DIR}/\n")

X_all, y_all = [], []

for fname in sorted(os.listdir(DATA_DIR)):
    if not fname.endswith('.csv'):
        continue

    label = None
    for prefix, cls in FILE_CLASS_MAP.items():
        if fname.lower().startswith(prefix):
            label = cls
            break

    if label is None:
        print(f"  ⚠️  Skipping {fname} — no matching prefix")
        continue

    try:
        df = pd.read_csv(os.path.join(DATA_DIR, fname))
        # Filter: only rows where a target was actually detected (pred_y > 0)
        df = df[pd.to_numeric(df['target1_pred_y'], errors='coerce') > 0]
        if len(df) < WINDOW_SIZE + 1:
            print(f"  ⚠️  Skipping {fname} — too few valid rows ({len(df)})")
            continue

        features  = extract_features(df)
        label_idx = CLASSES.index(label)
        X, y      = make_windows(features, label_idx)
        X_all.extend(X)
        y_all.extend(y)
        print(f"  ✅ {fname:<30} → class '{label}'  ({len(X)} windows)")

    except Exception as e:
        print(f"  ❌ Error loading {fname}: {e}")

if len(X_all) == 0:
    print("\n❌ No data loaded! Make sure labeled_data/ has CSV files named:")
    print("   walking_01.csv, static_01.csv, creeping_01.csv, running_01.csv, pacing_01.csv")
    exit(1)

X_all = np.array(X_all, dtype=np.float32)
y_all = np.array(y_all, dtype=np.int32)
y_cat = keras.utils.to_categorical(y_all, num_classes=len(CLASSES))

print(f"\n📊 Dataset summary:")
print(f"   Total windows : {len(X_all)}")
print(f"   Input shape   : {X_all.shape}")
for i, cls in enumerate(CLASSES):
    count = int(np.sum(y_all == i))
    bar   = '█' * (count // 20)
    print(f"   {cls:<10}: {count:>5} windows  {bar}")

# ── Train / Test Split ──────────────────────────────────────────────────────
X_train, X_test, y_train, y_test = train_test_split(
    X_all, y_cat, test_size=0.2, random_state=42, stratify=y_all
)
print(f"\n   Train: {len(X_train)} | Test: {len(X_test)}")

# ── Model Definition ────────────────────────────────────────────────────────
print("\n🧠 Building model...")

model = keras.Sequential([
    keras.layers.Input(shape=(WINDOW_SIZE * N_FEATURES,)),   # 70 inputs
    keras.layers.Dense(32, activation='relu'),
    keras.layers.Dropout(0.2),
    keras.layers.Dense(16, activation='relu'),
    keras.layers.Dense(len(CLASSES), activation='softmax'),
], name='ld2450_motion_classifier')

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='categorical_crossentropy',
    metrics=['accuracy']
)
model.summary()

# ── Training ────────────────────────────────────────────────────────────────
print(f"\n🚀 Training for {EPOCHS} epochs...\n")

callbacks = [
    keras.callbacks.EarlyStopping(patience=12, restore_best_weights=True, verbose=1),
    keras.callbacks.ReduceLROnPlateau(patience=6, factor=0.5, verbose=1),
]

history = model.fit(
    X_train, y_train,
    epochs=EPOCHS,
    batch_size=BATCH_SIZE,
    validation_data=(X_test, y_test),
    callbacks=callbacks,
    verbose=1,
)

# ── Evaluation ──────────────────────────────────────────────────────────────
test_loss, test_acc = model.evaluate(X_test, y_test, verbose=0)
print(f"\n{'='*60}")
print(f"  ✅ Test Accuracy : {test_acc * 100:.1f}%")
print(f"  ✅ Test Loss     : {test_loss:.4f}")
print(f"{'='*60}\n")

y_pred = np.argmax(model.predict(X_test, verbose=0), axis=1)
y_true = np.argmax(y_test, axis=1)

print("Classification Report:")
print(classification_report(y_true, y_pred, target_names=CLASSES))

print("Confusion Matrix (rows=true, cols=predicted):")
cm = confusion_matrix(y_true, y_pred)
header = f"{'':10}" + "".join(f"{c:>10}" for c in CLASSES)
print(header)
for i, cls in enumerate(CLASSES):
    row = f"{cls:<10}" + "".join(f"{cm[i,j]:>10}" for j in range(len(CLASSES)))
    print(row)

# ── Save Model ──────────────────────────────────────────────────────────────
model.save(MODEL_OUT)
print(f"\n💾 Model saved: {MODEL_OUT}")
print(f"\n▶  Next step: python export_weights.py")
