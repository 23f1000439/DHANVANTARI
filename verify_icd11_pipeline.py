import sys
import os
import json

# Ensure root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.application.services.icd11_coder import AutonomousICD11Coder

def verify_pipeline():
    print("--- Starting ICD-11 Pipeline Verification ---")
    
    # 1. Initialize Coder
    try:
        coder = AutonomousICD11Coder()
        print("✅ AutonomousICD11Coder initialized.")
    except Exception as e:
        print(f"❌ Failed to initialize coder: {e}")
        return

    # 2. Define Test Data
    note = """
    Patient presented with polyuria and polydipsia. 
    Fasting blood glucose 180 mg/dL. 
    Diagnosis: Type 2 DM. 
    Also noted BP 150/95, started on Lisinopril.
    """
    
    context = {
        "patient_age": 55,
        "conditions": ["Hypertension"],
        "medications": ["Lisinopril"]
    }

    # 3. specific test for validation
    print("\n--- Testing Coding Generation ---")
    try:
        result = coder.generate_codes(note, context)
        
        entities = result.get('entities', [])
        print(f"✅ BERT Entities Extracted: {len(entities)}")
        for e in entities:
            print(f"   - {e['entity']}: {e['text']}")
            
        coding_result = result.get('coding_result', {})
        codes = coding_result.get('codes', [])
        
        if codes:
            print(f"✅ Gemini Generated {len(codes)} ICD-11 Codes:")
            for c in codes:
                print(f"   - Code: {c.get('code')}")
                print(f"     Desc: {c.get('description')}")
                print(f"     Conf: {c.get('confidence')}")
                print(f"     Justification: {c.get('justification')}")
        else:
            print("⚠️ No codes generated (check API response).")
            print(f"Reasoning: {coding_result.get('reasoning_summary')}")
            
    except Exception as e:
        print(f"❌ Coding Generation Failed: {e}")

if __name__ == "__main__":
    verify_pipeline()
