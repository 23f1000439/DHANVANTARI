"""
Pipeline 3: Bedside Risk Stratification
LSTM Vitals Analysis -> Triage Gate -> MedGemma Lab Review -> Gemini 3 Alert Synthesis
"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class BedsideRiskStratifier:
    def __init__(self):
        # Risk thresholds
        self.sepsis_threshold = 0.7
        self.cardiac_threshold = 0.75
        print("BedsideRiskStratifier initialized with mock LSTM/RF models.")

    # ============ LIMB 1: Triage Gate (Naive Bayes Mock) ============
    def triage_gate_nb(self, text_input: str) -> Dict[str, Any]:
        """
        Fast text-based triage classification.
        Mocked Naive Bayes: Keyword-based emergency detection.
        """
        emergency_keywords = [
            "chest pain", "difficulty breathing", "unresponsive", "cardiac arrest",
            "severe bleeding", "stroke", "seizure", "anaphylaxis", "sepsis"
        ]
        
        urgent_keywords = [
            "high fever", "vomiting blood", "severe pain", "confusion", 
            "high blood pressure", "low oxygen"
        ]
        
        text_lower = text_input.lower()
        
        if any(kw in text_lower for kw in emergency_keywords):
            return {
                "status": "EMERGENCY",
                "confidence": 0.95,
                "matched_trigger": [kw for kw in emergency_keywords if kw in text_lower],
                "recommended_action": "Immediate escalation to ICU/ER"
            }
        elif any(kw in text_lower for kw in urgent_keywords):
            return {
                "status": "URGENT",
                "confidence": 0.80,
                "matched_trigger": [kw for kw in urgent_keywords if kw in text_lower],
                "recommended_action": "Priority review by on-call physician"
            }
        else:
            return {
                "status": "ROUTINE",
                "confidence": 0.70,
                "matched_trigger": [],
                "recommended_action": "Standard care pathway"
            }

    # ============ LIMB 2: Vitals Anomaly Detection (LSTM/RF Mock) ============
    def vitals_anomaly_forest(self, vitals_stream: Dict[str, float]) -> Dict[str, Any]:
        """
        Analyzes vital signs for anomaly patterns.
        Mocked LSTM/Random Forest: Rule-based risk scoring.
        """
        # Extract vitals
        hr = vitals_stream.get('heart_rate', 75)
        bp_sys = vitals_stream.get('bp_systolic', 120)
        bp_dia = vitals_stream.get('bp_diastolic', 80)
        spo2 = vitals_stream.get('spo2', 98)
        temp = vitals_stream.get('temperature', 37.0)
        resp_rate = vitals_stream.get('respiratory_rate', 16)
        
        # Risk scoring rules (Mocked LSTM output)
        risk_score = 0.0
        risk_factors = []
        
        # Tachycardia
        if hr > 100:
            risk_score += 0.15
            risk_factors.append(f"Tachycardia (HR: {hr})")
        elif hr > 130:
            risk_score += 0.3
            risk_factors.append(f"Severe Tachycardia (HR: {hr})")
        
        # Bradycardia
        if hr < 50:
            risk_score += 0.2
            risk_factors.append(f"Bradycardia (HR: {hr})")
        
        # Hypotension
        if bp_sys < 90:
            risk_score += 0.25
            risk_factors.append(f"Hypotension (BP: {bp_sys}/{bp_dia})")
        
        # Hypertensive Crisis
        if bp_sys > 180 or bp_dia > 120:
            risk_score += 0.3
            risk_factors.append(f"Hypertensive Emergency (BP: {bp_sys}/{bp_dia})")
        
        # Hypoxia
        if spo2 < 90:
            risk_score += 0.35
            risk_factors.append(f"Severe Hypoxia (SpO2: {spo2}%)")
        elif spo2 < 94:
            risk_score += 0.15
            risk_factors.append(f"Mild Hypoxia (SpO2: {spo2}%)")
        
        # Fever (Sepsis indicator)
        if temp > 38.3:
            risk_score += 0.2
            risk_factors.append(f"Fever (Temp: {temp}°C)")
        elif temp < 36.0:
            risk_score += 0.2
            risk_factors.append(f"Hypothermia (Temp: {temp}°C)")
        
        # Tachypnea
        if resp_rate > 22:
            risk_score += 0.15
            risk_factors.append(f"Tachypnea (RR: {resp_rate})")
        
        # Normalize risk score
        risk_score = min(risk_score, 1.0)
        
        # Determine alert level
        if risk_score >= 0.7:
            alert_level = "CRITICAL"
        elif risk_score >= 0.4:
            alert_level = "WARNING"
        else:
            alert_level = "STABLE"
        
        return {
            "risk_score": round(risk_score, 2),
            "alert_level": alert_level,
            "risk_factors": risk_factors,
            "model": "LSTM-RF Ensemble (Mocked)",
            "timestamp": datetime.now().isoformat()
        }

    # ============ SPECIALIST: MedGemma Lab Analysis ============
    def analyze_lab_pdf(self, lab_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        MedGemma analyzes lab results for clinical context.
        Mocked: Checks for key markers (Lactate, WBC, Bandemia).
        """
        # Extract lab values
        lactate = lab_data.get('lactate', 1.0)
        wbc = lab_data.get('wbc', 8.0)
        bands = lab_data.get('bands_percent', 5)
        creatinine = lab_data.get('creatinine', 1.0)
        
        findings = []
        severity = "NORMAL"
        
        # Lactate (Sepsis marker)
        if lactate > 4.0:
            findings.append(f"Elevated Lactate ({lactate} mmol/L) - Sepsis/Shock indicator")
            severity = "CRITICAL"
        elif lactate > 2.0:
            findings.append(f"Mildly elevated Lactate ({lactate} mmol/L)")
            severity = "WARNING"
        
        # WBC
        if wbc > 12.0:
            findings.append(f"Leukocytosis (WBC: {wbc}k) - Infection likely")
        elif wbc < 4.0:
            findings.append(f"Leukopenia (WBC: {wbc}k) - Immunocompromised")
        
        # Bandemia (Immature WBCs)
        if bands > 10:
            findings.append(f"Bandemia ({bands}%) - Left shift, acute infection")
            severity = "CRITICAL" if severity != "CRITICAL" else severity
        
        # Creatinine (Kidney function)
        if creatinine > 2.0:
            findings.append(f"Elevated Creatinine ({creatinine} mg/dL) - AKI risk")
        
        return {
            "findings": findings,
            "severity": severity,
            "sepsis_markers": lactate > 2.0 or bands > 10,
            "analyzer": "MedGemma (Mocked)"
        }

    # ============ BRAIN: Gemini 3 Alert Synthesis ============
    def synthesize_alert(self, vitals_result: Dict, lab_result: Dict, ai_service, thinking_level: str = "LOW") -> Dict:
        """
        Gemini 3 synthesizes the final alert with dynamic thinking level.
        """
        prompt = f"""
        ROLE: ICU Clinical Decision Support System.
        THINKING_LEVEL: {thinking_level}
        
        VITALS ANALYSIS (LSTM Model):
        - Risk Score: {vitals_result['risk_score']}
        - Alert Level: {vitals_result['alert_level']}
        - Factors: {vitals_result['risk_factors']}
        
        LAB ANALYSIS (MedGemma):
        - Severity: {lab_result['severity']}
        - Sepsis Markers: {lab_result['sepsis_markers']}
        - Findings: {lab_result['findings']}
        
        TASK:
        1. Synthesize a clinical alert for the nursing/ICU staff.
        2. Provide an immediate action plan (numbered steps).
        3. Assign an Evidence Grade.
        
        OUTPUT FORMAT (JSON):
        {{
          "emergency_status": "Critical/Urgent/Stable",
          "clinical_summary": "Brief synthesis of findings",
          "action_plan": ["Step 1", "Step 2", "Step 3"],
          "evidence_grade": "Level 1-5",
          "escalation_required": boolean
        }}
        """
        
        try:
            # Adjust temperature based on thinking level
            temp = 0.1 if thinking_level == "HIGH" else 0.3
            
            response = ai_service.pro_model.generate_content(
                prompt,
                generation_config=ai_service.analytical_config
            )
            try:
                return json.loads(response.text)
            except:
                return self._generate_fallback_alert(vitals_result, lab_result)
        except Exception as e:
            print(f"Alert Synthesis Error: {e}")
            return self._generate_fallback_alert(vitals_result, lab_result)

    def _generate_fallback_alert(self, vitals: Dict, labs: Dict) -> Dict:
        """Fallback alert generator."""
        is_critical = vitals['alert_level'] == 'CRITICAL' or labs['severity'] == 'CRITICAL'
        
        return {
            "emergency_status": "Critical" if is_critical else "Stable",
            "clinical_summary": f"Risk Score: {vitals['risk_score']}. Factors: {', '.join(vitals['risk_factors'][:2])}. Labs: {labs['severity']}.",
            "action_plan": [
                "Notify attending physician",
                "Prepare for IV access",
                "Order stat labs if not done"
            ] if is_critical else ["Continue monitoring"],
            "evidence_grade": "Level 3",
            "escalation_required": is_critical
        }

    # ============ ORCHESTRATED PIPELINE ============
    def run_pipeline(self, vitals: Dict, lab_data: Dict, chief_complaint: str, ai_service) -> Dict:
        """Full risk stratification pipeline execution."""
        print("[RISK] Starting Bedside Risk Stratification Pipeline...")
        
        # Step 1: Limb - Text Triage
        print("[RISK] Step 1: Triage Gate (NB)...")
        triage = self.triage_gate_nb(chief_complaint)
        
        # Determine thinking level
        thinking_level = "HIGH" if triage['status'] == 'EMERGENCY' else "LOW"
        print(f"[RISK] Thinking Level set to: {thinking_level}")
        
        # Step 2: Limb - Vitals Analysis
        print("[RISK] Step 2: Vitals Anomaly Detection (LSTM)...")
        vitals_result = self.vitals_anomaly_forest(vitals)
        
        # Step 3: Specialist - Lab Analysis
        print("[RISK] Step 3: MedGemma Lab Analysis...")
        lab_result = self.analyze_lab_pdf(lab_data)
        
        # Step 4: Brain - Alert Synthesis
        print("[RISK] Step 4: Gemini 3 Alert Synthesis...")
        alert = self.synthesize_alert(vitals_result, lab_result, ai_service, thinking_level)
        
        return {
            "triage": triage,
            "vitals_analysis": vitals_result,
            "lab_analysis": lab_result,
            "final_alert": alert,
            "thinking_level_used": thinking_level
        }

if __name__ == "__main__":
    stratifier = BedsideRiskStratifier()
    
    # Test critical case
    vitals = {"heart_rate": 120, "bp_systolic": 85, "spo2": 88, "temperature": 39.0, "respiratory_rate": 28}
    labs = {"lactate": 4.5, "wbc": 15.0, "bands_percent": 12, "creatinine": 2.5}
    
    print(stratifier.vitals_anomaly_forest(vitals))
    print(stratifier.analyze_lab_pdf(labs))
