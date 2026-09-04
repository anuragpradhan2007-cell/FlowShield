"""
Runtime ML Predictor for Worker Risk Classification.

Loads the trained GradientBoosting model + scaler at first call, extracts features
from raw earnings records, and returns a stability score + risk tier.

Falls back gracefully if the model files have not been trained yet.
"""

import os
from typing import Any, Dict, List, Tuple

import numpy as np
import joblib

from app.ml.feature_engineering import extract_features, FEATURE_NAMES
from app.schemas.risk_score import RiskTier

# ── Paths to persisted model artifacts ───────────────────────────────────
_MODEL_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_MODEL_DIR, "model.joblib")
_SCALER_PATH = os.path.join(_MODEL_DIR, "scaler.joblib")

# Lazy-loaded singletons
_model = None
_scaler = None

# Class-index → RiskTier mapping (must match LABEL_MAP in train_model.py)
_TIER_MAP = {0: RiskTier.STABLE, 1: RiskTier.AT_RISK, 2: RiskTier.CRITICAL}

# Midpoints used to convert class probabilities into a continuous 0–100 score
_TIER_MIDPOINTS = {
    0: 85.0,   # Stable  → center of [70, 100]
    1: 55.0,   # At Risk → center of [40, 70]
    2: 20.0,   # Critical → center of [0, 40]
}


def _load_model():
    """Load model + scaler from disk on first call (singleton)."""
    global _model, _scaler
    if _model is None:
        if not os.path.exists(_MODEL_PATH):
            raise FileNotFoundError(
                f"Trained ML model not found at {_MODEL_PATH}. "
                "Run 'python -m app.ml.train_model' to train it first."
            )
        _model = joblib.load(_MODEL_PATH)
        _scaler = joblib.load(_SCALER_PATH)
    return _model, _scaler


def is_model_available() -> bool:
    """Check whether a trained model exists on disk."""
    return os.path.exists(_MODEL_PATH) and os.path.exists(_SCALER_PATH)


def predict_risk(
    earnings_records: List[Dict[str, Any]],
    emergency_fund: float = 0.0
) -> Tuple[float, RiskTier, Dict[str, Any]]:
    """
    Predict worker risk tier and stability score from earnings records.

    Args:
        earnings_records: List of dicts, each with keys:
            "date" (datetime/date), "amount" (float), "is_missing_data" (bool)

    Returns:
        (stability_score, risk_tier, details_dict)
        - stability_score: float bounded [0.0, 100.0]
        - risk_tier:       RiskTier enum
        - details_dict:    feature values, probabilities, and importances
    """
    model, scaler = _load_model()

    # ── Feature extraction (same pipeline as training) ───────────────────
    features = extract_features(earnings_records, emergency_fund=emergency_fund)
    features_scaled = scaler.transform(features.reshape(1, -1))

    # ── Inference ────────────────────────────────────────────────────────
    predicted_class = int(model.predict(features_scaled)[0])
    probabilities = model.predict_proba(features_scaled)[0]

    risk_tier = _TIER_MAP[predicted_class]

    # ── Stability score from probability-weighted midpoints ──────────────
    stability_score = sum(
        probabilities[cls] * _TIER_MIDPOINTS[cls] for cls in range(3)
    )
    stability_score = round(max(0.0, min(100.0, stability_score)), 2)

    # ── Explainability details ───────────────────────────────────────────
    feature_values = {
        name: round(float(val), 4) for name, val in zip(FEATURE_NAMES, features)
    }

    feature_importances = {
        name: round(float(imp), 4)
        for name, imp in zip(FEATURE_NAMES, model.feature_importances_)
    }

    details = {
        "predicted_class": predicted_class,
        "class_probabilities": {
            "Stable": round(float(probabilities[0]), 4),
            "At Risk": round(float(probabilities[1]), 4),
            "Critical": round(float(probabilities[2]), 4),
        },
        "extracted_features": feature_values,
        "learned_feature_importances": feature_importances,
        "model_type": "GradientBoostingClassifier",
        "model_path": _MODEL_PATH,
    }

    return stability_score, risk_tier, details
