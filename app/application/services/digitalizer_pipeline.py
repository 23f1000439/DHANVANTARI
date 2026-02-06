"""
Pipeline 2: Clinical Slip Digitalizer
OCR Extraction -> Drug Catalog Matching -> MedGemma Validation -> Gemini 3 FHIR Bundle
"""
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

class ClinicalSlipDigitalizer:
    def __init__(self):
        # Mock drug catalog (In production: RxNorm API or CIMS database)
        self.drug_catalog = self._init_drug_catalog()
        print("ClinicalSlipDigitalizer initialized with mock drug catalog.")

    def _init_drug_catalog(self) -> Dict[str, Dict]:
        """Initialize mock drug catalog for normalization."""
        return {
            "amoxicillin": {"rxnorm_code": "723", "standard_name": "Amoxicillin", "forms": ["250mg", "500mg", "875mg"]},
            "metformin": {"rxnorm_code": "6809", "standard_name": "Metformin", "forms": ["500mg", "850mg", "1000mg"]},
            "lisinopril": {"rxnorm_code": "29046", "standard_name": "Lisinopril", "forms": ["5mg", "10mg", "20mg", "40mg"]},
            "atorvastatin": {"rxnorm_code": "83367", "standard_name": "Atorvastatin", "forms": ["10mg", "20mg", "40mg", "80mg"]},
            "omeprazole": {"rxnorm_code": "7646", "standard_name": "Omeprazole", "forms": ["20mg", "40mg"]},
            "paracetamol": {"rxnorm_code": "161", "standard_name": "Acetaminophen", "forms": ["325mg", "500mg", "650mg"]},
            "azithromycin": {"rxnorm_code": "18631", "standard_name": "Azithromycin", "forms": ["250mg", "500mg"]},
        }

    # ============ LIMB 1: OCR Extraction (Mocked) ============
    def extract_text_ocr(self, image_or_text: Any) -> Dict[str, Any]:
        """
        Extracts text from prescription image.
        Mocked: Accepts text directly for demo, simulates OCR errors.
        """
        # In production: Use PaddleOCR or Tesseract
        if isinstance(image_or_text, str):
            raw_text = image_or_text
        else:
            # Simulate OCR on image (mock)
            raw_text = "Rx: Amox 500mg TID x 7 days. Metformin 850 BD."
        
        # Simulate common OCR errors
        ocr_result = {
            "raw_text": raw_text,
            "confidence": 0.85,
            "extracted_items": self._parse_prescription_text(raw_text),
            "ocr_engine": "PaddleOCR (Mocked)"
        }
        return ocr_result

    def _parse_prescription_text(self, text: str) -> List[Dict]:
        """Simple regex-based prescription parsing."""
        items = []
        # Pattern: Drug Name + Dose + Frequency
        patterns = [
            r"(amox(?:icillin)?)\s*(\d+)\s*(?:mg)?\s*(tid|bid|od|qid)?",
            r"(metformin)\s*(\d+)\s*(?:mg)?\s*(bd|od)?",
            r"(lisinopril)\s*(\d+)\s*(?:mg)?\s*(od)?",
            r"(paracetamol|pcm)\s*(\d+)\s*(?:mg)?\s*(sos|tid|qid)?",
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            match = re.search(pattern, text_lower)
            if match:
                drug = match.group(1)
                dose = match.group(2) + "mg"
                freq = match.group(3) if match.lastindex >= 3 and match.group(3) else "OD"
                items.append({
                    "drug_raw": drug,
                    "dose_raw": dose,
                    "frequency_raw": freq.upper() if freq else "OD"
                })
        
        return items

    # ============ LIMB 2: Drug Catalog Matching (Naive Bayes Mock) ============
    def match_drug_catalog(self, ocr_items: List[Dict]) -> List[Dict]:
        """
        Probabilistic matching to normalize drug names.
        Mocked Naive Bayes: Simple string similarity.
        """
        matched = []
        for item in ocr_items:
            drug_raw = item['drug_raw'].lower()
            
            best_match = None
            best_score = 0
            
            for catalog_key, catalog_entry in self.drug_catalog.items():
                # Simple similarity (Mocked NB probability)
                if drug_raw in catalog_key or catalog_key in drug_raw:
                    score = 0.95
                elif drug_raw[:3] == catalog_key[:3]:
                    score = 0.7
                else:
                    score = 0.1
                
                if score > best_score:
                    best_score = score
                    best_match = catalog_entry
            
            if best_match and best_score > 0.5:
                matched.append({
                    **item,
                    "normalized_drug": best_match['standard_name'],
                    "rxnorm_code": best_match['rxnorm_code'],
                    "match_confidence": best_score,
                    "valid_forms": best_match['forms']
                })
            else:
                matched.append({
                    **item,
                    "normalized_drug": item['drug_raw'].title(),
                    "rxnorm_code": "UNKNOWN",
                    "match_confidence": 0.0,
                    "warning": "Drug not found in catalog"
                })
        
        return matched

    # ============ SPECIALIST: MedGemma Prescription Validation ============
    def validate_prescription(self, matched_items: List[Dict], patient_weight_kg: Optional[float] = None) -> Dict:
        """
        MedGemma validates dose appropriateness.
        Mocked: Checks if dose is within standard forms.
        """
        validations = []
        has_errors = False
        
        for item in matched_items:
            dose = item.get('dose_raw', '')
            valid_forms = item.get('valid_forms', [])
            
            if dose in valid_forms:
                validation_status = "VALID"
            elif item.get('rxnorm_code') == 'UNKNOWN':
                validation_status = "UNVERIFIED"
                has_errors = True
            else:
                validation_status = "DOSE_CHECK_REQUIRED"
                has_errors = True
            
            validations.append({
                "drug": item.get('normalized_drug'),
                "dose": dose,
                "status": validation_status,
                "medgemma_note": f"Standard forms: {valid_forms}" if valid_forms else "Unknown drug"
            })
        
        return {
            "validation_status": "PASSED" if not has_errors else "REVIEW_REQUIRED",
            "items": validations,
            "validator": "MedGemma (Mocked)"
        }

    # ============ BRAIN: Gemini 3 FHIR Bundle Generation ============
    def generate_fhir_bundle(self, validated_data: Dict, ai_service) -> Dict:
        """
        Gemini 3 generates a FHIR-compliant MedicationRequest bundle.
        """
        items = validated_data.get('items', [])
        
        prompt = f"""
        ROLE: Healthcare Interoperability Specialist.
        
        VALIDATED PRESCRIPTION DATA:
        {json.dumps(items, indent=2)}
        
        TASK:
        Generate a FHIR R4 MedicationRequest Bundle in JSON format.
        
        REQUIREMENTS:
        1. Each medication becomes one MedicationRequest resource.
        2. Include resourceType, id, status, intent, medicationCodeableConcept, dosageInstruction.
        3. Use standard FHIR coding (RxNorm where available).
        
        OUTPUT: Valid FHIR Bundle JSON only.
        """
        
        try:
            response = ai_service.pro_model.generate_content(
                prompt,
                generation_config=ai_service.analytical_config
            )
            try:
                return json.loads(response.text)
            except:
                # Return a basic FHIR structure if parsing fails
                return self._generate_basic_fhir(items)
        except Exception as e:
            print(f"FHIR Generation Error: {e}")
            return self._generate_basic_fhir(items)

    def _generate_basic_fhir(self, items: List[Dict]) -> Dict:
        """Fallback FHIR bundle generator."""
        entries = []
        for i, item in enumerate(items):
            entries.append({
                "resource": {
                    "resourceType": "MedicationRequest",
                    "id": f"med-req-{i+1}",
                    "status": "active",
                    "intent": "order",
                    "medicationCodeableConcept": {
                        "coding": [{
                            "system": "http://www.nlm.nih.gov/research/umls/rxnorm",
                            "code": item.get('rxnorm_code', 'UNKNOWN'),
                            "display": item.get('drug', 'Unknown Drug')
                        }]
                    },
                    "dosageInstruction": [{
                        "text": f"{item.get('dose', '')} {item.get('frequency', 'OD')}"
                    }]
                }
            })
        
        return {
            "resourceType": "Bundle",
            "type": "collection",
            "entry": entries
        }

    # ============ ORCHESTRATED PIPELINE ============
    def run_pipeline(self, prescription_input: Any, ai_service, patient_weight: Optional[float] = None) -> Dict:
        """Full digitalizer pipeline execution."""
        print("[DIGITALIZER] Starting Clinical Slip Digitalizer Pipeline...")
        
        # Step 1: Limb - OCR Extraction
        print("[DIGITALIZER] Step 1: OCR Extraction...")
        ocr_result = self.extract_text_ocr(prescription_input)
        
        # Step 2: Limb - Drug Catalog Matching
        print("[DIGITALIZER] Step 2: Drug Catalog Matching...")
        matched = self.match_drug_catalog(ocr_result['extracted_items'])
        
        # Step 3: Specialist - MedGemma Validation
        print("[DIGITALIZER] Step 3: MedGemma Validation...")
        validated = self.validate_prescription(matched, patient_weight)
        
        # Step 4: Brain - FHIR Bundle Generation
        print("[DIGITALIZER] Step 4: Gemini 3 FHIR Generation...")
        fhir_bundle = self.generate_fhir_bundle(validated, ai_service)
        
        return {
            "ocr_raw": ocr_result['raw_text'],
            "ocr_confidence": ocr_result['confidence'],
            "matched_drugs": matched,
            "validation": validated,
            "fhir_bundle": fhir_bundle
        }

if __name__ == "__main__":
    digitalizer = ClinicalSlipDigitalizer()
    result = digitalizer.extract_text_ocr("Rx: Amox 500mg TID x 7 days. Metformin 850 BD.")
    print(json.dumps(result, indent=2))
