"""
backend/app/services/prediction.py
Model prediction service for Forecast Bust Probability, Confidence Indicators,
Expected Forecast Error, and AI Error Correction.
"""

import os
import sys
import pickle
import logging
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class BustPredictionService:
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            model_path = os.path.join(current_dir, "..", "models", "bust_model.pkl")
            
        self.model_path = model_path
        self.bundle = None
        self._load_model()
        
    def _load_model(self):
        if os.path.exists(self.model_path):
            logger.info(f"Loading bust model bundle from {self.model_path}...")
            with open(self.model_path, "rb") as f:
                self.bundle = pickle.load(f)
            self.classifier = self.bundle["bust_classifier"]
            self.rain_regressor = self.bundle["rain_error_regressor"]
            self.temp_regressor = self.bundle["temp_error_regressor"]
            self.feature_cols = self.bundle["feature_cols"]
            self.climatology_stats = self.bundle.get("climatology_stats")
            self.metrics_summary = self.bundle.get("metrics_summary", {})
            logger.info("Model bundle successfully loaded.")
        else:
            logger.warning(f"Model file not found at {self.model_path}. Placeholder mode active.")
            self.bundle = None
            
    def is_ready(self) -> bool:
        return self.bundle is not None

    def compute_confidence(self, bust_prob: float, lead_time: int) -> Tuple[float, str, str]:
        """
        Converts raw bust probability into an operational forecast confidence score (0-100%)
        and assigns risk category and color code:
        - High Confidence: >= 75% (Green)
        - Moderate Confidence: 55-74% (Blue/Yellow)
        - Low Confidence: 35-54% (Orange)
        - Critical Bust Risk: < 35% (Red Alert)
        """
        # Linear/calibrated confidence mapping
        raw_conf = (1.0 - bust_prob) * 100.0
        # Mild penalty for long lead times if probability is borderline
        lead_penalty = max(0.0, (lead_time - 3) * 1.2) if bust_prob > 0.35 else 0.0
        conf_score = round(float(np.clip(raw_conf - lead_penalty, 5.0, 98.0)), 1)
        
        if conf_score >= 75.0:
            category = "High Confidence"
            color = "#10b981" # Emerald green
        elif conf_score >= 55.0:
            category = "Moderate Confidence"
            color = "#3b82f6" # Oceanic blue
        elif conf_score >= 35.0:
            category = "Low Confidence"
            color = "#f59e0b" # Amber orange
        else:
            category = "Critical Bust Risk"
            color = "#ef4444" # Crimson alert
            
        return conf_score, category, color

    def predict_single(self, features_df: pd.DataFrame, raw_rain: float, raw_temp: float, lead_time: int) -> Dict[str, Any]:
        """
        Predicts bust probability, expected error residual, corrected forecast, and confidence.
        """
        if not self.is_ready():
            self._load_model()
            if not self.is_ready():
                raise RuntimeError("Model is not trained or loaded yet.")
                
        X = features_df[self.feature_cols]
        
        # 1. Bust Probability
        bust_prob = float(self.classifier.predict_proba(X)[0, 1])
        conf_score, conf_category, conf_color = self.compute_confidence(bust_prob, lead_time)
        
        # 2. Expected Errors (signed residuals)
        pred_rain_error = float(self.rain_regressor.predict(X)[0])
        pred_temp_error = float(self.temp_regressor.predict(X)[0])
        
        # 3. AI Corrected Forecast (Forecast - Expected_Error)
        corrected_rain = round(float(np.maximum(0.0, raw_rain - pred_rain_error)), 1)
        corrected_temp = round(float(raw_temp - pred_temp_error), 1)
        
        return {
            "bust_probability": round(bust_prob, 3),
            "bust_probability_percent": round(bust_prob * 100.0, 1),
            "confidence_score": conf_score,
            "confidence_category": conf_category,
            "confidence_color": conf_color,
            "expected_rain_error_mm": round(pred_rain_error, 1),
            "expected_temp_error_c": round(pred_temp_error, 1),
            "raw_rain_forecast": round(raw_rain, 1),
            "corrected_rain_forecast": corrected_rain,
            "raw_temp_forecast": round(raw_temp, 1),
            "corrected_temp_forecast": corrected_temp,
            "error_reduction_applied": True
        }

    def predict_batch(self, features_df: pd.DataFrame, raw_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        High-throughput batch prediction for spatial grid cells.
        """
        if not self.is_ready():
            self._load_model()
            
        X = features_df[self.feature_cols]
        bust_probs = self.classifier.predict_proba(X)[:, 1]
        pred_rain_errs = self.rain_regressor.predict(X)
        pred_temp_errs = self.temp_regressor.predict(X)
        
        results = []
        for i in range(len(raw_df)):
            bp = float(bust_probs[i])
            lead = int(raw_df["lead_time_days"].iloc[i])
            conf_score, conf_category, conf_color = self.compute_confidence(bp, lead)
            
            raw_r = float(raw_df["rain_forecast"].iloc[i])
            raw_t = float(raw_df["temp_forecast"].iloc[i])
            p_r_err = float(pred_rain_errs[i])
            p_t_err = float(pred_temp_errs[i])
            
            corr_r = round(float(np.maximum(0.0, raw_r - p_r_err)), 1)
            corr_t = round(float(raw_t - p_t_err), 1)
            
            results.append({
                "bust_probability": round(bp, 3),
                "bust_probability_percent": round(bp * 100.0, 1),
                "confidence_score": conf_score,
                "confidence_category": conf_category,
                "confidence_color": conf_color,
                "expected_rain_error_mm": round(p_r_err, 1),
                "expected_temp_error_c": round(p_t_err, 1),
                "raw_rain_forecast": round(raw_r, 1),
                "corrected_rain_forecast": corr_r,
                "raw_temp_forecast": round(raw_t, 1),
                "corrected_temp_forecast": corr_t
            })
        return results

# Singleton instance
prediction_service = BustPredictionService()
