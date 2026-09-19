"""
calculate_error.py
Calculates historical NWP forecast errors (MAE, RMSE, bias, residual distributions)
and detects operational 'forecast bust' events based on meteorological thresholds.
Saves and organizes the historical forecast-error database.
"""

import logging
from typing import Dict, Tuple
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# IMD & Operational Meteorological Bust Thresholds
BUST_THRESHOLDS = {
    "rain_abs_mm": 25.0,        # Severe rainfall forecast bust (e.g. cloudburst missed or false alarm)
    "rain_rel_ratio": 1.0,      # >100% relative error when obs > 15mm
    "temp_abs_c": 3.0,          # >3.0°C deviation (critical for heat waves / cold waves)
    "wind_abs_ms": 6.0,         # >6.0 m/s deviation (critical for cyclonic / squall events)
    "mslp_abs_hpa": 4.0         # >4.0 hPa deviation (indicates synoptic pressure depth failure)
}

def assign_meteorological_season(date_series: pd.Series) -> pd.Series:
    """
    Categorizes dates into the four standard Indian Meteorological Department (IMD) seasons:
    - Winter: January - February
    - Pre-Monsoon (Summer): March - May
    - Southwest Monsoon: June - September
    - Post-Monsoon (NE Monsoon): October - December
    """
    months = pd.to_datetime(date_series).dt.month
    seasons = pd.Series(index=date_series.index, dtype="object")
    
    seasons[months.isin([1, 2])] = "Winter"
    seasons[months.isin([3, 4, 5])] = "Pre-Monsoon"
    seasons[months.isin([6, 7, 8, 9])] = "SW-Monsoon"
    seasons[months.isin([10, 11, 12])] = "Post-Monsoon"
    return seasons

def calculate_errors_and_busts(aligned_df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes residual errors (Forecast - Observed), absolute errors, and flags forecast busts.
    Organizes data by location, lead time, season, and synoptic conditions.
    """
    df = aligned_df.copy()
    
    # 1. Residuals (Forecast - Observation)
    df["rain_error"] = df["rain_forecast"] - df["rain_observed"]
    df["temp_error"] = df["temp_forecast"] - df["temp_observed"]
    df["mslp_error"] = df["mslp_forecast"] - df["mslp_observed"]
    df["rh_error"] = df["rh_forecast"] - df["rh_observed"]
    df["wind_error"] = df["wind_forecast"] - df["wind_observed"]
    
    # 2. Absolute errors
    df["rain_abs_error"] = df["rain_error"].abs()
    df["temp_abs_error"] = df["temp_error"].abs()
    df["mslp_abs_error"] = df["mslp_error"].abs()
    df["rh_abs_error"] = df["rh_error"].abs()
    df["wind_abs_error"] = df["wind_error"].abs()
    
    # 3. Variable-specific bust indicators
    # Rainfall bust: absolute error >= 25 mm/day OR (obs > 15mm and relative error >= 100%)
    rel_rain_error = df["rain_abs_error"] / np.maximum(df["rain_observed"], 5.0)
    df["is_rain_bust"] = (
        (df["rain_abs_error"] >= BUST_THRESHOLDS["rain_abs_mm"]) |
        ((df["rain_observed"] >= 15.0) & (rel_rain_error >= BUST_THRESHOLDS["rain_rel_ratio"]))
    ).astype(int)
    
    df["is_temp_bust"] = (df["temp_abs_error"] >= BUST_THRESHOLDS["temp_abs_c"]).astype(int)
    df["is_wind_bust"] = (df["wind_abs_error"] >= BUST_THRESHOLDS["wind_abs_ms"]).astype(int)
    df["is_mslp_bust"] = (df["mslp_abs_error"] >= BUST_THRESHOLDS["mslp_abs_hpa"]).astype(int)
    
    # Composite Forecast Bust: If any primary variable suffers a major operational bust
    df["is_forecast_bust"] = (
        (df["is_rain_bust"] == 1) |
        (df["is_temp_bust"] == 1) |
        (df["is_wind_bust"] == 1) |
        (df["is_mslp_bust"] == 1)
    ).astype(int)
    
    # Assign season
    if "season" not in df.columns and "valid_date" in df.columns:
        df["season"] = assign_meteorological_season(df["valid_date"])
        
    logger.info(f"Calculated errors. Total samples: {len(df)}. Overall bust rate: {df['is_forecast_bust'].mean()*100:.1f}%.")
    return df

def generate_historical_error_climatology(error_df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """
    Aggregates historical forecast error statistics (MAE, RMSE, Bias, Bust Rate)
    organized by:
    1. Region & Lead Time
    2. Region, Lead Time & Season
    3. Region & Synoptic Weather Regime
    """
    # Group 1: Region & Lead Time
    reg_lead_stats = error_df.groupby(["region_id", "lead_time_days"]).agg(
        sample_count=("forecast_id", "count"),
        rain_mae=("rain_abs_error", "mean"),
        rain_rmse=("rain_error", lambda x: np.sqrt(np.mean(x**2))),
        rain_bias=("rain_error", "mean"),
        temp_mae=("temp_abs_error", "mean"),
        temp_rmse=("temp_error", lambda x: np.sqrt(np.mean(x**2))),
        temp_bias=("temp_error", "mean"),
        wind_mae=("wind_abs_error", "mean"),
        wind_rmse=("wind_error", lambda x: np.sqrt(np.mean(x**2))),
        mslp_mae=("mslp_abs_error", "mean"),
        mslp_rmse=("mslp_error", lambda x: np.sqrt(np.mean(x**2))),
        bust_rate=("is_forecast_bust", "mean")
    ).reset_index()
    
    # Group 2: Regime-specific error behaviour
    regime_stats = error_df.groupby(["synoptic_regime", "lead_time_days"]).agg(
        sample_count=("forecast_id", "count"),
        rain_mae=("rain_abs_error", "mean"),
        temp_mae=("temp_abs_error", "mean"),
        wind_mae=("wind_abs_error", "mean"),
        bust_rate=("is_forecast_bust", "mean")
    ).reset_index()

    return {
        "region_lead_stats": reg_lead_stats,
        "regime_stats": regime_stats
    }

if __name__ == "__main__":
    from read_nwp import generate_synthetic_meteorological_dataset
    from align_data import align_forecast_and_observations
    
    fc, obs = generate_synthetic_meteorological_dataset(n_samples=500)
    aligned = align_forecast_and_observations(fc, obs)
    error_df = calculate_errors_and_busts(aligned)
    stats = generate_historical_error_climatology(error_df)
    print("Region & Lead Time Error Summary (first 4):")
    print(stats["region_lead_stats"].head(4))
