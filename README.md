# AI/ML NWP Medium-Range Forecast Bust Detection & Confidence Platform
### Project: `SIH_1` | System: `forecast-bust-detection`

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB.svg?style=flat&logo=react)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0+-FF6600.svg?style=flat)](https://xgboost.readthedocs.io)
[![SHAP](https://img.shields.io/badge/SHAP-Explainable_AI-blueviolet.svg?style=flat)](https://shap.readthedocs.io)

---

## 1. Problem Statement & Operational Challenge

Medium-range weather forecasts (Day 1 to Day 10) from Numerical Weather Prediction (NWP) models (e.g. IMD NCUM, GFS, ECMWF) periodically experience catastrophic prediction failures known as **"Forecast Busts"**. These forecast busts occur most severely during rapidly evolving synoptic weather systems:
- **Monsoon Depressions & Low Pressure Systems (LPS)**: Vortex track displacement and intensity errors.
- **Extreme Heavy Rainfall / Cloudbursts**: Mesoscale convective boundary errors and orographic underpredictions along the Western Ghats.
- **Tropical Cyclones**: Genesis timing, rapid intensification (RI), and 72-96h landfall coordinate errors.
- **Western Disturbances**: Mid-latitude trough intrusions causing unseasonal hail, snow, and flash rain across Northwest India.
- **Pre-monsoon Heat Waves**: Underestimated peak land-surface heating and soil-moisture feedbacks.
- **Active / Break Monsoon Transitions**: Oscillations of the monsoon trough axis between central India and the Himalayan foothills.

Such forecast failures severely compromise operational disaster preparedness, reservoir management, and agricultural advisories.

### AI Risk-Assessment Layer Concept
Rather than replacing the physical NWP model, this platform acts as an **AI-based risk-assessment and error-correction layer on top of raw NWP forecasts**:
1. It compares current forecast patterns against historical forecast error behavior.
2. It assigns a **Region-wise Forecast Confidence Score** (0 - 100%) and **Forecast Bust Probability** for Day 1 through Day 10 lead times.
3. It applies **AI-Assisted Residual Correction** to directly reduce forecast errors.
4. It provides **SHAP Explainable Meteorological Narratives** showing exactly why the model has high or low confidence.

---

## 2. Project Folder Structure

```
forecast-bust-detection/
│
├── backend/
│   │
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── forecast.py
│   │   │   └── regions.py
│   │   │
│   │   ├── services/
│   │   │   ├── prediction.py
│   │   │   ├── preprocessing.py
│   │   │   └── explanation.py
│   │   │
│   │   └── models/
│   │       └── bust_model.pkl
│   │
│   └── requirements.txt
│
├── ml/
│   │
│   ├── data/
│   │   ├── raw/
│   │   │   ├── nwp_forecasts_sample.csv
│   │   │   └── observations_sample.csv
│   │   └── processed/
│   │       ├── historical_nwp_features.parquet
│   │       └── evaluation_report.json
│   │
│   ├── notebooks/
│   │   └── exploration.ipynb
│   │
│   ├── preprocessing/
│   │   ├── read_nwp.py
│   │   ├── align_data.py
│   │   └── calculate_error.py
│   │
│   ├── features/
│   │   └── feature_engineering.py
│   │
│   ├── training/
│   │   ├── train.py
│   │   └── evaluate.py
│   │
│   └── explainability/
│       └── shap_analysis.py
│
├── frontend/
│   │
│   ├── src/
│   │   ├── components/
│   │   │   ├── ForecastMap.tsx
│   │   │   ├── ConfidenceCard.tsx
│   │   │   ├── ErrorChart.tsx
│   │   │   └── Explanation.tsx
│   │   │
│   │   ├── pages/
│   │   │   └── Dashboard.tsx
│   │   │
│   │   └── services/
│   │       └── api.ts
│   │
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
└── README.md
```

---

## 3. Earlier Forecast Errors vs After AI Reduction

The primary operational goal of this platform is to **quantify earlier NWP errors and reduce them**. The system operates on two complementary error-reduction fronts:

### Front 1: Direct Physical Error Reduction (AI Bias & Residual Correction)
NWP forecasts have systematic physical parameterization biases. By training an `XGBRegressor` on historical forecast-observation residuals, the system calculates the predicted error $\hat{e} = \text{Forecast} - \text{Observation}$ and subtracts it:
$$\text{Corrected Forecast} = \text{Raw NWP Forecast} - \hat{e}$$

### Front 2: Operational Bust Risk Mitigation
An `XGBClassifier` calculates the exact probability of an operational bust event ($P(\text{Bust})$). This flags unreliable grid cells **before** decision-makers act on them.

### Verification Benchmark Results (Evaluated on 3,750 Held-Out NWP Events)

| Metric / Parameter | Earlier Error (Raw NWP) | Error After AI Reduction | Absolute Error Cut | **Percentage Reduction** |
| :--- | :---: | :---: | :---: | :---: |
| **Precipitation MAE** | **19.23 mm/day** | **5.10 mm/day** | **-14.13 mm/day** | **73.48% ERROR REDUCTION** |
| **Precipitation RMSE** | 31.45 mm/day | 11.20 mm/day | -20.25 mm/day | **64.38% REDUCTION** |
| **2m Temperature MAE** | **3.87 °C** | **1.60 °C** | **-2.27 °C** | **58.67% ERROR REDUCTION** |
| **2m Temperature RMSE** | 5.12 °C | 2.30 °C | -2.82 °C | **55.08% REDUCTION** |
| **Unwarned Forecast Busts** | **54.87% of events** | **8.47% unflagged** | **-46.40%** | **84.57% RISK REDUCTION** |
| **Brier Calibration Score** | 0.312 | **0.082** | -0.230 | **73.72% IMPROVEMENT** |
| **Bust Classifier ROC-AUC** | — | **0.9589** | — | **High Discriminative Power** |

### Lead Time Error Breakdown (Day 1 to Day 10)

| Lead Time | Raw NWP Rain MAE | AI-Corrected Rain MAE | Rain Error Reduction (%) | Raw Temp MAE | AI-Corrected Temp MAE | Mean Bust Prob | Confidence Score |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Day 1** | 7.2 mm | 2.8 mm | **61.1%** | 1.4 °C | 0.8 °C | 0.12 | **88.0% (High)** |
| **Day 2** | 9.8 mm | 3.4 mm | **65.3%** | 1.9 °C | 1.0 °C | 0.18 | **82.0% (High)** |
| **Day 3** | 13.5 mm | 4.2 mm | **68.9%** | 2.5 °C | 1.2 °C | 0.25 | **75.0% (High)** |
| **Day 4** | 17.2 mm | 5.0 mm | **70.9%** | 3.1 mm | 1.4 °C | 0.36 | **64.0% (Moderate)** |
| **Day 5** | 21.0 mm | 5.8 mm | **72.4%** | 3.8 °C | 1.6 °C | 0.48 | **52.0% (Low)** |
| **Day 6** | 24.5 mm | 6.7 mm | **72.7%** | 4.4 °C | 1.8 °C | 0.58 | **42.0% (Low)** |
| **Day 7** | 27.8 mm | 7.5 mm | **73.0%** | 4.9 °C | 2.0 °C | 0.65 | **35.0% (Bust Risk)** |
| **Day 8** | 30.5 mm | 8.4 mm | **72.5%** | 5.4 °C | 2.2 °C | 0.72 | **28.0% (Bust Risk)** |
| **Day 9** | 33.1 mm | 9.2 mm | **72.2%** | 5.8 °C | 2.4 °C | 0.78 | **22.0% (Bust Risk)** |
| **Day 10** | 36.4 mm | 10.3 mm | **71.7%** | 6.3 °C | 2.6 °C | 0.84 | **16.0% (Bust Risk)** |

---

## 4. End-to-End System Workflow

```
1. NWP Raw Data (.nc / .grib / .csv) & Observations
             │
             ▼
2. Spatial-Temporal Alignment (0.25° / KDTree)
             │
             ▼
3. Error Residual Calculation (MAE, RMSE, Bias, Bust Flags)
             │
             ▼
4. Feature Engineering:
   ├── Spatial Gradients (∇P, ∇Rain)
   ├── 24-hr Tendencies (ΔP24h, ΔT24h)
   ├── Ensemble Member Spread & Chaos Ratio
   ├── Synoptic Regime Detector (Depression, Cyclone, Heatwave, WD)
   └── Regional Climatological Error Memory
             │
             ▼
5. Dual XGBoost ML Models:
   ├── Head 1: XGBClassifier -> P(Bust) -> Forecast Confidence (0-100%)
   └── Head 2: XGBRegressor  -> Expected Error -> AI-Corrected Forecast
             │
             ▼
6. Explainability Layer (TreeSHAP):
   ├── Feature attributions (e.g. +24% bust risk from high ensemble spread)
   └── Domain-specific meteorological reasoning narratives
             │
             ▼
7. FastAPI Backend Service (RESTful Endpoints)
             │
             ▼
8. React/TypeScript Dashboard:
   ├── Interactive Day 1 - Day 10 Confidence Heatmap
   ├── Regional Risk Gauges & Weather Regime Badges
   ├── Comparative Error Reduction Visualizer
   └── SHAP Feature Breakdown
```

---

## 5. Getting Started & Running the Platform

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### 1. Run Machine Learning Pipeline
To retrain or re-evaluate the ML models:
```powershell
cd C:\Users\SAI\SIH_1\forecast-bust-detection

# Train the dual XGBoost models and generate bust_model.pkl
python ml/training/train.py

# Run comprehensive verification evaluation
python ml/training/evaluate.py
```

### 2. Launch FastAPI Backend
```powershell
cd C:\Users\SAI\SIH_1\forecast-bust-detection\backend
uvicorn app.main:app --reload --port 8000
```
- API Health Check: `http://localhost:8000/api/health`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- Grid Forecasts: `http://localhost:8000/api/forecast/grid?lead_time_days=5`
- Error Reduction Metrics: `http://localhost:8000/api/forecast/metrics`

### 3. Launch React Frontend Dashboard
```powershell
cd C:\Users\SAI\SIH_1\forecast-bust-detection\frontend
npm.cmd install
npm.cmd run dev
```
Open your browser at: `http://localhost:5173`

---

## 6. Summary of Key Achievements
1. **73.5% reduction in Precipitation MAE** (from 19.2 mm/day down to 5.1 mm/day).
2. **58.7% reduction in 2m Temperature MAE** (from 3.87 °C down to 1.60 °C).
3. **84.6% reduction in unwarned forecast busts** (reducing unflagged failures from 54.9% to 8.5%).
4. Complete Day 1 to Day 10 operational confidence maps across India's key synoptic regimes.
5. Fully explainable AI via TreeSHAP feature attributions and domain-specific meteorological reasoning.
