import urllib.request
import urllib.error
import json
import time

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def make_request(endpoint, data):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    json_data = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Request Error: {e}")
        return {}

def test_patient_wearable():
    print("\n--- Testing Patient: Wearable Agent ---")
    payload = {
        "query": "My heart rate is 110bpm resting.", 
        "role": "Patient",
        "conversation_id": 1
    }
    data = make_request("/api/agent/query", payload)
    print(f"Agent Selected: {data.get('agent')}")
    print(f"Response: {str(data.get('response'))[:100]}...")

def test_admin_scheduling():
    print("\n--- Testing Admin: Scheduling Agent ---")
    payload = {
        "query": "Schedule appointment for patient p_1 with doctor u_doctor_1 at 2026-02-01 10:00.", 
        "role": "Admin",
        "conversation_id": 1
    }
    data = make_request("/api/agent/query", payload)
    print(f"Agent Selected: {data.get('agent')}")
    
def test_clinician_protocol():
    print("\n--- Testing Clinician: Protocol Agent ---")
    payload = {
        "query": "What is the standard protocol for Sepsis?", 
        "role": "Doctor",
        "conversation_id": 1
    }
    data = make_request("/api/agent/query", payload)
    print(f"Agent Selected: {data.get('agent')}")

if __name__ == "__main__":
    test_patient_wearable()
    test_admin_scheduling()
    test_clinician_protocol()
    print("\n🏁 Hierarchy Tests Done.")
