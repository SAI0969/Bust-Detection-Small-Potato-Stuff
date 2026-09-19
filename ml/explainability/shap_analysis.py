"""
shap_analysis.py
Provides explainable AI for meteorological forecast bust predictions using SHAP (SHapley Additive exPlanations).
Generates both quantitative feature attributions and domain-specific meteorological explanations.
"""

import os
import sys
import pickle
import logging
from typing import Dict, List, Any, Optional
import numpy as np
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
ml_dir = os.path.abspath(os.path.join(current_dir, ".."))
project_dir = os.path.abspath(os.path.join(ml_dir, ".."))
if ml_dir not in sys.path:
    sys.path.append(ml_dir)

from features.feature_engineering import METEOROLOGICAL_FEATURE_COLS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Feature display mappings for user-friendly meteorological explanations
FEATURE_METEO_DESCRIPTIONS = {
    "ensemble_spread": "Ensemble Member Disagreement (Spread)",
    "lead_time_days": "Forecast Lead Time",
    "lead_time_sq": "Non-linear Lead Time Degradation",
    "rain_forecast": "NWP Forecasted Rainfall Magnitude",
    "mslp_tendency_24h": "24-hr Pressure Drop / Cyclone Deepening",
    "spatial_pressure_gradient": "Baroclinic Pressure Gradient",
    "convective_intensity_index": "Convective Instability & Wind Shear (CAPE x Wind)",
    "is_rapid_evolving_system": "Presence of Rapidly Evolving Weather System",
    "regime_monsoon_depression": "Monsoon Depression Synoptic Regime",
    "regime_heavy_rainfall": "Heavy Orographic / Convective Rainfall Regime",
    "regime_cyclone": "Tropical Cyclone System Active",
    "regime_heat_wave": "Severe Heat Wave Thermal Advection",
    "regime_western_disturbance": "Western Disturbance Mid-Latitude Trough",
    "hist_region_bust_rate": "Historical Regional Forecast Bust Climatology",
    "hist_region_rain_mae": "Historical Baseline Regional Error Memory",
    "spatial_rain_gradient": "Localized Rainfall Spatial Heterogeneity",
    "temp_forecast": "NWP Forecasted Surface Temperature",
    "mslp_forecast": "Mean Sea Level Pressure (Synoptic Depth)",
    "wind_forecast": "10m Wind Speed / Gale Intensity",
    "rh_forecast": "Relative Humidity (Moisture Availability)",
    "saturation_deficit": "Atmospheric Saturation Deficit",
    "temp_tendency_24h": "24-hr Rapid Temperature Trend",
    "rain_tendency_24h": "24-hr Rainfall Intensification Rate",
    "spread_lead_ratio": "Spread-to-Lead Ratio (Atmospheric Chaos)"
}

class MeteoSHAPExplainer:
    def __init__(self, model_bundle_or_path: Any):
        if isinstance(model_bundle_or_path, str):
            with open(model_bundle_or_path, "rb") as f:
                self.bundle = pickle.load(f)
        else:
            self.bundle = model_bundle_or_path
            
        self.model = self.bundle["bust_classifier"]
        self.feature_cols = self.bundle["feature_cols"]
        import shap
        self.explainer = shap.TreeExplainer(self.model)
        
    def explain_instance(self, sample_features: pd.DataFrame) -> Dict[str, Any]:
        """
        Computes SHAP attribution values for a single forecast instance
        and formats them into meteorological explanations.
        """
        if isinstance(sample_features, pd.Series):
            sample_features = pd.DataFrame([sample_features])
            
        # Ensure all columns exist
        for col in self.feature_cols:
            if col not in sample_features.columns:
                sample_features[col] = 0.0
                
        X_eval = sample_features[self.feature_cols]
        
        # Calculate SHAP values
        shap_values = self.explainer.shap_values(X_eval)
        if isinstance(shap_values, list):
            # For binary classification, take positive class (bust)
            sv = shap_values[1][0]
            base_val = float(self.explainer.expected_value[1])
        else:
            sv = shap_values[0]
            base_val = float(self.explainer.expected_value) if hasattr(self.explainer.expected_value, "__iter__") else float(self.explainer.expected_value)

        features_summary = []
        for idx, col in enumerate(self.feature_cols):
            val = float(X_eval[col].iloc[0])
            s_val = float(sv[idx])
            display_name = FEATURE_METEO_DESCRIPTIONS.get(col, col.replace("_", " ").title())
            
            features_summary.append({
                "feature": col,
                "display_name": display_name,
                "value": round(val, 2),
                "shap_value": round(s_val, 4),
                "impact": "Increases Bust Risk" if s_val > 0 else "Decreases Bust Risk / Increases Confidence",
                "abs_importance": abs(s_val)
            })
            
        # Sort by absolute SHAP attribution
        features_summary.sort(key=lambda x: x["abs_importance"], reverse=True)
        top_drivers = features_summary[:6]
        
        # Generate domain-specific meteorological narrative
        narratives = []
        for d in top_drivers[:4]:
            feat = d["feature"]
            val = d["value"]
            s_val = d["shap_value"]
            
            if feat == "ensemble_spread":
                narratives.append(f"Elevated ensemble spread ({val}) indicates high NWP member disagreement, adding +{abs(s_val*100):.1f}% to bust risk." if s_val > 0 else f"Tight ensemble clustering ({val}) reinforces forecast consensus.")
            elif feat == "lead_time_days":
                narratives.append(f"Day {int(val)} medium-range forecast lead time naturally increases atmospheric chaos uncertainty (+{abs(s_val*100):.1f}%)." if s_val > 0 else f"Short lead time (Day {int(val)}) affords high physical determinism.")
            elif feat in ["mslp_tendency_24h", "spatial_pressure_gradient"]:
                narratives.append(f"Steep 24-hr pressure tendency ({val} hPa) signals active cyclogenesis or depression deepening, driving error uncertainty (+{abs(s_val*100):.1f}%).")
            elif feat == "rain_forecast":
                narratives.append(f"Intense precipitation forecast ({val} mm/day) triggers high convective boundary sensitivity (+{abs(s_val*100):.1f}%)." if val > 50 else f"Moderate rainfall forecast reduces extreme bust likelihood.")
            elif feat.startswith("regime_") or feat == "is_rapid_evolving_system":
                if val > 0:
                    narratives.append(f"Active synoptic regime ({d['display_name']}) historically exhibits non-linear NWP track/intensity errors.")
            elif feat == "convective_intensity_index":
                narratives.append(f"Elevated convective instability index ({val}) points to mesoscale cloudburst volatility.")
            else:
                action = "raising" if s_val > 0 else "lowering"
                narratives.append(f"{d['display_name']} (value: {val}) is {action} forecast bust probability by {abs(s_val*100):.1f}%.")
                
        return {
            "base_value": round(base_val, 4),
            "top_drivers": top_drivers,
            "all_features": features_summary,
            "meteorological_narratives": narratives
        }

if __name__ == "__main__":
    model_file = os.path.join(project_dir, "backend", "app", "models", "bust_model.pkl")
    if os.path.exists(model_file):
        explainer = MeteoSHAPExplainer(model_file)
        sample = pd.DataFrame([{
            "rain_forecast": 115.0,
            "temp_forecast": 28.5,
            "mslp_forecast": 992.0,
            "rh_forecast": 94.0,
            "wind_forecast": 18.0,
            "cape_forecast": 2800.0,
            "lead_time_days": 5,
            "ensemble_spread": 14.2,
            "regime_monsoon_depression": 1,
            "is_rapid_evolving_system": 1,
            "mslp_tendency_24h": -6.5
        }])
        res = explainer.explain_instance(sample)
        print("SHAP Base Value:", res["base_value"])
        print("Top Drivers:", res["top_drivers"][:3])
        print("Meteorological Narratives:", res["meteorological_narratives"])
    else:
        print("Model not trained yet. Run train.py first.")
