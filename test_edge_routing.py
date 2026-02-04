import urllib.request
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def make_request(query, role, device_caps=None):
    url = f"{BASE_URL}/api/agent/query"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "query": query,
        "role": role,
        "conversation_id": 1
    }
    if device_caps:
        payload["device"] = device_caps
        
    json_data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Request Error: {e}")
        return {}

def run_tests():
    print("\n🧪 TEST 1: Simple Query + Capable Device (Expect: DELEGATE)")
    res = make_request(
        "What are the symptoms of a cold?", 
        "Patient",
        {"has_local_model": True, "battery_level": 80}
    )
    if res.get("delegated") == True:
        print("✅ PASS: Delegated to Edge AI")
    else:
        print(f"❌ FAIL: {res}")

    print("\n🧪 TEST 2: Complex Query + Capable Device (Expect: CLOUD)")
    res = make_request(
        "Interpret this MRI scan for glioblastoma.", 
        "Doctor",
        {"has_local_model": True, "battery_level": 80}
    )
    if res.get("delegated") != True and "agent" in res:
        print(f"✅ PASS: Routed to Cloud ({res.get('agent', 'Unknown')})")
    else:
        print(f"❌ FAIL: {res}")

    print("\n🧪 TEST 3: Simple Query + Low Battery (Expect: CLOUD)")
    res = make_request(
        "What is a fever?", 
        "Patient",
        {"has_local_model": True, "battery_level": 10}
    )
    if res.get("delegated") != True:
        print(f"✅ PASS: Routed to Cloud due to Low Battery")
    else:
        print(f"❌ FAIL: {res}")

if __name__ == "__main__":
    time.sleep(2) # Allow server to stabilize if just started
    run_tests()
