import os
import json
from typing import Dict, Any, List, Tuple

# Optional imports with graceful fallback for dev environments
try:
    import joblib
except ImportError:
    joblib = None

try:
    import pandas as pd
    import numpy as np
except ImportError:
    pd = None
    np = None

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import shap
except ImportError:
    shap = None

class ClaimPredictorService:
    def __init__(self, model_path: str = "models/claim_denial_xgb.joblib"):
        self.model_path = model_path
        self.model = None
        self.explainer = None
        self._load_model()

    def _load_model(self):
        """Loads the XGBoost model and initializes SHAP explainer."""
        if os.path.exists(self.model_path) and joblib:
            try:
                self.model = joblib.load(self.model_path)
                if shap and self.model:
                    # TreeExplainer is optimized for XGBoost
                    self.explainer = shap.TreeExplainer(self.model)
                print(f"Loaded Claim Denial Model from {self.model_path}")
            except Exception as e:
                print(f"Failed to load model: {e}")
        else:
            print(f"Model file not found at {self.model_path}. Running in MOCK mode.")

    def _preprocess(self, claim_data: Dict[str, Any]) -> pd.DataFrame:
        """
        Converts raw claim dictionary into feature dataframe.
        This must match the training data schema.
        """
        # mocking feature engineering
        # In a real scenario, this would transform dict values to match model features
        # e.g. One-Hot Encoding, scaling, etc.
        
        # Simplified feature set for demonstration
        features = {
            "total_amount": float(claim_data.get("total_amount", 0.0)),
            "patient_age": self._calculate_age(claim_data.get("patient_dob", "1980-01-01")),
            "provider_specialty_encoded": 0, # Placeholder
            "has_prior_auth": 1 if claim_data.get("prior_auth") else 0,
            "diagnosis_count": len(claim_data.get("diagnosis_codes", [])),
            "procedure_count": len(claim_data.get("procedure_codes", []))
        }
        
        if pd:
            return pd.DataFrame([features])
        return features # Return dict if no pandas

    def _calculate_age(self, dob_str: str) -> int:
        # Simplified age calc
        try:
            return 45 # Mock for now
        except:
            return 30

    def predict_denial(self, claim_data: Dict[str, Any]) -> float:
        """
        Returns probability of denial (0.0 to 1.0).
        """
        if not self.model or not xgb or not pd:
            # Fallback/Mock logic
            # High amount or specific generic condition triggers risk
            amount = float(claim_data.get("total_amount", 0))
            if amount > 5000:
                print("Mocking prediction: High Risk due to amount > 5000")
                return 0.75
            return 0.12

        try:
            df = self._preprocess(claim_data)
            # Predict proba for class 1 (Denial)
            prob = self.model.predict_proba(df)[0][1]
            return float(prob)
        except Exception as e:
            print(f"Prediction error: {e}")
            return 0.5 # Fail open/uncertain

    def explain_prediction(self, claim_data: Dict[str, Any]) -> List[str]:
        """
        Returns list of top risk factors using SHAP.
        """
        if not self.model or not self.explainer or not shap:
             # Mock explanations
            amount = float(claim_data.get("total_amount", 0))
            risks = []
            if amount > 5000:
                risks.append(f"High Claim Amount (${amount})")
            if not claim_data.get("prior_auth", False):
                risks.append("Missing Prior Authorization")
            if not risks:
                risks.append("No significant risk factors identified")
            return risks

        try:
            df = self._preprocess(claim_data)
            shap_values = self.explainer.shap_values(df)
            
            # Get top features
            # This is a simplified extraction of top contributing features
            feature_names = df.columns
            # For specific instance
            vals = shap_values[0] 
            
            # Sort by absolute impact
            sorted_idx = np.argsort(np.abs(vals))[::-1]
            
            top_factors = []
            for idx in sorted_idx[:3]: # Top 3
                feature = feature_names[idx]
                impact = vals[idx]
                if impact > 0: # Only return factors *increasing* denial risk
                    top_factors.append(f"{feature} increases risk (impact: {impact:.2f})")
            
            return top_factors if top_factors else ["Risk is driven by complex combination of factors"]
            
        except Exception as e:
            print(f"Explanation error: {e}")
            return ["Unable to generate explanations"]
