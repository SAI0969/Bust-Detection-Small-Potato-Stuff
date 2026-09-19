"""
feature_engineering.py
Extracts meteorological indicators, spatial gradients, temporal tendencies,
ensemble spreads, historical error climatologies, and detects rapidly evolving synoptic regimes.
"""

import logging
from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Feature columns list used across training, evaluation, and backend inference
METEOROLOGICAL_FEATURE_COLS = [
    # Core NWP variables
    "rain_forecast",
    "temp_forecast",
    "mslp_forecast",
    "rh_forecast",
    "wind_forecast",
    "cape_forecast",
    
    # Derived atmospheric dynamics
    "saturation_deficit",          # 100 - RH
    "convective_intensity_index",  # (CAPE * Wind) / 1000
    "pressure_anomaly",            # 1013.25 - MSLP
    
    # Spatial gradients (synthetic / derived)
    "spatial_pressure_gradient",   # hPa per 100km
    "spatial_rain_gradient",       # mm/day spatial variance
    
    # Temporal tendencies
    "temp_tendency_24h",           # 24-hr temp swing
    "mslp_tendency_24h",           # 24-hr pressure drop/rise
    "rain_tendency_24h",           # 24-hr rainfall amplification
    
    # Lead time & ensemble spread
    "lead_time_days",
    "lead_time_sq",
    "ensemble_spread",
    "spread_lead_ratio",
    
    # Synoptic weather regime indicators
    "regime_monsoon_depression",
    "regime_heavy_rainfall",
    "regime_cyclone",
    "regime_heat_wave",
    "regime_western_disturbance",
    "regime_active_break_monsoon",
    "is_rapid_evolving_system",
    
    # Historical climatological error memory
    "hist_region_bust_rate",
    "hist_region_rain_mae",
    "hist_region_temp_mae"
]

def identify_weather_regime_rules(row: pd.Series) -> str:
    """
    Identifies the synoptic regime based on meteorological thresholds if not already tagged.
    """
    rain = row.get("rain_forecast", 0.0)
    temp = row.get("temp_forecast", 25.0)
    mslp = row.get("mslp_forecast", 1010.0)
    wind = row.get("wind_forecast", 5.0)
    cape = row.get("cape_forecast", 500.0)
    month = pd.to_datetime(row.get("valid_date", "2024-07-01")).month if "valid_date" in row else 7
    region = row.get("region_id", "CI")
    
    # Cyclone: Deep pressure drop + extreme wind
    if mslp < 990.0 and wind >= 22.0:
        return "cyclone"
    # Heat wave: Extreme temperature during summer/pre-monsoon
    if temp >= 42.0 and rain < 5.0:
        return "heat_wave"
    # Monsoon depression: Low pressure, strong wind, high CAPE & rain during monsoon
    if month in [6, 7, 8, 9] and mslp <= 998.0 and rain >= 60.0 and wind >= 12.0:
        return "monsoon_depression"
    # Extreme heavy rainfall / orographic cloudburst
    if rain >= 80.0:
        return "heavy_rainfall"
    # Western Disturbance: North/NW India winter/spring with cold temp, precipitation & pressure drop
    if region in ["NW"] and month in [11, 12, 1, 2, 3] and rain >= 15.0 and temp <= 18.0:
        return "western_disturbance"
    # Active/Break monsoon
    if month in [6, 7, 8, 9] and rain < 5.0 and temp >= 32.0:
        return "active_break_monsoon"
        
    return "normal_pattern"

def extract_features(
    df: pd.DataFrame,
    hist_stats: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Engineers meteorological, gradient, temporal, ensemble, regime, and historical error features.
    Works for both historical training frames and single/batch live inference frames.
    """
    out = df.copy()
    
    # 1. Derived atmospheric indicators
    out["saturation_deficit"] = np.maximum(0.0, 100.0 - out["rh_forecast"])
    out["convective_intensity_index"] = (out["cape_forecast"] * out["wind_forecast"]) / 1000.0
    out["pressure_anomaly"] = 1013.25 - out["mslp_forecast"]
    
    # 2. Approximate spatial gradients
    # In live NWP grids, gradient is computed across neighbor cells.
    # Here we calculate physics-consistent gradients:
    # Pressure gradient increases with wind speed and pressure anomaly
    if "spatial_pressure_gradient" not in out.columns:
        out["spatial_pressure_gradient"] = np.round(
            (out["wind_forecast"] * 0.22) + (np.abs(out["pressure_anomaly"]) * 0.15) + np.random.uniform(0.1, 0.5, len(out)),
            2
        )
    if "spatial_rain_gradient" not in out.columns:
        out["spatial_rain_gradient"] = np.round(
            (out["rain_forecast"] * 0.35) + np.random.exponential(scale=1.2, size=len(out)),
            2
        )
        
    # 3. Temporal tendencies (24h rate of change)
    if "temp_tendency_24h" not in out.columns:
        out["temp_tendency_24h"] = np.round(np.random.normal(0.0, 1.2, size=len(out)), 2)
    if "mslp_tendency_24h" not in out.columns:
        # Steep pressure fall for cyclones and depressions
        mslp_tend = np.random.normal(0.0, 1.5, size=len(out))
        if "synoptic_regime" in out.columns:
            mslp_tend = np.where(out["synoptic_regime"] == "cyclone", -np.random.uniform(8.0, 18.0, len(out)), mslp_tend)
            mslp_tend = np.where(out["synoptic_regime"] == "monsoon_depression", -np.random.uniform(3.0, 8.0, len(out)), mslp_tend)
        out["mslp_tendency_24h"] = np.round(mslp_tend, 2)
    if "rain_tendency_24h" not in out.columns:
        out["rain_tendency_24h"] = np.round(np.random.normal(0.0, 4.0, size=len(out)), 2)
        
    # 4. Lead time & ensemble spread features
    out["lead_time_sq"] = out["lead_time_days"] ** 2
    if "ensemble_spread" not in out.columns:
        out["ensemble_spread"] = np.round(2.0 + 1.2 * out["lead_time_days"] + np.random.exponential(scale=1.0, size=len(out)), 2)
    out["spread_lead_ratio"] = out["ensemble_spread"] / np.maximum(out["lead_time_days"], 1.0)
    
    # 5. Synoptic weather regimes
    if "synoptic_regime" not in out.columns:
        out["synoptic_regime"] = out.apply(identify_weather_regime_rules, axis=1)
        
    out["regime_monsoon_depression"] = (out["synoptic_regime"] == "monsoon_depression").astype(int)
    out["regime_heavy_rainfall"] = (out["synoptic_regime"] == "heavy_rainfall").astype(int)
    out["regime_cyclone"] = (out["synoptic_regime"] == "cyclone").astype(int)
    out["regime_heat_wave"] = (out["synoptic_regime"] == "heat_wave").astype(int)
    out["regime_western_disturbance"] = (out["synoptic_regime"] == "western_disturbance").astype(int)
    out["regime_active_break_monsoon"] = (out["synoptic_regime"] == "active_break_monsoon").astype(int)
    
    out["is_rapid_evolving_system"] = (
        out["regime_monsoon_depression"] |
        out["regime_heavy_rainfall"] |
        out["regime_cyclone"] |
        out["regime_heat_wave"] |
        out["regime_western_disturbance"]
    ).astype(int)
    
    # 6. Historical error statistics mapping
    if hist_stats is not None and "region_id" in out.columns and "lead_time_days" in out.columns:
        merged = pd.merge(
            out,
            hist_stats[["region_id", "lead_time_days", "bust_rate", "rain_mae", "temp_mae"]],
            on=["region_id", "lead_time_days"],
            how="left"
        )
        out["hist_region_bust_rate"] = merged["bust_rate"].fillna(0.20)
        out["hist_region_rain_mae"] = merged["rain_mae"].fillna(12.0)
        out["hist_region_temp_mae"] = merged["temp_mae"].fillna(2.0)
    else:
        # Default baseline climatology heuristic based on lead time
        out["hist_region_bust_rate"] = np.clip(0.08 + 0.03 * out["lead_time_days"], 0.05, 0.50)
        out["hist_region_rain_mae"] = np.round(6.0 + 1.8 * out["lead_time_days"], 2)
        out["hist_region_temp_mae"] = np.round(1.0 + 0.25 * out["lead_time_days"], 2)
        
    return out

if __name__ == "__main__":
    from read_nwp import generate_synthetic_meteorological_dataset
    from align_data import align_forecast_and_observations
    from calculate_error import calculate_errors_and_busts, generate_historical_error_climatology
    
    fc, obs = generate_synthetic_meteorological_dataset(n_samples=200)
    aligned = align_forecast_and_observations(fc, obs)
    error_df = calculate_errors_and_busts(aligned)
    stats = generate_historical_error_climatology(error_df)
    
    featured_df = extract_features(error_df, stats["region_lead_stats"])
    print("Features extracted successfully! Shape:", featured_df[METEOROLOGICAL_FEATURE_COLS].shape)
    print("Available engineered features:", METEOROLOGICAL_FEATURE_COLS)
