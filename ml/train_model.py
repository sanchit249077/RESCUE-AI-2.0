from pathlib import Path
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "ml" / "rescueai_rf.joblib"
RNG = np.random.default_rng(42)

N = 12000
rain24 = RNG.gamma(shape=2.0, scale=50.0, size=N).clip(0, 500)
rain7 = (rain24 + RNG.gamma(shape=3.0, scale=90.0, size=N)).clip(0, 1200)
slope = RNG.uniform(5, 65, N)
elev = RNG.uniform(50, 3200, N)
geology = RNG.beta(2, 2, N)
landcover = RNG.beta(1.8, 3, N)
historical = RNG.beta(2, 2, N)

# Development-only synthetic target. This is NOT a real scientific label.
risk = (
    0.34*np.clip(rain24/220,0,1)
    + 0.16*np.clip(rain7/700,0,1)
    + 0.18*np.clip((slope-15)/35,0,1)
    + 0.06*np.clip((elev-300)/2200,0,1)
    + 0.12*geology
    + 0.06*landcover
    + 0.08*historical
)
noise = RNG.normal(0, 0.06, N)
prob = np.clip(risk + noise, 0, 1)
y = (prob >= 0.55).astype(int)

X = np.column_stack([rain24,rain7,slope,elev,geology,landcover,historical])
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

model = RandomForestClassifier(
    n_estimators=300,
    max_depth=12,
    min_samples_leaf=4,
    class_weight="balanced_subsample",
    random_state=42,
    n_jobs=-1,
)
model.fit(X_train, y_train)

pred = model.predict(X_test)
proba = model.predict_proba(X_test)[:,1]
print(classification_report(y_test, pred, digits=3))
print("ROC-AUC (synthetic development labels):", round(roc_auc_score(y_test, proba), 3))

joblib.dump(model, OUT)
print(f"Saved model to {OUT}")
print("WARNING: Replace synthetic development training data with validated NER labels before operational use.")
