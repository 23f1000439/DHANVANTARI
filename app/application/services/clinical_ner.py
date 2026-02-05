from typing import List, Dict, Any
import json
import re

class ClinicalNERService:
    def __init__(self, model_path="models/medgemma-1.5-4b-it.Q4KM.gguf"):
        """
        Initializes the Local LLM Service (MedGemma).
        In a real deployment, this would load the GGUF model via llama-cpp-python.
        """
        self.model_path = model_path
        print(f"ClinicalNERService initialized with Local LLM: {model_path} (Simulated)")
        # self.llm = Llama(model_path=model_path, n_ctx=2048) 

    def extract_entities(self, clinical_note: str) -> List[Dict[str, Any]]:
        """
        Extracts entities using a prompt-based approach for MedGemma.
        """
        prompt = f"""
        <start_of_turn>user
        You are an expert Clinical Named Entity Recognition system. 
        Extract all medical entities from the text below.
        
        Target Entity Types: 
        - DIAGNOSIS (e.g., Type 2 Diabetes, Hypertension)
        - SYMPTOM (e.g., polyuria, chest pain)
        - MEDICATION (e.g., Metformin, Lisinopril)
        - PROCEDURE (e.g., X-Ray, Blood Test)

        Return the output as a strictly valid JSON list of objects.
        Format: [{{"text": "entity_name", "entity": "TYPE", "confidence": 0.95}}]

        Clinical Note:
        {clinical_note}
        <end_of_turn>
        <start_of_turn>model
        ```json
        """
        
        # --- SIMULATED LLM GENERATION ---
        # In production: response = self.llm(prompt, stop=["```"], echo=False)
        # Here we mock the intelligence of MedGemma based on the input note.
        
        simulated_response = self._mock_medgemma_inference(clinical_note)
        return simulated_response

    def _mock_medgemma_inference(self, note: str) -> List[Dict[str, Any]]:
        """
        Simulates the output of MedGemma-1.5-4b for the demo.
        It uses heuristic matching but formats it exactly like the LLM output.
        """
        entities = []
        
        # 1. Medications
        med_keywords = ["Metformin", "Lisinopril", "Insulin", "Atorvastatin", "Aspirin"]
        for kw in med_keywords:
            if re.search(re.escape(kw), note, re.IGNORECASE):
                entities.append({"text": kw, "entity": "MEDICATION", "confidence": 0.98})

        # 2. Diagnoses
        diag_keywords = ["Type 2 Diabetes", "Diabetes Mellitus", "Hypertension", "Hyperlipidemia", "Fracture"]
        for kw in diag_keywords:
             if re.search(re.escape(kw), note, re.IGNORECASE):
                entities.append({"text": kw, "entity": "DIAGNOSIS", "confidence": 0.96})

        # 3. Symptoms
        sym_keywords = ["polyuria", "polydipsia", "fatigue", "pain", "swelling", "shortness of breath"]
        for kw in sym_keywords:
             if re.search(re.escape(kw), note, re.IGNORECASE):
                entities.append({"text": kw, "entity": "SYMPTOM", "confidence": 0.92})
        
        # 4. Procedures
        proc_keywords = ["Blood Glucose", "X-Ray", "MRI", "CT Scan"]
        for kw in proc_keywords:
             if re.search(re.escape(kw), note, re.IGNORECASE):
                entities.append({"text": kw, "entity": "PROCEDURE", "confidence": 0.94})

        return entities

if __name__ == "__main__":
    service = ClinicalNERService()
    note = "Patient with Type 2 Diabetes taking Metformin. Complains of fatigue."
    print(json.dumps(service.extract_entities(note), indent=2))
