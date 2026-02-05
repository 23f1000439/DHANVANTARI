import json
import sqlite3
from typing import Dict, Any, List
from .imaging_triage import LocalImagingTriage
# Import AIService cleanly
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from ai_service import AIService

class ImagingOrchestrator:
    def __init__(self, db_path="healthcare.db"):
        self.local_triage = LocalImagingTriage(db_path)
        self.ai_service = AIService()
        self.db_path = db_path
    
    def process_scan(self, patient_id: str, image_data: Any, feature_tags: List[str], clinical_notes: str) -> Dict[str, Any]:
        """
        Orchestrates the 2-Stage Imaging Pipeline.
        """
        results = {
            "stage_1_triage": None,
            "stage_2_report": None,
            "final_status": "PENDING"
        }
        
        # --- Stage 1: Edge Triage (MedGemma) ---
        print("Orchestrator: Executing Stage 1 (Local Triage)...")
        triage_result = self.local_triage.triage_scan(feature_tags)
        results["stage_1_triage"] = triage_result
        
        # --- Decision Point ---
        if triage_result["classification"] == "URGENT_ABNORMAL":
            print("Orchestrator: Urgent Flag Detected. Proceeding to Stage 2 (Cloud)...")
            
            # Context Fetching (Simulated)
            context = {
                "notes": clinical_notes,
                "history": self._fetch_patient_history(patient_id)
            }
            
            # --- Stage 2: Cloud Reporting (Gemini 3) ---
            report = self.ai_service.generate_preliminary_report(
                image_data, 
                triage_result["classification"], 
                context
            )
            results["stage_2_report"] = report
            results["final_status"] = "URGENT_REPORT_READY"
            
            # Governance: Discordance Check
            self._check_discordance(triage_result, report, patient_id)
            
        else:
            print("Orchestrator: Scan Normal. Skipping Cloud Stage.")
            results["final_status"] = "NORMAL_ROUTINE"
            
        # --- Persistence ---
        self._save_results(patient_id, results)
        
        return results

    def _fetch_patient_history(self, patient_id: str) -> str:
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            row = cursor.execute("SELECT conditions FROM patients WHERE id = ?", (patient_id,)).fetchone()
            conn.close()
            if row:
                return row['conditions']
        except Exception:
            pass
        return "Unknown History"

    def _check_discordance(self, triage: Dict, report: Dict, patient_id: str):
        """
        Checks if Cloud Model disagrees with Edge Model (Drift Detection).
        """
        edge_status = triage["classification"] # URGENT_ABNORMAL
        cloud_priority = report.get("priority", "").upper() # STAT / URGENT / ROUTINE
        
        discordance = False
        if edge_status == "URGENT_ABNORMAL" and "ROUTINE" in cloud_priority:
            discordance = True
            print(f"⚠️ Discordance Detected for Patient {patient_id}: Edge=Urgent, Cloud=Routine")
            # Log to audit_logs (omitted for brevity, assume shared logger)

    def _save_results(self, patient_id: str, results: Dict):
        """
        Updates the encounter record with the AI summary.
        """
        # simplified: just print or update a mock encounter
        pass

if __name__ == "__main__":
    orch = ImagingOrchestrator()
    # Test URGENT flow
    print(orch.process_scan("p1", None, ["pneumothorax", "haze"], "Patient complaining of chest pain."))
