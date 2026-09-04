"""
Feature Engineering for Worker Risk Classification.

Extracts numerical features from raw earnings records that the ML classifier uses
to predict worker risk tiers. Feature extraction is identical during training and
runtime inference to ensure consistency.
"""

import numpy as np
from typing import Any, Dict, List


# Ordered list of feature names — must match the order returned by extract_features()
FEATURE_NAMES = [
    "mean_earnings",
    "std_earnings",
    "cv_earnings",
    "missing_ratio",
    "work_frequency",
    "recent_mean_14d",
    "trend_ratio",
    "max_earnings",
    "total_earnings",
    "total_days",
    "emergency_fund"
]


def extract_features(records: List[Dict[str, Any]], emergency_fund: float = 0.0) -> np.ndarray:
    """
    Extract a feature vector from a list of daily earnings records for one worker.

    Each record dict should contain:
        - "date":            datetime or date (for sorting)
        - "amount":          float (gross income, 0.0 if missing)
        - "is_missing_data": bool (True if the record represents a data gap)

    Returns:
        1-D numpy array of shape (len(FEATURE_NAMES),)
    """
    if not records:
        return np.zeros(len(FEATURE_NAMES))

    # Sort chronologically
    records = sorted(records, key=lambda r: r["date"])

    amounts = np.array([float(r["amount"]) for r in records], dtype=np.float64)
    is_missing = np.array(
        [bool(r.get("is_missing_data", r["amount"] == 0)) for r in records]
    )

    # ── Basic earnings statistics (excluding missing-data days) ──────────
    non_missing_amounts = amounts[~is_missing]

    if len(non_missing_amounts) > 0:
        mean_earnings = float(np.mean(non_missing_amounts))
        std_earnings = (
            float(np.std(non_missing_amounts, ddof=1))
            if len(non_missing_amounts) > 1
            else 0.0
        )
        max_earnings = float(np.max(non_missing_amounts))
        total_earnings = float(np.sum(non_missing_amounts))
    else:
        mean_earnings = 0.0
        std_earnings = 0.0
        max_earnings = 0.0
        total_earnings = 0.0

    # Coefficient of variation
    cv_earnings = std_earnings / mean_earnings if mean_earnings > 0 else 0.0

    # ── Activity ratios ──────────────────────────────────────────────────
    missing_ratio = float(np.mean(is_missing))
    work_frequency = float(np.mean(amounts > 0))

    # ── Recent trend (last 14 days vs full baseline) ─────────────────────
    n_recent = min(14, len(records))
    recent_records = records[-n_recent:]
    recent_amounts = np.array([float(r["amount"]) for r in recent_records])
    recent_non_missing = recent_amounts[recent_amounts > 0]

    recent_mean = (
        float(np.mean(recent_non_missing)) if len(recent_non_missing) > 0 else 0.0
    )
    trend_ratio = recent_mean / mean_earnings if mean_earnings > 0 else 0.0
    trend_ratio = min(trend_ratio, 2.0)  # Cap to avoid extreme outliers

    # ── Assemble feature vector (order MUST match FEATURE_NAMES) ─────────
    features = np.array(
        [
            mean_earnings,
            std_earnings,
            cv_earnings,
            missing_ratio,
            work_frequency,
            recent_mean,
            trend_ratio,
            max_earnings,
            total_earnings,
            float(len(records)),
            float(emergency_fund),
        ]
    )

    return features
