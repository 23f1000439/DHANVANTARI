
import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.application.services.imaging_orchestrator import ImagingOrchestrator

def test_urgent_flow():
    print("\n--- Testing URGENT Flow (Pneumothorax) ---")
    orch = ImagingOrchestrator()
    
    # Inputs simulating a critical finding
    patient_id = "p1" # Assume exists or ignored by mock
    feature_tags = ["large right-sided pneumothorax", "midline shift", "mediastinal deviation"]
    notes = "Patient arriving via ambulance. SpO2 88%. C/O severe chest pain."
    
    # Run
    result = orch.process_scan(patient_id, None, feature_tags, notes)
    
    # Verify Stage 1
    triage = result["stage_1_triage"]
    print(f"Stage 1 Classification: {triage['classification']}")
    print(f"Stage 1 Latency: {triage['latency_ms']}ms")
    
    if triage['classification'] != "URGENT_ABNORMAL":
        print("❌ FAILED: Stage 1 did not flag urgent case.")
        return
        
    # Verify Stage 2
    report = result["stage_2_report"]
    if report:
        print("\nStage 2 Report Generated:")
        print(f"Impression: {report.get('impression')}")
        print(f"Priority: {report.get('priority')}")
        print("✅ SUCCESS: Full pipeline execution verified.")
    else:
        print("❌ FAILED: Stage 2 report not generated.")

def test_routine_flow():
    print("\n--- Testing ROUTINE Flow (Normal CXR) ---")
    orch = ImagingOrchestrator()
    
    # Inputs simulating normal
    feature_tags = ["clear lung fields", "normal cardiac silhouette", "no effusions"]
    notes = "Routine annual physical."
    
    # Run
    result = orch.process_scan("p1", None, feature_tags, notes)
    
    # Verify
    triage = result["stage_1_triage"]
    print(f"Stage 1 Classification: {triage['classification']}")
    
    if triage['classification'] == "NORMAL_ROUTINE" and result["stage_2_report"] is None:
         print("✅ SUCCESS: Routine case stopped at Edge (Cloud saved).")
    else:
         print(f"❌ FAILED: Routine case escalated incorrectly. Status: {result['final_status']}")

if __name__ == "__main__":
    test_urgent_flow()
    test_routine_flow()
