"""
Pipeline: Revenue Cycle Management (RCM) & Claims
CRF Code Extraction -> Isolation Forest Audit -> Decision Tree Rules -> Gemini Appeal
"""
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class RCMPipeline:
    """
    Revenue Cycle Management Pipeline for claim processing.
    Stages:
    1. CRF: ICD-11/CPT code extraction from discharge summaries
    2. Isolation Forest: Anomalous billing detection
    3. Decision Trees: TPA rule validation
    4. Gemini: Denial appeal drafting
    """
    
    def __init__(self):
        # Common procedure code mappings
        self.procedure_codes = {
            "appendectomy": {"cpt": "44970", "icd": "K35.2", "avg_duration_min": 60, "avg_charge": 15000},
            "cholecystectomy": {"cpt": "47562", "icd": "K80.20", "avg_duration_min": 90, "avg_charge": 18000},
            "cesarean section": {"cpt": "59510", "icd": "O82", "avg_duration_min": 45, "avg_charge": 22000},
            "knee replacement": {"cpt": "27447", "icd": "M17.11", "avg_duration_min": 120, "avg_charge": 45000},
            "cardiac catheterization": {"cpt": "93458", "icd": "I25.10", "avg_duration_min": 60, "avg_charge": 25000},
            "coronary bypass": {"cpt": "33533", "icd": "I25.10", "avg_duration_min": 240, "avg_charge": 75000},
            "hip replacement": {"cpt": "27130", "icd": "M16.11", "avg_duration_min": 150, "avg_charge": 50000},
        }
        
        # TPA (Insurance) rules
        self.tpa_rules = {
            "pre_authorization_required": ["knee replacement", "hip replacement", "coronary bypass"],
            "length_of_stay_limits": {
                "appendectomy": 2,
                "cholecystectomy": 1,
                "cesarean section": 3,
                "knee replacement": 4,
                "hip replacement": 5
            },
            "documentation_required": ["operative report", "anesthesia record", "h&p", "discharge summary"]
        }
        
        print("RCMPipeline initialized with ICD-11/CPT knowledge base.")

    # ============ LIMB 1: CRF Code Extractor (Mocked) ============
    def crf_code_extractor(self, discharge_summary: str) -> Dict[str, Any]:
        """
        Sequence Labeling / CRF-based code extraction.
        Mocked: Regex + keyword matching for procedure identification.
        """
        text_lower = discharge_summary.lower()
        extracted_codes = []
        diagnoses = []
        procedures = []
        
        # Extract procedures
        for proc_name, codes in self.procedure_codes.items():
            if proc_name in text_lower:
                procedures.append({
                    "procedure": proc_name.title(),
                    "cpt_code": codes["cpt"],
                    "icd_code": codes["icd"],
                    "confidence": 0.92
                })
        
        # Extract common diagnosis patterns
        diagnosis_patterns = [
            (r"diagnosis[:\s]+([a-z\s]+)", "primary"),
            (r"secondary diagnosis[:\s]+([a-z\s]+)", "secondary"),
            (r"comorbidities[:\s]+([a-z\s,]+)", "comorbidity")
        ]
        
        for pattern, diag_type in diagnosis_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                diagnoses.append({
                    "type": diag_type,
                    "text": match.strip()[:50],
                    "icd_code": "AUTO-ASSIGN"
                })
        
        # Extract length of stay
        los_match = re.search(r"length of stay[:\s]+(\d+)", text_lower)
        los = int(los_match.group(1)) if los_match else None
        
        # Extract charges
        charge_match = re.search(r"total charges[:\s]+\$?([\d,]+)", text_lower)
        total_charges = float(charge_match.group(1).replace(",", "")) if charge_match else None
        
        return {
            "procedures": procedures,
            "diagnoses": diagnoses,
            "length_of_stay_days": los,
            "total_charges": total_charges,
            "extraction_confidence": 0.88,
            "extractor": "CRF Sequence Labeling (Mocked)"
        }

    # ============ LIMB 2: Isolation Forest Auditor (Mocked) ============
    def isolation_forest_auditor(self, claim_data: Dict) -> Dict[str, Any]:
        """
        Isolation Forest for anomalous billing detection.
        Mocked: Rule-based outlier detection.
        """
        anomalies = []
        risk_score = 0.0
        
        procedures = claim_data.get("procedures", [])
        los = claim_data.get("length_of_stay_days")
        total_charges = claim_data.get("total_charges")
        
        for proc in procedures:
            proc_name = proc.get("procedure", "").lower()
            
            if proc_name in self.procedure_codes:
                ref_data = self.procedure_codes[proc_name]
                
                # Check if charges are outliers
                if total_charges and total_charges > ref_data["avg_charge"] * 1.5:
                    anomalies.append({
                        "type": "CHARGE_OUTLIER",
                        "severity": "HIGH",
                        "details": f"Charges ${total_charges:,.0f} exceed typical ${ref_data['avg_charge']:,} by >50%",
                        "recommendation": "Verify itemized billing for add-on procedures"
                    })
                    risk_score += 0.3
                
                # Check LOS outliers
                if proc_name in self.tpa_rules["length_of_stay_limits"] and los:
                    expected_los = self.tpa_rules["length_of_stay_limits"][proc_name]
                    if los > expected_los * 2:
                        anomalies.append({
                            "type": "LOS_OUTLIER",
                            "severity": "MEDIUM",
                            "details": f"LOS {los} days exceeds typical {expected_los} days",
                            "recommendation": "Document medical necessity for extended stay"
                        })
                        risk_score += 0.2
        
        # Flag duplicate codes
        cpt_codes = [p.get("cpt_code") for p in procedures]
        if len(cpt_codes) != len(set(cpt_codes)):
            anomalies.append({
                "type": "DUPLICATE_CODES",
                "severity": "HIGH",
                "details": "Duplicate procedure codes detected",
                "recommendation": "Review for unbundling or duplicate entry"
            })
            risk_score += 0.4
        
        # Determine overall status
        risk_score = min(risk_score, 1.0)
        if risk_score >= 0.5:
            status = "FLAGGED_FOR_REVIEW"
        elif risk_score >= 0.2:
            status = "MINOR_CONCERNS"
        else:
            status = "CLEAN"
        
        return {
            "status": status,
            "risk_score": round(risk_score, 2),
            "anomalies": anomalies,
            "auditor": "Isolation Forest (Mocked)"
        }

    # ============ LIMB 3: Decision Tree Rules (Mocked) ============
    def decision_tree_rules(self, claim_data: Dict, tpa_name: str = "Generic TPA") -> Dict[str, Any]:
        """
        Explainable decision tree for TPA rule validation.
        Mocked: Hard-coded insurance rules.
        """
        procedures = claim_data.get("procedures", [])
        violations = []
        passed_checks = []
        
        for proc in procedures:
            proc_name = proc.get("procedure", "").lower()
            
            # Rule 1: Pre-authorization check
            if proc_name in self.tpa_rules["pre_authorization_required"]:
                has_auth = claim_data.get("pre_authorization", False)
                if not has_auth:
                    violations.append({
                        "rule": "PRE_AUTH_REQUIRED",
                        "procedure": proc_name.title(),
                        "explanation": f"{proc_name.title()} requires prior authorization per TPA policy",
                        "action": "Obtain retroactive authorization or document emergency exception"
                    })
                else:
                    passed_checks.append(f"Pre-authorization verified for {proc_name.title()}")
            
            # Rule 2: Length of stay limits
            los = claim_data.get("length_of_stay_days")
            if proc_name in self.tpa_rules["length_of_stay_limits"] and los:
                limit = self.tpa_rules["length_of_stay_limits"][proc_name]
                if los > limit:
                    violations.append({
                        "rule": "LOS_EXCEEDED",
                        "procedure": proc_name.title(),
                        "explanation": f"LOS ({los} days) exceeds TPA limit ({limit} days)",
                        "action": "Submit medical necessity documentation for extended stay"
                    })
                else:
                    passed_checks.append(f"LOS within limits for {proc_name.title()}")
        
        # Rule 3: Documentation completeness
        required_docs = self.tpa_rules["documentation_required"]
        provided_docs = claim_data.get("documentation", [])
        missing_docs = [doc for doc in required_docs if doc not in provided_docs]
        
        if missing_docs:
            violations.append({
                "rule": "MISSING_DOCUMENTATION",
                "procedure": "General",
                "explanation": f"Missing required documents: {', '.join(missing_docs)}",
                "action": "Attach missing documentation before submission"
            })
        else:
            passed_checks.append("All required documentation present")
        
        # Overall adjudication
        if violations:
            adjudication = "HOLD_FOR_REVIEW"
        else:
            adjudication = "APPROVED_FOR_SUBMISSION"
        
        return {
            "adjudication": adjudication,
            "violations": violations,
            "passed_checks": passed_checks,
            "tpa_name": tpa_name,
            "decision_tree": "Explainable Decision Tree (Mocked)",
            "explainability": "100%"
        }

    # ============ BRAIN: Gemini Appeal Drafting ============
    def draft_appeal_gemini(self, denial_letter: str, claim_data: Dict, 
                            clinical_evidence: str, ai_service) -> Dict[str, Any]:
        """
        Gemini drafts formal appeal letter for denied claims.
        """
        prompt = f"""
        ROLE: Medical Billing Appeals Specialist.
        
        DENIAL LETTER SUMMARY:
        {denial_letter}
        
        CLAIM DATA:
        - Procedures: {claim_data.get('procedures')}
        - Total Charges: ${claim_data.get('total_charges', 0):,.0f}
        - Length of Stay: {claim_data.get('length_of_stay_days')} days
        
        CLINICAL EVIDENCE (from EHR):
        {clinical_evidence}
        
        TASK:
        1. Identify the exact denial reason.
        2. Draft a formal appeal letter citing specific clinical evidence that proves medical necessity.
        3. Reference applicable coding guidelines (CPT, ICD-11).
        4. Suggest additional documentation if needed.
        
        OUTPUT FORMAT (JSON):
        {{
          "denial_reason_identified": "Reason from letter",
          "appeal_letter": "Formal appeal text",
          "key_evidence_cited": ["Evidence 1", "Evidence 2"],
          "additional_docs_needed": ["Doc 1"],
          "success_probability": "High/Medium/Low"
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
                return self._generate_fallback_appeal(denial_letter, claim_data)
        except Exception as e:
            print(f"Appeal Drafting Error: {e}")
            return self._generate_fallback_appeal(denial_letter, claim_data)

    def _generate_fallback_appeal(self, denial_letter: str, claim_data: Dict) -> Dict:
        """Fallback appeal generator."""
        procedures = claim_data.get("procedures", [])
        proc_names = ", ".join([p.get("procedure", "") for p in procedures])
        
        return {
            "denial_reason_identified": "Coverage determination requires additional documentation",
            "appeal_letter": f"To Whom It May Concern,\n\nWe are writing to appeal the denial of the claim for {proc_names}. The procedure was medically necessary based on the patient's clinical presentation. Please find attached the operative report and physician attestation supporting the medical necessity of this procedure.\n\nSincerely,\nBilling Department",
            "key_evidence_cited": ["Operative report", "Physician attestation", "H&P documentation"],
            "additional_docs_needed": ["Prior authorization (if applicable)", "Peer-to-peer review request"],
            "success_probability": "Medium"
        }

    # ============ ORCHESTRATED PIPELINE ============
    def run_pipeline(self, discharge_summary: str, claim_metadata: Dict,
                     ai_service, denial_letter: Optional[str] = None) -> Dict[str, Any]:
        """Full RCM pipeline execution."""
        print("\n[RCM] Starting Revenue Cycle Management Pipeline...")
        
        result = {
            "timestamp": datetime.now().isoformat(),
            "claim_id": claim_metadata.get("claim_id", "AUTO-GENERATED")
        }
        
        # Step 1: CRF Code Extraction
        print("[RCM] Step 1: CRF Code Extraction from Discharge Summary...")
        extracted = self.crf_code_extractor(discharge_summary)
        extracted.update({
            "pre_authorization": claim_metadata.get("pre_authorization", False),
            "documentation": claim_metadata.get("documentation", [])
        })
        result["extraction"] = extracted
        
        # Step 2: Isolation Forest Audit
        print("[RCM] Step 2: Isolation Forest Anomaly Detection...")
        audit = self.isolation_forest_auditor(extracted)
        result["audit"] = audit
        
        # Step 3: Decision Tree Rule Validation
        print("[RCM] Step 3: Decision Tree TPA Rule Validation...")
        tpa_name = claim_metadata.get("tpa_name", "Generic TPA")
        rules = self.decision_tree_rules(extracted, tpa_name)
        result["rule_validation"] = rules
        
        # Step 4: Appeal Drafting (if denial letter provided)
        if denial_letter:
            print("[RCM] Step 4: Gemini Appeal Letter Drafting...")
            clinical_evidence = claim_metadata.get("clinical_evidence", "Patient presented with typical symptoms warranting procedure.")
            appeal = self.draft_appeal_gemini(denial_letter, extracted, clinical_evidence, ai_service)
            result["appeal"] = appeal
        
        # Final Recommendation
        if rules["adjudication"] == "APPROVED_FOR_SUBMISSION" and audit["status"] == "CLEAN":
            result["recommendation"] = "SUBMIT_CLAIM"
        elif audit["status"] == "FLAGGED_FOR_REVIEW":
            result["recommendation"] = "MANUAL_REVIEW_REQUIRED"
        else:
            result["recommendation"] = "ADDRESS_VIOLATIONS_FIRST"
        
        return result


if __name__ == "__main__":
    pipeline = RCMPipeline()
    
    # Test CRF extraction
    sample_note = """
    Discharge Summary
    Patient underwent laparoscopic appendectomy for acute appendicitis.
    Diagnosis: Acute appendicitis with peritonitis.
    Length of Stay: 3 days.
    Total Charges: $18,500.
    """
    
    result = pipeline.crf_code_extractor(sample_note)
    print(json.dumps(result, indent=2))
