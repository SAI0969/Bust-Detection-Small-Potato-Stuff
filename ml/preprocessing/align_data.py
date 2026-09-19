"""
align_data.py
Performs spatial and temporal alignment between raw NWP forecasts and ground-truth observations.
Associates each forecast lead-time slice with corresponding verifying observations.
"""

import logging
from typing import Optional
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def align_forecast_and_observations(
    forecast_df: pd.DataFrame,
    obs_df: pd.DataFrame,
    coord_tolerance_deg: float = 0.5
) -> pd.DataFrame:
    """
    Spatially and temporally aligns NWP forecasts with ground truth observations.
    
    If datasets share exact lat/lon/valid_date keys, it performs direct inner merge.
    If spatial coordinates have small grid offsets (e.g. 0.25° vs station locations),
    uses KDTree spatial matching per date slice.
    """
    logger.info(f"Aligning {len(forecast_df)} forecast records with {len(obs_df)} observation records...")
    
    # Check for direct key match
    common_cols = ["valid_date", "latitude", "longitude"]
    if all(col in forecast_df.columns for col in common_cols) and all(col in obs_df.columns for col in common_cols):
        # Round lat/lon to 2 decimals to ensure clean merge
        fc_copy = forecast_df.copy()
        obs_copy = obs_df.copy()
        fc_copy["lat_round"] = fc_copy["latitude"].round(2)
        fc_copy["lon_round"] = fc_copy["longitude"].round(2)
        obs_copy["lat_round"] = obs_copy["latitude"].round(2)
        obs_copy["lon_round"] = obs_copy["longitude"].round(2)
        
        # Merge on valid_date and rounded coordinates
        merged = pd.merge(
            fc_copy,
            obs_copy.drop(columns=["latitude", "longitude"], errors="ignore"),
            on=["valid_date", "lat_round", "lon_round"],
            how="inner",
            suffixes=("", "_obs_dup")
        )
        
        # Clean duplicate suffix columns if any
        dup_cols = [c for c in merged.columns if c.endswith("_obs_dup")]
        merged = merged.drop(columns=dup_cols + ["lat_round", "lon_round"])
        
        if len(merged) > 0:
            logger.info(f"Direct spatial-temporal alignment successful: {len(merged)} matched records.")
            return merged

    # Fallback to KDTree spatial proximity alignment per date
    aligned_rows = []
    obs_df["date_str"] = pd.to_datetime(obs_df["valid_date"]).dt.strftime("%Y-%m-%d")
    forecast_df["date_str"] = pd.to_datetime(forecast_df["valid_date"]).dt.strftime("%Y-%m-%d")
    
    unique_dates = forecast_df["date_str"].unique()
    for d in unique_dates:
        fc_slice = forecast_df[forecast_df["date_str"] == d].copy()
        obs_slice = obs_df[obs_df["date_str"] == d].copy()
        
        if obs_slice.empty:
            continue
            
        tree = cKDTree(obs_slice[["latitude", "longitude"]].values)
        distances, indices = tree.query(fc_slice[["latitude", "longitude"]].values)
        
        valid_mask = distances <= coord_tolerance_deg
        matched_fc = fc_slice[valid_mask].reset_index(drop=True)
        matched_obs_idx = indices[valid_mask]
        matched_obs = obs_slice.iloc[matched_obs_idx].reset_index(drop=True)
        
        # Combine row-wise
        combined = pd.concat([
            matched_fc,
            matched_obs[[c for c in matched_obs.columns if c.endswith("_observed")]]
        ], axis=1)
        aligned_rows.append(combined)
        
    if not aligned_rows:
        raise ValueError("Could not find matching spatial/temporal pairs between forecast and observations.")
        
    result_df = pd.concat(aligned_rows, ignore_index=True)
    result_df = result_df.drop(columns=["date_str"], errors="ignore")
    logger.info(f"KDTree alignment successful: {len(result_df)} matched records.")
    return result_df

if __name__ == "__main__":
    from read_nwp import generate_synthetic_meteorological_dataset
    fc, obs = generate_synthetic_meteorological_dataset(n_samples=200)
    aligned = align_forecast_and_observations(fc, obs)
    print("Aligned sample shape:", aligned.shape)
    print(aligned.head(2))
