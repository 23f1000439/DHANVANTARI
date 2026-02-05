from typing import List, Dict, Any
import json
import os
import sys

# Ensure root is in path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from app.application.services.clinical_ner import ClinicalNERService
from ai_service import AIService

class AutonomousICD11Coder:
    def __init__(self, ner_model_path="models/medgemma-1.5-4b"):
        self.ner_service = ClinicalNERService(model_path=ner_model_path)
        self.ai_service = AIService()

    def generate_codes(self, clinical_note: str, encounter_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrates the coding pipeline:
        1. Extract entities using Local LLM (MedGemma)
        2. Enhance/Reason using Gemini (AIService)
        """
        # Stage 1: Local NER
        print("Stage 1: MedGemma extracting entities...")
        entities = self.ner_service.extract_entities(clinical_note)
        
        # Stage 2: Reasoning
        print("Stage 2: Gemini Reasoning...")
        reasoning_result = self.ai_service.generate_icd11_with_reasoning(
            entities, clinical_note, encounter_context
        )
        
        return {
            "entities": entities,
            "coding_result": reasoning_result
        }

if __name__ == "__main__":
    coder = AutonomousICD11Coder()
    note = "Patient has Type 2 Diabetes and complains of polyuria."
    context = {"patient_age": 45}
    result = coder.generate_codes(note, context)
    print(json.dumps(result, indent=2))
