"""
read_nwp.py
Module for reading and ingesting NWP forecast files (.nc, .grib, .grib2, .csv)
and observational datasets using xarray, netCDF4, and pandas.
Includes high-fidelity synthetic generator for historical NWP benchmarks.
"""

import os
import glob
import logging
from typing import Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

try:
    import xarray as xr
except ImportError:
    xr = None

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Key meteorological regions in India
INDIAN_REGIONS = [
    {"region_id": "NW", "name": "Northwest India", "lat_bounds": (24.0, 37.0), "lon_bounds": (68.0, 78.0), "primary_risks": ["Western Disturbance", "Heat Wave"]},
    {"region_id": "CI", "name": "Central India", "lat_bounds": (18.0, 26.0), "lon_bounds": (74.0, 84.0), "primary_risks": ["Monsoon Depression", "Active/Break Phase"]},
    {"region_id": "WG", "name": "Western Ghats & West Coast", "lat_bounds": (8.0, 20.0), "lon_bounds": (72.5, 77.0), "primary_risks": ["Heavy Rainfall", "Orographic Busts"]},
    {"region_id": "NE", "name": "East & Northeast India", "lat_bounds": (21.0, 29.5), "lon_bounds": (85.0, 97.0), "primary_risks": ["Flash Floods", "Monsoon Trough Shift"]},
    {"region_id": "EC", "name": "Bay of Bengal & East Coast", "lat_bounds": (11.0, 22.0), "lon_bounds": (80.0, 89.0), "primary_risks": ["Tropical Cyclone", "Depression Landfall"]},
    {"region_id": "SP", "name": "Southern Peninsula", "lat_bounds": (8.0, 16.0), "lon_bounds": (75.0, 80.5), "primary_risks": ["Northeast Monsoon", "Convective Thunderstorms"]}
]

def read_netcdf_forecast(file_path: str, variables: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Reads an NWP NetCDF (.nc) file using xarray and converts to a standardized Pandas DataFrame.
    """
    if xr is None:
        raise ImportError("xarray is required for reading NetCDF files. Please run `pip install xarray netCDF4`.")
    
    logger.info(f"Loading NetCDF file: {file_path}")
    with xr.open_dataset(file_path) as ds:
        if variables:
            available_vars = [v for v in variables if v in ds.data_vars]
            ds = ds[available_vars]
        df = ds.to_dataframe().reset_index()
    return df

def read_csv_data(file_path: str) -> pd.DataFrame:
    """
    Reads meteorological forecasts or observation tabular data from CSV.
    """
    logger.info(f"Loading CSV data: {file_path}")
    df = pd.read_csv(file_path)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    return df

def read_grib_file(file_path: str) -> pd.DataFrame:
    """
    Reads GRIB/GRIB2 files using xarray with cfgrib engine or fallback.
    """
    if xr is None:
        raise ImportError("xarray is required for reading GRIB files.")
    try:
        ds = xr.open_dataset(file_path, engine="cfgrib")
        return ds.to_dataframe().reset_index()
    except Exception as e:
        logger.warning(f"cfgrib engine not available or failed: {e}. Attempting standard open_dataset...")
        ds = xr.open_dataset(file_path)
        return ds.to_dataframe().reset_index()

def generate_synthetic_meteorological_dataset(
    n_samples: int = 12000,
    start_year: int = 2021,
    end_year: int = 2024,
    random_seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Generates realistic paired NWP Forecast and Observation datasets for Indian meteorological regimes.
    Simulates real atmospheric physics, lead time degradation (Day 1 to Day 10), ensemble spread,
    and characteristic 'forecast bust' dynamics during rapidly evolving synoptic events:
    - Monsoon Depressions (track / precipitation displacement)
    - Extreme Heavy Rainfall (orographic underprediction or convective displacement)
    - Cyclones (rapid intensification, landfall timing bust)
    - Heat Waves (underpredicted extreme max temperatures)
    - Western Disturbances (unseasonal precipitation & sudden pressure drop)
    - Active / Break Monsoon transitions
    
    Returns:
        (forecasts_df, observations_df)
    """
    np.random.seed(random_seed)
    
    dates = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-12-31", freq="D")
    sampled_dates = np.random.choice(dates, size=n_samples, replace=True)
    
    # Sample regions
    region_indices = np.random.choice(len(INDIAN_REGIONS), size=n_samples)
    regions = [INDIAN_REGIONS[i]["region_id"] for i in region_indices]
    region_names = [INDIAN_REGIONS[i]["name"] for i in region_indices]
    
    # Generate coordinates within region bounding boxes
    lats = []
    lons = []
    for i in region_indices:
        r = INDIAN_REGIONS[i]
        lats.append(np.round(np.random.uniform(r["lat_bounds"][0], r["lat_bounds"][1]), 2))
        lons.append(np.round(np.random.uniform(r["lon_bounds"][0], r["lon_bounds"][1]), 2))
    lats = np.array(lats)
    lons = np.array(lons)
    
    # Lead time in days (1 to 10)
    lead_time_days = np.random.choice(np.arange(1, 11), size=n_samples)
    
    months = np.array([pd.Timestamp(d).month for d in sampled_dates])
    
    # Weather regimes simulation
    regimes = []
    for m, reg in zip(months, regions):
        rand = np.random.rand()
        if m in [6, 7, 8, 9]: # SW Monsoon
            if reg in ["CI", "EC"] and rand < 0.35:
                regimes.append("monsoon_depression")
            elif reg == "WG" and rand < 0.45:
                regimes.append("heavy_rainfall")
            elif rand < 0.25:
                regimes.append("active_break_monsoon")
            else:
                regimes.append("normal_monsoon")
        elif m in [4, 5, 6]: # Pre-monsoon / Summer
            if reg in ["NW", "CI"] and rand < 0.40:
                regimes.append("heat_wave")
            elif reg == "EC" and rand < 0.25:
                regimes.append("cyclone")
            else:
                regimes.append("pre_monsoon")
        elif m in [10, 11, 12]: # Post-monsoon
            if reg in ["EC", "SP"] and rand < 0.30:
                regimes.append("cyclone")
            elif reg == "NW" and rand < 0.25:
                regimes.append("western_disturbance")
            else:
                regimes.append("post_monsoon")
        else: # Winter (Jan-Feb)
            if reg == "NW" and rand < 0.40:
                regimes.append("western_disturbance")
            else:
                regimes.append("fair_weather")
    regimes = np.array(regimes)
    
    # True physical baseline observations
    obs_rain = np.zeros(n_samples)
    obs_temp = np.zeros(n_samples)
    obs_mslp = np.zeros(n_samples)
    obs_rh = np.zeros(n_samples)
    obs_wind = np.zeros(n_samples)
    obs_cape = np.zeros(n_samples)
    
    for i in range(n_samples):
        reg = regimes[i]
        m = months[i]
        
        # Baseline temperature
        if reg == "heat_wave":
            t = np.random.uniform(42.0, 48.5)
            r = np.random.exponential(scale=0.5)
            p = np.random.uniform(998.0, 1004.0)
            rh = np.random.uniform(15.0, 35.0)
            w = np.random.uniform(4.0, 10.0)
            c = np.random.uniform(500.0, 1500.0)
        elif reg == "monsoon_depression":
            t = np.random.uniform(26.0, 31.0)
            r = np.random.gamma(shape=3.5, scale=25.0) # 80-160mm
            p = np.random.uniform(988.0, 998.0) # Deep pressure fall
            rh = np.random.uniform(85.0, 98.0)
            w = np.random.uniform(12.0, 24.0)
            c = np.random.uniform(1800.0, 3800.0)
        elif reg == "heavy_rainfall":
            t = np.random.uniform(24.0, 29.0)
            r = np.random.gamma(shape=4.0, scale=30.0) # 100-200mm
            p = np.random.uniform(998.0, 1006.0)
            rh = np.random.uniform(90.0, 100.0)
            w = np.random.uniform(10.0, 20.0)
            c = np.random.uniform(2000.0, 4000.0)
        elif reg == "cyclone":
            t = np.random.uniform(26.0, 30.0)
            r = np.random.gamma(shape=5.0, scale=35.0) # Extreme rain
            p = np.random.uniform(965.0, 988.0) # Extreme low pressure
            rh = np.random.uniform(90.0, 100.0)
            w = np.random.uniform(25.0, 50.0) # Gale / hurricane force
            c = np.random.uniform(2500.0, 4500.0)
        elif reg == "western_disturbance":
            t = np.random.uniform(8.0, 18.0)
            r = np.random.gamma(shape=2.0, scale=12.0)
            p = np.random.uniform(1004.0, 1014.0)
            rh = np.random.uniform(65.0, 90.0)
            w = np.random.uniform(8.0, 16.0)
            c = np.random.uniform(400.0, 1200.0)
        elif reg == "active_break_monsoon":
            t = np.random.uniform(28.0, 34.0)
            r = np.random.exponential(scale=12.0)
            p = np.random.uniform(1002.0, 1009.0)
            rh = np.random.uniform(60.0, 85.0)
            w = np.random.uniform(6.0, 14.0)
            c = np.random.uniform(1200.0, 2600.0)
        else: # Normal conditions
            t = np.random.uniform(22.0, 33.0)
            r = np.random.exponential(scale=6.0)
            p = np.random.uniform(1006.0, 1015.0)
            rh = np.random.uniform(40.0, 75.0)
            w = np.random.uniform(3.0, 8.0)
            c = np.random.uniform(300.0, 1200.0)
            
        obs_rain[i] = np.maximum(0.0, r)
        obs_temp[i] = t
        obs_mslp[i] = p
        obs_rh[i] = np.clip(rh, 5.0, 100.0)
        obs_wind[i] = w
        obs_cape[i] = c

    # NWP Forecasts generation with systematic bias, lead-time error growth, and severe "Forecast Busts"
    # The lead time factor increases error non-linearly: error_sd ~ 1.0 + 0.35 * lead_time**1.2
    lead_error_mult = 1.0 + 0.28 * (lead_time_days ** 1.15)
    
    # Severe forecast bust probability increases strongly during rapidly evolving regimes and higher lead times
    is_rapid_regime = np.isin(regimes, ["monsoon_depression", "heavy_rainfall", "cyclone", "heat_wave", "western_disturbance"])
    bust_prob_latent = 0.08 + 0.035 * lead_time_days + 0.32 * is_rapid_regime
    is_bust_event = np.random.rand(n_samples) < np.clip(bust_prob_latent, 0.05, 0.75)
    
    nwp_rain = np.zeros(n_samples)
    nwp_temp = np.zeros(n_samples)
    nwp_mslp = np.zeros(n_samples)
    nwp_rh = np.zeros(n_samples)
    nwp_wind = np.zeros(n_samples)
    nwp_cape = np.zeros(n_samples)
    ensemble_spread = np.zeros(n_samples)
    
    for i in range(n_samples):
        lm = lead_error_mult[i]
        bust = is_bust_event[i]
        
        # Raw NWP base noise
        rain_err = np.random.normal(loc=1.5, scale=4.0 * lm) # Slight positive rain drizzle bias
        temp_err = np.random.normal(loc=-0.5, scale=0.8 * lm) # Slight cold bias
        mslp_err = np.random.normal(loc=0.3, scale=1.1 * lm)
        rh_err = np.random.normal(loc=2.0, scale=4.0 * lm)
        wind_err = np.random.normal(loc=0.2, scale=1.0 * lm)
        cape_err = np.random.normal(loc=50.0, scale=180.0 * lm)
        
        # In a forecast bust event, NWP creates massive forecast discrepancies:
        # e.g., missing a convective cloudburst (severe underprediction), or completely displacing a depression track
        if bust:
            if regimes[i] in ["heavy_rainfall", "monsoon_depression"]:
                # Underpredict heavy rainfall or misplace core
                rain_err = -0.65 * obs_rain[i] + np.random.normal(0, 15.0)
                mslp_err = np.random.uniform(5.0, 14.0) # NWP missed the low pressure depth
                wind_err = -np.random.uniform(6.0, 15.0) # NWP underpredicted gales
            elif regimes[i] == "cyclone":
                rain_err = -0.55 * obs_rain[i] if np.random.rand() < 0.5 else 0.8 * obs_rain[i]
                mslp_err = np.random.uniform(12.0, 30.0) # Catastrophic central pressure bust
                wind_err = -np.random.uniform(14.0, 28.0)
            elif regimes[i] == "heat_wave":
                temp_err = -np.random.uniform(3.5, 7.5) # NWP missed 4-7 degrees of scorching heat
            elif regimes[i] == "western_disturbance":
                rain_err = np.random.uniform(20.0, 50.0) if np.random.rand() < 0.5 else -0.7 * obs_rain[i]
                temp_err = np.random.uniform(3.0, 6.0)
            else:
                rain_err = np.random.normal(0, 25.0 * lm)
                temp_err = np.random.normal(0, 3.5 * lm)
        
        nwp_rain[i] = np.maximum(0.0, obs_rain[i] + rain_err)
        nwp_temp[i] = obs_temp[i] + temp_err
        nwp_mslp[i] = obs_mslp[i] + mslp_err
        nwp_rh[i] = np.clip(obs_rh[i] + rh_err, 5.0, 100.0)
        nwp_wind[i] = np.maximum(0.5, obs_wind[i] + wind_err)
        nwp_cape[i] = np.maximum(50.0, obs_cape[i] + cape_err)
        
        # Ensemble spread is larger when uncertainty/bust risk is high and at longer lead times
        base_spread = 2.0 + 1.2 * lead_time_days[i]
        if bust:
            base_spread *= np.random.uniform(1.8, 3.5)
        ensemble_spread[i] = np.round(base_spread + np.random.exponential(scale=1.5), 2)
    
    # Forecasts DataFrame
    forecasts_df = pd.DataFrame({
        "forecast_id": [f"FC_{k:07d}" for k in range(n_samples)],
        "valid_date": sampled_dates,
        "region_id": regions,
        "region_name": region_names,
        "latitude": lats,
        "longitude": lons,
        "lead_time_days": lead_time_days,
        "rain_forecast": np.round(nwp_rain, 2),
        "temp_forecast": np.round(nwp_temp, 2),
        "mslp_forecast": np.round(nwp_mslp, 2),
        "rh_forecast": np.round(nwp_rh, 2),
        "wind_forecast": np.round(nwp_wind, 2),
        "cape_forecast": np.round(nwp_cape, 1),
        "ensemble_spread": ensemble_spread,
        "synoptic_regime": regimes
    })
    
    # Observations DataFrame
    observations_df = pd.DataFrame({
        "valid_date": sampled_dates,
        "latitude": lats,
        "longitude": lons,
        "region_id": regions,
        "rain_observed": np.round(obs_rain, 2),
        "temp_observed": np.round(obs_temp, 2),
        "mslp_observed": np.round(obs_mslp, 2),
        "rh_observed": np.round(obs_rh, 2),
        "wind_observed": np.round(obs_wind, 2),
        "cape_observed": np.round(obs_cape, 1)
    })
    
    logger.info(f"Generated synthetic paired NWP benchmark dataset with {n_samples} samples across {len(INDIAN_REGIONS)} regions.")
    return forecasts_df, observations_df

if __name__ == "__main__":
    fc_df, obs_df = generate_synthetic_meteorological_dataset(n_samples=500)
    print("NWP Forecast sample:")
    print(fc_df.head(3))
    print("Observation sample:")
    print(obs_df.head(3))
