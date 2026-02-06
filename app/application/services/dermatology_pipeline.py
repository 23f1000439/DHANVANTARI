"""
Pipeline: Dermatology (Skin Lesion Analysis)
CNN + NB Triage -> MedGemma VLM -> K-Means Clustering -> Gemini Synthesis
"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class DermatologyPipeline:
    """
    End-to-End Dermatology Pipeline for skin lesion analysis.
    Stages:
    1. CNN: Image quality check and enhancement
    2. NB: Text triage for priority
    3. MedGemma: Lesion analysis (VLM)
    4. K-Means: Risk cohort clustering
    5. Gemini: Referral synthesis + patient explanation
    """
    
    def __init__(self):
        # Risk cohort definitions
        self.risk_cohorts = {
            0: {"name": "Low Risk", "followup": "6 months", "action": "Self-monitoring"},
            1: {"name": "Moderate Risk", "followup": "3 months", "action": "Dermatology review"},
            2: {"name": "High Risk", "followup": "Immediate", "action": "Urgent biopsy referral"}
        }
        
        # Lesion feature keywords for mock analysis
        self.malignant_features = [
            "asymmetry", "irregular border", "color variation", "diameter >6mm",
            "evolving", "ulceration", "bleeding", "rapid growth", "dark pigmentation"
        ]
        
        print("DermatologyPipeline initialized.")

    # ============ LIMB 1: CNN Image Processor (Mocked) ============
    def cnn_image_processor(self, image_data: Any) -> Dict[str, Any]:
        """
        CNN-based image quality check and enhancement.
        Mocked: Returns quality metrics based on image presence.
        """
        if image_data is None:
            return {
                "status": "rejected",
                "reason": "No image provided",
                "quality_score": 0.0,
                "enhanced": False
            }
        
        # Simulate quality check (In production: OpenCV/TensorFlow)
        quality_score = 0.85  # Mock score
        
        return {
            "status": "accepted",
            "quality_score": quality_score,
            "enhanced": True,
            "preprocessing": ["cropped", "color_normalized", "contrast_enhanced"],
            "resolution": "1024x1024",
            "processor": "CNN ResNet-50 (Mocked)"
        }

    # ============ LIMB 2: Text Triage (Naive Bayes) ============
    def triage_text_nb(self, description: str) -> Dict[str, Any]:
        """
        Text-based triage using Naive Bayes classification.
        Mocked: Keyword-based priority assignment.
        """
        high_priority_keywords = [
            "severe pain", "bleeding", "rapid growth", "changing color",
            "new spot", "irregular", "getting bigger", "itching", "ulcer"
        ]
        
        moderate_keywords = [
            "slight change", "mild discomfort", "small bump", "dry patch"
        ]
        
        text_lower = description.lower()
        
        # Check for high priority
        if any(kw in text_lower for kw in high_priority_keywords):
            priority = "HIGH"
            confidence = 0.92
            matched = [kw for kw in high_priority_keywords if kw in text_lower]
        elif any(kw in text_lower for kw in moderate_keywords):
            priority = "MODERATE"
            confidence = 0.78
            matched = [kw for kw in moderate_keywords if kw in text_lower]
        else:
            priority = "LOW"
            confidence = 0.65
            matched = []
        
        return {
            "priority": priority,
            "confidence": confidence,
            "matched_triggers": matched,
            "classifier": "Naive Bayes (Mocked)"
        }

    # ============ SPECIALIST: MedGemma Lesion Analysis ============
    def analyze_lesion_medgemma(self, image_data: Any, description: str) -> Dict[str, Any]:
        """
        MedGemma VLM analyzes the skin lesion.
        Mocked: Feature extraction based on description keywords.
        """
        desc_lower = description.lower()
        
        # Extract features from description
        detected_features = []
        for feature in self.malignant_features:
            if feature in desc_lower:
                detected_features.append(feature)
        
        # Determine lesion classification
        malignancy_score = len(detected_features) / len(self.malignant_features)
        
        if malignancy_score >= 0.4:
            classification = "Suspicious for Malignancy"
            differential = ["Basal Cell Carcinoma", "Melanoma", "Squamous Cell Carcinoma"]
            recommendation = "Urgent dermatology referral and biopsy recommended"
        elif malignancy_score >= 0.2:
            classification = "Atypical Lesion"
            differential = ["Dysplastic Nevus", "Seborrheic Keratosis", "Actinic Keratosis"]
            recommendation = "Dermatology evaluation within 2 weeks"
        else:
            classification = "Likely Benign"
            differential = ["Common Nevus", "Dermatofibroma", "Cherry Angioma"]
            recommendation = "Monitor for changes; routine follow-up"
        
        return {
            "classification": classification,
            "malignancy_score": round(malignancy_score, 2),
            "detected_features": detected_features,
            "differential_diagnosis": differential,
            "recommendation": recommendation,
            "analyzer": "MedGemma 4B VLM (Mocked)"
        }

    # ============ LIMB 4: K-Means Risk Clustering ============
    def cluster_patient_kmeans(self, patient_data: Dict) -> Dict[str, Any]:
        """
        K-Means clustering for risk cohort assignment.
        Mocked: Rule-based clustering using demographic + clinical features.
        """
        age = patient_data.get("age", 40)
        skin_type = patient_data.get("skin_type", "II")  # Fitzpatrick scale
        sun_exposure = patient_data.get("sun_exposure", "moderate")
        family_history = patient_data.get("family_history_cancer", False)
        previous_lesions = patient_data.get("previous_lesions", 0)
        
        # Calculate risk factors
        risk_score = 0
        
        if age > 50:
            risk_score += 1
        if skin_type in ["I", "II"]:
            risk_score += 1
        if sun_exposure == "high":
            risk_score += 1
        if family_history:
            risk_score += 2
        if previous_lesions > 2:
            risk_score += 1
        
        # Assign cohort
        if risk_score >= 4:
            cohort_id = 2
        elif risk_score >= 2:
            cohort_id = 1
        else:
            cohort_id = 0
        
        cohort = self.risk_cohorts[cohort_id]
        
        return {
            "cohort_id": cohort_id,
            "cohort_name": cohort["name"],
            "risk_score": risk_score,
            "recommended_followup": cohort["followup"],
            "action": cohort["action"],
            "clusterer": "K-Means (Mocked)"
        }

    # ============ BRAIN: Gemini Synthesis ============
    def synthesize_referral(self, triage: Dict, analysis: Dict, clustering: Dict, ai_service) -> Dict[str, Any]:
        """
        Gemini 3 synthesizes the referral note and patient explanation.
        """
        prompt = f"""
        ROLE: Dermatology Clinical Decision Support.
        
        TRIAGE PRIORITY: {triage['priority']}
        
        LESION ANALYSIS (MedGemma):
        - Classification: {analysis['classification']}
        - Malignancy Score: {analysis['malignancy_score']}
        - Features: {analysis['detected_features']}
        - Differential: {analysis['differential_diagnosis']}
        
        RISK COHORT (K-Means):
        - Cohort: {clustering['cohort_name']}
        - Risk Score: {clustering['risk_score']}
        - Recommended Follow-up: {clustering['recommended_followup']}
        
        TASK:
        1. Generate a professional referral note for a dermatologist.
        2. Generate a plain-language explanation for the patient.
        3. List next steps.
        
        OUTPUT FORMAT (JSON):
        {{
          "referral_note": "Formal clinical referral text",
          "patient_explanation": "Simple, reassuring explanation for the patient",
          "next_steps": ["Step 1", "Step 2"],
          "urgency": "Immediate/Urgent/Routine"
        }}
        """
        
        try:
            response = ai_service.pro_model.generate_content(
                prompt,
                generation_config=ai_service.analytical_config
            )
            try:
                return json.loads(response.text)
            except:
                return self._generate_fallback_referral(triage, analysis, clustering)
        except Exception as e:
            print(f"Synthesis Error: {e}")
            return self._generate_fallback_referral(triage, analysis, clustering)

    def _generate_fallback_referral(self, triage: Dict, analysis: Dict, clustering: Dict) -> Dict:
        """Fallback referral generator."""
        urgency = "Immediate" if triage['priority'] == 'HIGH' else "Routine"
        
        return {
            "referral_note": f"Referral for dermatology evaluation. Classification: {analysis['classification']}. Differential includes {', '.join(analysis['differential_diagnosis'][:2])}. Risk cohort: {clustering['cohort_name']}.",
            "patient_explanation": f"We recommend you see a skin specialist to examine this area more closely. This is a precautionary measure based on the features we observed. Please follow up as recommended.",
            "next_steps": [
                f"Schedule dermatology appointment within {clustering['recommended_followup']}",
                "Avoid sun exposure to the affected area",
                "Take photos to monitor any changes"
            ],
            "urgency": urgency
        }

    # ============ GOVERNANCE: Audit Trail ============
    def log_audit_trail(self, patient_id: str, result: Dict) -> Dict:
        """Log the entire decision process for compliance."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "patient_id": patient_id,
            "pipeline": "DERMATOLOGY",
            "decision_path": {
                "triage_priority": result.get("triage", {}).get("priority"),
                "lesion_classification": result.get("analysis", {}).get("classification"),
                "risk_cohort": result.get("clustering", {}).get("cohort_name"),
                "final_urgency": result.get("synthesis", {}).get("urgency")
            },
            "compliance": "HIPAA_LOGGED"
        }
        print(f"[AUDIT] Dermatology decision logged: {audit_entry['decision_path']}")
        return audit_entry

    # ============ ORCHESTRATED PIPELINE ============
    def run_pipeline(self, patient_id: str, image_data: Any, description: str, 
                     patient_demographics: Dict, ai_service) -> Dict[str, Any]:
        """Full dermatology pipeline execution."""
        print("\n[DERM] Starting Dermatology Analysis Pipeline...")
        
        result = {
            "patient_id": patient_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Step 1: CNN Image Processing
        print("[DERM] Step 1: CNN Image Quality Check...")
        image_result = self.cnn_image_processor(image_data)
        result["image_processing"] = image_result
        
        if image_result["status"] == "rejected":
            result["error"] = "Image quality insufficient"
            return result
        
        # Step 2: NB Text Triage
        print("[DERM] Step 2: Naive Bayes Text Triage...")
        triage = self.triage_text_nb(description)
        result["triage"] = triage
        
        # Step 3: MedGemma Analysis
        print("[DERM] Step 3: MedGemma Lesion Analysis...")
        analysis = self.analyze_lesion_medgemma(image_data, description)
        result["analysis"] = analysis
        
        # Step 4: K-Means Clustering
        print("[DERM] Step 4: K-Means Risk Clustering...")
        clustering = self.cluster_patient_kmeans(patient_demographics)
        result["clustering"] = clustering
        
        # Step 5: Gemini Synthesis
        print("[DERM] Step 5: Gemini Synthesis (Referral + Explanation)...")
        synthesis = self.synthesize_referral(triage, analysis, clustering, ai_service)
        result["synthesis"] = synthesis
        
        # Governance
        self.log_audit_trail(patient_id, result)
        
        return result


if __name__ == "__main__":
    pipeline = DermatologyPipeline()
    
    # Test triage
    print(pipeline.triage_text_nb("I have a mole that is getting bigger and bleeding"))
    
    # Test lesion analysis
    print(pipeline.analyze_lesion_medgemma(None, "asymmetric dark spot with irregular border"))
