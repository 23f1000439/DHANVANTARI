"""
Dhanvantr.ai Central Orchestrator
The "Brain" that routes tasks between Limbs (ML) and Specialist (MedGemma).
"""
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import all pipelines
from .rag_pipeline import HybridSearchRAG
from .digitalizer_pipeline import ClinicalSlipDigitalizer
from .risk_stratification_pipeline import BedsideRiskStratifier
from .dermatology_pipeline import DermatologyPipeline
from .chronic_disease_pipeline import ChronicDiseasePipeline
from .rcm_pipeline import RCMPipeline
from .ed_triage_pipeline import EDTriagePipeline
from .radiology_pipeline import RadiologyPipeline

# Import AIService (Gemini 3)
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from ai_service import AIService

class DhanvantariCentralOrchestrator:
    """
    Central Orchestrator for Dhanvantr.ai.
    Routes incoming requests to the appropriate pipeline:
    - GUIDELINE_SEARCH -> HybridSearchRAG
    - PRESCRIPTION_DIGITIZE -> ClinicalSlipDigitalizer
    - BEDSIDE_MONITOR -> BedsideRiskStratifier
    - DERMATOLOGY_ANALYSIS -> DermatologyPipeline
    - CHRONIC_DISEASE_MONITOR -> ChronicDiseasePipeline
    - RCM_CLAIM_PROCESS -> RCMPipeline
    - ED_TRIAGE -> EDTriagePipeline
    """
    
    def __init__(self):
        # Initialize AI Service (The Brain)
        self.ai_service = AIService()
        
        # Initialize Core Pipelines
        self.rag_pipeline = HybridSearchRAG()
        self.digitalizer_pipeline = ClinicalSlipDigitalizer()
        self.risk_pipeline = BedsideRiskStratifier()
        
        # Initialize New End-to-End Pipelines
        self.dermatology_pipeline = DermatologyPipeline()
        self.chronic_disease_pipeline = ChronicDiseasePipeline()
        self.rcm_pipeline = RCMPipeline()
        self.ed_triage_pipeline = EDTriagePipeline()
        self.radiology_pipeline = RadiologyPipeline()
        
        # Track current thinking level
        self.current_thinking_level = "LOW"
        
        print("🧠 DhanvantariCentralOrchestrator initialized with 8 pipelines.")

    def set_thinking_level(self, status: str):
        """
        Dynamically toggle Gemini 3's reasoning depth.
        - EMERGENCY -> HIGH (Maximum reasoning)
        - URGENT -> MEDIUM
        - ROUTINE -> LOW (Cost-saving mode)
        """
        if status in ["EMERGENCY", "CRITICAL"]:
            self.current_thinking_level = "HIGH"
        elif status == "URGENT":
            self.current_thinking_level = "MEDIUM"
        else:
            self.current_thinking_level = "LOW"
        
        print(f"🧠 Thinking Level adjusted to: {self.current_thinking_level}")
        return self.current_thinking_level

    def route_request(self, request_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main routing method. Determines which pipeline to invoke.
        
        Supported request_types:
        - GUIDELINE_SEARCH: RAG pipeline for clinical guidelines
        - PRESCRIPTION_DIGITIZE: OCR + FHIR pipeline
        - BEDSIDE_MONITOR: Risk stratification pipeline
        - TRIAGE_ONLY: Quick triage classification
        - DERMATOLOGY_ANALYSIS: Skin lesion analysis pipeline
        - CHRONIC_DISEASE_MONITOR: RPM wearables monitoring
        - RCM_CLAIM_PROCESS: Revenue cycle claims processing
        - ED_TRIAGE: Emergency department triage
        """
        start_time = datetime.now()
        
        print(f"\n{'='*60}")
        print(f"📍 Central Orchestrator | Request: {request_type}")
        print(f"{'='*60}")
        
        result = {
            "request_type": request_type,
            "timestamp": start_time.isoformat(),
            "thinking_level": self.current_thinking_level,
            "response": None,
            "error": None
        }
        
        try:
            if request_type == "GUIDELINE_SEARCH":
                result["response"] = self._handle_guideline_search(payload)
                
            elif request_type == "PRESCRIPTION_DIGITIZE":
                result["response"] = self._handle_prescription_digitize(payload)
                
            elif request_type == "BEDSIDE_MONITOR":
                result["response"] = self._handle_bedside_monitor(payload)
                
            elif request_type == "TRIAGE_ONLY":
                result["response"] = self._handle_triage_only(payload)
            
            # ========== NEW PIPELINES ==========
            elif request_type == "DERMATOLOGY_ANALYSIS":
                result["response"] = self._handle_dermatology(payload)
                
            elif request_type == "CHRONIC_DISEASE_MONITOR":
                result["response"] = self._handle_chronic_disease(payload)
                
            elif request_type == "RCM_CLAIM_PROCESS":
                result["response"] = self._handle_rcm(payload)
                
            elif request_type == "ED_TRIAGE":
                result["response"] = self._handle_ed_triage(payload)
            
            elif request_type == "RADIOLOGY_ANALYSIS":
                result["response"] = self._handle_radiology(payload)
                
            else:
                result["error"] = f"Unknown request type: {request_type}"
        
        except Exception as e:
            result["error"] = str(e)
        
        # Calculate latency
        end_time = datetime.now()
        result["latency_ms"] = (end_time - start_time).total_seconds() * 1000
        
        # Format final output
        return self._format_output(result)

    def _handle_guideline_search(self, payload: Dict) -> Dict:
        """Route to RAG Pipeline."""
        query = payload.get("query", "")
        return self.rag_pipeline.run_pipeline(query, self.ai_service)

    def _handle_prescription_digitize(self, payload: Dict) -> Dict:
        """Route to Digitalizer Pipeline."""
        prescription = payload.get("prescription_text", "")
        patient_weight = payload.get("patient_weight_kg")
        return self.digitalizer_pipeline.run_pipeline(prescription, self.ai_service, patient_weight)

    def _handle_bedside_monitor(self, payload: Dict) -> Dict:
        """Route to Risk Stratification Pipeline."""
        vitals = payload.get("vitals", {})
        labs = payload.get("labs", {})
        chief_complaint = payload.get("chief_complaint", "")
        
        # Pre-triage to set thinking level
        triage = self.risk_pipeline.triage_gate_nb(chief_complaint)
        self.set_thinking_level(triage["status"])
        
        return self.risk_pipeline.run_pipeline(vitals, labs, chief_complaint, self.ai_service)

    def _handle_triage_only(self, payload: Dict) -> Dict:
        """Quick triage without full pipeline."""
        text = payload.get("text", "")
        triage = self.risk_pipeline.triage_gate_nb(text)
        self.set_thinking_level(triage["status"])
        return triage

    # ========== NEW PIPELINE HANDLERS ==========
    
    def _handle_dermatology(self, payload: Dict) -> Dict:
        """Route to Dermatology Pipeline."""
        patient_id = payload.get("patient_id", "DERM-001")
        image_data = payload.get("image_data")
        description = payload.get("description", "")
        demographics = payload.get("demographics", {})
        
        return self.dermatology_pipeline.run_pipeline(
            patient_id, image_data, description, demographics, self.ai_service
        )
    
    def _handle_chronic_disease(self, payload: Dict) -> Dict:
        """Route to Chronic Disease Pipeline."""
        patient_id = payload.get("patient_id", "RPM-001")
        wearable_data = payload.get("wearable_data", [])
        patient_profile = payload.get("patient_profile", {})
        lab_report = payload.get("lab_report", {})
        language = payload.get("language", "English")
        
        return self.chronic_disease_pipeline.run_pipeline(
            patient_id, wearable_data, patient_profile, lab_report, self.ai_service, language
        )
    
    def _handle_rcm(self, payload: Dict) -> Dict:
        """Route to RCM Pipeline."""
        discharge_summary = payload.get("discharge_summary", "")
        claim_metadata = payload.get("claim_metadata", {})
        denial_letter = payload.get("denial_letter")
        
        return self.rcm_pipeline.run_pipeline(
            discharge_summary, claim_metadata, self.ai_service, denial_letter
        )
    
    def _handle_ed_triage(self, payload: Dict) -> Dict:
        """Route to ED Triage Pipeline."""
        patient_id = payload.get("patient_id", "ED-001")
        vitals = payload.get("vitals", {})
        chief_complaint = payload.get("chief_complaint", "")
        patient_data = payload.get("patient_data", {})
        scan_data = payload.get("scan_data")
        scan_type = payload.get("scan_type", "CT")
        
        # Set thinking level based on vitals
        esi_preview = self.ed_triage_pipeline.naive_bayes_esi(vitals, chief_complaint)
        if esi_preview["esi_level"] <= 2:
            self.set_thinking_level("EMERGENCY")
        
        return self.ed_triage_pipeline.run_pipeline(
            patient_id, vitals, chief_complaint, patient_data, scan_data, scan_type, self.ai_service
        )

    def _handle_radiology(self, payload: Dict) -> Dict:
        """Route to Radiology Pipeline."""
        study_id = payload.get("study_id", "RAD-001")
        image_data = payload.get("image_data")
        modality = payload.get("modality", "X-Ray")
        referral_notes = payload.get("referral_notes", "")
        patient_info = payload.get("patient_info", {})
        clinical_history = payload.get("clinical_history")
        
        # Set thinking level based on triage
        triage_preview = self.radiology_pipeline.triage_referral_nb(referral_notes)
        if triage_preview["priority"] == "STAT":
            self.set_thinking_level("EMERGENCY")
        
        return self.radiology_pipeline.run_pipeline(
            study_id, image_data, modality, referral_notes, patient_info, 
            self.ai_service, clinical_history
        )

    def _format_output(self, result: Dict) -> Dict:
        """
        Standardize output format per operational protocols.
        """
        response = result.get("response", {})
        
        # Determine emergency status
        if "final_alert" in response:
            emergency_status = response["final_alert"].get("emergency_status", "Stable")
        elif "triage" in response:
            emergency_status = response["triage"].get("status", "ROUTINE")
        elif "status" in response:
            # TRIAGE_ONLY returns status directly
            emergency_status = response.get("status", "ROUTINE")
        else:
            emergency_status = "Stable"
        
        # Extract clinical summary
        if "final_alert" in response:
            clinical_summary = response["final_alert"].get("clinical_summary", "")
        elif "response" in response and isinstance(response["response"], dict):
            clinical_summary = response["response"].get("answer", "")
        elif "validation" in response:
            clinical_summary = f"Prescription processed. Status: {response['validation'].get('validation_status', 'Unknown')}"
        else:
            clinical_summary = "Processing complete."
        
        # Extract action plan
        if "final_alert" in response:
            action_plan = response["final_alert"].get("action_plan", [])
        elif "triage" in response:
            action_plan = [response["triage"].get("recommended_action", "")]
        else:
            action_plan = []
        
        # Evidence grade
        if "final_alert" in response:
            evidence_grade = response["final_alert"].get("evidence_grade", "N/A")
        elif "response" in response and isinstance(response["response"], dict):
            evidence_grade = response["response"].get("evidence_grade", "N/A")
        else:
            evidence_grade = "N/A"
        
        return {
            "emergency_status": emergency_status,
            "clinical_summary": clinical_summary,
            "action_plan": action_plan,
            "evidence_grade": evidence_grade,
            "thinking_level": result.get("thinking_level"),
            "latency_ms": result.get("latency_ms"),
            "raw_response": response,
            "error": result.get("error")
        }

    # ============ THOUGHT SIGNATURE REFLECTION ============
    def reflect_on_result(self, result: Dict) -> str:
        """
        Maintains 'Thought Signature' across tool calls.
        Reflects on how the result changes the patient's risk profile.
        """
        emergency_status = result.get("emergency_status", "Stable")
        
        if emergency_status in ["EMERGENCY", "Critical", "CRITICAL"]:
            reflection = "⚠️ Thought Signature: Patient risk elevated. All subsequent decisions must prioritize life-critical pathways."
        elif emergency_status in ["URGENT", "WARNING"]:
            reflection = "⚠️ Thought Signature: Patient requires prioritized attention. Monitor closely."
        else:
            reflection = "✅ Thought Signature: Patient stable. Standard care pathway appropriate."
        
        print(reflection)
        return reflection


if __name__ == "__main__":
    orchestrator = DhanvantariCentralOrchestrator()
    
    # Test 1: Guideline Search
    print("\n--- Test 1: Guideline Search ---")
    result1 = orchestrator.route_request("GUIDELINE_SEARCH", {"query": "sepsis management protocol"})
    print(json.dumps(result1, indent=2, default=str))
    
    # Test 2: Triage Only
    print("\n--- Test 2: Triage Only ---")
    result2 = orchestrator.route_request("TRIAGE_ONLY", {"text": "Patient has chest pain and difficulty breathing"})
    print(json.dumps(result2, indent=2, default=str))
