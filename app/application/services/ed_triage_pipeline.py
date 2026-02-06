"""
Pipeline: Emergency Department (ED) Triage & Acute Care
NB ESI Triage -> CNN X-Ray Quality -> MedGemma 3D Scan -> Gemini Coordination
"""
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

class EDTriagePipeline:
    """
    Emergency Department Triage Pipeline for acute care.
    Stages:
    1. NB: ESI (Emergency Severity Index) assignment
    2. CNN: X-Ray quality/orientation check
    3. MedGemma 1.5: CT/MRI critical finding detection
    4. Gemini: Trauma team coordination + handoff summary
    5. Governance: Audit trail logging
    """
    
    def __init__(self):
        # ESI Level Definitions
        self.esi_levels = {
            1: {"name": "Resuscitation", "color": "🔴 RED", "triage_time": "Immediate", "resources": "All available"},
            2: {"name": "Emergent", "color": "🟠 ORANGE", "triage_time": "<10 min", "resources": "High"},
            3: {"name": "Urgent", "color": "🟡 YELLOW", "triage_time": "<30 min", "resources": "Moderate"},
            4: {"name": "Less Urgent", "color": "🟢 GREEN", "triage_time": "<60 min", "resources": "Low"},
            5: {"name": "Non-Urgent", "color": "🔵 BLUE", "triage_time": "<120 min", "resources": "Minimal"}
        }
        
        # Critical chief complaint keywords
        self.critical_keywords = {
            1: ["cardiac arrest", "unresponsive", "not breathing", "severe hemorrhage", "major trauma"],
            2: ["chest pain", "stroke symptoms", "severe pain", "high fever with immunocompromised", 
                "altered mental status", "difficulty breathing", "overdose"],
            3: ["moderate pain", "mild respiratory distress", "laceration requiring sutures",
                "high fever", "abdominal pain", "vomiting blood"],
            4: ["minor injury", "mild pain", "chronic complaint", "rash", "earache"],
            5: ["prescription refill", "minor cold", "follow-up", "suture removal"]
        }
        
        # Critical imaging findings
        self.critical_findings = [
            "hemorrhage", "intracranial hemorrhage", "subdural hematoma", "epidural hematoma",
            "pneumothorax", "aortic dissection", "pulmonary embolism", "splenic rupture",
            "liver laceration", "bowel perforation", "cervical spine fracture", "midline shift"
        ]
        
        # Audit log storage (in-memory for demo)
        self.audit_log = []
        
        print("EDTriagePipeline initialized with ESI protocols.")

    # ============ LIMB 1: Naive Bayes ESI Assignment (Mocked) ============
    def naive_bayes_esi(self, vitals: Dict, chief_complaint: str, medical_history: Optional[str] = None) -> Dict[str, Any]:
        """
        Naive Bayes-based ESI level assignment.
        Mocked: Keyword + vitals-based classification.
        """
        cc_lower = chief_complaint.lower()
        assigned_esi = 5  # Start with lowest priority
        matched_triggers = []
        
        # Check keywords for each ESI level
        for esi_level, keywords in self.critical_keywords.items():
            if any(kw in cc_lower for kw in keywords):
                assigned_esi = min(assigned_esi, esi_level)
                matched_triggers.extend([kw for kw in keywords if kw in cc_lower])
        
        # Adjust based on vitals
        vitals_flags = []
        
        hr = vitals.get("heart_rate", 80)
        bp_sys = vitals.get("bp_systolic", 120)
        spo2 = vitals.get("spo2", 98)
        temp = vitals.get("temperature", 37.0)
        gcs = vitals.get("gcs", 15)  # Glasgow Coma Scale
        
        if gcs < 8:
            assigned_esi = 1
            vitals_flags.append(f"GCS {gcs} - Coma/Obtunded")
        elif gcs < 12:
            assigned_esi = min(assigned_esi, 2)
            vitals_flags.append(f"GCS {gcs} - Altered")
        
        if spo2 < 88:
            assigned_esi = min(assigned_esi, 1)
            vitals_flags.append(f"Severe Hypoxia (SpO2: {spo2}%)")
        elif spo2 < 92:
            assigned_esi = min(assigned_esi, 2)
            vitals_flags.append(f"Hypoxia (SpO2: {spo2}%)")
        
        if bp_sys < 70:
            assigned_esi = 1
            vitals_flags.append(f"Severe Hypotension (BP: {bp_sys})")
        elif bp_sys < 90:
            assigned_esi = min(assigned_esi, 2)
            vitals_flags.append(f"Hypotension (BP: {bp_sys})")
        
        if hr > 150 or hr < 40:
            assigned_esi = min(assigned_esi, 2)
            vitals_flags.append(f"Abnormal HR: {hr}")
        
        if temp > 40.0:
            assigned_esi = min(assigned_esi, 2)
            vitals_flags.append(f"High Fever: {temp}°C")
        
        esi_info = self.esi_levels[assigned_esi]
        
        return {
            "esi_level": assigned_esi,
            "esi_name": esi_info["name"],
            "color_code": esi_info["color"],
            "max_wait_time": esi_info["triage_time"],
            "expected_resources": esi_info["resources"],
            "matched_triggers": matched_triggers,
            "vitals_flags": vitals_flags,
            "confidence": 0.88,
            "classifier": "Naive Bayes (Mocked)"
        }

    # ============ LIMB 2: CNN X-Ray Quality Check (Mocked) ============
    def cnn_xray_quality(self, image_data: Any, modality: str = "X-Ray") -> Dict[str, Any]:
        """
        CNN-based image quality and orientation check.
        Mocked: Returns quality assessment.
        """
        if image_data is None:
            return {
                "status": "no_image",
                "quality_score": 0.0,
                "issues": ["No image provided"]
            }
        
        # Simulate quality assessment
        return {
            "status": "accepted",
            "quality_score": 0.92,
            "modality": modality,
            "orientation": "correct",
            "preprocessing_applied": ["contrast_enhanced", "noise_reduced"],
            "ready_for_ai_analysis": True,
            "quality_checks": {
                "exposure": "optimal",
                "positioning": "correct",
                "artifacts": "none",
                "coverage": "complete"
            },
            "processor": "CNN Quality Control (Mocked)"
        }

    # ============ SPECIALIST: MedGemma 3D Scan Analysis ============
    def medgemma_3d_scan(self, scan_data: Any, scan_type: str, clinical_context: str) -> Dict[str, Any]:
        """
        MedGemma 1.5 analyzes CT/MRI for critical findings.
        Mocked: Keyword-based detection from clinical context.
        """
        context_lower = clinical_context.lower()
        detected_findings = []
        critical_alert = False
        
        for finding in self.critical_findings:
            if finding in context_lower:
                detected_findings.append({
                    "finding": finding.title(),
                    "severity": "CRITICAL",
                    "location": "See scan coordinates",
                    "confidence": 0.91
                })
                critical_alert = True
        
        # Trauma-specific detection
        if "trauma" in context_lower or "mvc" in context_lower or "fall" in context_lower:
            if "spleen" in context_lower or "liver" in context_lower:
                detected_findings.append({
                    "finding": "Suspected Solid Organ Injury",
                    "severity": "CRITICAL",
                    "location": "Abdominal",
                    "confidence": 0.87
                })
                critical_alert = True
            
            if "head" in context_lower or "brain" in context_lower:
                detected_findings.append({
                    "finding": "Possible Intracranial Pathology",
                    "severity": "CRITICAL",
                    "location": "Intracranial",
                    "confidence": 0.85
                })
                critical_alert = True
        
        # If no critical findings, report normal
        if not detected_findings:
            detected_findings.append({
                "finding": "No acute critical findings detected",
                "severity": "NORMAL",
                "confidence": 0.82
            })
        
        return {
            "scan_type": scan_type,
            "critical_alert": critical_alert,
            "findings": detected_findings,
            "recommendation": "Immediate surgical consultation" if critical_alert else "Continue standard workup",
            "pre_read_complete": True,
            "analyzer": "MedGemma 1.5 VLM (Mocked)"
        }

    # ============ BRAIN: Gemini Trauma Team Coordination ============
    def coordinate_trauma_team(self, esi_result: Dict, scan_result: Dict, 
                                patient_data: Dict, ai_service) -> Dict[str, Any]:
        """
        Gemini coordinates trauma team notification and generates handoff summary.
        """
        is_critical = esi_result["esi_level"] <= 2 or scan_result.get("critical_alert", False)
        
        prompt = f"""
        ROLE: Emergency Department Coordinator.
        
        ESI TRIAGE:
        - Level: {esi_result['esi_level']} ({esi_result['esi_name']})
        - Color: {esi_result['color_code']}
        - Triggers: {esi_result['matched_triggers']}
        - Vital Flags: {esi_result['vitals_flags']}
        
        IMAGING FINDINGS (MedGemma):
        - Critical Alert: {scan_result.get('critical_alert', False)}
        - Findings: {scan_result.get('findings', [])}
        - Recommendation: {scan_result.get('recommendation')}
        
        PATIENT DATA:
        - Age: {patient_data.get('age', 'Unknown')}
        - Gender: {patient_data.get('gender', 'Unknown')}
        - Mechanism: {patient_data.get('mechanism_of_injury', 'Unknown')}
        
        TASK:
        1. Generate a concise "Patient Handoff" summary for the surgical/trauma team.
        2. Determine which specialist teams to alert.
        3. Fetch applicable hospital protocol name.
        
        OUTPUT FORMAT (JSON):
        {{
          "handoff_summary": "Concise clinical summary",
          "teams_to_alert": ["Team 1", "Team 2"],
          "protocol": "Hospital protocol name",
          "priority": "STAT/Urgent/Routine"
        }}
        """
        
        try:
            response = ai_service.pro_model.generate_content(
                prompt,
                generation_config=ai_service.analytical_config
            )
            try:
                result = json.loads(response.text)
            except:
                result = self._generate_fallback_coordination(esi_result, scan_result, patient_data)
        except Exception as e:
            print(f"Coordination Error: {e}")
            result = self._generate_fallback_coordination(esi_result, scan_result, patient_data)
        
        # Add push notification simulation
        result["push_notification"] = {
            "sent_to": result.get("teams_to_alert", ["Trauma Team"]),
            "message": f"ED ALERT: {patient_data.get('age', 'Unknown')}yo {patient_data.get('gender', '')}, ESI-{esi_result['esi_level']}. {scan_result.get('findings', [{}])[0].get('finding', 'Assessment pending')}",
            "timestamp": datetime.now().isoformat()
        }
        
        return result

    def _generate_fallback_coordination(self, esi: Dict, scan: Dict, patient: Dict) -> Dict:
        """Fallback coordination generator."""
        is_critical = esi["esi_level"] <= 2
        
        teams = ["Trauma Surgery"] if is_critical else ["Emergency Medicine"]
        if any("intracranial" in f.get("finding", "").lower() for f in scan.get("findings", [])):
            teams.append("Neurosurgery")
        if any("spleen" in f.get("finding", "").lower() or "liver" in f.get("finding", "").lower() 
               for f in scan.get("findings", [])):
            teams.append("General Surgery")
        
        return {
            "handoff_summary": f"ESI-{esi['esi_level']} patient, {patient.get('age', 'Unknown')}yo {patient.get('gender', '')}. Chief complaint triggers: {', '.join(esi['matched_triggers'][:2])}. MedGemma flagged: {scan.get('findings', [{}])[0].get('finding', 'pending')}.",
            "teams_to_alert": teams,
            "protocol": "Trauma Activation Protocol" if is_critical else "Standard ED Evaluation",
            "priority": "STAT" if esi["esi_level"] == 1 else ("Urgent" if esi["esi_level"] == 2 else "Routine")
        }

    # ============ GOVERNANCE: Audit Trail Logger ============
    def audit_trail_logger(self, patient_id: str, esi_result: Dict, scan_result: Dict, 
                           coordination: Dict) -> Dict[str, Any]:
        """
        Logs every decision point for hospital compliance.
        """
        audit_entry = {
            "audit_id": f"ED-{datetime.now().strftime('%Y%m%d%H%M%S')}-{patient_id[:8]}",
            "timestamp": datetime.now().isoformat(),
            "patient_id": patient_id,
            "pipeline": "ED_TRIAGE",
            "decision_points": [
                {
                    "step": "ESI_ASSIGNMENT",
                    "result": f"ESI-{esi_result['esi_level']}",
                    "triggers": esi_result.get("matched_triggers"),
                    "model": esi_result.get("classifier")
                },
                {
                    "step": "IMAGING_ANALYSIS",
                    "critical_alert": scan_result.get("critical_alert"),
                    "findings_count": len(scan_result.get("findings", [])),
                    "model": scan_result.get("analyzer")
                },
                {
                    "step": "TEAM_COORDINATION",
                    "teams_alerted": coordination.get("teams_to_alert"),
                    "protocol_activated": coordination.get("protocol"),
                    "priority": coordination.get("priority")
                }
            ],
            "compliance": {
                "hipaa_logged": True,
                "timestamp_recorded": True,
                "decision_traceable": True
            }
        }
        
        self.audit_log.append(audit_entry)
        print(f"[AUDIT] ED Triage logged: {audit_entry['audit_id']}")
        
        return audit_entry

    # ============ ORCHESTRATED PIPELINE ============
    def run_pipeline(self, patient_id: str, vitals: Dict, chief_complaint: str,
                     patient_data: Dict, scan_data: Any, scan_type: str,
                     ai_service, include_audit: bool = True) -> Dict[str, Any]:
        """Full ED Triage pipeline execution."""
        print("\n[ED] Starting Emergency Department Triage Pipeline...")
        
        result = {
            "patient_id": patient_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # Step 1: NB ESI Assignment
        print("[ED] Step 1: Naive Bayes ESI Triage...")
        esi_result = self.naive_bayes_esi(vitals, chief_complaint, patient_data.get("medical_history"))
        result["esi_triage"] = esi_result
        
        # Priority gate: If ESI-1, fast-track everything
        if esi_result["esi_level"] == 1:
            print("[ED] ⚠️  ESI-1 DETECTED - FAST TRACK ACTIVATED")
        
        # Step 2: CNN X-Ray Quality
        print(f"[ED] Step 2: CNN {scan_type} Quality Check...")
        xray_quality = self.cnn_xray_quality(scan_data, scan_type)
        result["xray_quality"] = xray_quality
        
        # Step 3: MedGemma 3D Analysis
        print("[ED] Step 3: MedGemma Critical Finding Detection...")
        scan_result = self.medgemma_3d_scan(scan_data, scan_type, chief_complaint)
        result["scan_analysis"] = scan_result
        
        # Step 4: Gemini Coordination
        print("[ED] Step 4: Gemini Trauma Team Coordination...")
        coordination = self.coordinate_trauma_team(esi_result, scan_result, patient_data, ai_service)
        result["coordination"] = coordination
        
        # Step 5: Audit Logging
        if include_audit:
            print("[ED] Step 5: Audit Trail Logging...")
            audit = self.audit_trail_logger(patient_id, esi_result, scan_result, coordination)
            result["audit"] = audit
        
        return result


if __name__ == "__main__":
    pipeline = EDTriagePipeline()
    
    # Test ESI assignment
    vitals = {"heart_rate": 120, "bp_systolic": 85, "spo2": 90, "temperature": 38.5, "gcs": 13}
    print(pipeline.naive_bayes_esi(vitals, "70yo male, MVC, chest pain and difficulty breathing"))
