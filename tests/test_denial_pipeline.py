import unittest
import sqlite3
import json
import sys
import os

# Append root to sys.path to resolve imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.application.services.claim_predictor import ClaimPredictorService
from ai_service import AIService 
# Mocking BillingAgent logic locally or importing if manageable, 
# for end-to-end we might simulate the agent's logic on top of the components

class TestClaimDenialPredictor(unittest.TestCase):
    def setUp(self):
        # Initialize Services
        self.predictor = ClaimPredictorService(model_path="models/denial_v1.joblib")
        # Ensure fallback handled in service if model missing
        
        self.ai_service = AIService()
        self.db_path = "healthcare.db"
        self.db = sqlite3.connect(self.db_path)

    def test_01_ml_prediction_range(self):
        """Test if XGBoost returns a valid probability."""
        print("\n--- Test 01: ML Prediction Range ---")
        mock_claim = {
            "total_amount": 5000, 
            "diagnosis_codes": ["E11.9"], 
            "provider_specialty": "Cardiology"
        }
        prob = self.predictor.predict_denial(mock_claim)
        print(f"Predicted Probability: {prob}")
        self.assertGreaterEqual(prob, 0.0)
        self.assertLessEqual(prob, 1.0)

    def test_02_shap_feature_extraction(self):
        """Ensure SHAP provides explainable risk factors."""
        print("\n--- Test 02: SHAP Feature Extraction ---")
        # Using the same mock claim
        mock_claim = {
            "total_amount": 7500, # High amount to trigger potential risks
            "prior_auth": False
        }
        risk_factors = self.predictor.explain_prediction(mock_claim)
        print(f"Risk Factors: {risk_factors}")
        self.assertTrue(len(risk_factors) > 0, "SHAP must return at least one risk factor.")

    def test_03_gemini_synthesis_schema(self):
        """Verify Gemini 3.0 Thinking generates valid remediation JSON."""
        print("\n--- Test 03: Gemini Synthesis Schema ---")
        ml_results = {
            "probability": 0.75, 
            "risk_factors": ["High Claim Amount", "Missing Prior Authorization"]
        }
        claim_data = {
             "total_amount": 7500,
             "codes": ["ICD-11-X"]
        }
        notes = "Patient has diabetes but billed for hypertension checkup."
        
        # Calling your Gemini 3 integration
        analysis = self.ai_service.get_enhanced_denial_analysis(claim_data, ml_results, notes)
        
        print(f"Gemini Analysis: {json.dumps(analysis, indent=2)}")
        
        # Validation
        self.assertIn("remediation_steps", analysis)
        self.assertIn("reasoning_summary", analysis)
        self.assertIn("clinical_validation", analysis)
        
        # If API key is missing, our mock fallback returns specific structure, check for that too
        if "clinical_validation" in analysis and "Error" in analysis["clinical_validation"] and "API_KEY" in analysis["reasoning_summary"]:
             print("⚠️  Gemini API Key missing, validating fallback error structure.")
             self.assertIn("Manual Review Required", analysis["remediation_steps"])

    def test_04_end_to_end_db_write(self):
        """Verify that we can write analysis results to the DB (Simulation)."""
        print("\n--- Test 04: DB Write Simulation ---")
        claim_id = 'claim_gap_001' # From mock generator
        
        cursor = self.db.cursor()
        
        # verify claim exists
        cursor.execute("SELECT id, ai_analysis FROM claims WHERE id = ?", (claim_id,))
        row = cursor.fetchone()
        
        if not row:
            self.fail(f"Mock claim {claim_id} not found. Run mock_generator.py first.")
            
        before = row[1]
        print(f"Before Analysis: {before}")
        
        # Trigger Pipeline Logic (Simulating BillingAgent Work)
        # 1. Fetch info
        cursor.execute("""
            SELECT c.total_amount, e.clinical_notes 
            FROM claims c JOIN encounters e ON c.encounter_id = e.id 
            WHERE c.id = ?
        """, (claim_id,))
        claim_info = cursor.fetchone()
        
        if claim_info:
            amount, notes = claim_info
            
            # 2. Predict
            claim_data = {"total_amount": amount}
            prob = self.predictor.predict_denial(claim_data)
            risks = self.predictor.explain_prediction(claim_data)
            
            # 3. Analyze
            ml_results = {"probability": prob, "risk_factors": risks}
            analysis_json = self.ai_service.get_enhanced_denial_analysis(
                claim_data, ml_results, notes
            )
            
            # 4. Write
            # Serialize for DB
            analysis_str = json.dumps(analysis_json)
            cursor.execute("UPDATE claims SET ai_analysis = ? WHERE id = ?", (analysis_str, claim_id))
            self.db.commit()
            
            # 5. Verify
            cursor.execute("SELECT ai_analysis FROM claims WHERE id = ?", (claim_id,))
            after = cursor.fetchone()[0]
            print(f"After Analysis: {after}")
            
            self.assertNotEqual(before, after, "The database was not updated with AI analysis.")
            self.assertTrue(len(after) > 10, "Analysis string seems too short.")

    def tearDown(self):
        self.db.close()

if __name__ == '__main__':
    unittest.main()
