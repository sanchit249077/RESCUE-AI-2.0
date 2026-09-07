from pathlib import Path
import argparse
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[1]

FEATURES = [
    "rainfall_24h_mm",
    "rainfall_7d_mm",
    "slope_deg",
    "elevation_m",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=str(ROOT / "data" / "processed" / "training_table.csv"))
    ap.add_argument("--target", default="historical_landslide")
    ap.add_argument("--model-out", default=str(ROOT / "ml" / "rescueai_real_rf.joblib"))
    args = ap.parse_args()

    df = pd.read_csv(args.table)
    needed = FEATURES + [args.target]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.dropna(subset=[args.target])
    X = df[FEATURES]
    y = df[args.target].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("rf", RandomForestClassifier(
            n_estimators=400,
            max_depth=16,
            min_samples_leaf=5,
            class_weight="balanced_subsample",
            random_state=42,
            n_jobs=-1,
        ))
    ])
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    proba = model.predict_proba(X_test)[:, 1]

    print(classification_report(y_test, pred, digits=3))
    if len(set(y_test)) == 2:
        print("ROC-AUC:", round(roc_auc_score(y_test, proba), 4))

    Path(args.model_out).parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, args.model_out)
    print(f"Saved: {args.model_out}")
    print("IMPORTANT: Use spatial/temporal holdout before interpreting this as operational performance.")


if __name__ == "__main__":
    main()
