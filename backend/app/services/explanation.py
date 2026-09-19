"""
backend/app/services/explanation.py
Explainability service that integrates SHAP TreeExplainer with meteorological reasoning.
"""

import os
import sys
import logging
from typing import Dict, Any, Optional
import pandas as pd

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.abspath(os.path.join(current_dir, "..", ".."))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
ml_dir = os.path.join(root_dir, "ml")
if ml_dir not in sys.path:
    sys.path.append(ml_dir)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class ExplanationService:
    def __init__(self, model_path: Optional[str] = None):
        if model_path is None:
            model_path = os.path.join(current_dir, "..", "models", "bust_model.pkl")
            
        self.model_path = model_path
        self.explainer = None

    def _init_explainer(self):
        if self.explainer is not None:
            return
        if os.path.exists(self.model_path):
            try:
                from explainability.shap_analysis import MeteoSHAPExplainer
                logger.info("Initializing SHAP Explainer on demand...")
                self.explainer = MeteoSHAPExplainer(self.model_path)
                logger.info("SHAP Explainer initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize SHAP Explainer: {e}")
                self.explainer = None

    def explain(self, featured_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Computes SHAP waterfall/attributions and domain-specific meteorological insights.
        """
        if self.explainer is None:
            self._init_explainer()
            if self.explainer is None:
                return {
                    "base_value": 0.25,
                    "top_drivers": [],
                    "all_features": [],
                    "meteorological_narratives": ["Explainability model is initializing..."]
                }
                
        return self.explainer.explain_instance(featured_df)

# Singleton instance
explanation_service = ExplanationService()
