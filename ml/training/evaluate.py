"""
evaluate.py
Evaluates the Forecast Bust Detection and AI Error Reduction model.
Generates comprehensive benchmark reports comparing Earlier NWP errors vs After AI reduction.
"""

import os
import sys
import pickle
import json
import logging
from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.metrics import (
    classification_report, confusion_matrix, roc_auc_score,
    mean_absolute_error, mean_squared_error, r2_score, brier_score_loss
)

current_dir = os.path.dirname(os.path.abspath(__file__))
ml_dir = os.path.abspath(os.path.join(current_dir, ".."))
project_dir = os.path.abspath(os.path.join(ml_dir, ".."))
if ml_dir not in sys.path:
    sys.path.append(ml_dir)

from features.feature_engineering import METEOROLOGICAL_FEATURE_COLS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def evaluate_system(
    model_path: str = None,
    dataset_path: str = None,
    report_output_path: str = None
) -> Dict[str, Any]:
    """
    Loads saved model bundle and test dataset, computes comprehensive verification metrics,
    and formats an operational evaluation report with exact before vs after error reduction figures.
    """
    if model_path is None:
        model_path = os.path.join(project_dir, "backend", "app", "models", "bust_model.pkl")
    if dataset_path is None:
        dataset_path = os.path.join(ml_dir, "data", "processed", "historical_nwp_features.parquet")
    if report_output_path is None:
        report_output_path = os.path.join(ml_dir, "data", "processed", "evaluation_report.json")
        
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}. Please run train.py first.")
        
    with open(model_path, "rb") as f:
        bundle = pickle.load(f)
        
    clf = bundle["bust_classifier"]
    reg_rain = bundle["rain_error_regressor"]
    reg_temp = bundle["temp_error_regressor"]
    feature_cols = bundle["feature_cols"]
    
    logger.info(f"Loading test dataset from {dataset_path}...")
    df = pd.read_parquet(dataset_path) if dataset_path.endswith(".parquet") else pd.read_csv(dataset_path)
    
    # Evaluate on the last 25% chronological / held-out samples
    test_size = int(len(df) * 0.25)
    test_df = df.iloc[-test_size:].copy()
    
    X_test = test_df[feature_cols]
    y_bust_true = test_df["is_forecast_bust"].values
    
    # Model predictions
    bust_probs = clf.predict_proba(X_test)[:, 1]
    bust_preds = (bust_probs >= 0.5).astype(int)
    pred_rain_err = reg_rain.predict(X_test)
    pred_temp_err = reg_temp.predict(X_test)
    
    test_df["bust_prob"] = bust_probs
    test_df["pred_rain_error"] = pred_rain_err
    test_df["corrected_rain"] = np.maximum(0.0, test_df["rain_forecast"] - pred_rain_err)
    test_df["corrected_temp"] = test_df["temp_forecast"] - pred_temp_err
    
    # 1. Classification Metrics
    auc = roc_auc_score(y_bust_true, bust_probs)
    brier = brier_score_loss(y_bust_true, bust_probs)
    conf_matrix = confusion_matrix(y_bust_true, bust_preds).tolist()
    class_report = classification_report(y_bust_true, bust_preds, output_dict=True)
    
    # 2. Overall Error Reduction Comparison
    # Rainfall
    raw_rain_mae = mean_absolute_error(test_df["rain_observed"], test_df["rain_forecast"])
    raw_rain_rmse = np.sqrt(mean_squared_error(test_df["rain_observed"], test_df["rain_forecast"]))
    ai_rain_mae = mean_absolute_error(test_df["rain_observed"], test_df["corrected_rain"])
    ai_rain_rmse = np.sqrt(mean_squared_error(test_df["rain_observed"], test_df["corrected_rain"]))
    rain_reduction_pct = ((raw_rain_mae - ai_rain_mae) / raw_rain_mae) * 100.0
    
    # Temperature
    raw_temp_mae = mean_absolute_error(test_df["temp_observed"], test_df["temp_forecast"])
    raw_temp_rmse = np.sqrt(mean_squared_error(test_df["temp_observed"], test_df["temp_forecast"]))
    ai_temp_mae = mean_absolute_error(test_df["temp_observed"], test_df["corrected_temp"])
    ai_temp_rmse = np.sqrt(mean_squared_error(test_df["temp_observed"], test_df["corrected_temp"]))
    temp_reduction_pct = ((raw_temp_mae - ai_temp_mae) / raw_temp_mae) * 100.0
    
    # 3. Lead Time Breakdown (Day 1 to Day 10)
    lead_time_table = []
    for day in range(1, 11):
        day_slice = test_df[test_df["lead_time_days"] == day]
        if len(day_slice) > 0:
            day_raw_rain_mae = mean_absolute_error(day_slice["rain_observed"], day_slice["rain_forecast"])
            day_ai_rain_mae = mean_absolute_error(day_slice["rain_observed"], day_slice["corrected_rain"])
            day_raw_temp_mae = mean_absolute_error(day_slice["temp_observed"], day_slice["temp_forecast"])
            day_ai_temp_mae = mean_absolute_error(day_slice["temp_observed"], day_slice["corrected_temp"])
            
            lead_time_table.append({
                "lead_time": f"Day {day}",
                "raw_rain_mae": round(float(day_raw_rain_mae), 2),
                "ai_rain_mae": round(float(day_ai_rain_mae), 2),
                "rain_error_reduction_pct": round(float(((day_raw_rain_mae - day_ai_rain_mae)/day_raw_rain_mae)*100), 1),
                "raw_temp_mae": round(float(day_raw_temp_mae), 2),
                "ai_temp_mae": round(float(day_ai_temp_mae), 2),
                "temp_error_reduction_pct": round(float(((day_raw_temp_mae - day_ai_temp_mae)/day_raw_temp_mae)*100), 1),
                "bust_frequency_pct": round(float(day_slice["is_forecast_bust"].mean() * 100), 1),
                "mean_confidence": round(float((1.0 - day_slice["bust_prob"].mean()) * 100), 1)
            })
            
    # 4. Regional Breakdown
    regional_table = []
    for reg in test_df["region_id"].unique():
        reg_slice = test_df[test_df["region_id"] == reg]
        reg_raw_mae = mean_absolute_error(reg_slice["rain_observed"], reg_slice["rain_forecast"])
        reg_ai_mae = mean_absolute_error(reg_slice["rain_observed"], reg_slice["corrected_rain"])
        regional_table.append({
            "region_id": str(reg),
            "region_name": str(reg_slice["region_name"].iloc[0]) if "region_name" in reg_slice else reg,
            "raw_rain_mae": round(float(reg_raw_mae), 2),
            "ai_rain_mae": round(float(reg_ai_mae), 2),
            "rain_error_reduction_pct": round(float(((reg_raw_mae - reg_ai_mae)/reg_raw_mae)*100), 1),
            "bust_rate_pct": round(float(reg_slice["is_forecast_bust"].mean() * 100), 1)
        })

    report = {
        "summary": {
            "test_samples": len(test_df),
            "roc_auc": round(float(auc), 4),
            "brier_score": round(float(brier), 4),
            "rain_mae_earlier_mm": round(float(raw_rain_mae), 2),
            "rain_mae_after_ai_mm": round(float(ai_rain_mae), 2),
            "rain_mae_reduction_percent": round(float(rain_reduction_pct), 2),
            "temp_mae_earlier_c": round(float(raw_temp_mae), 2),
            "temp_mae_after_ai_c": round(float(ai_temp_mae), 2),
            "temp_mae_reduction_percent": round(float(temp_reduction_pct), 2)
        },
        "lead_time_performance": lead_time_table,
        "regional_performance": regional_table,
        "confusion_matrix": conf_matrix,
        "classification_report": class_report
    }
    
    with open(report_output_path, "w") as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Evaluation report saved to {report_output_path}")
    return report

if __name__ == "__main__":
    rep = evaluate_system()
    print("Evaluation Summary:")
    print(json.dumps(rep["summary"], indent=2))
