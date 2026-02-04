import urllib.request
import urllib.error
import json
import os
import time
import subprocess
import signal
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def start_server():
    print("🚀 Starting Agentic FastAPI server...")
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = "AIzaSyDLQt-Yx4VK1v2z1qKErNd8iOAdjYQcGdI"
    env["PYTHONPATH"] = os.getcwd()
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    time.sleep(10) 
    return process

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

def test_agent_triage():
    print("\n--- Testing Triage Agent (via Orchestrator) ---")
    payload = {
        "query": "I have a severe headache and blurred vision.", 
        "role": "Patient",
        "conversation_id": 1,
        "context": {"name": "TestUser", "conditions": ["Migraine"]}
    }
    data = make_request("/api/agent/query", payload)
    print(f"Agent Selected: {data.get('agent')}")
    print(f"Response: {str(data.get('response'))[:100]}...")
    
    if data.get('agent') == "TriageAgent":
        print("✅ Routing Correct")
    else:
        print("❌ Routing Failed")

def test_agent_clinical():
    print("\n--- Testing Clinical Agent (via Orchestrator) ---")
    payload = {
        "query": "Protocol for T2DM management?", 
        "role": "Doctor",
        "conversation_id": 1
    }
    data = make_request("/api/agent/query", payload)
    print(f"Agent Selected: {data.get('agent')}")
    
    if data.get('agent') == "ClinicalAgent":
        print("✅ Routing Correct")
    else:
        print("❌ Routing Failed")

if __name__ == "__main__":
    # server = start_server()
    try:
        time.sleep(2)
        test_agent_triage()
        test_agent_clinical()
        print("\n🏁 Tests Done.")
    finally:
        pass
        # os.kill(server.pid, signal.SIGTERM)
