from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from ...domain.models import AgentRequest, LoginRequest
from ...application.services.root_orchestrator import RootOrchestrator
from ..persistence.database import DB_FILE, get_db_connection
import json
import sqlite3

# --- APP INIT ---
app = FastAPI(title="Dhanvantari Hierarchical Agentic API", version="3.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Fleet
orchestrator = RootOrchestrator()

# --- ENDPOINTS ---

@app.post("/api/login")
async def login(request: LoginRequest):
    role_map = {
        "User": "u_patient_1",
        "Patient": "u_patient_1",
        "Doctor": "u_doctor_1", 
        "Admin": "u_admin_1"
    }
    user_id = role_map.get(request.role, "u_patient_1")
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    patient_data = {}
    if user['role'] == 'patient':
        patient = conn.execute("SELECT * FROM patients WHERE user_id = ?", (user['id'],)).fetchone()
        if patient:
            patient_data = {
                "name": user['full_name'],
                "conditions": json.loads(patient['conditions']),
                "allergies": json.loads(patient['allergies'])
            }
            
    cursor = conn.execute(
        "INSERT INTO conversations (user_id, context_type, started_at) VALUES (?, ?, datetime('now'))",
        (user['id'], request.role)
    )
    conn.commit()
    conv_id = cursor.lastrowid
    conn.close()
    
    return {
        "user": dict(user),
        "patient": patient_data,
        "conversation_id": conv_id
    }

@app.post("/api/agent/query")
async def agent_query(request: AgentRequest):
    try:
        if not request.conversation_id:
            return {"error": "Missing conversation_id"}

        # Use new Application Layer Service
        result = orchestrator.route_request(
            request.query, 
            request.role.lower(), 
            request.conversation_id, 
            request.context,
            request.device
        )
        
        return result
    except Exception as e:
        print(f"Agent Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Mount Static Files
app.mount("/", StaticFiles(directory="static", html=True), name="static")
