"""
Verification Script for Central Orchestrator Pipelines
Tests: RAG, Digitalizer, Risk Stratification
"""
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.application.services.central_orchestrator import DhanvantariCentralOrchestrator

def test_guideline_rag():
    print("\n" + "="*60)
    print("TEST 1: Grounded Guideline RAG Pipeline")
    print("="*60)
    
    orchestrator = DhanvantariCentralOrchestrator()
    
    result = orchestrator.route_request("GUIDELINE_SEARCH", {
        "query": "What is the latest sepsis management protocol?"
    })
    
    print(f"\nQuery: What is the latest sepsis management protocol?")
    print(f"Emergency Status: {result.get('emergency_status')}")
    print(f"Clinical Summary: {result.get('clinical_summary')[:200]}..." if result.get('clinical_summary') and len(result.get('clinical_summary')) > 200 else f"Clinical Summary: {result.get('clinical_summary')}")
    print(f"Evidence Grade: {result.get('evidence_grade')}")
    print(f"Latency: {result.get('latency_ms'):.2f}ms")
    
    if result.get('clinical_summary') and 'sepsis' in result.get('clinical_summary', '').lower():
        print("✅ TEST PASSED: RAG returned relevant sepsis protocol.")
        return True
    else:
        print("❌ TEST FAILED: RAG did not return expected content.")
        return False

def test_prescription_digitalizer():
    print("\n" + "="*60)
    print("TEST 2: Clinical Slip Digitalizer Pipeline")
    print("="*60)
    
    orchestrator = DhanvantariCentralOrchestrator()
    
    result = orchestrator.route_request("PRESCRIPTION_DIGITIZE", {
        "prescription_text": "Rx: Amox 500mg TID x 7 days. Metformin 850 BD."
    })
    
    print(f"\nInput: Rx: Amox 500mg TID x 7 days. Metformin 850 BD.")
    print(f"Latency: {result.get('latency_ms'):.2f}ms")
    
    raw = result.get('raw_response', {})
    matched_drugs = raw.get('matched_drugs', [])
    
    print(f"Matched Drugs: {len(matched_drugs)}")
    for drug in matched_drugs:
        print(f"  - {drug.get('normalized_drug')}: {drug.get('dose_raw')} (Confidence: {drug.get('match_confidence', 0)*100:.0f}%)")
    
    fhir = raw.get('fhir_bundle', {})
    print(f"FHIR Bundle Generated: {fhir.get('resourceType') == 'Bundle'}")
    
    if len(matched_drugs) >= 2 and fhir.get('resourceType') == 'Bundle':
        print("✅ TEST PASSED: Digitizer matched drugs and generated FHIR bundle.")
        return True
    else:
        print("❌ TEST FAILED: Digitizer did not match drugs correctly.")
        return False

def test_bedside_risk_stratification():
    print("\n" + "="*60)
    print("TEST 3: Bedside Risk Stratification Pipeline")
    print("="*60)
    
    orchestrator = DhanvantariCentralOrchestrator()
    
    # Critical case: Sepsis
    vitals = {
        "heart_rate": 120,
        "bp_systolic": 85,
        "bp_diastolic": 50,
        "spo2": 88,
        "temperature": 39.5,
        "respiratory_rate": 28
    }
    labs = {
        "lactate": 5.0,
        "wbc": 18.0,
        "bands_percent": 15,
        "creatinine": 2.5
    }
    
    result = orchestrator.route_request("BEDSIDE_MONITOR", {
        "vitals": vitals,
        "labs": labs,
        "chief_complaint": "Patient with fever, hypotension, and confusion - sepsis suspected"
    })
    
    print(f"\nInput Vitals: HR={vitals['heart_rate']}, BP={vitals['bp_systolic']}/{vitals['bp_diastolic']}, SpO2={vitals['spo2']}%")
    print(f"Input Labs: Lactate={labs['lactate']}, WBC={labs['wbc']}, Bands={labs['bands_percent']}%")
    print(f"\nEmergency Status: {result.get('emergency_status')}")
    print(f"Thinking Level Used: {result.get('thinking_level')}")
    print(f"Clinical Summary: {result.get('clinical_summary')}")
    print(f"Action Plan: {result.get('action_plan')}")
    print(f"Latency: {result.get('latency_ms'):.2f}ms")
    
    if result.get('emergency_status') in ['Critical', 'EMERGENCY', 'CRITICAL']:
        print("✅ TEST PASSED: Risk stratifier correctly identified CRITICAL case.")
        return True
    else:
        print("❌ TEST FAILED: Risk stratifier did not flag emergency.")
        return False

def test_triage_only():
    print("\n" + "="*60)
    print("TEST 4: Quick Triage (Bypass Full Pipeline)")
    print("="*60)
    
    orchestrator = DhanvantariCentralOrchestrator()
    
    # Emergency text
    result = orchestrator.route_request("TRIAGE_ONLY", {
        "text": "Patient experiencing chest pain and difficulty breathing"
    })
    
    print(f"\nInput: Patient experiencing chest pain and difficulty breathing")
    print(f"Triage Status: {result.get('emergency_status')}")
    print(f"Thinking Level: {result.get('thinking_level')}")
    
    if result.get('emergency_status') == 'EMERGENCY':
        print("✅ TEST PASSED: Quick triage correctly flagged emergency.")
        return True
    else:
        print("❌ TEST FAILED: Quick triage did not flag emergency.")
        return False

if __name__ == "__main__":
    print("\n" + "#"*60)
    print("# DHANVANTR.AI CENTRAL ORCHESTRATOR VERIFICATION")
    print("#"*60)
    
    results = []
    results.append(("Guideline RAG", test_guideline_rag()))
    results.append(("Prescription Digitalizer", test_prescription_digitalizer()))
    results.append(("Bedside Risk Stratification", test_bedside_risk_stratification()))
    results.append(("Quick Triage", test_triage_only()))
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed.")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Central Orchestrator is operational.")
    else:
        print("\n⚠️ Some tests failed. Review the output above.")
