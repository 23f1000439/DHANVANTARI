import unittest
import sqlite3
import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
import socket

# Adjust path to find backend modules
sys.path.append(os.getcwd())

from backend.agents.root_orchestrator import RootOrchestrator
from main import DeviceCapabilities

DB_FILE = "healthcare.db"
BASE_URL = "http://127.0.0.1:8000"

def wait_for_port(port, timeout=15):
    """Wait until a port is accepting connections."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('127.0.0.1', port))
            if result == 0:
                print(f"✅ Port {port} is open!")
                return True
        time.sleep(0.5)
    print(f"❌ Port {port} never opened.")
    return False

class TestDatabaseReadiness(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_01_connection(self):
        """Verify database connection is established."""
        self.assertIsNotNone(self.conn)
        print("✅ Database Connection: FAST")

    def test_02_required_tables(self):
        """Verify all critical tables exist (V3 Schema)."""
        required_tables = [
            "users", "patients", "encounters", 
            "appointments", "payments", "wearable_metrics",
            "audit_logs", "protocols", "conversations"
        ]
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in self.cursor.fetchall()]
        
        missing = [t for t in required_tables if t not in existing_tables]
        if missing:
            self.fail(f"Missing critical tables: {missing}")
        print(f"✅ Schema Integrity: {len(existing_tables)} tables found.")

    def test_03_seed_data(self):
        """Verify seed data exists."""
        self.cursor.execute("SELECT count(*) FROM patients")
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 0, "No patients found in DB")
        print(f"✅ Data Persistence: {count} patients seeded.")

class TestBackendLogic(unittest.TestCase):
    def test_01_smart_routing_logic(self):
        """Unit Test: RootOrchestrator complexity assessment."""
        orch = RootOrchestrator()
        
        # Test Simple Heuristic
        self.assertEqual(orch.assess_complexity("symptom check"), "simple")
        self.assertEqual(orch.assess_complexity("schedule appointment"), "simple")
        
        # Test Complex Heuristic
        self.assertEqual(orch.assess_complexity("interpret MRI scan"), "complex")
        print("✅ Logic Check: Smart Routing Heuristics passed.")

class TestserverIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Start the server in background."""
        print("🚀 Starting Test Server...")
        cls.server_process = subprocess.Popen(
            ["uvicorn", "main:app", "--port", "8000"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env={**os.environ, "GEMINI_API_KEY": "AIzaSyDLQt-Yx4VK1v2z1qKErNd8iOAdjYQcGdI", "PYTHONPATH": os.getcwd()}
        )
        if not wait_for_port(8000):
            raise RuntimeError("Server failed to start")

    @classmethod
    def tearDownClass(cls):
        """Kill the server."""
        if cls.server_process:
            cls.server_process.terminate()
            cls.server_process.wait()
        print("🛑 Test Server Stopped.")

    def test_01_api_health(self):
        """Verify API accepts connections."""
        try:
            url = f"{BASE_URL}/docs"
            req = urllib.request.Request(url, method='GET')
            with urllib.request.urlopen(req) as response:
                self.assertEqual(response.status, 200)
            print("✅ API Status: Online & Responding.")
        except urllib.error.URLError as e:
            self.fail(f"API unreachable: {e}")

    def test_02_post_agent_query(self):
        """Integration Test: Mock Agent Query to check Pydantic validation."""
        url = f"{BASE_URL}/api/agent/query"
        payload = {
            "query": "Hello", 
            "role": "Patient", 
            "conversation_id": 1,
            "device": {"has_local_model": False}
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                self.assertIn("agent", result)
            print("✅ End-to-End: Request processed successfully.")
        except Exception as e:
            self.fail(f"Agent Query failed: {e}")

    def test_03_edge_ai_delegation(self):
        """Integration Test: Verify Smart Routing to Edge."""
        url = f"{BASE_URL}/api/agent/query"
        # query "symptoms" is 'simple', device has model -> Should delegate
        payload = {
            "query": "flu symptoms", 
            "role": "Patient", 
            "conversation_id": 1,
            "device": {"has_local_model": True, "battery_level": 90}
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'}, method='POST')
        
        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                self.assertTrue(result.get("delegated"), "Failed to delegate simple query to Edge")
                self.assertEqual(result.get("instruction"), "USE_LOCAL_MODEL")
            print("✅ Edge-AI: Smart Routing verified.")
        except Exception as e:
            self.fail(f"Edge Routing failed: {e}")

class TestEdgeReadiness(unittest.TestCase):
    def test_model_file_exists(self):
        """Verify MedGemma GGUF model is present."""
        model_path = os.path.join(os.getcwd(), "backend/inference/medgemma-1.5-4b-it.Q4_K_M.gguf")
        if os.path.exists(model_path):
             print(f"✅ Edge-AI: Model file found ({os.path.getsize(model_path) // (1024*1024)} MB).")
        else:
             self.fail(f"❌ Edge-AI: Model file missing at {model_path}")

if __name__ == "__main__":
    unittest.main(verbosity=0)
