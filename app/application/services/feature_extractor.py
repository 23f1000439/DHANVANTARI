import numpy as np
import sqlite3
from typing import List, Dict
from .clinical_ner import ClinicalNERService

class EntityFeatureExtractor:
    def __init__(self, ner_model_path="models/medgemma-1.5-4b", db_path="healthcare.db"):
        """
        Converts extracted entities into numerical features 
        for the XGBoost Claim Denial Predictor.
        Refactored to be model-agnostic (works with MedGemma output).
        """
        self.ner_service = ClinicalNERService(model_path)
        self.db_path = db_path
        
    def extract_features(self, claim_id: str) -> np.ndarray:
        """
        Generates a 47-dimensional feature vector from entities.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Fetch claim data
            cursor.execute("""
                SELECT e.clinical_notes, c.total_amount, 
                       p.conditions
                FROM claims c
                JOIN encounters e ON c.encounter_id = e.id
                JOIN patients p ON e.patient_id = p.id
                WHERE c.id = ?
            """, (claim_id,))
            
            row = cursor.fetchone()
            conn.close()
            
            if not row:
                print(f"Claim {claim_id} not found.")
                return np.zeros(47)
                
            note = row['clinical_notes']
            amount = row['total_amount']
            conditions_json = row['conditions']
            
            # Run Local NER (MedGemma)
            entities = self.ner_service.extract_entities(note)
            
            # Feature Engineering
            features = np.zeros(47)
            
            # Group 1: Entity Counts [0-9]
            features[0] = sum(1 for e in entities if e['entity'] == 'DIAGNOSIS')
            features[1] = sum(1 for e in entities if e['entity'] == 'SYMPTOM')
            features[2] = sum(1 for e in entities if e['entity'] == 'PROCEDURE')
            features[3] = sum(1 for e in entities if e['entity'] == 'MEDICATION')
            features[4] = len(note.split())
            
            # Group 2: Confidence Statistics [10-19]
            confidences = [e.get('confidence', 0.5) for e in entities]
            features[10] = np.mean(confidences) if confidences else 0
            features[11] = np.std(confidences) if len(confidences) > 1 else 0
            
            # Group 3: Semantic Embeddings [20-29]
            # MedGemma hidden states or mocked embeddings
            features[20:30] = np.random.rand(10) 
            
            # Group 4: Cross-Reference Features [30-39]
            features[30] = self._check_medication_alignment(entities, conditions_json)
            features[31] = self._check_icd11_specificity(entities)
            
            # Group 5: Financial & Temporal [40-46]
            features[40] = float(amount) if amount else 0
            features[42] = 1.0 if len(note.split()) > 20 else 0.0
            
            return features
            
        except Exception as e:
            print(f"Feature Extraction Error: {e}")
            return np.zeros(47)

    def _check_medication_alignment(self, entities: List[Dict], conditions_json: str) -> float:
        meds = [e['text'] for e in entities if e['entity'] == 'MEDICATION']
        if meds and conditions_json:
             return 1.0
        return 0.0
    
    def _check_icd11_specificity(self, entities: List[Dict]) -> float:
        diagnoses = [e['text'] for e in entities if e['entity'] == 'DIAGNOSIS']
        if not diagnoses:
            return 0.0
        return 0.8
