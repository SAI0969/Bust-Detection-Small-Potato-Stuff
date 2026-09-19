"""
backend/app/main.py
Main FastAPI application entrypoint for AI/ML Forecast Bust Detection & Confidence System.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any

from .api.forecast import router as forecast_router
from .api.regions import router as regions_router
from .services.prediction import prediction_service

app = FastAPI(
    title="AI/ML NWP Forecast Bust Detection & Confidence Platform",
    description="Operational risk-assessment layer providing Day 1 - Day 10 forecast confidence maps, bust probability, expected error magnitude, AI bias correction, and SHAP explainability.",
    version="1.0.0"
)

# CORS configuration for Frontend dev and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(forecast_router)
app.include_router(regions_router)

@app.get("/")
def root_status() -> Dict[str, Any]:
    return {
        "status": "online",
        "service": "AI/ML Forecast Bust Detection & Confidence System",
        "model_loaded": prediction_service.is_ready(),
        "documentation": "/docs",
        "supported_lead_times": "Day 1 to Day 10"
    }

@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "model_loaded": prediction_service.is_ready(),
        "endpoints": [
            "/api/forecast/grid",
            "/api/forecast/region-summary",
            "/api/forecast/custom-predict",
            "/api/forecast/metrics",
            "/api/forecast/explain/{region_id}",
            "/api/regions"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
