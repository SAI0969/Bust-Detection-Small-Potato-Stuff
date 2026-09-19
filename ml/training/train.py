"""
train.py
Trains the dual-head AI/ML Forecast Bust Detection & Error Correction System:
1. Bust Probability Classifier (XGBClassifier): Predicts P(Bust) and Forecast Confidence
2. Expected Error Regressor (XGBRegressor): Predicts forecast error residual for AI bias correction
Saves the production model bundle to backend/app/models/bust_model.pkl.
"""

import os
import sys
import pickle
import logging
from typing import Dict, Any, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, brier_score_loss, mean_absolute_error, mean_squared_error, r2_score
)
from xgboost import XGBClassifier, XGBRegressor

# Add parent directories to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
ml_dir = os.path.abspath(os.path.join(current_dir, ".."))
project_dir = os.path.abspath(os.path.join(ml_dir, ".."))
if ml_dir not in sys.path:
    sys.path.append(ml_dir)

from preprocessing.read_nwp import generate_synthetic_meteorological_dataset
from preprocessing.align_data import align_forecast_and_observations
from preprocessing.calculate_error import calculate_errors_and_busts, generate_historical_error_climatology
from features.feature_engineering import extract_features, METEOROLOGICAL_FEATURE_COLS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def train_bust_system(
    n_samples: int = 15000,
    model_output_path: str = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Executes end-to-end data generation, preprocessing, alignment, feature engineering,
    dual model training (XGBoost Classifier + Regressor), and benchmark serialization.
    """
    if model_output_path is None:
        model_output_path = os.path.join(project_dir, "backend", "app", "models", "bust_model.pkl")
        
    os.makedirs(os.path.dirname(model_output_path), exist_ok=True)
    processed_dir = os.path.join(ml_dir, "data", "processed")
    os.makedirs(processed_dir, exist_ok=True)
    
    # 1. Ingest/Generate historical NWP and Observation datasets
    logger.info("Step 1: Ingesting/Generating historical meteorological datasets...")
    fc_df, obs_df = generate_synthetic_meteorological_dataset(n_samples=n_samples, random_seed=42)
    
    # Save raw sample files for reference
    raw_dir = os.path.join(ml_dir, "data", "raw")
    os.makedirs(raw_dir, exist_ok=True)
    fc_df.head(1000).to_csv(os.path.join(raw_dir, "nwp_forecasts_sample.csv"), index=False)
    obs_df.head(1000).to_csv(os.path.join(raw_dir, "observations_sample.csv"), index=False)
    
    # 2. Align forecast and observation datasets
    logger.info("Step 2: Spatially and temporally aligning forecast with observations...")
    aligned_df = align_forecast_and_observations(fc_df, obs_df)
    
    # 3. Calculate historical errors & bust flags
    logger.info("Step 3: Calculating historical errors, MAE/RMSE residuals, and bust thresholds...")
    error_df = calculate_errors_and_busts(aligned_df)
    climatology = generate_historical_error_climatology(error_df)
    
    # 4. Feature Engineering
    logger.info("Step 4: Performing feature engineering (gradients, tendencies, spread, regimes)...")
    dataset = extract_features(error_df, climatology["region_lead_stats"])
    
    # Save processed training dataset
    dataset.to_parquet(os.path.join(processed_dir, "historical_nwp_features.parquet"), index=False)
    dataset.head(1000).to_csv(os.path.join(processed_dir, "historical_nwp_features_sample.csv"), index=False)
    
    X = dataset[METEOROLOGICAL_FEATURE_COLS]
    y_bust = dataset["is_forecast_bust"]
    y_rain_err = dataset["rain_error"]
    y_temp_err = dataset["temp_error"]
    
    # Train / Test split (80% train, 20% test)
    X_train, X_test, y_bust_train, y_bust_test, y_rain_train, y_rain_test, y_temp_train, y_temp_test, df_train, df_test = train_test_split(
        X, y_bust, y_rain_err, y_temp_err, dataset, test_size=0.20, random_state=42, stratify=y_bust
    )
    
    logger.info(f"Dataset split: {len(X_train)} train samples, {len(X_test)} test samples.")
    logger.info(f"Train bust rate: {y_bust_train.mean()*100:.2f}%, Test bust rate: {y_bust_test.mean()*100:.2f}%")
    
    # 5. Train Bust Classifier
    logger.info("Step 5a: Training XGBoost Bust Probability Classifier...")
    bust_classifier = XGBClassifier(
        n_estimators=250,
        max_depth=5,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        eval_metric="logloss",
        random_state=42,
        use_label_encoder=False
    )
    bust_classifier.fit(X_train, y_bust_train)
    
    # 6. Train Rain Residual Error Regressor
    logger.info("Step 5b: Training XGBoost Rain Residual Error Regressor...")
    rain_error_regressor = XGBRegressor(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42
    )
    rain_error_regressor.fit(X_train, y_rain_train)
    
    # 7. Train Temperature Residual Error Regressor
    logger.info("Step 5c: Training XGBoost Temperature Error Regressor...")
    temp_error_regressor = XGBRegressor(
        n_estimators=150,
        max_depth=4,
        learning_rate=0.06,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42
    )
    temp_error_regressor.fit(X_train, y_temp_train)
    
    # 8. Evaluation & Before vs After Error Reduction Calculations
    logger.info("Step 6: Computing test set predictions and error reduction metrics...")
    test_prob = bust_classifier.predict_proba(X_test)[:, 1]
    test_pred_bust = (test_prob >= 0.5).astype(int)
    
    pred_rain_error = rain_error_regressor.predict(X_test)
    pred_temp_error = temp_error_regressor.predict(X_test)
    
    # Raw NWP vs ML-Corrected Forecasts
    raw_rain_forecast = df_test["rain_forecast"].values
    obs_rain = df_test["rain_observed"].values
    corrected_rain_forecast = np.maximum(0.0, raw_rain_forecast - pred_rain_error)
    
    raw_temp_forecast = df_test["temp_forecast"].values
    obs_temp = df_test["temp_observed"].values
    corrected_temp_forecast = raw_temp_forecast - pred_temp_error
    
    # Error Before (Raw NWP) vs Error After (AI-Corrected)
    raw_rain_mae = mean_absolute_error(obs_rain, raw_rain_forecast)
    raw_rain_rmse = np.sqrt(mean_squared_error(obs_rain, raw_rain_forecast))
    corrected_rain_mae = mean_absolute_error(obs_rain, corrected_rain_forecast)
    corrected_rain_rmse = np.sqrt(mean_squared_error(obs_rain, corrected_rain_forecast))
    rain_mae_reduction_pct = ((raw_rain_mae - corrected_rain_mae) / raw_rain_mae) * 100.0
    rain_rmse_reduction_pct = ((raw_rain_rmse - corrected_rain_rmse) / raw_rain_rmse) * 100.0
    
    raw_temp_mae = mean_absolute_error(obs_temp, raw_temp_forecast)
    raw_temp_rmse = np.sqrt(mean_squared_error(obs_temp, raw_temp_forecast))
    corrected_temp_mae = mean_absolute_error(obs_temp, corrected_temp_forecast)
    corrected_temp_rmse = np.sqrt(mean_squared_error(obs_temp, corrected_temp_forecast))
    temp_mae_reduction_pct = ((raw_temp_mae - corrected_temp_mae) / raw_temp_mae) * 100.0
    temp_rmse_reduction_pct = ((raw_temp_rmse - corrected_temp_rmse) / raw_temp_rmse) * 100.0
    
    # Bust Detection Metrics
    auc = roc_auc_score(y_bust_test, test_prob)
    prec = precision_score(y_bust_test, test_pred_bust)
    rec = recall_score(y_bust_test, test_pred_bust)
    f1 = f1_score(y_bust_test, test_pred_bust)
    brier = brier_score_loss(y_bust_test, test_prob)
    
    # Lead-time wise error reduction breakdown (Day 1 to Day 10)
    lead_time_breakdown = []
    df_test_res = df_test.copy()
    df_test_res["pred_rain_error"] = pred_rain_error
    df_test_res["corrected_rain"] = corrected_rain_forecast
    df_test_res["bust_prob"] = test_prob
    
    for day in range(1, 11):
        day_sub = df_test_res[df_test_res["lead_time_days"] == day]
        if len(day_sub) > 0:
            day_raw_mae = mean_absolute_error(day_sub["rain_observed"], day_sub["rain_forecast"])
            day_corr_mae = mean_absolute_error(day_sub["rain_observed"], day_sub["corrected_rain"])
            day_raw_t_mae = mean_absolute_error(day_sub["temp_observed"], day_sub["temp_forecast"])
            day_corr_t_mae = mean_absolute_error(day_sub["temp_observed"], day_sub["temp_forecast"] - day_sub["pred_rain_error"]*0.1) # approx
            day_red_pct = ((day_raw_mae - day_corr_mae) / day_raw_mae) * 100.0
            
            lead_time_breakdown.append({
                "lead_time_day": int(day),
                "raw_rain_mae_mm": round(float(day_raw_mae), 2),
                "corrected_rain_mae_mm": round(float(day_corr_mae), 2),
                "rain_mae_reduction_pct": round(float(day_red_pct), 2),
                "raw_temp_mae_c": round(float(day_raw_t_mae), 2),
                "mean_bust_prob": round(float(day_sub["bust_prob"].mean()), 3),
                "mean_confidence_score": round(float((1.0 - day_sub["bust_prob"].mean()) * 100), 1)
            })
            
    # Benchmark Metrics Dictionary
    metrics_summary = {
        "bust_detection": {
            "roc_auc": round(float(auc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "brier_score": round(float(brier), 4),
            "accuracy": round(float(accuracy_score(y_bust_test, test_pred_bust)), 4)
        },
        "error_reduction": {
            "rainfall": {
                "raw_nwp_mae_mm": round(float(raw_rain_mae), 2),
                "ai_corrected_mae_mm": round(float(corrected_rain_mae), 2),
                "mae_reduction_mm": round(float(raw_rain_mae - corrected_rain_mae), 2),
                "mae_reduction_percent": round(float(rain_mae_reduction_pct), 2),
                "raw_nwp_rmse_mm": round(float(raw_rain_rmse), 2),
                "ai_corrected_rmse_mm": round(float(corrected_rain_rmse), 2),
                "rmse_reduction_percent": round(float(rain_rmse_reduction_pct), 2)
            },
            "temperature": {
                "raw_nwp_mae_c": round(float(raw_temp_mae), 2),
                "ai_corrected_mae_c": round(float(corrected_temp_mae), 2),
                "mae_reduction_c": round(float(raw_temp_mae - corrected_temp_mae), 2),
                "mae_reduction_percent": round(float(temp_mae_reduction_pct), 2),
                "raw_nwp_rmse_c": round(float(raw_temp_rmse), 2),
                "ai_corrected_rmse_c": round(float(corrected_temp_rmse), 2),
                "rmse_reduction_percent": round(float(temp_rmse_reduction_pct), 2)
            },
            "operational_bust_risk": {
                "earlier_unmitigated_bust_frequency_pct": round(float(y_bust_test.mean() * 100.0), 2),
                "residual_unflagged_bust_rate_pct": round(float((y_bust_test * (1 - test_pred_bust)).mean() * 100.0), 2),
                "unflagged_bust_reduction_percent": round(float((1.0 - (y_bust_test * (1 - test_pred_bust)).mean() / y_bust_test.mean()) * 100.0), 2)
            }
        },
        "lead_time_breakdown": lead_time_breakdown
    }
    
    # 9. Package & Save Model Bundle
    logger.info(f"Saving model bundle to: {model_output_path}")
    model_bundle = {
        "bust_classifier": bust_classifier,
        "rain_error_regressor": rain_error_regressor,
        "temp_error_regressor": temp_error_regressor,
        "feature_cols": METEOROLOGICAL_FEATURE_COLS,
        "climatology_stats": climatology["region_lead_stats"],
        "metrics_summary": metrics_summary
    }
    
    with open(model_output_path, "wb") as f:
        pickle.dump(model_bundle, f)
        
    logger.info("="*60)
    logger.info("MODEL TRAINING COMPLETE & BENCHMARKS SAVED!")
    logger.info(f"Bust Detection ROC-AUC: {auc:.4f} | Recall: {rec*100:.1f}% | Precision: {prec*100:.1f}%")
    logger.info(f"Rainfall MAE Earlier: {raw_rain_mae:.2f} mm -> After AI: {corrected_rain_mae:.2f} mm (Reduced by {rain_mae_reduction_pct:.1f}%)")
    logger.info(f"Temperature MAE Earlier: {raw_temp_mae:.2f} °C -> After AI: {corrected_temp_mae:.2f} °C (Reduced by {temp_mae_reduction_pct:.1f}%)")
    logger.info(f"Unwarned Busts Reduced from {metrics_summary['error_reduction']['operational_bust_risk']['earlier_unmitigated_bust_frequency_pct']}% to {metrics_summary['error_reduction']['operational_bust_risk']['residual_unflagged_bust_rate_pct']}% ({metrics_summary['error_reduction']['operational_bust_risk']['unflagged_bust_reduction_percent']}% reduction)")
    logger.info("="*60)
    
    return model_bundle, metrics_summary

if __name__ == "__main__":
    train_bust_system()
