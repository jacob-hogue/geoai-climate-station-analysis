from dataclasses import dataclass, field
from datetime import datetime

import meteostat
import numpy as np
import pandas as pd
from meteostat import Point

from cities import CITIES_BY_ZONE

# Date range for the full analysis.
ANALYSIS_START = datetime(1950, 1, 1)
ANALYSIS_END = datetime(2023, 12, 31)

# The 1981-2010 period is the WMO standard baseline for computing climate anomalies.
BASELINE_START = datetime(1981, 1, 1)
BASELINE_END = datetime(2010, 12, 31)

# Months with a z-score beyond this threshold are flagged as outliers.
OUTLIER_ZSCORE_THRESHOLD = 2.0

# Minimum fraction of months that must be present to include a city in the analysis.
MINIMUM_DATA_COVERAGE = 0.5

# Number of nearby stations to evaluate when looking for the best historical record.
# The geographically closest station is not always the one with the most complete data.
NEARBY_STATIONS_TO_CHECK = 15


def celsius_to_fahrenheit(celsius: pd.Series) -> pd.Series:
    return celsius * 9 / 5 + 32


@dataclass
class StationRecord:
    city: str
    climate_zone: str
    df: pd.DataFrame
    outlier_count: int
    missing_months: int
    warnings: list[str] = field(default_factory=list)


def find_best_station(location: Point) -> tuple[str | None, object]:
    """
    Return the station ID and raw DataFrame with the least missing temperature data,
    checking up to NEARBY_STATIONS_TO_CHECK candidates.

    The geographically closest station often has fewer historical records than a
    slightly farther one, so checking multiple candidates produces better coverage.
    """
    nearby_stations = meteostat.stations.nearby(location).head(NEARBY_STATIONS_TO_CHECK)
    best_station_id = None
    best_raw_data = None
    best_missing_count = float("inf")

    full_date_range = pd.date_range(ANALYSIS_START, ANALYSIS_END, freq="MS")

    for station_id in nearby_stations.index:
        raw = meteostat.monthly(station_id, ANALYSIS_START, ANALYSIS_END).fetch()
        if raw is None or raw.empty or "temp" not in raw.columns:
            continue
        missing_count = int(raw.reindex(full_date_range)["temp"].isna().sum())
        if missing_count < best_missing_count:
            best_missing_count = missing_count
            best_station_id = station_id
            best_raw_data = raw

    return best_station_id, best_raw_data


def fetch_monthly_data(city: dict, climate_zone: str) -> StationRecord:
    """Fetch and clean monthly temperature data for one city."""
    location = Point(city["latitude"], city["longitude"], city["altitude"])
    station_id, raw = find_best_station(location)

    if station_id is None or raw is None or raw.empty:
        warnings = [f"{city['name']}: no usable monthly data found in {NEARBY_STATIONS_TO_CHECK} nearby stations"]
        return StationRecord(
            city=city["name"],
            climate_zone=climate_zone,
            df=pd.DataFrame(columns=["temp"]),
            outlier_count=0,
            missing_months=0,
            warnings=warnings,
        )

    warnings = []

    # Keep only temperature. Precipitation is available from meteostat but not used.
    df = raw[["temp"]].copy() if "temp" in raw.columns else pd.DataFrame(columns=["temp"])

    # Ensure the index covers the full analysis period so gaps are explicit NaNs.
    full_date_range = pd.date_range(ANALYSIS_START, ANALYSIS_END, freq="MS")
    df = df.reindex(full_date_range)

    # Convert temperature to Fahrenheit. All downstream functions use °F from this point.
    # Anomalies are computed as differences so the +32 offset cancels automatically.
    if "temp" in df.columns:
        df["temp"] = celsius_to_fahrenheit(df["temp"])

    missing_months = int(df["temp"].isna().sum()) if "temp" in df.columns else 0
    total_months = len(df)
    data_coverage = (total_months - missing_months) / total_months

    if data_coverage < MINIMUM_DATA_COVERAGE:
        warnings.append(
            f"{city['name']}: only {data_coverage:.0%} of months have temperature data"
        )

    outlier_count = count_temperature_outliers(df) if "temp" in df.columns else 0

    return StationRecord(
        city=city["name"],
        climate_zone=climate_zone,
        df=df,
        outlier_count=outlier_count,
        missing_months=missing_months,
        warnings=warnings,
    )


def count_temperature_outliers(df: pd.DataFrame) -> int:
    """Return the number of months whose temperature falls outside the z-score threshold."""
    temperature_series = df["temp"].dropna()
    if len(temperature_series) < 2:
        return 0
    z_scores = (temperature_series - temperature_series.mean()) / temperature_series.std()
    return int((z_scores.abs() > OUTLIER_ZSCORE_THRESHOLD).sum())


def compute_anomalies(df: pd.DataFrame) -> pd.Series:
    """
    Compute monthly temperature anomalies relative to the 1981-2010 baseline.

    For each calendar month (Jan-Dec), the baseline mean is subtracted from
    every observation of that month. This removes the seasonal cycle so that
    anomalies represent deviation from expected temperature for that time of year.
    """
    if "temp" not in df.columns or df["temp"].dropna().empty:
        return pd.Series(dtype=float)

    baseline_mask = (df.index >= BASELINE_START) & (df.index <= BASELINE_END)
    baseline_monthly_means = (
        df.loc[baseline_mask, "temp"]
        .groupby(df.loc[baseline_mask].index.month)
        .mean()
    )

    # For each calendar month (1=Jan through 12=Dec), subtract that month's
    # baseline average from every observation of that same month.
    anomalies = df["temp"].copy()
    for month_number in range(1, 13):
        month_mask = anomalies.index.month == month_number
        baseline_mean = baseline_monthly_means.get(month_number, np.nan)
        anomalies.loc[month_mask] -= baseline_mean

    return anomalies


def compute_decadal_means(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """Group data into decades and return the mean value per decade."""
    if column not in df.columns or df[column].dropna().empty:
        return pd.DataFrame()

    decade_labels = (df.index.year // 10) * 10
    decade_series = pd.Series(decade_labels, index=df.index)
    return df[column].groupby(decade_series).mean().rename("mean_value").to_frame()


def load_all_cities() -> list[StationRecord]:
    records = []
    for climate_zone, cities in CITIES_BY_ZONE.items():
        for city in cities:
            print(f"  fetching {city['name']} ({climate_zone})...")
            record = fetch_monthly_data(city, climate_zone)
            records.append(record)
            for warning in record.warnings:
                print(f"    warning: {warning}")
    return records


if __name__ == "__main__":
    print("Fetching climate data for 20 cities across 5 climate zones...\n")
    records = load_all_cities()

    print("\nSummary:")
    print(f"  {'City':<14} {'Zone':<14} {'Missing months':>14} {'Outliers':>10}")
    print(f"  {'-'*14} {'-'*14} {'-'*14} {'-'*10}")
    for record in records:
        print(
            f"  {record.city:<14} {record.climate_zone:<14} "
            f"{record.missing_months:>14} {record.outlier_count:>10}"
        )
