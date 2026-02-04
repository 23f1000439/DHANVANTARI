import urllib.request
import urllib.parse
import json
import os
import time
import subprocess
import signal
import sys

# Configuration
BASE_URL = "http://127.0.0.1:8000"

def start_server():
    """Start the FastAPI server in a subprocess."""
    print("🚀 Starting FastAPI server...")
    
    # Inject API Key provided by user
    env = os.environ.copy()
    env["GEMINI_API_KEY"] = "AIzaSyDLQt-Yx4VK1v2z1qKErNd8iOAdjYQcGdI"
    
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env
    )
    time.sleep(5) # Wait for startup
    return process

def make_request(endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    headers = {'Content-Type': 'application/json'}
    
    try:
        if data:
            json_data = json.dumps(data).encode('utf-8')
            req = urllib.request.Request(url, data=json_data, headers=headers, method='POST')
        else:
            req = urllib.request.Request(url, method='GET')
            
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                return json.loads(response.read().decode())
            return None
    except urllib.error.URLError as e:
        print(f"   Request Error: {e}")
        return None

def test_connection():
    try:
        url = f"{BASE_URL}/docs"
        req = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                print("✅ Server is UP")
                return True
    except:
        print("❌ Server is DOWN")
        return False

def test_login():
    print("\n--- Testing Login ---")
    payload = {"role": "Patient"}
    res = make_request("/api/login", payload)
    
    if res and res.get('user', {}).get('role') == 'patient':
        print("✅ Login Successful (Patient data retrieved)")
    else:
        print(f"❌ Login Failed: {res}")

def test_chat():
    print("\n--- Testing Patient Chat ---")
    payload = {
        "message": "Hello",
        "history": [],
        "patient_context": {"name": "Test", "conditions": []}
    }
    res = make_request("/api/chat", payload)
    
    if res and 'response' in res:
        print(f"✅ Chat Response: {res['response'][:50]}...")
    else:
        print(f"❌ Chat Failed")

def test_coding():
    print("\n--- Testing Admin Coding ---")
    payload = {"note": "Patient has Type 2 Diabetes."}
    res = make_request("/api/coding", payload)
    
    if res and 'codes' in res:
        print(f"✅ Coding Response: {res}")
    else:
        print(f"❌ Coding Failed")

if __name__ == "__main__":
    # Start Server
    server_proc = start_server()
    
    try:
        if test_connection():
            test_login()
            test_chat()
            test_coding()
            print("\n✨ All Backend Tests Completed. Ready for UI integration.")
        else:
            print("Could not connect to server.")
    finally:
        # Kill Server
        os.kill(server_proc.pid, signal.SIGTERM)
        print("🏁 Server stopped.")
