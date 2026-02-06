"""
Verify Full Backend Integration of Dhanvantr.ai
Checks: Database, Unified AI Service, FastAPI Routes, and Orchestration.
"""
import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.web.api_main import app
from app.infrastructure.persistence.models import init_db, get_db, SessionLocal, engine
from app.application.services.unified_ai_service import get_unified_ai_service

# Client for API tests
client = TestClient(app)

def test_01_database_initialization():
    """Verify database tables are created."""
    print("\n[TEST] Verifying Database Initialization...")
    init_db()
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    expected_tables = [
        "patients", "encounters", "clinical_notes", "prescriptions",
        "claims", "imaging_studies", "audit_logs", "alert_history"
    ]
    
    missing = [t for t in expected_tables if t not in tables]
    assert not missing, f"Missing tables: {missing}"
    print(f"✅ Database initialized with {len(tables)} tables.")

def test_02_unified_ai_service_status():
    """Verify AI services are reachable."""
    print("\n[TEST] Verifying Unified AI Service...")
    service = get_unified_ai_service()
    status = service.get_status()
    
    print(f"   Gemini Available: {status['gemini_available']}")
    print(f"   MedGemma Available: {status['medgemma_available']}")
    
    # We expect at least one service to be available for a passing test in this environment
    # ideally both if properly configured.
    assert status['gemini_available'] or status['medgemma_available'], "No AI models available!"
    print("✅ Unified AI Service is operational.")

def test_03_api_health_check():
    """Verify API health endpoint."""
    print("\n[TEST] Verifying API Health...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("✅ API Health check passed.")

def test_04_clinical_triage_flow():
    """Verify Clinical Triage Route (Backend + AI + Orchestration)."""
    print("\n[TEST] Verifying Clinical Triage Route...")
    payload = {
        "chief_complaint": "severe chest pain radiating to left arm, sweating",
        "clinical_history": "Hypertension, Smoker"
    }
    response = client.post("/api/v1/clinical/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "priority" in data
    assert "esi_level" in data
    print(f"   Triage Result: Priority={data['priority']}, ESI={data['esi_level']}")
    print("✅ Clinical route integration verified.")

def test_05_monitoring_ed_flow():
    """Verify Monitoring/ED Route."""
    print("\n[TEST] Verifying ED Triage Route...")
    payload = {
        "vitals": {"heart_rate": 110, "bp_systolic": 90, "spo2": 94, "gcs": 15},
        "chief_complaint": "shortness of breath, history of asthma"
    }
    response = client.post("/api/v1/monitoring/ed/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "esi_level" in data
    assert "teams_to_alert" in data
    print(f"   ED Response: ESI={data['esi_level']}, Teams={data['teams_to_alert']}")
    print("✅ ED Monitoring route verified.")

def test_06_admin_claims_flow():
    """Verify Admin/Claims Route (RCM pipeline integration)."""
    print("\n[TEST] Verifying RCM/Claims Route...")
    payload = {
        "patient_id": 123,  # Mock ID
        "procedures": [{"procedure": "Knee Replacement", "cpt_code": "27447"}],
        "diagnosis_codes": ["M17.11"],
        "total_charges": 25000.0,
        "payer": "Medicare",
        "pre_authorization": False,
        "clinical_notes": "Patient elected for surgery."
    }
    # Create mock patient first to avoid FK error if DB is fresh and strictly enforced
    # For this unit test, we might get an error if patient doesn't exist depending on sqlite settings
    # But let's try. If it fails due to FK, we'll create a patient.
    
    # Pre-create patient
    try:
        from app.infrastructure.persistence.repository import DhanvantariRepository
        db = SessionLocal()
        repo = DhanvantariRepository(db)
        if not repo.patients.get(123):
             repo.patients.create(id=123, mrn="TEST001", first_name="Test", last_name="Patient")
        db.close()
    except Exception as e:
        print(f"   (Warning: DB setup for claim test: {e})")

    response = client.post("/api/v1/admin/claims/analyze", json=payload)
    if response.status_code != 200:
        print(f"   Error: {response.text}")
    assert response.status_code == 200
    data = response.json()
    
    assert "denial_risk_score" in data
    print(f"   Claim Analysis: Risk Score={data['denial_risk_score']}")
    print("✅ RCM/Admin route verified.")

if __name__ == "__main__":
    # Run tests manually
    try:
        test_01_database_initialization()
        test_02_unified_ai_service_status()
        test_03_api_health_check()
        test_04_clinical_triage_flow()
        test_05_monitoring_ed_flow()
        test_06_admin_claims_flow()
        print("\n🎉 ALL BACKEND INTEGRATION TESTS PASSED!")
    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)
