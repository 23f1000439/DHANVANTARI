from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import sqlite3
import shutil
from pathlib import Path
from PIL import Image
import io
import os

from ai_service import AIService

# --- APP INIT ---
app = FastAPI(title="Dhanvantari AI API", version="1.0.0")

# CORS (Allow all for hackathon simplicity)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize AI Service
ai_service = AIService()

# Database Helper
DB_FILE = "healthcare.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- DATA MODELS ---
class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]]
    patient_context: Dict[str, Any]

class SearchRequest(BaseModel):
    query: str
    patient_meds: str

class CodingRequest(BaseModel):
    note: str

class LoginRequest(BaseModel):
    role: str

# --- ENDPOINTS ---

@app.post("/api/login")
async def login(request: LoginRequest):
    role_map = {
        "User": "u_patient_1", # Default to patient if generic
        "Patient": "u_patient_1",
        "Doctor": "u_doctor_1", 
        "Admin": "u_admin_1"
    }
    user_id = role_map.get(request.role)
    
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # If patient, fetch patient details
    patient_data = {}
    if user['role'] == 'patient':
        patient = conn.execute("SELECT * FROM patients WHERE user_id = ?", (user['id'],)).fetchone()
        if patient:
            patient_data = {
                "id": patient['id'],
                "dob": patient['dob'],
                "conditions": json.loads(patient['conditions']),
                "allergies": json.loads(patient['allergies']),
                # Mock meds for now, ideally fetch from Rx table
                "medications": ["Metformin 500mg", "Lisinopril 10mg"] 
            }
            
    conn.close()
    
    return {
        "user": dict(user),
        "patient": patient_data
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Patient triage and chat"""
    try:
        # Construct message history correctly for the AI service
        # Ensure role is 'user' or 'model'
        formatted_history = []
        for msg in request.history:
            formatted_history.append({"role": msg.get("role"), "content": msg.get("content")})
            
        # Add current message? Service expects history + latest separately or appended?
        # ai_service.get_patient_chat_response expects the FULL history including the latest user message
        formatted_history.append({"role": "user", "content": request.message})
        
        response = ai_service.get_patient_chat_response(formatted_history, request.patient_context)
        
        is_emergency = "STATUS: EMERGENCY" in response
        
        return {
            "response": response,
            "is_emergency": is_emergency
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/search")
async def search_endpoint(request: SearchRequest):
    """Doctor clinical search"""
    try:
        response = ai_service.get_clinical_search_response(request.query, request.patient_meds)
        return {"result": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/coding")
async def coding_endpoint(request: CodingRequest):
    """Admin auto-coding"""
    try:
        codes = ai_service.generate_medical_codes(request.note)
        return {"codes": codes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/upload_rx")
async def upload_rx(file: UploadFile = File(...)):
    """Prescription OCR"""
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        
        result = ai_service.analyze_prescription_image(image)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount Static Files (Frontend)
# We will create the 'static' directory next
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
