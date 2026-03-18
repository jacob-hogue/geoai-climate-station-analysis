"""
Visualization functions for the climate station analysis.

Each function takes the list of StationRecord objects produced by analysis.py
and writes a plot to the plots/ directory. All plots use a dark background theme.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.dates as mdates
import numpy as np
import pandas as pd

from analysis import compute_anomalies, compute_decadal_means, load_all_cities, StationRecord

PLOTS_DIR = Path("plots")

ZONE_COLORS = {
    "tropical":    "#f97316",
    "arid":        "#ef4444",
    "temperate":   "#22c55e",
    "continental": "#3b82f6",
    "polar":       "#a78bfa",
}

DARK_BACKGROUND = "#0f172a"
DARK_PANEL      = "#1e293b"
LIGHT_TEXT      = "#e2e8f0"
GRID_COLOR      = "#334155"


def apply_dark_style(figure, axes_list: list) -> None:
    """Apply consistent dark styling to a figure and all its axes."""
    figure.patch.set_facecolor(DARK_BACKGROUND)
    for axis in axes_list:
        axis.set_facecolor(DARK_PANEL)
        axis.tick_params(colors=LIGHT_TEXT, labelsize=8)
        axis.xaxis.label.set_color(LIGHT_TEXT)
        axis.yaxis.label.set_color(LIGHT_TEXT)
        axis.title.set_color(LIGHT_TEXT)
        for spine in axis.spines.values():
            spine.set_edgecolor(GRID_COLOR)
        axis.grid(color=GRID_COLOR, linewidth=0.5, alpha=0.6)


def save_figure(filename: str) -> None:
    PLOTS_DIR.mkdir(exist_ok=True)
    output_path = PLOTS_DIR / filename
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=DARK_BACKGROUND)
    plt.close()
    print(f"  saved {output_path}")


def plot_temperature_timeseries(records: list[StationRecord]) -> None:
    """One subplot per climate zone showing monthly average temperature for all cities."""
    climate_zones = list(ZONE_COLORS.keys())
    figure, axes = plt.subplots(len(climate_zones), 1, figsize=(14, 16), sharex=True)
    figure.suptitle("Monthly Average Temperature by Climate Zone (1950-2023)", fontsize=14, color=LIGHT_TEXT, y=0.995)

    for axis, zone_name in zip(axes, climate_zones):
        zone_color = ZONE_COLORS[zone_name]
        zone_records = [r for r in records if r.climate_zone == zone_name and not r.df.empty]
        for record in zone_records:
            if "temp" not in record.df.columns:
                continue
            axis.plot(
                record.df.index,
                record.df["temp"],
                label=record.city,
                linewidth=0.9,
                alpha=0.85,
                color=zone_color,
            )
        axis.set_ylabel("Temp (°F)", fontsize=8)
        axis.set_title(zone_name.capitalize(), fontsize=9, loc="left", pad=4, color=LIGHT_TEXT)
        axis.legend(
            loc="upper left",
            fontsize=7,
            ncol=2,
            facecolor=DARK_PANEL,
            edgecolor=GRID_COLOR,
            labelcolor=LIGHT_TEXT,
        )
        axis.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        axis.xaxis.set_major_locator(mdates.YearLocator(10))

    axes[-1].set_xlabel("Year", fontsize=9)
    apply_dark_style(figure, list(axes))
    plt.tight_layout()
    save_figure("temperature_timeseries.png")


def plot_anomaly_heatmap(records: list[StationRecord]) -> None:
    """Heatmap of annual mean temperature anomalies, one row per city."""
    anomaly_rows = {}
    for record in records:
        if record.df.empty or "temp" not in record.df.columns:
            continue
        anomalies = compute_anomalies(record.df)
        if anomalies.empty:
            continue
        # Resample to annual mean so the heatmap is readable.
        annual_anomalies = anomalies.resample("YS").mean()
        anomaly_rows[record.city] = annual_anomalies

    if not anomaly_rows:
        print("  no anomaly data available for heatmap")
        return

    heatmap_df = pd.DataFrame(anomaly_rows).T
    heatmap_df.columns = heatmap_df.columns.year

    # Mask NaN cells so they render as a distinct "no data" colour rather than
    # blending into the anomaly colour scale, which would be misleading.
    heatmap_values = np.ma.masked_invalid(heatmap_df.values.astype(float))
    colormap = plt.cm.RdBu_r.copy()
    colormap.set_bad(color="#1e293b")  # matches DARK_PANEL so gaps look intentionally empty

    figure, axis = plt.subplots(figsize=(18, 8))
    image = axis.imshow(
        heatmap_values,
        aspect="auto",
        cmap=colormap,
        vmin=-5,
        vmax=5,
        interpolation="nearest",
    )
    colorbar = figure.colorbar(image, ax=axis, label="Temperature anomaly (°F)", shrink=0.8)
    colorbar.ax.yaxis.label.set_color(LIGHT_TEXT)
    colorbar.ax.tick_params(colors=LIGHT_TEXT)

    axis.set_yticks(range(len(heatmap_df.index)))
    axis.set_yticklabels(heatmap_df.index, fontsize=8)
    axis.set_xticks(range(len(heatmap_df.columns)))
    axis.set_xticklabels(heatmap_df.columns, rotation=90, fontsize=7)
    axis.set_title("Annual Temperature Anomaly vs 1981-2010 Baseline", fontsize=13, pad=10)

    apply_dark_style(figure, [axis])
    plt.tight_layout()
    save_figure("anomaly_heatmap.png")


def plot_decadal_trends(records: list[StationRecord]) -> None:
    """
    Grouped bar chart: x-axis = decade (1950s through 2020s),
    one bar group per climate zone, bars show average temperature anomaly
    relative to the 1981-2010 baseline.

    Showing anomalies instead of absolute temperatures removes the baseline
    difference between zones (polar cities are always colder than tropical),
    so the warming trend becomes visible across all zones on the same scale.
    """
    decades = list(range(1950, 2030, 10))
    zone_names = list(ZONE_COLORS.keys())

    # Compute anomalies for each city, then group into decades.
    zone_decade_means = {zone: {} for zone in zone_names}
    for record in records:
        if record.df.empty or "temp" not in record.df.columns:
            continue
        anomalies = compute_anomalies(record.df)
        if anomalies.empty:
            continue
        anomaly_df = anomalies.to_frame(name="anomaly")
        decadal_means = compute_decadal_means(anomaly_df, "anomaly")
        if decadal_means.empty:
            continue
        for decade, row in decadal_means.iterrows():
            zone = record.climate_zone
            if decade not in zone_decade_means[zone]:
                zone_decade_means[zone][decade] = []
            zone_decade_means[zone][decade].append(row["mean_value"])

    # Average across cities within each zone per decade, skipping NaN values.
    zone_decade_averages = {}
    for zone_name, decade_data in zone_decade_means.items():
        zone_decade_averages[zone_name] = {}
        for decade, values in decade_data.items():
            valid_values = [v for v in values if pd.notna(v)]
            if valid_values:
                zone_decade_averages[zone_name][decade] = sum(valid_values) / len(valid_values)

    figure, axis = plt.subplots(figsize=(14, 6))

    number_of_zones = len(zone_names)
    bar_width = 0.15
    offsets = [(i - number_of_zones / 2 + 0.5) * bar_width for i in range(number_of_zones)]

    for zone_index, zone_name in enumerate(zone_names):
        x_positions = []
        bar_heights = []
        for decade_index, decade in enumerate(decades):
            if decade in zone_decade_averages[zone_name]:
                x_positions.append(decade_index + offsets[zone_index])
                bar_heights.append(zone_decade_averages[zone_name][decade])
        if x_positions:
            axis.bar(
                x_positions,
                bar_heights,
                width=bar_width,
                color=ZONE_COLORS[zone_name],
                alpha=0.9,
                label=zone_name.capitalize(),
            )

    # Zero line marks the 1981-2010 baseline. Bars above it are warmer than
    # average, bars below are cooler.
    axis.axhline(0, color=LIGHT_TEXT, linewidth=0.8, linestyle="--", alpha=0.5)

    decade_labels = [f"{d}s" for d in decades]
    axis.set_xticks(range(len(decades)))
    axis.set_xticklabels(decade_labels, fontsize=9)
    axis.set_ylabel("Temperature anomaly (°F) vs 1981-2010 baseline", fontsize=9)
    axis.set_xlabel("Decade", fontsize=9)
    axis.set_title("Zone-Averaged Decadal Temperature Anomaly (1950s-2020s)", fontsize=13, pad=10)

    legend_patches = [
        mpatches.Patch(color=ZONE_COLORS[zone], label=zone.capitalize())
        for zone in zone_names
    ]
    axis.legend(
        handles=legend_patches,
        loc="upper left",
        fontsize=8,
        facecolor=DARK_PANEL,
        edgecolor=GRID_COLOR,
        labelcolor=LIGHT_TEXT,
    )

    apply_dark_style(figure, [axis])
    plt.tight_layout()
    save_figure("decadal_trends.png")


if __name__ == "__main__":
    print("Loading city data...")
    records = load_all_cities()

    print("\nGenerating plots...")
    plot_temperature_timeseries(records)
    plot_anomaly_heatmap(records)
    plot_decadal_trends(records)

    print("\nDone. All plots saved to plots/")
