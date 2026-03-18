"""
Three tests covering the core math in analysis.py.

Run with: pytest tests/
For full data verification, run: python analysis.py
"""

import numpy as np
import pandas as pd
from datetime import datetime

from analysis import (
    BASELINE_START,
    BASELINE_END,
    compute_anomalies,
    compute_decadal_means,
    count_temperature_outliers,
)


def make_monthly_temperature_series(
    start_year: int,
    end_year: int,
    base_temperature: float = 15.0,
    seasonal_amplitude: float = 10.0,
) -> pd.DataFrame:
    date_range = pd.date_range(
        datetime(start_year, 1, 1),
        datetime(end_year, 12, 31),
        freq="MS",
    )
    seasonal_offsets = seasonal_amplitude * np.sin(
        2 * np.pi * (date_range.month - 1) / 12
    )
    return pd.DataFrame({"temp": base_temperature + seasonal_offsets}, index=date_range)


def test_outlier_detection_catches_a_spike():
    df = make_monthly_temperature_series(1981, 2010)
    df.iloc[100, df.columns.get_loc("temp")] = df["temp"].mean() + 10 * df["temp"].std()
    assert count_temperature_outliers(df) >= 1


def test_baseline_anomalies_are_near_zero():
    df = make_monthly_temperature_series(1950, 2023)
    anomalies = compute_anomalies(df)
    baseline_mask = (anomalies.index >= BASELINE_START) & (anomalies.index <= BASELINE_END)
    assert anomalies[baseline_mask].dropna().abs().mean() < 0.5


def test_warming_trend_produces_positive_anomalies():
    df = make_monthly_temperature_series(1950, 2023)
    df.loc[df.index.year > 2010, "temp"] += 3.0
    anomalies = compute_anomalies(df)
    assert anomalies[anomalies.index.year > 2010].dropna().mean() > 1.0
