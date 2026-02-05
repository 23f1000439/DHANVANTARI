import time
import json
import sqlite3
from typing import List, Dict, Any

class LocalImagingTriage:
    def __init__(self, db_path="healthcare.db"):
        """
        Simulates the Edge AI component running MedGemma-1.5-4b.
        """
        self.db_path = db_path
        print("LocalImagingTriage initialized (MedGemma Mock).")

    def triage_scan(self, feature_tags: List[str]) -> Dict[str, Any]:
        """
        Stage 1: Local Triage.
        Returns a classification and latency metric.
        """
        start_time = time.time()
        
        # 1. Construct the prompt (Simulated)
        prompt = f"Medical Triage Task. Features: {', '.join(feature_tags)}. Priority?"
        
        # 2. Local LLM Inference (Mocked Logic)
        # In real life: response = local_engine.generate(prompt)
        response = self._mock_medgemma_inference(feature_tags)
        
        latency_ms = (time.time() - start_time) * 1000
        
        # 3. Log to Audit Trail (Governance)
        self._log_audit_event("medgemma_triage", f"Tags: {feature_tags} -> {response}", latency_ms)
        
        return {
            "classification": response,
            "latency_ms": round(latency_ms, 2),
            "model_version": "medgemma-1.5-4b-quantized"
        }

    def _mock_medgemma_inference(self, tags: List[str]) -> str:
        """
        Heuristic mock of MedGemma's reasoning.
        """
        urgent_keywords = [
            "pneumothorax", "hemorrhage", "fracture", "mass", "opacity", 
            "effusion", "intracranial", "lesion", "obstruction", "midline shift"
        ]
        
        # Check for urgent tags, but exclude if preceded by "no", "absent", "clear"
        is_urgent = False
        for tag in tags:
            tag_lower = tag.lower()
            if any(k in tag_lower for k in urgent_keywords):
                # Negation check
                if not any(neg in tag_lower for neg in ["no ", "absent", "clear", "normal"]):
                    is_urgent = True
                    break
        
        if is_urgent:
            return "URGENT_ABNORMAL"
        return "NORMAL_ROUTINE"

    def _log_audit_event(self, action: str, details: str, latency: float):
        """
        Logs the edge decision for drift detection later.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO audit_logs (agent_name, action, details, timestamp)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, ("LocalMedGemma", action, f"{details} [Latency: {latency:.2f}ms]"))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Audit Log Failed: {e}")

if __name__ == "__main__":
    triage = LocalImagingTriage()
    tags = ["clear lung fields", "cardiac shadow normal"]
    print(triage.triage_scan(tags))
    
    tags_urgent = ["large right-sided pneumothorax", "midline shift"]
    print(triage.triage_scan(tags_urgent))
