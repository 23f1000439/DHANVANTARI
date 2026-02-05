from ....infrastructure.ai.gemini import GeminiAgent
from ...services.claim_predictor import ClaimPredictorService
from ...services.icd11_coder import AutonomousICD11Coder
# Assuming root directory is in PYTHONPATH for this import
try:
    import ai_service
except ImportError:
    # Fallback for relative import if ai_service was moved or package structure differs
    import sys
    import os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../..")))
    import ai_service

from ai_service import AIService
import json

class BillingAgent(GeminiAgent):
    def __init__(self):
        super().__init__("BillingAgent")
        self.predictor = ClaimPredictorService()
        self.ai_service = AIService()
        self.coder = AutonomousICD11Coder()

    def generate_coding_recommendations(self, clinical_note, context=None):
        """
        Generates ICD-11 codes with reasoning.
        """
        if context is None:
            context = {}
        return self.coder.generate_codes(clinical_note, context)

    def generate_response(self, prompt, conversation_id, context=None):
        """
        Orchestrates the Claim Denial Prediction workflow.
        Expected 'prompt' to be a JSON string or dict containing claim data.
        """
        
        # 1. Parse Input
        try:
            if isinstance(prompt, str):
                try:
                    claim_data = json.loads(prompt)
                except:
                    return super().generate_response(prompt, conversation_id, context)
            else:
                claim_data = prompt
        except Exception:
             return super().generate_response(prompt, conversation_id, context)

        # CHECK INTENT: If prompt asks for "coding" or "codes", route to coder
        # This is a simple keyword check; ideally an Intent Classifier would sit before this.
        if isinstance(claim_data, dict) and claim_data.get("action") == "generate_codes":
             return json.dumps(self.generate_coding_recommendations(
                 context.get('clinical_notes', ""), context
             ), indent=2)

        # 2. ML Prediction (XGBoost)
        denial_prob = self.predictor.predict_denial(claim_data)
        risk_factors = self.predictor.explain_prediction(claim_data)
        
        ml_results = {
            "probability": denial_prob,
            "risk_factors": risk_factors
        }

        # 3. Decision Threshold
        # If Risk is Low (< 15%), just return approval/low risk msg
        if denial_prob < 0.15:
            return json.dumps({
                "status": "Low Risk",
                "denial_probability": denial_prob,
                "message": "Claim appears clean based on ML model.",
                "risk_factors": []
            })
        
        # 4. Clinical Reasoning (Gemini 3.0)
        clinical_notes = context.get('clinical_notes', "No clinical notes provided.")
        
        enhanced_analysis = self.ai_service.get_enhanced_denial_analysis(
            claim_data, 
            ml_results, 
            clinical_notes
        )
        
        # 5. Final Synthesis
        final_response = {
            "status": "High Risk" if denial_prob > 0.5 else "Medium Risk",
            "denial_probability": denial_prob,
            "ml_risk_factors": risk_factors,
            "clinical_analysis": enhanced_analysis,
            "actionable_next_steps": enhanced_analysis.get('remediation_steps', [])
        }
        
        return json.dumps(final_response, indent=2)
