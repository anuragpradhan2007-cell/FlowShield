"""
Training Script for the Worker Risk Classifier.

Generates synthetic training data using the exact same distributions as the team's
Supabase seeder script, then trains a GradientBoostingClassifier to predict
Stable / At Risk / Critical tiers.

Run:
    python -m app.ml.train_model
"""

import os
import random
import numpy as np
from datetime import datetime, timedelta, timezone

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report
import joblib

from app.ml.feature_engineering import extract_features, FEATURE_NAMES

# ── Label mapping ────────────────────────────────────────────────────────
LABEL_MAP = {"stable": 0, "at_risk": 1, "critical": 2}
LABEL_NAMES = ["Stable", "At Risk", "Critical"]


def generate_worker_earnings(profile: str, n_days: int = 61) -> list:
    """
    Generate synthetic daily earnings records matching the team seeder distributions.

    Distributions (from the seeder script):
        Stable   — amount ∈ [100, 130],  0% missing
        At Risk  — amount ∈ [70, 95] normally, drops to [30, 50] in last 7 days,
                   20% missing
        Critical — amount ∈ [15, 35],   60% missing
    """
    records = []
    now = datetime.now(timezone.utc)

    for days_ago in range(n_days - 1, -1, -1):
        current_date = now - timedelta(days=days_ago)
        is_missing = False
        amount = 0.0

        if profile == "stable":
            amount = round(random.uniform(100.0, 130.0), 2)

        elif profile == "at_risk":
            is_missing = random.random() < 0.20
            if not is_missing:
                if days_ago <= 7:
                    amount = round(random.uniform(30.0, 50.0), 2)
                else:
                    amount = round(random.uniform(70.0, 95.0), 2)

        elif profile == "critical":
            is_missing = random.random() < 0.60
            if not is_missing:
                amount = round(random.uniform(15.0, 35.0), 2)

        records.append(
            {
                "date": current_date,
                "amount": amount if not is_missing else 0.0,
                "is_missing_data": is_missing,
            }
        )

    return records


def train(n_samples_per_class: int = 200, seed: int = 42) -> None:
    """Generate synthetic data, train the classifier, and save artifacts."""
    random.seed(seed)
    np.random.seed(seed)

    X = []
    y = []

    print("=" * 60)
    print("WORKER RISK CLASSIFIER — TRAINING PIPELINE")
    print("=" * 60)
    print(f"\nGenerating {n_samples_per_class} synthetic workers per class...")

    for profile, label in LABEL_MAP.items():
        for _ in range(n_samples_per_class):
            records = generate_worker_earnings(profile, n_days=61)
            features = extract_features(records)
            X.append(features)
            y.append(label)

    X = np.array(X)
    y = np.array(y)

    print(f"Training data shape: {X.shape}")
    print(f"Class distribution : {dict(zip(LABEL_NAMES, np.bincount(y)))}")

    # ── Feature scaling ──────────────────────────────────────────────────
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # ── Model ────────────────────────────────────────────────────────────
    clf = GradientBoostingClassifier(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.1,
        min_samples_split=5,
        min_samples_leaf=3,
        random_state=seed,
    )

    # ── Cross-validation ─────────────────────────────────────────────────
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=seed)
    scores = cross_val_score(clf, X_scaled, y, cv=cv, scoring="accuracy")
    print(f"\n5-Fold CV accuracy : {scores.mean():.4f} (+/- {scores.std():.4f})")

    # ── Train on full data ───────────────────────────────────────────────
    clf.fit(X_scaled, y)
    y_pred = clf.predict(X_scaled)

    print("\nClassification Report (training set):")
    print(classification_report(y, y_pred, target_names=LABEL_NAMES))

    # ── Feature importances ──────────────────────────────────────────────
    print("Feature Importances (learned weights):")
    for name, imp in sorted(
        zip(FEATURE_NAMES, clf.feature_importances_), key=lambda x: -x[1]
    ):
        bar = "=" * int(imp * 50)
        print(f"  {name:<20s} {imp:.4f}  {bar}")

    # ── Persist model artifacts ──────────────────────────────────────────
    model_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(model_dir, "model.joblib")
    scaler_path = os.path.join(model_dir, "scaler.joblib")

    joblib.dump(clf, model_path)
    joblib.dump(scaler, scaler_path)

    print(f"\n[SUCCESS] Model  saved -> {model_path}")
    print(f"[SUCCESS] Scaler saved -> {scaler_path}")
    print("=" * 60)


if __name__ == "__main__":
    train()
