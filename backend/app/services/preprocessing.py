"""
backend/app/services/preprocessing.py
Handles preprocessing and feature preparation for live incoming forecast requests.
"""

import sys
import os
from typing import Dict, Any, List
import numpy as np
import pandas as pd

# Path routing
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
ml_dir = os.path.join(root_dir, "ml")
if ml_dir not in sys.path:
    sys.path.append(ml_dir)

try:
    from features.feature_engineering import extract_features, METEOROLOGICAL_FEATURE_COLS
except ModuleNotFoundError:
    try:
        from ..features.feature_engineering import extract_features, METEOROLOGICAL_FEATURE_COLS
    except Exception:
        from app.features.feature_engineering import extract_features, METEOROLOGICAL_FEATURE_COLS

def prepare_forecast_input(data: Dict[str, Any], climatology_stats: Any = None) -> pd.DataFrame:
    """
    Transforms raw user or NWP forecast payload into model-ready feature vector.
    """
    row = {
        "valid_date": data.get("valid_date", "2024-07-15"),
        "region_id": data.get("region_id", "CI"),
        "latitude": float(data.get("latitude", 22.5)),
        "longitude": float(data.get("longitude", 78.0)),
        "lead_time_days": int(data.get("lead_time_days", 3)),
        "rain_forecast": float(data.get("rain_forecast", 0.0)),
        "temp_forecast": float(data.get("temp_forecast", 28.0)),
        "mslp_forecast": float(data.get("mslp_forecast", 1008.0)),
        "rh_forecast": float(data.get("rh_forecast", 70.0)),
        "wind_forecast": float(data.get("wind_forecast", 5.0)),
        "cape_forecast": float(data.get("cape_forecast", 800.0)),
        "ensemble_spread": float(data.get("ensemble_spread", 4.5)),
        "synoptic_regime": data.get("synoptic_regime", "normal_monsoon")
    }
    
    if "mslp_tendency_24h" in data:
        row["mslp_tendency_24h"] = float(data["mslp_tendency_24h"])
    if "temp_tendency_24h" in data:
        row["temp_tendency_24h"] = float(data["temp_tendency_24h"])
    if "rain_tendency_24h" in data:
        row["rain_tendency_24h"] = float(data["rain_tendency_24h"])
    if "spatial_pressure_gradient" in data:
        row["spatial_pressure_gradient"] = float(data["spatial_pressure_gradient"])
    if "spatial_rain_gradient" in data:
        row["spatial_rain_gradient"] = float(data["spatial_rain_gradient"])
        
    df = pd.DataFrame([row])
    featured_df = extract_features(df, climatology_stats)
    return featured_df[METEOROLOGICAL_FEATURE_COLS]

def prepare_grid_batch(grid_items: List[Dict[str, Any]], climatology_stats: Any = None) -> pd.DataFrame:
    """
    Transforms a batch of grid cell forecasts into model-ready feature DataFrame.
    """
    df = pd.DataFrame(grid_items)
    featured_df = extract_features(df, climatology_stats)
    return featured_df[METEOROLOGICAL_FEATURE_COLS]
