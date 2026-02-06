"""
Pipeline: Chronic Disease & Remote Patient Monitoring (RPM)
LSTM Wearables -> K-Means Risk Personas -> MedGemma Labs -> Gemini Health Nudges
"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import random

class ChronicDiseasePipeline:
    """
    Remote Patient Monitoring Pipeline for chronic disease management.
    Stages:
    1. LSTM: Time-series anomaly detection from wearables
    2. K-Means: Risk persona clustering
    3. MedGemma: Lab report analysis
    4. Gemini: Multilingual health nudges + teleconsult scheduling
    """
    
    def __init__(self):
        # Risk persona definitions
        self.risk_personas = {
            0: {"name": "Stable Maintainer", "intensity": "low", "check_frequency": "monthly"},
            1: {"name": "Moderate Risk", "intensity": "medium", "check_frequency": "weekly"},
            2: {"name": "High Alert", "intensity": "high", "check_frequency": "daily"}
        }
        
        # Normal ranges for vitals
        self.normal_ranges = {
            "heart_rate": (60, 100),
            "glucose": (70, 140),  # mg/dL
            "blood_pressure_systolic": (90, 140),
            "blood_pressure_diastolic": (60, 90),
            "spo2": (95, 100),
            "steps": (5000, 15000)
        }
        
        print("ChronicDiseasePipeline initialized with RPM capabilities.")

    # ============ LIMB 1: LSTM Wearable Monitor (Mocked) ============
    def lstm_wearable_monitor(self, wearable_data: List[Dict], window_days: int = 3) -> Dict[str, Any]:
        """
        LSTM-based time-series anomaly detection.
        Mocked: Trend analysis and threshold-based detection.
        
        wearable_data: List of daily readings [{date, heart_rate, glucose, steps, ...}]
        """
        if not wearable_data or len(wearable_data) < window_days:
            return {
                "status": "insufficient_data",
                "anomalies": [],
                "trend_analysis": None
            }
        
        # Analyze last N days
        recent_data = wearable_data[-window_days:]
        anomalies = []
        trends = {}
        
        # Check heart rate trend
        hr_values = [d.get("heart_rate", 75) for d in recent_data]
        hr_trend = hr_values[-1] - hr_values[0]
        
        if hr_trend > 10:
            anomalies.append({
                "type": "RISING_HEART_RATE",
                "severity": "WARNING",
                "details": f"Heart rate increased by {hr_trend} bpm over {window_days} days",
                "values": hr_values
            })
            trends["heart_rate"] = "increasing"
        elif hr_trend < -10:
            trends["heart_rate"] = "decreasing"
        else:
            trends["heart_rate"] = "stable"
        
        # Check glucose trend (for diabetics)
        glucose_values = [d.get("glucose", 100) for d in recent_data if d.get("glucose")]
        if glucose_values:
            avg_glucose = sum(glucose_values) / len(glucose_values)
            if avg_glucose > 180:
                anomalies.append({
                    "type": "HYPERGLYCEMIA_TREND",
                    "severity": "CRITICAL",
                    "details": f"Average glucose {avg_glucose:.0f} mg/dL over {window_days} days",
                    "values": glucose_values
                })
            trends["glucose"] = "elevated" if avg_glucose > 140 else "normal"
        
        # Check SpO2
        spo2_values = [d.get("spo2", 98) for d in recent_data if d.get("spo2")]
        if spo2_values:
            min_spo2 = min(spo2_values)
            if min_spo2 < 92:
                anomalies.append({
                    "type": "HYPOXIA_DETECTED",
                    "severity": "CRITICAL",
                    "details": f"SpO2 dropped to {min_spo2}%",
                    "values": spo2_values
                })
        
        # Check activity (steps) trend
        steps_values = [d.get("steps", 5000) for d in recent_data if d.get("steps")]
        if steps_values:
            avg_steps = sum(steps_values) / len(steps_values)
            if avg_steps < 2000:
                anomalies.append({
                    "type": "REDUCED_ACTIVITY",
                    "severity": "WARNING",
                    "details": f"Average steps {avg_steps:.0f}/day - significantly below normal"
                })
        
        # Determine overall status
        if any(a["severity"] == "CRITICAL" for a in anomalies):
            overall_status = "ALERT_CRITICAL"
        elif anomalies:
            overall_status = "ALERT_WARNING"
        else:
            overall_status = "NORMAL"
        
        return {
            "status": overall_status,
            "anomalies": anomalies,
            "trend_analysis": trends,
            "window_days": window_days,
            "data_points_analyzed": len(recent_data),
            "model": "LSTM Time-Series (Mocked)"
        }

    # ============ LIMB 2: K-Means Risk Persona (Mocked) ============
    def kmeans_risk_persona(self, patient_profile: Dict) -> Dict[str, Any]:
        """
        K-Means clustering into risk personas.
        Mocked: Rule-based persona assignment.
        """
        # Extract features
        age = patient_profile.get("age", 50)
        duration_years = patient_profile.get("disease_duration_years", 5)
        hba1c = patient_profile.get("hba1c", 6.5)
        comorbidities = patient_profile.get("comorbidities", [])
        medication_adherence = patient_profile.get("medication_adherence", 0.9)
        recent_hospitalizations = patient_profile.get("recent_hospitalizations", 0)
        
        # Calculate risk score
        risk_score = 0
        
        if age > 65:
            risk_score += 1
        if duration_years > 10:
            risk_score += 1
        if hba1c > 8.0:
            risk_score += 2
        if len(comorbidities) > 2:
            risk_score += 1
        if medication_adherence < 0.7:
            risk_score += 2
        if recent_hospitalizations > 0:
            risk_score += 2
        
        # Assign persona
        if risk_score >= 5:
            persona_id = 2
        elif risk_score >= 2:
            persona_id = 1
        else:
            persona_id = 0
        
        persona = self.risk_personas[persona_id]
        
        return {
            "persona_id": persona_id,
            "persona_name": persona["name"],
            "risk_score": risk_score,
            "intervention_intensity": persona["intensity"],
            "check_frequency": persona["check_frequency"],
            "features_used": {
                "age": age,
                "disease_duration": duration_years,
                "hba1c": hba1c,
                "comorbidities_count": len(comorbidities),
                "medication_adherence": medication_adherence
            },
            "clusterer": "K-Means (Mocked)"
        }

    # ============ SPECIALIST: MedGemma Lab Analysis ============
    def analyze_labs_medgemma(self, lab_report: Dict) -> Dict[str, Any]:
        """
        MedGemma analyzes lab reports for clinical progression.
        Mocked: Threshold-based analysis.
        """
        findings = []
        severity = "NORMAL"
        correlations = []
        
        # HbA1c (Diabetes control)
        hba1c = lab_report.get("hba1c")
        if hba1c:
            if hba1c > 9.0:
                findings.append(f"Poor glycemic control (HbA1c: {hba1c}%)")
                severity = "CRITICAL"
                correlations.append("Risk of diabetic complications increased")
            elif hba1c > 7.0:
                findings.append(f"Suboptimal HbA1c ({hba1c}%)")
                severity = "WARNING" if severity == "NORMAL" else severity
        
        # Creatinine / eGFR (Kidney)
        creatinine = lab_report.get("creatinine")
        egfr = lab_report.get("egfr")
        if creatinine and creatinine > 1.5:
            findings.append(f"Elevated creatinine ({creatinine} mg/dL) - potential renal impairment")
            severity = "CRITICAL" if creatinine > 2.0 else "WARNING"
            correlations.append("Possible diabetic nephropathy progression")
        if egfr and egfr < 60:
            findings.append(f"Reduced eGFR ({egfr} mL/min) - Stage 3+ CKD")
            severity = "CRITICAL"
        
        # Lipid Panel
        ldl = lab_report.get("ldl")
        if ldl and ldl > 130:
            findings.append(f"Elevated LDL ({ldl} mg/dL)")
            correlations.append("Cardiovascular risk factor")
        
        # Microalbumin (Early kidney damage)
        microalbumin = lab_report.get("microalbumin")
        if microalbumin and microalbumin > 30:
            findings.append(f"Microalbuminuria detected ({microalbumin} mg/L)")
            severity = "WARNING" if severity == "NORMAL" else severity
            correlations.append("Early diabetic kidney disease marker")
        
        return {
            "findings": findings,
            "severity": severity,
            "correlations": correlations,
            "biomarker_trends": lab_report,
            "analyzer": "MedGemma 4B (Mocked)"
        }

    # ============ BRAIN: Gemini Health Nudge Generator ============
    def generate_health_nudge(self, lstm_result: Dict, persona: Dict, lab_result: Dict, 
                               ai_service, language: str = "English") -> Dict[str, Any]:
        """
        Gemini generates personalized, multilingual health nudges.
        """
        prompt = f"""
        ROLE: Chronic Disease Health Coach.
        TARGET LANGUAGE: {language}
        
        WEARABLE ANALYSIS (LSTM):
        - Status: {lstm_result['status']}
        - Anomalies: {lstm_result['anomalies']}
        - Trends: {lstm_result['trend_analysis']}
        
        PATIENT RISK PERSONA (K-Means):
        - Persona: {persona['persona_name']}
        - Risk Score: {persona['risk_score']}
        - Recommended Check Frequency: {persona['check_frequency']}
        
        LAB ANALYSIS (MedGemma):
        - Severity: {lab_result['severity']}
        - Findings: {lab_result['findings']}
        
        TASK:
        1. Generate a supportive, empathetic health nudge for the patient in {language}.
        2. Include actionable recommendations specific to their condition.
        3. Determine if a teleconsult should be scheduled.
        
        OUTPUT FORMAT (JSON):
        {{
          "nudge_message": "Supportive message in {language}",
          "action_items": ["Action 1", "Action 2"],
          "teleconsult_recommended": boolean,
          "urgency": "routine/urgent/immediate"
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
                return self._generate_fallback_nudge(lstm_result, persona)
        except Exception as e:
            print(f"Nudge Generation Error: {e}")
            return self._generate_fallback_nudge(lstm_result, persona)

    def _generate_fallback_nudge(self, lstm_result: Dict, persona: Dict) -> Dict:
        """Fallback nudge generator."""
        is_critical = lstm_result['status'] == 'ALERT_CRITICAL'
        
        return {
            "nudge_message": "We noticed some changes in your health data. Please take a moment to check in with yourself and follow the recommended actions below." if not is_critical else "Important: We've detected changes in your vitals that need attention. Please contact your care team today.",
            "action_items": [
                "Check your blood sugar if you have diabetes",
                "Stay hydrated and rest",
                "Take your medications as prescribed"
            ],
            "teleconsult_recommended": is_critical,
            "urgency": "immediate" if is_critical else "routine"
        }

    # ============ BRAIN: Doctor Notification ============
    def schedule_teleconsult(self, patient_id: str, urgency: str, summary: str, ai_service) -> Dict[str, Any]:
        """
        Generate doctor notification and teleconsult scheduling.
        """
        scheduling_result = {
            "patient_id": patient_id,
            "teleconsult_scheduled": True,
            "urgency": urgency,
            "estimated_wait": "< 1 hour" if urgency == "immediate" else "24-48 hours",
            "notification_sent_to": "On-call endocrinologist",
            "summary": summary,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"[RPM] Teleconsult scheduled for patient {patient_id}: {urgency}")
        return scheduling_result

    # ============ ORCHESTRATED PIPELINE ============
    def run_pipeline(self, patient_id: str, wearable_data: List[Dict], patient_profile: Dict,
                     lab_report: Dict, ai_service, language: str = "English") -> Dict[str, Any]:
        """Full RPM pipeline execution."""
        print("\n[RPM] Starting Chronic Disease Monitoring Pipeline...")
        
        result = {
            "patient_id": patient_id,
            "timestamp": datetime.now().isoformat(),
            "language": language
        }
        
        # Step 1: LSTM Wearable Analysis
        print("[RPM] Step 1: LSTM Wearable Anomaly Detection...")
        lstm_result = self.lstm_wearable_monitor(wearable_data)
        result["wearable_analysis"] = lstm_result
        
        # Step 2: K-Means Persona Classification
        print("[RPM] Step 2: K-Means Risk Persona Classification...")
        persona = self.kmeans_risk_persona(patient_profile)
        result["risk_persona"] = persona
        
        # Step 3: MedGemma Lab Analysis
        print("[RPM] Step 3: MedGemma Lab Analysis...")
        lab_result = self.analyze_labs_medgemma(lab_report)
        result["lab_analysis"] = lab_result
        
        # Step 4: Gemini Health Nudge
        print(f"[RPM] Step 4: Generating Health Nudge ({language})...")
        nudge = self.generate_health_nudge(lstm_result, persona, lab_result, ai_service, language)
        result["health_nudge"] = nudge
        
        # Step 5: Schedule Teleconsult if Needed
        if nudge.get("teleconsult_recommended", False):
            print("[RPM] Step 5: Scheduling Teleconsult...")
            summary = f"Anomalies: {len(lstm_result['anomalies'])}. Lab severity: {lab_result['severity']}"
            teleconsult = self.schedule_teleconsult(patient_id, nudge["urgency"], summary, ai_service)
            result["teleconsult"] = teleconsult
        
        return result


if __name__ == "__main__":
    pipeline = ChronicDiseasePipeline()
    
    # Simulate 5 days of wearable data with rising heart rate
    wearable = [
        {"date": "2026-02-01", "heart_rate": 72, "glucose": 110, "steps": 6000, "spo2": 98},
        {"date": "2026-02-02", "heart_rate": 75, "glucose": 125, "steps": 5500, "spo2": 97},
        {"date": "2026-02-03", "heart_rate": 80, "glucose": 140, "steps": 4000, "spo2": 96},
        {"date": "2026-02-04", "heart_rate": 85, "glucose": 160, "steps": 3000, "spo2": 95},
        {"date": "2026-02-05", "heart_rate": 92, "glucose": 185, "steps": 2000, "spo2": 94}
    ]
    
    result = pipeline.lstm_wearable_monitor(wearable)
    print(json.dumps(result, indent=2))
