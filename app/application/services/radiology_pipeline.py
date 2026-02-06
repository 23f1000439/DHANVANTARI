"""
Pipeline: Radiology (Medical Imaging Analysis)
CNN Quality Check -> MedGemma VLM -> Clinical Prioritization -> Gemini Report Synthesis
Similar structure to Dermatology Pipeline, specialized for X-Ray/CT/MRI
"""
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class RadiologyPipeline:
    """
    End-to-End Radiology Pipeline for medical imaging analysis.
    Stages:
    1. CNN: Image quality check and DICOM preprocessing
    2. NB: Clinical urgency triage from referral notes
    3. MedGemma: VLM analysis of X-Ray/CT/MRI
    4. Statistical: BIRADS/TIRADS/Lung-RADS scoring
    5. Gemini: Structured radiology report synthesis
    """
    
    def __init__(self):
        # Modality-specific configurations
        self.modality_configs = {
            "X-Ray": {"slice_count": 1, "ai_models": ["DenseNet-121"], "report_template": "XRAY_STANDARD"},
            "CT": {"slice_count": "multi", "ai_models": ["3D-UNet", "nnUNet"], "report_template": "CT_STRUCTURED"},
            "MRI": {"slice_count": "multi", "ai_models": ["VNet", "ResNet-3D"], "report_template": "MRI_DETAILED"},
            "Mammography": {"slice_count": 4, "ai_models": ["BIRADS-Net"], "report_template": "MAMMO_BIRADS"},
            "Ultrasound": {"slice_count": 1, "ai_models": ["TIRADS-CNN"], "report_template": "US_TIRADS"}
        }
        
        # Critical findings that require immediate attention
        self.critical_findings = [
            "pneumothorax", "pulmonary embolism", "aortic dissection", "stroke", "hemorrhage",
            "intracranial hemorrhage", "tension pneumothorax", "cardiac tamponade",
            "bowel obstruction", "bowel perforation", "ruptured aortic aneurysm",
            "spinal cord compression", "cauda equina", "fracture with displacement",
            "midline shift", "herniation", "acute infarction"
        ]
        
        # Incidental findings categories
        self.incidental_categories = [
            "nodule", "cyst", "calcification", "lymphadenopathy", "adrenal mass",
            "thyroid nodule", "liver lesion", "kidney lesion"
        ]
        
        # Scoring systems
        self.scoring_systems = {
            "BIRADS": {0: "Incomplete", 1: "Negative", 2: "Benign", 3: "Probably Benign", 
                       4: "Suspicious", 5: "Highly Suggestive", 6: "Known Malignancy"},
            "TIRADS": {1: "Benign", 2: "Not Suspicious", 3: "Mildly Suspicious", 
                       4: "Moderately Suspicious", 5: "Highly Suspicious"},
            "LungRADS": {1: "Negative", 2: "Benign", 3: "Probably Benign", 
                         4: "Suspicious", 0: "Incomplete"}
        }
        
        print("RadiologyPipeline initialized with multi-modality support.")

    # ============ LIMB 1: CNN Image Quality Check (Mocked) ============
    def cnn_image_quality_check(self, image_data: Any, modality: str = "X-Ray") -> Dict[str, Any]:
        """
        CNN-based image quality assessment and DICOM preprocessing.
        Mocked: Returns quality metrics based on modality.
        """
        if image_data is None:
            return {
                "status": "rejected",
                "reason": "No image data provided",
                "quality_score": 0.0,
                "ready_for_analysis": False
            }
        
        modality_config = self.modality_configs.get(modality, self.modality_configs["X-Ray"])
        
        # Simulate quality assessment
        quality_score = 0.88
        
        return {
            "status": "accepted",
            "quality_score": quality_score,
            "modality": modality,
            "preprocessing_applied": [
                "DICOM_parsed",
                "window_level_optimized",
                "resolution_normalized",
                "orientation_corrected"
            ],
            "slice_count": modality_config["slice_count"],
            "ai_models_available": modality_config["ai_models"],
            "quality_checks": {
                "exposure": "optimal",
                "positioning": "correct",
                "motion_artifacts": "none",
                "coverage": "complete",
                "contrast": "adequate" if modality in ["CT", "MRI"] else "N/A"
            },
            "ready_for_analysis": True,
            "processor": "CNN DenseNet-121 (Mocked)"
        }

    # ============ LIMB 2: Clinical Urgency Triage (Naive Bayes) ============
    def triage_referral_nb(self, referral_notes: str, clinical_history: Optional[str] = None) -> Dict[str, Any]:
        """
        Naive Bayes-based urgency classification from referral notes.
        Mocked: Keyword-based priority assignment.
        """
        notes_lower = referral_notes.lower()
        history_lower = (clinical_history or "").lower()
        combined = notes_lower + " " + history_lower
        
        # STAT indicators
        stat_keywords = [
            "stat", "urgent", "emergency", "trauma", "code", "acute",
            "r/o pe", "r/o stroke", "chest pain", "sob", "fall",
            "motor vehicle", "mvc", "altered mental status", "unresponsive"
        ]
        
        # Routine indicators
        routine_keywords = [
            "routine", "follow-up", "screening", "annual", "chronic",
            "stable", "recheck", "comparison", "baseline"
        ]
        
        # Check priority
        if any(kw in combined for kw in stat_keywords):
            priority = "STAT"
            max_report_time = "1 hour"
            confidence = 0.92
            matched = [kw for kw in stat_keywords if kw in combined]
        elif "urgent" in combined or "asap" in combined:
            priority = "URGENT"
            max_report_time = "4 hours"
            confidence = 0.85
            matched = ["urgent", "asap"]
        elif any(kw in combined for kw in routine_keywords):
            priority = "ROUTINE"
            max_report_time = "24-48 hours"
            confidence = 0.80
            matched = [kw for kw in routine_keywords if kw in combined]
        else:
            priority = "ROUTINE"
            max_report_time = "24 hours"
            confidence = 0.75
            matched = []
        
        return {
            "priority": priority,
            "max_report_time": max_report_time,
            "confidence": confidence,
            "matched_triggers": matched,
            "classifier": "Naive Bayes (Mocked)"
        }

    # ============ SPECIALIST: MedGemma VLM Analysis ============
    def analyze_imaging_medgemma(self, image_data: Any, modality: str, 
                                  clinical_context: str) -> Dict[str, Any]:
        """
        MedGemma VLM analyzes the medical imaging.
        Mocked: Context-based finding detection.
        """
        context_lower = clinical_context.lower()
        
        findings = []
        critical_alert = False
        incidentals = []
        
        # Check for critical findings
        for finding in self.critical_findings:
            if finding in context_lower:
                findings.append({
                    "finding": finding.replace("_", " ").title(),
                    "severity": "CRITICAL",
                    "location": "See image annotation",
                    "confidence": 0.89,
                    "action_required": "Immediate clinical correlation"
                })
                critical_alert = True
        
        # Modality-specific findings
        if modality == "X-Ray":
            if "pneumonia" in context_lower or "infiltrate" in context_lower:
                findings.append({
                    "finding": "Pulmonary Opacity/Infiltrate",
                    "severity": "MODERATE",
                    "location": "Right lower lobe",
                    "confidence": 0.84,
                    "differential": ["Pneumonia", "Atelectasis", "Effusion"]
                })
            if "fracture" in context_lower:
                findings.append({
                    "finding": "Fracture Suspected",
                    "severity": "MODERATE",
                    "location": "See clinical correlation",
                    "confidence": 0.86
                })
        
        elif modality == "CT":
            if "mass" in context_lower or "tumor" in context_lower or "nodule" in context_lower:
                findings.append({
                    "finding": "Pulmonary Nodule/Mass",
                    "severity": "MODERATE",
                    "size_mm": "12mm",
                    "location": "Right upper lobe",
                    "confidence": 0.88,
                    "recommendation": "Lung-RADS scoring recommended"
                })
            if "appendicitis" in context_lower:
                findings.append({
                    "finding": "Appendicitis",
                    "severity": "HIGH",
                    "location": "Right lower quadrant",
                    "confidence": 0.91,
                    "secondary_signs": ["Periappendiceal fat stranding", "Appendicolith"]
                })
        
        elif modality == "MRI":
            if "tear" in context_lower or "ligament" in context_lower:
                findings.append({
                    "finding": "Ligament Abnormality",
                    "severity": "MODERATE",
                    "location": "Knee - ACL",
                    "confidence": 0.87,
                    "grade": "Partial tear (Grade II)"
                })
            if "disc" in context_lower or "herniation" in context_lower:
                findings.append({
                    "finding": "Disc Herniation",
                    "severity": "MODERATE",
                    "location": "L4-L5",
                    "confidence": 0.85,
                    "neural_compression": "Mild left neural foraminal narrowing"
                })
        
        elif modality == "Mammography":
            if "mass" in context_lower or "calcification" in context_lower:
                findings.append({
                    "finding": "Breast Mass/Calcification",
                    "severity": "MODERATE",
                    "location": "Right breast, upper outer quadrant",
                    "confidence": 0.83,
                    "action_required": "BIRADS scoring"
                })
        
        # Check for incidentals
        for incidental in self.incidental_categories:
            if incidental in context_lower:
                incidentals.append({
                    "finding": incidental.title(),
                    "severity": "INCIDENTAL",
                    "recommendation": f"Consider follow-up imaging for {incidental}"
                })
        
        # Default normal finding if nothing detected
        if not findings:
            findings.append({
                "finding": "No acute abnormality detected",
                "severity": "NORMAL",
                "confidence": 0.80
            })
        
        return {
            "modality": modality,
            "critical_alert": critical_alert,
            "findings": findings,
            "incidentals": incidentals,
            "finding_count": len(findings),
            "requires_comparison": "comparison" in context_lower,
            "analyzer": "MedGemma 1.5 VLM (Mocked)"
        }

    # ============ LIMB 4: Scoring System (BIRADS/TIRADS/LungRADS) ============
    def compute_standardized_score(self, findings: List[Dict], modality: str) -> Dict[str, Any]:
        """
        Compute standardized radiology scoring (BIRADS, TIRADS, Lung-RADS).
        Mocked: Rule-based scoring.
        """
        scoring_system = None
        score = None
        interpretation = None
        recommendation = None
        
        # Determine which scoring system to use
        if modality == "Mammography":
            scoring_system = "BIRADS"
            # Count suspicious findings
            suspicious_count = sum(1 for f in findings if f.get("severity") in ["HIGH", "CRITICAL", "MODERATE"])
            if suspicious_count == 0:
                score = 1
            elif suspicious_count == 1 and not any(f.get("severity") == "CRITICAL" for f in findings):
                score = 3
            else:
                score = 4
            interpretation = self.scoring_systems["BIRADS"].get(score, "Unknown")
            recommendation = "Biopsy recommended" if score >= 4 else "Short-interval follow-up" if score == 3 else "Routine screening"
        
        elif modality == "Ultrasound" and any("thyroid" in str(f).lower() for f in findings):
            scoring_system = "TIRADS"
            suspicious_count = sum(1 for f in findings if f.get("severity") in ["HIGH", "CRITICAL", "MODERATE"])
            score = min(5, suspicious_count + 1)
            interpretation = self.scoring_systems["TIRADS"].get(score, "Unknown")
            recommendation = "FNA recommended" if score >= 4 else "Follow-up ultrasound"
        
        elif modality == "CT" and any("nodule" in str(f).lower() or "lung" in str(f).lower() for f in findings):
            scoring_system = "LungRADS"
            has_nodule = any("nodule" in str(f).lower() for f in findings)
            if has_nodule:
                score = 3
            else:
                score = 1
            interpretation = self.scoring_systems["LungRADS"].get(score, "Unknown")
            recommendation = "6-month follow-up CT" if score >= 3 else "Annual screening"
        
        if scoring_system is None:
            return {
                "scoring_applicable": False,
                "message": f"No standardized scoring for {modality} with these findings"
            }
        
        return {
            "scoring_applicable": True,
            "scoring_system": scoring_system,
            "score": score,
            "interpretation": interpretation,
            "recommendation": recommendation
        }

    # ============ BRAIN: Gemini Report Synthesis ============
    def synthesize_report(self, triage: Dict, analysis: Dict, scoring: Dict, 
                          patient_info: Dict, ai_service) -> Dict[str, Any]:
        """
        Gemini 3 synthesizes the structured radiology report.
        """
        modality = analysis.get("modality", "X-Ray")
        
        prompt = f"""
        ROLE: Expert Radiologist generating a structured report.
        
        MODALITY: {modality}
        PRIORITY: {triage['priority']}
        
        IMAGING FINDINGS (MedGemma):
        - Critical Alert: {analysis['critical_alert']}
        - Findings: {analysis['findings']}
        - Incidentals: {analysis['incidentals']}
        
        SCORING:
        {scoring}
        
        PATIENT INFO:
        - Age: {patient_info.get('age', 'Unknown')}
        - Gender: {patient_info.get('gender', 'Unknown')}
        - Clinical Indication: {patient_info.get('indication', 'Not provided')}
        
        TASK: Generate a structured radiology report with:
        1. TECHNIQUE
        2. COMPARISON (if available)
        3. FINDINGS (by anatomic region)
        4. IMPRESSION (numbered, most important first)
        5. RECOMMENDATIONS
        
        OUTPUT FORMAT (JSON):
        {{
          "technique": "Brief technique description",
          "comparison": "Prior studies if available",
          "findings_by_region": {{"region": "finding"}},
          "impression": ["1. Most critical finding", "2. Secondary findings"],
          "recommendations": ["Recommendation 1"],
          "critical_results_communicated": boolean
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
                return self._generate_fallback_report(modality, analysis, triage, scoring)
        except Exception as e:
            print(f"Report Synthesis Error: {e}")
            return self._generate_fallback_report(modality, analysis, triage, scoring)

    def _generate_fallback_report(self, modality: str, analysis: Dict, 
                                   triage: Dict, scoring: Dict) -> Dict:
        """Fallback report generator."""
        findings_text = [f.get("finding", "") for f in analysis.get("findings", [])]
        
        impression = []
        for i, f in enumerate(analysis.get("findings", [])[:3], 1):
            impression.append(f"{i}. {f.get('finding', 'Finding noted')}")
        
        if not impression:
            impression = ["1. No acute findings."]
        
        recommendations = []
        if analysis.get("critical_alert"):
            recommendations.append("STAT: Communicate critical findings to ordering physician immediately")
        if scoring.get("scoring_applicable"):
            recommendations.append(scoring.get("recommendation", "Follow-up as clinically indicated"))
        if not recommendations:
            recommendations.append("Clinical correlation recommended")
        
        return {
            "technique": f"{modality} imaging performed per standard protocol.",
            "comparison": "No prior studies available for comparison.",
            "findings_by_region": {"Primary": findings_text[0] if findings_text else "No significant findings"},
            "impression": impression,
            "recommendations": recommendations,
            "critical_results_communicated": analysis.get("critical_alert", False)
        }

    # ============ GOVERNANCE: Audit Trail ============
    def log_audit_trail(self, study_id: str, result: Dict) -> Dict:
        """Log the radiology decision process for compliance."""
        audit_entry = {
            "timestamp": datetime.now().isoformat(),
            "study_id": study_id,
            "pipeline": "RADIOLOGY",
            "modality": result.get("analysis", {}).get("modality"),
            "decision_path": {
                "priority": result.get("triage", {}).get("priority"),
                "critical_alert": result.get("analysis", {}).get("critical_alert"),
                "finding_count": result.get("analysis", {}).get("finding_count"),
                "scoring": result.get("scoring", {}).get("scoring_system")
            },
            "compliance": {
                "hipaa_logged": True,
                "critical_results_protocol": result.get("analysis", {}).get("critical_alert", False)
            }
        }
        print(f"[AUDIT] Radiology study logged: {study_id}")
        return audit_entry

    # ============ ORCHESTRATED PIPELINE ============
    def run_pipeline(self, study_id: str, image_data: Any, modality: str,
                     referral_notes: str, patient_info: Dict, 
                     ai_service, clinical_history: Optional[str] = None) -> Dict[str, Any]:
        """Full radiology pipeline execution."""
        print(f"\n[RAD] Starting Radiology Analysis Pipeline ({modality})...")
        
        result = {
            "study_id": study_id,
            "modality": modality,
            "timestamp": datetime.now().isoformat()
        }
        
        # Step 1: CNN Image Quality Check
        print("[RAD] Step 1: CNN Image Quality Check...")
        quality = self.cnn_image_quality_check(image_data, modality)
        result["image_quality"] = quality
        
        if not quality.get("ready_for_analysis"):
            result["error"] = "Image quality insufficient for analysis"
            return result
        
        # Step 2: NB Urgency Triage
        print("[RAD] Step 2: Naive Bayes Urgency Triage...")
        triage = self.triage_referral_nb(referral_notes, clinical_history)
        result["triage"] = triage
        
        # Step 3: MedGemma Analysis
        print("[RAD] Step 3: MedGemma VLM Imaging Analysis...")
        clinical_context = f"{referral_notes} {clinical_history or ''}"
        analysis = self.analyze_imaging_medgemma(image_data, modality, clinical_context)
        result["analysis"] = analysis
        
        # Step 4: Standardized Scoring
        print("[RAD] Step 4: Computing Standardized Scores...")
        scoring = self.compute_standardized_score(analysis["findings"], modality)
        result["scoring"] = scoring
        
        # Step 5: Gemini Report Synthesis
        print("[RAD] Step 5: Gemini Report Synthesis...")
        report = self.synthesize_report(triage, analysis, scoring, patient_info, ai_service)
        result["report"] = report
        
        # Governance
        self.log_audit_trail(study_id, result)
        
        # Critical alert flag
        if analysis.get("critical_alert"):
            result["CRITICAL_ALERT"] = "⚠️ CRITICAL FINDINGS - IMMEDIATE NOTIFICATION REQUIRED"
        
        return result


if __name__ == "__main__":
    pipeline = RadiologyPipeline()
    
    # Test quality check
    print(pipeline.cnn_image_quality_check(b"fake_dicom", "CT"))
    
    # Test triage
    print(pipeline.triage_referral_nb("STAT CT abdomen, r/o appendicitis, acute abdominal pain"))
    
    # Test MedGemma analysis
    print(pipeline.analyze_imaging_medgemma(b"fake_ct", "CT", "r/o appendicitis, RLQ pain"))
