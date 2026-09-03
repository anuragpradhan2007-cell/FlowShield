import uuid
from datetime import date, timedelta
import pytest
import pandas as pd
import numpy as np

from app.schemas.risk_score import DailyIncomeRecord, WorkerDataInput
from app.services.metrics import (
    calculate_income_consistency,
    calculate_work_frequency,
    calculate_recent_income_trend,
    calculate_savings_buffer,
    calculate_external_risk,
    extract_worker_metrics,
    parse_income_dataframe,
    WEIGHT_INCOME_CONSISTENCY,
    WEIGHT_WORK_FREQUENCY,
    WEIGHT_RECENT_TREND,
    WEIGHT_SAVINGS_BUFFER,
    WEIGHT_EXTERNAL_RISK,
)


def generate_daily_records(days_count: int, base_amount: float, variance_pct: float = 0.0):
    start = date(2026, 1, 1)
    records = []
    for i in range(days_count):
        d = start + timedelta(days=i)
        # Add deterministic variance
        if variance_pct == 0.0:
            amt = base_amount
        else:
            mult = 1.0 + (variance_pct * (1 if i % 2 == 0 else -1))
            amt = max(0.0, base_amount * mult)
        records.append(DailyIncomeRecord(date=str(d), amount=amt))
    return records


# -------------------------------------------------------------------------
# Metric 1: Income Consistency (Weight: 30%)
# -------------------------------------------------------------------------

def test_income_consistency_perfect():
    """Identical daily income has 0 std dev and CV = 0 -> 100.0 score"""
    records = generate_daily_records(30, 150.0, variance_pct=0.0)
    df = parse_income_dataframe(records)
    metric = calculate_income_consistency(df)

    assert metric.weight == WEIGHT_INCOME_CONSISTENCY
    assert metric.normalized_score == 100.0
    assert metric.standard_deviation == 0.0
    assert metric.mean == 150.0
    assert metric.raw_value == 0.0  # CV is 0
    assert "100.0%" in metric.tooltip


def test_income_consistency_high_volatility():
    """Extreme sporadic earnings should yield high CV and lower score"""
    # Alternating between 0 and 300
    records = generate_daily_records(30, 150.0, variance_pct=1.0)
    df = parse_income_dataframe(records)
    metric = calculate_income_consistency(df)

    assert metric.weight == 0.30
    assert metric.standard_deviation > 0.0
    assert metric.normalized_score < 40.0
    assert metric.raw_value > 0.8  # High CV


def test_income_consistency_zero_earnings():
    """All zeros should yield score 0.0"""
    records = generate_daily_records(30, 0.0, variance_pct=0.0)
    df = parse_income_dataframe(records)
    metric = calculate_income_consistency(df)

    assert metric.normalized_score == 0.0
    assert metric.mean == 0.0


# -------------------------------------------------------------------------
# Metric 2: Work Frequency (Weight: 25%)
# -------------------------------------------------------------------------

def test_work_frequency_full_capacity():
    """24 active work days in 30 days matches 24 expected capacity -> 100%"""
    records = generate_daily_records(24, 100.0)
    df = parse_income_dataframe(records)
    metric = calculate_work_frequency(df, expected_capacity_days=24, window_days=30)

    assert metric.weight == WEIGHT_WORK_FREQUENCY
    assert metric.normalized_score == 100.0
    assert metric.raw_value == 24.0
    assert "24 of 24" in metric.tooltip


def test_work_frequency_partial():
    """12 active days out of 24 capacity -> 50%"""
    records = generate_daily_records(12, 100.0)
    df = parse_income_dataframe(records)
    metric = calculate_work_frequency(df, expected_capacity_days=24, window_days=30)

    assert metric.normalized_score == 50.0
    assert metric.raw_value == 12.0


def test_work_frequency_zero_active():
    """0 active days -> 0.0"""
    records = generate_daily_records(30, 0.0)
    df = parse_income_dataframe(records)
    metric = calculate_work_frequency(df, expected_capacity_days=24, window_days=30)

    assert metric.normalized_score == 0.0


# -------------------------------------------------------------------------
# Metric 3: Recent Income Trend (Weight: 20%)
# -------------------------------------------------------------------------

def test_recent_income_trend_stable():
    """Constant earnings across 60 days gives 100% trend score"""
    records = generate_daily_records(60, 100.0)
    df = parse_income_dataframe(records)
    metric = calculate_recent_income_trend(df, recent_window_days=14, baseline_window_days=60)

    assert metric.weight == WEIGHT_RECENT_TREND
    assert metric.normalized_score == 100.0
    assert metric.raw_value == 1.0  # ratio is 1.0


def test_recent_income_trend_50_percent_drop():
    """Earnings drop by 50% in the last 14 days"""
    records_baseline = generate_daily_records(46, 200.0)
    # Add recent 14 days at $100/day
    start_recent = date(2026, 1, 1) + timedelta(days=46)
    records_recent = [
        DailyIncomeRecord(date=str(start_recent + timedelta(days=i)), amount=100.0)
        for i in range(14)
    ]
    df = parse_income_dataframe(records_baseline + records_recent)
    metric = calculate_recent_income_trend(df, recent_window_days=14, baseline_window_days=60)

    # Baseline average is (46*200 + 14*100) / 60 = (9200 + 1400) / 60 = 10600 / 60 ≈ 176.67
    # Recent average is 100.0
    # Ratio = 100 / 176.67 ≈ 0.566 -> score ≈ 56.6
    assert metric.normalized_score < 65.0
    assert metric.intermediate_calculations["trend_ratio"] < 0.70
    assert "Recent income dropped" in metric.tooltip


# -------------------------------------------------------------------------
# Metric 4: Savings Buffer (Weight: 15%)
# -------------------------------------------------------------------------

def test_savings_buffer_full_cushion():
    """$2000 savings with $500/week expenses = 4 weeks buffer -> 100.0"""
    records = generate_daily_records(30, 100.0)
    df = parse_income_dataframe(records)
    metric = calculate_savings_buffer(
        current_savings=2000.0,
        df=df,
        weekly_expenses=500.0,
        target_weeks=4.0,
    )

    assert metric.weight == WEIGHT_SAVINGS_BUFFER
    assert metric.normalized_score == 100.0
    assert metric.raw_value == 4.0  # 4 weeks
    assert "4.0 weeks" in metric.tooltip


def test_savings_buffer_partial_cushion():
    """$1000 savings with $500/week expenses = 2 weeks buffer -> 50.0"""
    records = generate_daily_records(30, 100.0)
    df = parse_income_dataframe(records)
    metric = calculate_savings_buffer(
        current_savings=1000.0,
        df=df,
        weekly_expenses=500.0,
        target_weeks=4.0,
    )

    assert metric.normalized_score == 50.0
    assert metric.raw_value == 2.0


def test_savings_buffer_depleted():
    """$0 savings -> 0.0"""
    records = generate_daily_records(30, 100.0)
    df = parse_income_dataframe(records)
    metric = calculate_savings_buffer(
        current_savings=0.0,
        df=df,
        weekly_expenses=500.0,
        target_weeks=4.0,
    )

    assert metric.normalized_score == 0.0


# -------------------------------------------------------------------------
# Metric 5: External Risk Factors (Weight: 10%)
# -------------------------------------------------------------------------

def test_external_risk_weather_conditions():
    m_clear = calculate_external_risk("CLEAR")
    assert m_clear.normalized_score == 100.0
    assert m_clear.weight == WEIGHT_EXTERNAL_RISK

    m_rain = calculate_external_risk("MODERATE_RAIN")
    assert m_rain.normalized_score == 70.0

    m_severe = calculate_external_risk("SEVERE_ALERT")
    assert m_severe.normalized_score == 20.0


def test_external_risk_custom_override():
    m_override = calculate_external_risk("CLEAR", custom_score=45.5)
    assert m_override.normalized_score == 45.5


# -------------------------------------------------------------------------
# Full Pipeline Test & Explainability Validation
# -------------------------------------------------------------------------

def test_extract_worker_metrics_pipeline():
    worker_id = uuid.uuid4()
    income_records = generate_daily_records(60, 120.0, variance_pct=0.1)

    payload = WorkerDataInput(
        worker_id=worker_id,
        income_history=income_records,
        current_savings=1500.0,
        weekly_expenses=400.0,
        weather_condition="CLEAR",
        expected_capacity_days=24,
    )

    breakdown = extract_worker_metrics(payload)

    # Verify all 5 metrics are present
    assert breakdown.income_consistency is not None
    assert breakdown.work_frequency is not None
    assert breakdown.recent_income_trend is not None
    assert breakdown.savings_buffer is not None
    assert breakdown.external_risk_factors is not None

    # Verify exact weights sum to 1.0
    weights_sum = (
        breakdown.income_consistency.weight +
        breakdown.work_frequency.weight +
        breakdown.recent_income_trend.weight +
        breakdown.savings_buffer.weight +
        breakdown.external_risk_factors.weight
    )
    assert round(weights_sum, 2) == 1.0

    # Verify standard deviations and statistical logs are preserved
    assert breakdown.income_consistency.standard_deviation is not None
    assert breakdown.income_consistency.mean is not None
    assert "coefficient_of_variation" in breakdown.income_consistency.intermediate_calculations

    # Verify frontend tooltip strings exist
    for metric in [
        breakdown.income_consistency,
        breakdown.work_frequency,
        breakdown.recent_income_trend,
        breakdown.savings_buffer,
        breakdown.external_risk_factors,
    ]:
        assert metric.tooltip is not None
        assert len(metric.tooltip) > 0
        assert 0.0 <= metric.normalized_score <= 100.0
