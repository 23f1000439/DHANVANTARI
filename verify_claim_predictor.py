import os
import json
import sys

# Ensure app is in path
sys.path.append(os.getcwd())

from app.application.agents.admin.billing import BillingAgent

def test_claim_denial_flow():
    print("Initializing Billing Agent...")
    agent = BillingAgent()
    
    # Mock Data
    mock_claim = {
        "claim_id": "CLM-2026-001",
        "total_amount": 7500.00, # High amount to trigger ML risk
        "codes": ["ICD-11-X", "CPT-99214"],
        "prior_auth": False
    }
    
    mock_context = {
        "clinical_notes": "Patient presented with mild symptoms. No evidence of severe complications justifying high-level coding."
    }
    
    print("\n--- Testing High Risk Claim ---")
    response_json = agent.generate_response(json.dumps(mock_claim), "test_conv_1", mock_context)
    
    try:
        response = json.loads(response_json)
        print("Response Parsed Successfully:")
        print(json.dumps(response, indent=2))
        
        if response.get("denial_probability") > 0.5:
            print("\n✅ Verification Passed: High risk claim correctly flagged.")
        else:
            print("\n❌ Verification Warning: Claim should have been high risk (check mock logic).")
            
        if "clinical_analysis" in response:
             print("✅ Verification Passed: Enhanced Clinical Analysis present.")
        else:
             print("❌ Verification Failed: Missing Clinical Analysis.")
             
    except Exception as e:
        print(f"\n❌ Verification Failed: Invalid JSON response. {response_json}")
        print(e)

if __name__ == "__main__":
    test_claim_denial_flow()
