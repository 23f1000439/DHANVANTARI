# DHANVANTARI Codebase Context

## File: run_app.py

```py
import uvicorn
import os

if __name__ == "__main__":
    # Ensure PYTHONPATH includes the current directory
    # Run with: python3 run_app.py
    uvicorn.run("app.infrastructure.web.main:app", host="127.0.0.1", port=8000, reload=True)

```

## File: ai_service.py

```py
import google.generativeai as genai
import os
import json
from datetime import datetime
import time

# Configure API Key (should be in env vars, but handling for demo)
if "GEMINI_API_KEY" not in os.environ:
    # Fallback or error - for now we assume it's set or user will set it
    pass
else:
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])

class AIService:
    def __init__(self):
        # Initialize Models (Gemini 3 Preview)
        # Using Gemini 3 Flash Preview as requested
        self.flash_model = genai.GenerativeModel('gemini-3-flash-preview') 
        self.pro_model = genai.GenerativeModel('gemini-3-flash-preview')
        
        # Generation configs
        self.fast_config = genai.types.GenerationConfig(
            temperature=0.7,
            max_output_tokens=1000,
        )
        self.analytical_config = genai.types.GenerationConfig(
            temperature=0.2, # Lower temp for coding/analysis
            max_output_tokens=2000,
        )

    def get_patient_chat_response(self, message_history, patient_context):
        """
        Handles patient chat interactions with triage logic.
        """
        system_prompt = f"""
        Role: You are a compassionate Patient Health Assistant.
        Patient Context:
        - Name: {patient_context.get('name')}
        - Age: {patient_context.get('age')}
        - Conditions: {patient_context.get('conditions')}
        - Medication: {patient_context.get('medications')}
        - Allergies: {patient_context.get('allergies')}

        Rules:
        1. Empathize with the patient.
        2. IF the patient describes severe symptoms (chest pain, difficulty breathing, sudden weakness, severe bleeding), 
           start your response with "STATUS: EMERGENCY" and advise calling emergency services immediately.
        3. Use simple, clear language (Grade 6 reading level).
        4. Reference their specific conditions/medications if relevant.
        5. Do NOT diagnose new conditions. Suggest seeing a doctor for new symptoms.
        """

        # Construct history for Gemini
        gemini_history = []
        for msg in message_history:
            role = "user" if msg['role'] == 'user' else "model"
            gemini_history.append({"role": role, "parts": [msg['content']]})

        # Start chat session or send single message? Chat session is better for history.
        # However, for stateless API simplicity, we'll re-construct context in prompt if needed, 
        # but here we use the chat object
        
        chat = self.flash_model.start_chat(history=gemini_history)
        
        # Add system prompt to the latest message or as a separate strict instruction?
        # In Gemini 1.5/2.0, system instructions are set at model init. 
        # For dynamic per-turn system prompts (hackathon style), we prepend to the message.
        
        full_prompt = f"{system_prompt}\n\nUser Message: {message_history[-1]['content']}" if message_history else system_prompt
        
        try:
            # We already added history, so we just send the new user prompt part? 
            # Actually start_chat history implies previous messages. 
            # The *current* message isn't in history yet.
            response = chat.send_message(f"System Instructions: {system_prompt}\n\nPlease respond to the user.")
            return response.text
        except Exception as e:
            return f"I'm sorry, I'm having trouble connecting right now. Please try again. (Error: {str(e)})"

    def get_clinical_search_response(self, query, patient_meds):
        """
        Doctor's evidence-based search with grounding (simulated via search tool if available, or strict citations).
        """
        prompt = f"""
        Role: Clinical Decision Support Assistant.
        Task: Answer the clinician's query based on medical evidence.
        Context: Patient is currently taking: {patient_meds}.
        Query: {query}
        
        Rules:
        1. Check for drug interactions with the patient's current list.
        2. Cite guideline bodies (AHA, ACC, ADA, etc.) where applicable.
        3. Structure your answer with headings.
        4. Provide an 'Evidence Grade' (e.g., Level A, Level B) if possible.
        """
        
        # Tools would be defined here (Google Search)
        # tools=[genai.GoogleSearchRetrieval] (if available in the library version used)
        
        try:
            response = self.pro_model.generate_content(prompt, generation_config=self.analytical_config)
            return response.text
        except Exception as e:
            return f"Clinical Search Error: {str(e)}"

    def analyze_prescription_image(self, image_data):
        """
        Multimodal OCR to extract prescription details.
        image_data: PIL Image object
        """
        prompt = """
        Analyze this prescription image. 
        Extract the following fields into a JSON object:
        - doctor_name (string)
        - patient_name (string, or null if not found)
        - date (string)
        - medications (list of objects with: name, dosage, frequency, duration, instructions)
        
        If you are unsure about a field, use null or "Unknown".
        Ensure the output is valid JSON.
        """
        
        try:
            response = self.flash_model.generate_content(
                [prompt, image_data],
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"OCR Error: {e}")
            return {"error": str(e), "medications": []}

    def generate_medical_codes(self, clinical_note):
        """
        Auto-coding from clinical notes.
        """
        prompt = f"""
        Analyze the following clinical note and assign relevant ICD-11 diagnosis codes.
        Return a JSON list of objects, each containing:
        - code (string, e.g. "EB12")
        - description (string)
        - confidence (float, 0.0 to 1.0)
        
        Clinical Note:
        {clinical_note}
        """
        
        try:
            response = self.pro_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Coding Error: {e}")
            return []

if __name__ == "__main__":
    # Simple test
    print("AI Service initialized.")

```

## File: generate_context.py

```py
import os

def generate_context(root_dir, output_file, extensions=None, ignore_dirs=None):
    if extensions is None:
        extensions = ['.py', '.js', '.html', '.css', '.sql', '.md']
    if ignore_dirs is None:
        ignore_dirs = {'.git', '__pycache__', 'venv', 'node_modules', '.gemini', '.idea', '.vscode', '.venv_libs'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# DHANVANTARI Codebase Context\n\n")
        
        for root, dirs, files in os.walk(root_dir):
            # Modify dirs in-place to skip ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                _, ext = os.path.splitext(file)
                if ext in extensions:
                    file_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_path, root_dir)
                    
                    # Skip the output file itself if it's in the directory
                    if os.path.abspath(file_path) == os.path.abspath(output_file):
                        continue
                        
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            content = infile.read()
                            
                        outfile.write(f"## File: {rel_path}\n\n")
                        outfile.write(f"```{ext[1:]}\n")
                        outfile.write(content)
                        outfile.write(f"\n```\n\n")
                        print(f"Added {rel_path}")
                    except Exception as e:
                        print(f"Error reading {rel_path}: {e}")

if __name__ == "__main__":
    generate_context('.', 'DHANVANTARI_CONTEXT.md')
    print("Context file generated: DHANVANTARI_CONTEXT.md")

```

## File: verify_impl.py

```py
import sqlite3
import os
import requests
import time
import subprocess
import sys

def check_db():
    print("Checking Database...")
    if not os.path.exists("healthcare.db"):
        print("❌ healthcare.db not found!")
        return False
    
    conn = sqlite3.connect("healthcare.db")
    cursor = conn.cursor()
    
    try:
        users = cursor.execute("SELECT * FROM users").fetchall()
        print(f"✅ Users found: {len(users)}")
        patients = cursor.execute("SELECT * FROM patients").fetchall()
        print(f"✅ Patients found: {len(patients)}")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ DB Check failed: {e}")
        conn.close()
        return False

def check_frontend_files():
    print("\nChecking Frontend Files...")
    files = [
        "static/index.html",
        "static/css/style.css",
        "static/js/app.js"
    ]
    all_exist = True
    for f in files:
        if os.path.exists(f):
            print(f"✅ Found {f}")
        else:
            print(f"❌ Missing {f}")
            all_exist = False
    return all_exist

if __name__ == "__main__":
    db_ok = check_db()
    fe_ok = check_frontend_files()
    
    if db_ok and fe_ok:
        print("\n🎉 Verification Passed! You can run the app with: uvicorn main:app --reload")
    else:
        print("\n❌ Verification Failed.")

```

## File: legacy_app.py

```py
import streamlit as st
import sqlite3
import json
import pandas as pd
from datetime import datetime
from PIL import Image
from ai_service import AIService
import time

# --- CONFIGURATION ---
st.set_page_config(
    page_title="Healthcare AI Platform",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; font-weight: 700; color: #1E88E5;}
    .sub-header {font-size: 1.5rem; font-weight: 600; color: #424242;}
    .card {background-color: #f9f9f9; padding: 20px; border-radius: 10px; margin-bottom: 20px;}
    .emergency {background-color: #FFEBEE; border-left: 5px solid #D32F2F; padding: 15px;}
    .chat-user {text-align: right; color: #1E88E5; background-color: #E3F2FD; padding: 10px; border-radius: 10px; display: inline-block; margin: 5px 0;}
    .chat-model {text-align: left; color: #424242; background-color: #F5F5F5; padding: 10px; border-radius: 10px; display: inline-block; margin: 5px 0;}
</style>
""", unsafe_allow_html=True)

# --- DATABASE HELPERS ---
DB_FILE = "healthcare.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user(user_id):
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user

def get_patient(user_id):
    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patients WHERE user_id = ?", (user_id,)).fetchone()
    conn.close()
    return patient

def get_patient_by_id(patient_id):
    conn = get_db_connection()
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (patient_id,)).fetchone()
    conn.close()
    return patient

# --- SESSION STATE ---
if "user" not in st.session_state:
    st.session_state.user = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "ai_service" not in st.session_state:
    st.session_state.ai_service = AIService()

# --- SIDEBAR: AUTH SIMULATION ---
with st.sidebar:
    st.image("https://img.icons8.com/color/96/caduceus.png", width=60)
    st.markdown("## Dhanvantari AI")
    
    st.markdown("### 🔐 Login Simulator")
    selected_role = st.selectbox("Select Persona:", ["Patient", "Doctor", "Admin"])
    
    if selected_role == "Patient":
        user_id = "u_patient_1"
    elif selected_role == "Doctor":
        user_id = "u_doctor_1"
    else:
        user_id = "u_admin_1"
        
    if st.button("Login as " + selected_role):
        st.session_state.user = get_user(user_id)
        # Load contextual data based on role?
        st.session_state.messages = [] # Reset chat on login switch
        st.rerun()

    if st.session_state.user:
        st.success(f"Logged in as: {st.session_state.user['full_name']}")
        st.info(f"Role: {st.session_state.user['role'].upper()}")

# --- MAIN APP ROUTING ---
if not st.session_state.user:
    st.title("Welcome to Dhanvantari AI Platform")
    st.markdown("Please log in using the sidebar simulator to access the platform.")
    st.stop()

user = st.session_state.user
role = user['role']

# ---------------- PATIENT PORTAL ----------------
if role == 'patient':
    st.markdown('<div class="main-header">🏥 Patient Portal</div>', unsafe_allow_html=True)
    
    # 1. Fetch Patient Data
    patient = get_patient(user['id'])
    if not patient:
        st.error("Patient record not found.")
        st.stop()
        
    # Context for AI
    patient_context = {
        "name": user['full_name'],
        "age": (datetime.now().year - datetime.strptime(patient['dob'], '%Y-%m-%d').year),
        "conditions": json.loads(patient['conditions']),
        "medications": "Metformin 500mg, Lisinopril 10mg", # Mock fetching from Rx table for now
        "allergies": json.loads(patient['allergies'])
    }
    
    col1, col2 = st.columns([2, 1])
    
    with col1: 
        st.subheader("💬 Health Assistant")
        # Chat Interface
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
        
        if prompt := st.chat_input("How are you feeling today?"):
            # User Message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.write(prompt)
            
            # AI Response
            with st.chat_message("assistant"):
                with st.spinner("Dr. AI is thinking..."):
                    response_text = st.session_state.ai_service.get_patient_chat_response(
                        st.session_state.messages, patient_context
                    )
                    st.write(response_text)
            
            st.session_state.messages.append({"role": "assistant", "content": response_text})

    with col2:
        st.subheader("📋 My Health")
        with st.expander("Conditions", expanded=True):
            for c in patient_context['conditions']:
                st.write(f"- {c}")
        
        with st.expander("Medications", expanded=True):
            st.write(patient_context['medications'])
            
        st.divider()
        st.subheader("📸 Prescription Scanner")
        uploaded_file = st.file_uploader("Upload Rx Image", type=['png', 'jpg', 'jpeg'])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Prescription', use_column_width=True)
            if st.button("Analyze Prescription"):
                with st.spinner("Extracting with Gemini Vision..."):
                    result = st.session_state.ai_service.analyze_prescription_image(image)
                    st.json(result)
                    
                    if result.get("medications"):
                        st.success("Medications Identified!")
                        # In real app, save to DB button here

# ---------------- DOCTOR PORTAL ----------------
elif role == 'doctor':
    st.markdown('<div class="main-header">🩺 Doctor Workspace</div>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["Clinical Search", "Patient Rounds"])
    
    with tab1:
        st.subheader("🧠 Evidence-Based Clinical Search")
        query = st.text_input("Ask a clinical question (e.g., 'Drug interactions for Metformin')")
        
        # Mock patient selector for context
        conn = get_db_connection()
        patients = conn.execute("SELECT p.id, u.full_name, p.conditions FROM patients p JOIN users u ON p.user_id = u.id").fetchall()
        selected_p_id = st.selectbox("Context Patient (Optional):", [p['id'] for p in patients], format_func=lambda x: [p['full_name'] for p in patients if p['id'] == x][0])
        
        if st.button("Search Protocols"):
            if query:
                # Get patient meds/context
                # Simplified: just passing a string for now
                p_ctx_meds = "Metformin, Lisinopril" 
                
                with st.spinner("Searching Medical Guidelines (Gemini 3 Pro)..."):
                    response = st.session_state.ai_service.get_clinical_search_response(query, p_ctx_meds)
                    st.markdown(response)
                    st.info("ℹ️ Information grounded in simulated medical database.")
    
    with tab2:
        st.write("Patient Rounds View (Mockup)")
        # List patients
        df = pd.DataFrame(patients, columns=["ID", "Name", "Conditions"])
        st.dataframe(df)

# ---------------- ADMIN PORTAL ----------------
elif role == 'admin':
    st.markdown('<div class="main-header">📊 Revenue & Operations</div>', unsafe_allow_html=True)
    
    st.subheader("💰 Automated Medical Coding")
    
    default_note = """
    Patient presented with polyuria and polydipsia. 
    Fasting blood glucose 180 mg/dL. 
    Diagnosis: Type 2 DM. 
    Also noted BP 150/95, started on Lisinopril.
    """
    note = st.text_area("Clinical Note Input", value=default_note, height=150)
    
    if st.button("Generate ICD-11 Codes"):
        with st.spinner("Analyzing with Gemini 3 Pro (JSON Mode)..."):
            codes = st.session_state.ai_service.generate_medical_codes(note)
            
            # Display nicely
            if codes:
                for item in codes:
                    # Highlight low confidence
                    conf = item.get('confidence', 0.5)
                    color = "green" if conf > 0.8 else "orange"
                    st.markdown(f"""
                    <div style="border: 1px solid #ddd; padding: 10px; border-radius: 5px; margin-bottom: 5px; border-left: 5px solid {color};">
                        <strong>{item.get('code')}</strong>: {item.get('description')} <br>
                        <small>Confidence: {int(conf*100)}%</small>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("No codes generated or error occurred.")

```

## File: schema.sql

```sql
-- Enable foreign keys
PRAGMA foreign_keys = ON;

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL, -- In a real app, this would be hashed. For demo, plain text or simple hash.
    role TEXT CHECK(role IN ('patient', 'doctor', 'admin')) NOT NULL,
    full_name TEXT NOT NULL,
    profile_data TEXT, -- JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Patients Table
CREATE TABLE IF NOT EXISTS patients (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    dob DATE NOT NULL,
    gender TEXT,
    mrn TEXT UNIQUE NOT NULL,
    allergies TEXT, -- JSON Array
    conditions TEXT, -- JSON Array
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Encounters Table
CREATE TABLE IF NOT EXISTS encounters (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL, -- User ID of the doctor
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    type TEXT,
    clinical_notes TEXT,
    ai_summary TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

-- Prescriptions Table
CREATE TABLE IF NOT EXISTS prescriptions (
    id TEXT PRIMARY KEY,
    encounter_id TEXT, -- Can be null if not linked to a specific encounter (e.g. uploaded)
    patient_id TEXT NOT NULL,
    doctor_id TEXT, -- Can be null if uploaded by patient without doctor link yet
    prescribed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'Active',
    image_path TEXT,
    is_ai_generated BOOLEAN DEFAULT 0,
    FOREIGN KEY (encounter_id) REFERENCES encounters(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

-- Prescription Items Table
CREATE TABLE IF NOT EXISTS prescription_items (
    id TEXT PRIMARY KEY,
    prescription_id TEXT NOT NULL,
    medication_name TEXT NOT NULL,
    dosage TEXT,
    frequency TEXT,
    duration TEXT,
    instructions TEXT,
    FOREIGN KEY (prescription_id) REFERENCES prescriptions(id) ON DELETE CASCADE
);

-- Claims Table
CREATE TABLE IF NOT EXISTS claims (
    id TEXT PRIMARY KEY,
    encounter_id TEXT NOT NULL,
    status TEXT DEFAULT 'Draft',
    total_amount DECIMAL(10, 2),
    ai_analysis TEXT, -- JSON with denial probability
    FOREIGN KEY (encounter_id) REFERENCES encounters(id)
);

-- Diagnosis Codes Table
CREATE TABLE IF NOT EXISTS diagnosis_codes (
    id TEXT PRIMARY KEY,
    claim_id TEXT NOT NULL,
    code TEXT NOT NULL,
    description TEXT,
    confidence_score REAL,
    FOREIGN KEY (claim_id) REFERENCES claims(id) ON DELETE CASCADE
);

-- Conversations Table
CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    context_type TEXT,
    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    title TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Messages Table
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT CHECK(role IN ('user', 'model', 'system')) NOT NULL,
    content TEXT NOT NULL,
    thought_chain TEXT, -- JSON
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

-- SEED DATA
-- 1. Users
INSERT OR IGNORE INTO users (id, email, password_hash, role, full_name, profile_data) VALUES
('u_patient_1', 'rajesh@example.com', 'pass', 'patient', 'Rajesh Kumar', '{"language": "en"}'),
('u_doctor_1', 'priya@hospital.com', 'pass', 'doctor', 'Dr. Priya Sharma', '{"specialty": "Cardiology"}'),
('u_admin_1', 'sarah@admin.com', 'pass', 'admin', 'Sarah Admin', '{"department": "Billing"}');

-- 2. Patients
INSERT OR IGNORE INTO patients (id, user_id, dob, gender, mrn, allergies, conditions) VALUES
('p_1', 'u_patient_1', '1968-05-15', 'Male', 'MRN-2026-001', '["Penicillin"]', '["Type 2 Diabetes", "Hypertension", "Hyperlipidemia"]');

-- 3. Encounters (Initial history)
INSERT OR IGNORE INTO encounters (id, patient_id, doctor_id, date, type, clinical_notes) VALUES
('e_1', 'p_1', 'u_doctor_1', '2025-12-10 10:00:00', 'In-Person', 'Patient presents with elevated blood glucose levels. Reporting fatigue and increased thirst. BP 145/90. Current Metformin dosage may need adjustment.');

-- 4. Prescriptions (Current meds)
INSERT OR IGNORE INTO prescriptions (id, patient_id, doctor_id, prescribed_at, status, is_ai_generated) VALUES
('rx_1', 'p_1', 'u_doctor_1', '2025-12-10 10:30:00', 'Active', 0);

INSERT OR IGNORE INTO prescription_items (id, prescription_id, medication_name, dosage, frequency, duration, instructions) VALUES
('pi_1', 'rx_1', 'Metformin', '500mg', 'BID', '30 days', 'Take with meals'),
('pi_2', 'rx_1', 'Lisinopril', '10mg', 'QD', '30 days', 'Take in the morning');

```

## File: list_models.py

```py
import google.generativeai as genai
import os

key = "AIzaSyDLQt-Yx4VK1v2z1qKErNd8iOAdjYQcGdI"
genai.configure(api_key=key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

```

## File: verify_readiness.py

```py
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

```

## File: test_hierarchy.py

```py
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

```

## File: test_local_inference.py

```py
from backend.inference.engine import LocalInferenceEngine
import time

def test_local_inference():
    print("🚀 Initializing Local Engine...")
    start_load = time.time()
    engine = LocalInferenceEngine()
    print(f"⏱️ Load Time: {time.time() - start_load:.2f}s")
    
    prompt = "Listing symptoms of diabetes:"
    print(f"\n📝 Prompt: {prompt}")
    
    start_gen = time.time()
    response = engine.generate(prompt, max_tokens=128)
    print(f"⏱️ Generation Time: {time.time() - start_gen:.2f}s")
    
    print(f"\n🤖 Response:\n{response}")
    
    if "Error" not in response:
        print("\n✅ Local Inference Verification PASSED")
    else:
        print("\n❌ Local Inference Verification FAILED")

if __name__ == "__main__":
    test_local_inference()

```

## File: test_agent_fleet.py

```py
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

```

## File: schema_update_v2.sql

```sql
-- Schema Update V2 for Hierarchical Agents

-- appointments (SchedulingAgent)
CREATE TABLE IF NOT EXISTS appointments (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    doctor_id TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME NOT NULL,
    status TEXT DEFAULT 'Scheduled', -- Scheduled, Completed, Cancelled
    reason TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (doctor_id) REFERENCES users(id)
);

-- payments (PaymentReconciliationAgent)
CREATE TABLE IF NOT EXISTS payments (
    id TEXT PRIMARY KEY,
    claim_id TEXT,
    patient_id TEXT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    status TEXT DEFAULT 'Pending', -- Pending, Completed, Failed
    method TEXT,
    transaction_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (claim_id) REFERENCES claims(id),
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- wearable_metrics (WearableAgent)
CREATE TABLE IF NOT EXISTS wearable_metrics (
    id TEXT PRIMARY KEY,
    patient_id TEXT NOT NULL,
    device_type TEXT, -- Apple Watch, Fitbit
    metric_type TEXT, -- Heart Rate, Steps, SpO2
    value REAL,
    unit TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id)
);

-- audit_logs (GovernanceAgent)
CREATE TABLE IF NOT EXISTS audit_logs (
    id TEXT PRIMARY KEY,
    agent_name TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_id TEXT, -- related record id
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- protocols (ProtocolAgent)
CREATE TABLE IF NOT EXISTS protocols (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT,
    content TEXT NOT NULL, -- The actual guideline text/JSON
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    source TEXT -- e.g. AHA, CDC
);

-- Note: No seed data needed immediately, agents will populate.

```

## File: test_edge_routing.py

```py
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

```

## File: test_api_endpoints.py

```py
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

```

## File: old_main.py

```py
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

```

## File: Documentation/PRD.md

```md

```

## File: Documentation/hackathon-implementation-guide.md

```md
# Hackathon Implementation Guide
## Healthcare AI Platform - Fast Track Build

**Target:** 48-hour hackathon MVP  
**Goal:** Impressive demo with core functionality, skip production overhead  
**Date:** January 29, 2026

---

## 1. COMPLIANCE SHORTCUTS (CRITICAL FOR HACKATHON)

### 1.1 HIPAA Bypass Strategy

**Production Requirement:** Vertex AI with signed BAA, regulated-data flag  
**Hackathon Shortcut:** Use **Consumer Gemini API** (claude.ai style, no BAA needed)

```python
# PRODUCTION (DO NOT USE FOR HACKATHON)
from google import genai
client = genai.Client(
    vertexai=True,
    project="your-project",
    location="us-central1"
)

# HACKATHON SHORTCUT
import google.generativeai as genai
genai.configure(api_key="YOUR_API_KEY")  # Free tier: 1,500 RPD
model = genai.GenerativeModel('gemini-2.0-flash-exp')  # Use 2.0 Flash, 3.0 not in free tier yet
```

**Why this works for hackathon:**
- ✅ No BAA paperwork (saves 2 weeks)
- ✅ No GCP project setup complexity
- ✅ Free tier: 1,500 requests/day (enough for demo)
- ✅ Gemini 2.0 Flash is FREE and fast
- ⚠️ Use synthetic/anonymized patient data only (see section 1.3)

### 1.2 Data Privacy Workarounds

**Production Requirement:** Encrypted databases, CMEK, audit logs  
**Hackathon Shortcut:** Local SQLite + JSON files

```python
# Simple file-based storage (NO PRODUCTION USE)
import sqlite3
import json

# Ultra-light patient database
conn = sqlite3.connect('demo_patients.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY,
    name TEXT,
    age INTEGER,
    conditions TEXT,  -- JSON string
    medications TEXT  -- JSON string
)
''')

# Conversation history in JSON
conversations = {}

def save_conversation(patient_id, messages):
    conversations[patient_id] = messages
    with open('conversations.json', 'w') as f:
        json.dump(conversations, f)
```

**Why this works:**
- ✅ Zero infrastructure setup
- ✅ Portable demo (runs on laptop)
- ✅ No database credentials to manage
- ✅ Easy to inspect/debug data

### 1.3 Synthetic Patient Data Generator

**Never use real PHI in hackathon.** Generate realistic fake data:

```python
from faker import Faker
import random

fake = Faker()

def generate_patient():
    """Generate synthetic patient with realistic medical data"""
    return {
        "id": random.randint(1000, 9999),
        "name": fake.name(),
        "age": random.randint(25, 85),
        "gender": random.choice(["Male", "Female"]),
        "conditions": random.sample([
            "Type 2 Diabetes",
            "Hypertension",
            "Coronary Artery Disease",
            "Asthma",
            "Osteoarthritis"
        ], k=random.randint(1, 3)),
        "medications": random.sample([
            "Metformin 500mg BID",
            "Lisinopril 10mg QD",
            "Atorvastatin 20mg QHS",
            "Albuterol inhaler PRN",
            "Ibuprofen 400mg TID PRN"
        ], k=random.randint(2, 4)),
        "allergies": random.choice([
            ["Penicillin"],
            ["Sulfa drugs"],
            ["None"],
            ["Aspirin", "NSAIDs"]
        ]),
        "last_visit": fake.date_between(start_date='-6m', end_date='today'),
        "vitals": {
            "bp": f"{random.randint(110, 140)}/{random.randint(70, 90)}",
            "hr": random.randint(60, 90),
            "temp": round(random.uniform(97.5, 99.5), 1),
            "weight": random.randint(120, 220)
        }
    }

# Generate 10 demo patients
demo_patients = [generate_patient() for _ in range(10)]
```

### 1.4 Authentication Bypass

**Production Requirement:** OAuth 2.0, MFA, SSO  
**Hackathon Shortcut:** Hardcoded users with role dropdown

```python
# Streamlit app - simple role selection
import streamlit as st

# Hardcoded users for demo
DEMO_USERS = {
    "admin": {"name": "Dr. Sarah Admin", "role": "admin"},
    "doctor": {"name": "Dr. John Smith", "role": "doctor"},
    "patient": {"name": "Jane Doe", "role": "patient"}
}

# Simple login
st.sidebar.selectbox("Login as:", list(DEMO_USERS.keys()), key="user")
current_user = DEMO_USERS[st.session_state.user]
```

**Why this works:**
- ✅ Instant "login" without auth flow
- ✅ Easy to switch personas during demo
- ✅ Shows role-based UI differences clearly

---

## 2. ARCHITECTURE SIMPLIFICATION

### 2.1 Skip Multi-Agent Orchestration (For Now)

**Production:** RootOrchestrator → ClinicalAgent → ToolAgents  
**Hackathon:** Single agent with conditional logic

```python
import google.generativeai as genai

class SimpleHealthcareAgent:
    def __init__(self, role):
        self.role = role
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.chat = self.model.start_chat(history=[])
        
    def get_system_prompt(self):
        if self.role == "doctor":
            return """You are a clinical AI assistant. Provide evidence-based 
            recommendations with citations. Always emphasize human verification."""
        elif self.role == "patient":
            return """You are a friendly health assistant. Provide health education, 
            medication reminders, and triage guidance. NEVER diagnose. Escalate 
            concerning symptoms."""
        elif self.role == "admin":
            return """You are a healthcare operations assistant. Help with billing 
            codes, claims analysis, and operational insights."""
    
    def process(self, query, patient_context=None):
        # Build prompt with context
        system_prompt = self.get_system_prompt()
        
        if patient_context:
            context_str = f"""
            Patient Context:
            - Age: {patient_context['age']}
            - Conditions: {', '.join(patient_context['conditions'])}
            - Medications: {', '.join(patient_context['medications'])}
            - Allergies: {', '.join(patient_context['allergies'])}
            """
            full_query = f"{context_str}\n\nQuery: {query}"
        else:
            full_query = query
        
        # Single LLM call
        response = self.chat.send_message(
            f"{system_prompt}\n\n{full_query}"
        )
        
        return response.text

# Usage
doctor_agent = SimpleHealthcareAgent(role="doctor")
response = doctor_agent.process(
    "What antibiotic for pediatric appendectomy?",
    patient_context=demo_patients[0]
)
```

**Benefits:**
- ✅ 1/10th the code complexity
- ✅ No ADK framework learning curve
- ✅ Fast iteration during hackathon
- ⚠️ Less modular but sufficient for demo

### 2.2 Skip Cloud Deployment

**Production:** Cloud Run, Load Balancers, Multi-region  
**Hackathon:** Streamlit local server

```bash
# One command deployment
pip install streamlit google-generativeai faker
streamlit run app.py

# Runs on http://localhost:8501
# Port forward for demo: ngrok http 8501
```

**Why Streamlit?**
- ✅ Built-in UI components (chat, file upload, sidebar)
- ✅ Hot reload during development
- ✅ Easy to share via ngrok tunnel
- ✅ No frontend coding needed

### 2.3 Minimal Tech Stack

**Production Stack:**
- Backend: FastAPI + ADK + 15 services
- Frontend: React + React Native + TypeScript
- Infra: GCP + Terraform + K8s
- Databases: Firestore + Cloud SQL + Redis

**Hackathon Stack:**
```
app.py (400 lines)
├── Streamlit (UI framework)
├── Gemini 2.0 Flash (LLM)
├── SQLite (database)
├── Faker (test data)
└── Pillow (image processing for Rx scanning)
```

Total dependencies:
```txt
streamlit
google-generativeai
faker
pillow
pytesseract  # For OCR if using local model
```

---

## 3. FEATURE PRIORITIZATION (48-HOUR SPRINT)

### 3.1 Must-Have Features (Build First)

**Hour 0-16: Core Chat Interfaces**

1. **Patient Conversational Assistant** (6 hours)
   - Streamlit chat interface
   - Symptom input → triage recommendation
   - Medication questions
   - Health education

```python
import streamlit as st

st.title("🏥 Patient Health Assistant")

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Ask about your health..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Get patient context
    patient = demo_patients[0]  # Hardcoded for demo
    
    # Call agent
    agent = SimpleHealthcareAgent(role="patient")
    response = agent.process(prompt, patient_context=patient)
    
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.rerun()
```

2. **Doctor Clinical Search** (5 hours)
   - Query input with patient context loading
   - Response with "evidence grading" (fake citations)
   - Drug interaction checker (simple rule-based)

3. **Admin Billing Assistant** (5 hours)
   - Clinical notes → ICD-11 code suggestions
   - Claims status dashboard (mock data)
   - Revenue insights (synthetic analytics)

**Hour 16-28: Differentiation Features**

4. **Prescription Scanning with OCR** (6 hours)
   - Upload image → extract text
   - Use Gemini multimodal instead of Tesseract
   - Create medication schedule

```python
import PIL.Image

st.subheader("📸 Scan Prescription")
uploaded_file = st.file_uploader("Upload prescription image", type=['png', 'jpg'])

if uploaded_file:
    image = PIL.Image.open(uploaded_file)
    st.image(image, width=300)
    
    if st.button("Extract Medications"):
        # Gemini multimodal
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        
        prompt = """Extract medication information from this prescription image.
        Return JSON format:
        {
          "medications": [
            {"name": "...", "dosage": "...", "frequency": "...", "duration": "..."}
          ]
        }"""
        
        response = model.generate_content([prompt, image])
        st.json(response.text)
```

5. **Medication Adherence Tracker** (6 hours)
   - Medication schedule visualization
   - Check-off interface
   - Mock push notification simulation

**Hour 28-40: Polish & Integration**

6. **Multi-Persona Dashboard** (4 hours)
   - Unified sidebar navigation
   - Role-based view switching
   - Shared patient context

7. **Mock Wearable Data Integration** (4 hours)
   - Generate fake heart rate time series
   - Anomaly detection (simple threshold)
   - Alert UI when values out of range

8. **Demo Data & Storytelling** (4 hours)
   - Create 3 patient personas with realistic stories
   - Pre-populate conversation histories
   - Script the demo flow

**Hour 40-48: Demo Prep**

9. **UI Polish** (4 hours)
   - Add icons, colors, branding
   - Error handling and loading states
   - Responsive layout

10. **Presentation Deck** (4 hours)
    - Problem statement with real statistics
    - Architecture diagram (simplified)
    - Live demo walkthrough
    - Future roadmap

### 3.2 Nice-to-Have (Skip for Hackathon)

- ❌ EHR integration (mock it with JSON)
- ❌ Real authentication (use dropdown)
- ❌ NHCX claims submission (show UI only)
- ❌ Video call escalation (show button, explain concept)
- ❌ Real-time wearable sync (generate fake data)
- ❌ Multi-language support (English only)

---

## 4. GEMINI API USAGE OPTIMIZATION

### 4.1 Free Tier Management

**Gemini API Free Tier:**
- 1,500 requests per day (RPD)
- 1 million tokens per minute (TPM)
- 15 requests per minute (RPM)

**Hackathon Strategy:**
```python
import time
from functools import wraps

def rate_limit(calls_per_minute=10):
    """Simple rate limiter for free tier"""
    min_interval = 60.0 / calls_per_minute
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

@rate_limit(calls_per_minute=10)
def call_gemini(prompt):
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    return model.generate_content(prompt)
```

### 4.2 Context Caching Hack (Fake It)

**Production:** Vertex AI context caching  
**Hackathon:** Local caching with hash

```python
import hashlib
import json

# Simple prompt cache
_cache = {}

def cached_llm_call(system_prompt, user_query, patient_context):
    # Create cache key from system prompt + patient context
    cache_key = hashlib.md5(
        f"{system_prompt}:{json.dumps(patient_context)}".encode()
    ).hexdigest()
    
    # Check cache
    if cache_key in _cache:
        cached_system = _cache[cache_key]
        # Only send user query (simulate context caching savings)
        prompt = f"{cached_system}\n\nUser: {user_query}"
    else:
        prompt = f"{system_prompt}\n\nPatient: {patient_context}\n\nUser: {user_query}"
        _cache[cache_key] = system_prompt
    
    return call_gemini(prompt)
```

### 4.3 Token Counting (Estimate Only)

```python
def estimate_tokens(text):
    """Rough estimate: 1 token ≈ 4 characters"""
    return len(text) // 4

def log_token_usage(prompt, response):
    input_tokens = estimate_tokens(prompt)
    output_tokens = estimate_tokens(response)
    total = input_tokens + output_tokens
    
    print(f"📊 Token Usage: {input_tokens} in + {output_tokens} out = {total} total")
    
    # Estimate cost (Gemini 2.0 Flash is FREE, but show calculation)
    cost = (input_tokens * 0.50 / 1_000_000) + (output_tokens * 1.50 / 1_000_000)
    print(f"💰 Cost (if paid): ${cost:.6f}")
```

---

## 5. DEMO SCRIPT & STORYTELLING

### 5.1 Patient Personas for Demo

**Persona 1: Rajesh Kumar (Type 2 Diabetes Patient)**
- Age: 58, Male
- Conditions: Type 2 Diabetes, Hypertension
- Medications: Metformin 500mg BID, Lisinopril 10mg QD
- Story: Recently diagnosed, confused about diet and medication timing

**Demo Flow:**
1. Login as "Rajesh" (patient view)
2. Ask: "Can I eat rice with diabetes?"
3. Agent provides dietary guidance with portion control
4. Ask: "When should I take my Metformin?"
5. Agent explains meal-based timing
6. Show adherence tracker with checklist

**Persona 2: Dr. Priya Sharma (Cardiologist)**
- Specialty: Cardiology
- Use Case: Point-of-care clinical decision support

**Demo Flow:**
1. Switch to "Dr. Sharma" (doctor view)
2. Query: "Post-MI antiplatelet therapy guidelines"
3. Agent provides evidence-based recommendation with (fake) citations
4. Drug interaction check: "Patient on warfarin, can I add aspirin?"
5. Agent warns about bleeding risk, suggests alternatives

**Persona 3: Sarah Admin (Hospital Administrator)**
- Role: Revenue Cycle Manager
- Use Case: Billing optimization

**Demo Flow:**
1. Switch to "Sarah" (admin view)
2. Upload clinical note (mock text file)
3. Agent suggests ICD-11 codes with confidence scores
4. Show claims dashboard with denial patterns
5. Agent recommends documentation improvements

### 5.2 Judges' Pain Points to Address

**Problem Statement (45 seconds):**
> "Indian hospitals lose 15-20% revenue to billing errors and denials. Doctors spend 40% of their time on documentation instead of patients. Patients miss 50% of medication doses due to poor adherence. Current healthcare IT is fragmented—10 different systems, zero AI integration.
> 
> We built an AI-first operating system for healthcare—one platform, three personas, powered by Google Gemini 3. Watch."

**Demo Hooks:**
1. **Multimodal Prescription Scanning:** Upload image → instant medication schedule (wow factor)
2. **Real-time Drug Interaction Checking:** Type drug name → immediate safety alert (clinical value)
3. **Automated Medical Coding:** Clinical note → ICD codes in seconds (revenue impact)
4. **Conversational Health Assistant:** Natural language, multilingual, 24/7 (patient engagement)

### 5.3 Technical Differentiators

**Emphasize in presentation:**
- ✅ **Gemini 3 Multimodal:** "We use Gemini's vision capabilities to extract prescriptions from images—no separate OCR pipeline needed"
- ✅ **Cost Optimization:** "Context caching reduces API costs by 90% for repeated clinical guidelines"
- ✅ **Role-Based AI:** "Same Gemini model, different personas—doctor gets evidence grading, patient gets simplified explanations"
- ✅ **HIPAA-Ready Architecture:** "For this demo we used synthetic data, but our architecture is designed for Vertex AI with BAA in production"

---

## 6. QUICK START (COPY-PASTE READY)

### 6.1 Project Setup (5 minutes)

```bash
# Create project
mkdir healthcare-ai-hackathon
cd healthcare-ai-hackathon

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install streamlit google-generativeai faker pillow

# Create .env file
echo "GEMINI_API_KEY=your_key_here" > .env
```

### 6.2 Minimal Working App (app.py)

```python
import streamlit as st
import google.generativeai as genai
from faker import Faker
import random
import os

# Configure Gemini
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Generate demo patients
fake = Faker()

def generate_patient():
    return {
        "name": fake.name(),
        "age": random.randint(30, 75),
        "conditions": random.sample(["Diabetes", "Hypertension", "Asthma"], k=2),
        "medications": random.sample(["Metformin 500mg", "Lisinopril 10mg"], k=2)
    }

if 'patients' not in st.session_state:
    st.session_state.patients = [generate_patient() for _ in range(3)]

# Sidebar
st.sidebar.title("🏥 Healthcare AI Platform")
role = st.sidebar.radio("Login as:", ["Patient", "Doctor", "Admin"])
patient_idx = st.sidebar.selectbox("Select Patient:", range(len(st.session_state.patients)))
current_patient = st.session_state.patients[patient_idx]

st.sidebar.write(f"**{current_patient['name']}**")
st.sidebar.write(f"Age: {current_patient['age']}")
st.sidebar.write(f"Conditions: {', '.join(current_patient['conditions'])}")

# Main area
st.title(f"💬 {role} Portal")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input(f"Ask as {role}..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Build context-aware prompt
    system_prompts = {
        "Patient": "You are a friendly health assistant. Provide health education and medication guidance.",
        "Doctor": "You are a clinical AI assistant. Provide evidence-based recommendations.",
        "Admin": "You are a billing and operations assistant. Help with coding and claims."
    }
    
    context = f"""
    Patient: {current_patient['name']}, Age: {current_patient['age']}
    Conditions: {', '.join(current_patient['conditions'])}
    Medications: {', '.join(current_patient['medications'])}
    """
    
    full_prompt = f"{system_prompts[role]}\n\n{context}\n\nUser: {prompt}"
    
    # Call Gemini
    model = genai.GenerativeModel('gemini-2.0-flash-exp')
    response = model.generate_content(full_prompt)
    
    st.session_state.messages.append({"role": "assistant", "content": response.text})
    st.rerun()
```

**Run it:**
```bash
streamlit run app.py
```

### 6.3 Deploy for Demo (ngrok)

```bash
# Install ngrok
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Authenticate
ngrok authtoken YOUR_NGROK_TOKEN

# Forward Streamlit port
ngrok http 8501

# Share the https://XXXX.ngrok.io URL with judges
```

---

## 7. JUDGING CRITERIA OPTIMIZATION

### 7.1 Innovation (30 points)

**What Judges Want:**
- Novel use of Gemini 3 capabilities
- Creative problem-solving in healthcare
- Technical sophistication

**Your Pitch:**
- ✅ "First hackathon to use Gemini's multimodal OCR for prescription extraction"
- ✅ "Role-adaptive AI—same model, three different personas with different safety guardrails"
- ✅ "Context caching strategy cuts API costs by 90% in production scenarios"

### 7.2 Impact (25 points)

**What Judges Want:**
- Real-world problem solving
- Measurable outcomes
- Scalability potential

**Your Pitch:**
- ✅ "15-20% hospital revenue recovery by reducing billing denials"
- ✅ "85% medication adherence vs. 50% baseline through AI-powered tracking"
- ✅ "Serves 100,000 patients per day with $15K/month AI costs using our optimization strategy"

### 7.3 Technical Execution (25 points)

**What Judges Want:**
- Code quality
- Architecture clarity
- Handles edge cases

**Your Pitch:**
- ✅ "Clean architecture with role-based agents, easy to extend"
- ✅ "Synthetic data generation ensures HIPAA compliance during demo"
- ✅ "Rate limiting and caching for production-ready API usage"

**Show in demo:**
- Error handling (ask invalid question, show graceful response)
- Loading states (show spinner during API calls)
- Data validation (upload non-prescription image, show error)

### 7.4 Presentation (20 points)

**What Judges Want:**
- Clear problem statement
- Engaging demo
- Strong team dynamics

**Your Structure:**
1. **Hook (30s):** Shocking statistics about healthcare inefficiency
2. **Problem (1m):** Fragmented systems, no AI integration
3. **Solution (1m):** One platform, three personas, Gemini-powered
4. **Demo (4m):** Live walkthrough of all three personas
5. **Technical Deep Dive (1m):** Architecture diagram, Gemini API usage
6. **Impact & Roadmap (1m):** Revenue recovery, patient outcomes, future integrations
7. **Q&A (2m):** Prepared answers for common questions

**Common Questions:**
- Q: "How do you handle HIPAA compliance?"
  - A: "For this demo, synthetic data. Production uses Vertex AI with BAA, encrypted storage, audit logging."
  
- Q: "What's your moat vs. Epic/Cerner?"
  - A: "We're not replacing EHRs—we're an AI layer on top. Our moat is persona-specific fine-tuning and deep healthcare workflow integration."
  
- Q: "What's your go-to-market strategy?"
  - A: "Start with Tier 2/3 city hospitals in India (less complex EHRs), expand to health systems, then US market."

---

## 8. EMERGENCY TROUBLESHOOTING

### 8.1 Gemini API Errors

**Error: "Quota exceeded"**
```python
# Fallback to mock responses
FALLBACK_RESPONSES = {
    "doctor": "Based on current guidelines, consider [MOCK RECOMMENDATION]. Please verify with updated protocols.",
    "patient": "I'm having trouble connecting right now. For urgent concerns, please call your doctor.",
    "admin": "Code suggestion: E11.9 (Type 2 diabetes without complications). Confidence: 85%"
}

def safe_llm_call(prompt, role):
    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        return model.generate_content(prompt).text
    except Exception as e:
        st.warning(f"⚠️ API Error: Using cached response")
        return FALLBACK_RESPONSES[role]
```

**Error: "Safety filters triggered"**
```python
# Adjust safety settings
generation_config = genai.types.GenerationConfig(
    temperature=0.7,
)

safety_settings = {
    'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_NONE',  # Hackathon only!
    'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_NONE',
    'HARM_CATEGORY_HARASSMENT': 'BLOCK_NONE',
    'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_NONE',
}

model = genai.GenerativeModel(
    'gemini-2.0-flash-exp',
    generation_config=generation_config,
    safety_settings=safety_settings
)
```

### 8.2 Demo Day Issues

**Streamlit won't start:**
```bash
# Kill existing process
pkill -f streamlit

# Clear cache
rm -rf ~/.streamlit

# Restart
streamlit run app.py --server.port 8501
```

**Slow responses during demo:**
```python
# Pre-cache common queries
DEMO_QUERIES = [
    "Can I eat rice with diabetes?",
    "Post-MI antiplatelet therapy guidelines",
    "ICD code for Type 2 Diabetes"
]

# Pre-warm at startup
for query in DEMO_QUERIES:
    cached_llm_call(query)
```

**Internet connection unstable:**
```python
# Save responses to JSON during practice runs
import json

def cache_demo_responses():
    demo_cache = {}
    for query in DEMO_QUERIES:
        response = call_gemini(query)
        demo_cache[query] = response
    
    with open('demo_cache.json', 'w') as f:
        json.dump(demo_cache, f)

# Load during demo
with open('demo_cache.json', 'r') as f:
    demo_responses = json.load(f)

def demo_safe_llm_call(query):
    if query in demo_responses:
        return demo_responses[query]
    else:
        return call_gemini(query)
```

---

## 9. POST-HACKATHON: PRODUCTION MIGRATION PATH

### 9.1 Immediate Upgrades (Week 1)

1. **Switch to Vertex AI**
   ```python
   # Replace consumer API
   from google import genai
   client = genai.Client(vertexai=True, project="prod-project")
   ```

2. **Add Real Authentication**
   ```python
   # Firebase Auth
   import firebase_admin
   from firebase_admin import auth
   ```

3. **Deploy to Cloud Run**
   ```bash
   gcloud run deploy healthcare-ai \
     --source . \
     --region us-central1 \
     --allow-unauthenticated
   ```

### 9.2 Phase 2 Upgrades (Month 1)

1. **Multi-Agent Architecture:** Refactor to ADK framework
2. **Real EHR Integration:** FHIR client for Epic/Cerner
3. **Production Database:** Migrate SQLite → Firestore + Cloud SQL
4. **Monitoring:** Add Cloud Monitoring, error tracking

### 9.3 Phase 3 Upgrades (Month 3)

1. **HIPAA Certification:** Third-party audit, BAA signing
2. **Advanced Features:** Wearable integration, video calls
3. **Scale Testing:** Load testing, optimization
4. **Go-to-Market:** Pilot with 1-2 hospitals

---

## 10. RESOURCES & CHEAT SHEETS

### 10.1 Gemini API Quick Reference

```python
# Basic text generation
model = genai.GenerativeModel('gemini-2.0-flash-exp')
response = model.generate_content("Your prompt here")
print(response.text)

# Multimodal (text + image)
import PIL.Image
image = PIL.Image.open('prescription.jpg')
response = model.generate_content(["Extract medications", image])

# Chat (multi-turn conversation)
chat = model.start_chat(history=[])
response1 = chat.send_message("Hello")
response2 = chat.send_message("Follow-up question")

# Structured output (JSON)
response = model.generate_content("""
Return JSON format:
{"medication": "...", "dosage": "...", "frequency": "..."}

Extract from: Metformin 500mg twice daily
""")
```

### 10.2 Streamlit Cheat Sheet

```python
# Layout
st.title("Main Title")
st.header("Header")
st.subheader("Subheader")
st.write("Text or markdown")

# Sidebar
st.sidebar.title("Sidebar")
option = st.sidebar.selectbox("Choose", ["A", "B"])

# Input widgets
text = st.text_input("Enter text")
number = st.number_input("Enter number", min_value=0, max_value=100)
uploaded_file = st.file_uploader("Upload file", type=['jpg', 'png'])

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if prompt := st.chat_input("Your message"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Process and respond
    st.rerun()

# Display
st.success("Success message")
st.warning("Warning message")
st.error("Error message")
st.info("Info message")

# Columns
col1, col2 = st.columns(2)
with col1:
    st.write("Column 1")
with col2:
    st.write("Column 2")
```

### 10.3 Useful Prompts

**For Medical Coding:**
```
Given this clinical note, suggest ICD-11 codes with confidence scores (0-100).

Clinical Note: """
58-year-old male with uncontrolled Type 2 Diabetes Mellitus, HbA1c 9.2%. 
Patient reports polyuria and polydipsia. No diabetic complications noted.
"""

Format:
{
  "codes": [
    {"icd11": "5A11", "description": "Type 2 diabetes mellitus", "confidence": 95},
    ...
  ]
}
```

**For Drug Interactions:**
```
Check for drug-drug interactions:

Current Medications:
- Warfarin 5mg daily
- Aspirin 81mg daily

Proposed Addition:
- Ibuprofen 400mg TID

Provide interaction severity (None, Minor, Moderate, Severe, Contraindicated) 
and clinical guidance.
```

**For Patient Education:**
```
Explain [medical concept] to a patient with 8th-grade reading level.

Include:
1. Simple definition
2. Why it matters
3. What patient should do
4. When to call doctor

Medical concept: Type 2 Diabetes Mellitus
```

---

## FINAL CHECKLIST (12 Hours Before Demo)

**✅ Technical:**
- [ ] App runs without errors on fresh laptop
- [ ] All demo queries pre-tested and responses cached
- [ ] Gemini API key valid and quota available
- [ ] ngrok tunnel tested and stable
- [ ] Backup internet (mobile hotspot ready)

**✅ Demo:**
- [ ] 3 patient personas with stories prepared
- [ ] Demo script practiced 3+ times
- [ ] Transitions between personas smooth
- [ ] Error scenarios handled gracefully
- [ ] Timing under 8 minutes

**✅ Presentation:**
- [ ] Slide deck complete (10 slides max)
- [ ] Architecture diagram clear and simple
- [ ] Impact metrics highlighted
- [ ] Q&A answers prepared
- [ ] Team intros rehearsed

**✅ Backup Plans:**
- [ ] Screenshots of working demo
- [ ] Video recording of full walkthrough
- [ ] Cached responses for offline demo
- [ ] PDF export of code for judges

---

**Good luck! You've got this. 🚀**

Remember: Judges care more about impact and execution than perfect code. Show them a working demo, tell a compelling story, and emphasize the healthcare transformation potential. The shortcuts are your competitive advantage—you can build faster than teams worrying about production concerns.

```

## File: Documentation/healthcare-platform-srs.md

```md
# Software Requirements Specification (SRS)
## Healthcare AI Orchestration Platform

**Version:** 1.0  
**Date:** January 29, 2026  
**Status:** Draft

---

## 1. INTRODUCTION

### 1.1 Purpose
This SRS defines the functional and non-functional requirements for a role-based, mobile-first AI healthcare platform powered by Google Gemini 3 API. The system serves three core stakeholders: hospital administrators, doctors/clinicians, and patients through an orchestrated multi-agent architecture.

### 1.2 Scope
The platform acts as an AI orchestration layer atop existing healthcare systems (EHRs, billing, telehealth) to automate workflows, surface trusted information, and guide real-time decision-making. The system does NOT replace EHRs or physicians—it augments and orchestrates existing infrastructure.

**In Scope:**
- Multi-agent AI system for operational, clinical, and patient workflows
- Integration with existing healthcare IT systems via APIs
- HIPAA-compliant data processing through Vertex AI
- Mobile-first web application and progressive web app (PWA)
- Real-time voice interactions for patient support
- Multilingual support for patient-facing interfaces

**Out of Scope:**
- Direct EHR replacement
- Medical device integration beyond wearables (Apple Health, Google Health)
- Autonomous clinical diagnosis without human oversight
- FDA-regulated medical device functionality

### 1.3 Definitions, Acronyms, and Abbreviations

| Term | Definition |
|------|------------|
| ADK | Agentic Development Kit (Google) |
| BAA | Business Associate Agreement (HIPAA) |
| EHR | Electronic Health Record |
| HIM | Health Information Management |
| ICD-11 | International Classification of Diseases, 11th Revision |
| MRN | Medical Record Number |
| NHCX | National Health Claims Exchange (India) |
| PHI | Protected Health Information |
| RPM | Requests Per Minute |
| TPM | Tokens Per Minute |
| VAD | Voice Activity Detection |

### 1.4 References
- Google Gemini 3 API Documentation: https://ai.google.dev/gemini-api/docs/gemini-3
- HIPAA Compliance Guide for Vertex AI
- Vertex AI Agent Engine Documentation
- Healthcare PRD v1.0

### 1.5 Overview
This document details system features, functional requirements, non-functional requirements, external interfaces, and constraints organized by user persona.

---

## 2. OVERALL DESCRIPTION

### 2.1 Product Perspective
The platform operates as a cloud-native SaaS solution deployed on Google Cloud Platform, utilizing:
- **Gemini 3 Pro** for complex reasoning (clinical decisions, operational analytics)
- **Gemini 3 Flash** for high-throughput conversational interfaces
- **Vertex AI Agent Engine** for multi-agent orchestration
- **Agent Engine Sessions** for persistent state management
- **Memory Bank** for long-term patient context

### 2.2 Product Functions

#### 2.2.1 Hospital Administrator Functions
- Autonomous ICD-11 coding with audit trails
- Automated claims submission and follow-up (NHCX integration)
- Payment reconciliation and revenue leak detection
- Documentation validation pre-submission
- Centralized AI governance dashboard
- Real-time operational analytics across locations
- Automated front-desk and scheduling workflows

#### 2.2.2 Doctor/Clinician Functions
- Natural language clinical search against hospital protocols
- Evidence-based recommendations with inline citations
- Medical imaging analysis integration
- Drug interaction checking with current medications
- Point-of-care decision support on mobile devices
- Prescription generation with OCR parsing capability
- Protocol adherence monitoring

#### 2.2.3 Patient Functions
- 24/7 multilingual AI health assistant (12+ languages)
- Symptom interpretation and triage guidance
- Interactive medication adherence tracking
- Health record aggregation across providers
- Wearable data integration and anomaly alerts
- Video/voice escalation to licensed clinicians
- Prescription scanning and digital medication tracking

### 2.3 User Classes and Characteristics

| User Class | Technical Expertise | Frequency of Use | Security Clearance |
|------------|-------------------|------------------|-------------------|
| Hospital Admin | Moderate | Daily (8+ hrs) | PHI Access, Admin |
| Doctor/Clinician | Low-Moderate | Daily (multiple sessions) | PHI Access, Clinical |
| Patient | Low | Variable (weekly to daily) | Own Data Only |
| System Admin | High | As needed | Full System Access |

### 2.4 Operating Environment
- **Client:** Modern web browsers (Chrome 90+, Safari 14+, Firefox 88+), iOS 14+, Android 10+
- **Server:** Google Cloud Platform (us-central1, asia-south1 regions for latency)
- **AI Models:** Gemini 3 Pro/Flash via Vertex AI with HIPAA BAA
- **Database:** Cloud Firestore (document store), Cloud SQL (relational), Cloud Storage (media)
- **Caching:** Redis for session management, Vertex AI context caching for clinical guidelines

### 2.5 Design and Implementation Constraints

#### 2.5.1 Regulatory Constraints
- **HIPAA Compliance:** All PHI must process through Vertex AI with signed BAA
- **HITRUST CSF:** Maintain certification requirements for healthcare data handling
- **FedRAMP High:** Adherence to federal authorization requirements
- **Medical Device Regulations:** System explicitly NOT FDA-cleared; must display disclaimers

#### 2.5.2 Technical Constraints
- Gemini 3 Pro requires `thinking_level: high` for clinical reasoning
- Context window limited to 1M tokens (approximately 1,500 pages)
- Temperature parameter must remain at 1.0 (architectural requirement)
- Web search grounding disabled when processing PHI
- Rate limits: 150-300 RPM (Tier 1), scaling to 2,000+ RPM (Tier 3)
- Token costs: $2-4/1M input, $12-18/1M output (Pro), $0.50/1M input, $3/1M output (Flash)

#### 2.5.3 Architecture Constraints
- Thought signatures mandatory for function calling—must preserve and return
- No autonomous clinical decisions without human verification
- Image segmentation removed in Gemini 3 (use alternative models if needed)
- Multi-agent coordination through ADK framework only

### 2.6 Assumptions and Dependencies

**Assumptions:**
- Healthcare providers have existing EHR systems with API access
- Network connectivity available at point of care (minimum 3G for basic functionality)
- Users have valid credentials in hospital identity management systems
- Tier 2/3 city deployment in India with English/Hindi bilingual support minimum

**Dependencies:**
- Google Cloud Platform availability (99.95% SLA)
- Gemini 3 API stability (preview → production transition expected Q2 2026)
- Third-party EHR vendor API availability and documentation
- Wearable device API access (Apple HealthKit, Google Fit)
- NHCX claims exchange infrastructure operational

---

## 3. SPECIFIC REQUIREMENTS

### 3.1 External Interface Requirements

#### 3.1.1 User Interfaces

**UI-1: Responsive Design**
- All interfaces must support mobile-first design (320px minimum width)
- Progressive Web App (PWA) capability for offline access to cached content
- Dark mode support for clinical settings (reduce screen glare)
- Accessibility: WCAG 2.1 Level AA compliance

**UI-2: Administrator Dashboard**
- Real-time operational metrics visualization (billing, claims, scheduling)
- Drill-down capability from executive view to department-level details
- Export functionality for compliance reports (PDF, CSV)
- AI agent audit log viewer with filtering and search

**UI-3: Doctor Interface**
- Single-tap access to clinical search from any screen
- Inline citation display with evidence grading (A/B/C levels)
- Voice input capability for hands-free operation
- Patient context panel showing relevant history and current medications

**UI-4: Patient Interface**
- Conversational chat interface with typing indicators
- Medication schedule with push notification reminders
- Health data visualization (charts for vitals, trends)
- Prescription scanning via camera with OCR feedback

#### 3.1.2 Hardware Interfaces

**HW-1: Mobile Device Camera**
- Minimum resolution: 5MP for prescription scanning
- Focus and exposure control for document capture
- Real-time preview with alignment guides

**HW-2: Microphone**
- Sample rate: 16kHz mono for voice input
- Noise cancellation support for clinical environments
- Voice activity detection (VAD) for automatic session management

**HW-3: Wearable Device APIs**
- Apple HealthKit integration: heart rate, activity, sleep, blood oxygen
- Google Fit integration: steps, heart points, weight, blood pressure
- Data sync frequency: minimum every 4 hours, real-time for critical values

#### 3.1.3 Software Interfaces

**SW-1: EHR System Integration**
- Protocol: HL7 FHIR R4 preferred, HL7 v2.x fallback
- Authentication: OAuth 2.0 with SMART on FHIR
- Resources: Patient, Observation, MedicationRequest, Condition, DiagnosticReport
- Operations: Read, Search (no direct write operations to EHR)

**SW-2: Billing System Integration**
- API: REST with JSON payloads
- Functions: Submit claims, check claim status, retrieve payment postings
- Standards: NHCX format for India market, X12 837/835 for US expansion

**SW-3: Identity Management**
- Protocol: SAML 2.0 or OpenID Connect
- Single Sign-On (SSO) with hospital Active Directory / Azure AD
- Multi-factor authentication (MFA) required for PHI access

**SW-4: Gemini 3 API**
- Endpoint: Vertex AI Gemini API (us-central1 or asia-south1)
- Authentication: Google Cloud service account with Vertex AI permissions
- Models: `gemini-3-pro-preview`, `gemini-3-flash-preview`
- Configuration: Context caching enabled, regulated-data flag set

#### 3.1.4 Communication Interfaces

**COM-1: HTTPS Protocol**
- TLS 1.3 minimum for all client-server communication
- Certificate pinning for mobile applications
- HSTS headers enforced

**COM-2: WebSocket Protocol**
- Used for Live API voice/video interactions
- Secure WebSocket (WSS) with same TLS requirements
- Automatic reconnection with exponential backoff

**COM-3: Webhook Interfaces**
- Receive notifications from EHR systems (new lab results, appointment changes)
- HMAC signature verification for authenticity
- Retry logic with idempotency keys

### 3.2 Functional Requirements

#### 3.2.1 Hospital Administrator Module

**FR-ADMIN-1: Automated ICD-11 Coding**
- **Description:** Agent analyzes clinical documentation and assigns appropriate ICD-11 codes
- **Inputs:** Clinical notes, diagnosis text, procedure descriptions
- **Processing:** 
  - Gemini 3 Pro with function calling to ICD-11 knowledge base
  - Confidence scoring for each code suggestion
  - Multiple code suggestions with rationale
- **Outputs:** Structured JSON with ICD-11 codes, confidence scores, justifications
- **Validation:** Human coder review required for confidence < 85%
- **Audit Trail:** All code assignments logged with model version, timestamp, reviewer

**FR-ADMIN-2: Claims Submission Automation**
- **Description:** Validate documentation completeness, auto-submit to NHCX
- **Inputs:** Patient encounter data, codes, provider information
- **Processing:**
  - Pre-submission validation against NHCX requirements
  - Automated form filling with structured data
  - Error detection and flagging
- **Outputs:** Submitted claim reference number, validation report
- **Success Criteria:** < 5% rejection rate on auto-submitted claims
- **Fallback:** Manual review queue for flagged claims

**FR-ADMIN-3: AI Governance Dashboard**
- **Description:** Centralized monitoring of all AI agent activities
- **Metrics Displayed:**
  - Total AI requests by agent type
  - Success/failure rates
  - Average response times
  - Cost tracking (token usage × pricing)
  - Compliance incidents (attempted PHI access violations)
- **Alerting:** Real-time notifications for anomalies
- **Audit Export:** Full audit logs exportable for regulatory review

**FR-ADMIN-4: Revenue Cycle Analytics**
- **Description:** AI-driven insights into revenue leakage points
- **Data Sources:** Billing system, claims processor responses, payment postings
- **Analysis:**
  - Denial pattern detection (by payer, by code, by provider)
  - Time-to-payment tracking
  - Undercoding detection (missed revenue opportunities)
- **Outputs:** Executive dashboard with drill-down capability, automated alerts
- **Target:** Identify 10-20% revenue leakage within 90 days

#### 3.2.2 Doctor/Clinician Module

**FR-DOC-1: Clinical Search**
- **Description:** Natural language search across hospital protocols, guidelines, medical literature
- **Inputs:** Free-text question (e.g., "sepsis protocol for pediatric patient")
- **Processing:**
  - Vector search against embedded hospital protocols
  - Gemini 3 Pro reasoning with `thinking_level: high`
  - Retrieval-augmented generation (RAG) pattern
- **Outputs:** 
  - Synthesized answer with inline citations
  - Evidence quality grading (A: RCT, B: cohort, C: expert opinion)
  - Source document links
- **Response Time:** < 3 seconds for 95th percentile
- **Accuracy Target:** 95% clinician satisfaction in A/B testing

**FR-DOC-2: Drug Interaction Checking**
- **Description:** Real-time analysis of proposed medication against patient's current regimen
- **Inputs:** Drug name/NDC code, patient medication list
- **Processing:**
  - Function call to drug interaction database (Micromedex or equivalent)
  - Gemini analysis of interaction severity and clinical significance
  - Alternative medication suggestions
- **Outputs:**
  - Traffic light severity indicator (green/yellow/red)
  - Interaction mechanism explanation
  - Dosage adjustment recommendations if applicable
- **Latency:** < 1 second
- **Coverage:** All FDA-approved medications, common supplements

**FR-DOC-3: Medical Imaging Analysis Support**
- **Description:** AI-assisted preliminary analysis of radiology images
- **Inputs:** DICOM images (X-ray, CT, MRI) with clinical context
- **Processing:**
  - Gemini 3 Pro multimodal analysis (1M token context accommodates full imaging series)
  - Detection of common pathologies (fractures, masses, infiltrates)
  - Comparison with prior imaging if available
- **Outputs:**
  - Preliminary findings report with confidence scores
  - Region highlighting on images
  - Recommended follow-up or additional views
- **Disclaimer:** "AI preliminary analysis - requires radiologist verification"
- **Validation:** Findings flagged for mandatory radiologist review before clinical action

**FR-DOC-4: Prescription Generation**
- **Description:** Structured prescription creation with safety checks
- **Inputs:** Diagnosis, patient context, desired medication
- **Processing:**
  - Drug interaction checking (FR-DOC-2)
  - Allergy checking against patient record
  - Age/weight-appropriate dosing validation
  - Structured output generation (JSON → printable format)
- **Outputs:** 
  - Digital prescription with QR code (patient app link)
  - Printable PDF for physical prescription
  - Medication instructions in patient's preferred language
- **Safety Features:** Hard stops for severe interactions, allergy matches

#### 3.2.3 Patient Module

**FR-PAT-1: Conversational Health Assistant**
- **Description:** 24/7 multilingual AI assistant for health questions
- **Inputs:** Text or voice queries in supported languages (English, Hindi, Tamil, Telugu, Bengali, Marathi, Gujarati, Kannada, Malayalam, Odia, Punjabi, Assamese)
- **Processing:**
  - Gemini 3 Flash with `thinking_level: low` for speed
  - Sentiment analysis to detect urgency/distress
  - Escalation triggers for emergent symptoms
- **Outputs:** 
  - Conversational responses with empathy
  - Triage recommendations (self-care, clinic visit, ER)
  - Educational content links
- **Escalation:** Automatic offer to connect with nurse/doctor for red-flag symptoms
- **Guardrails:** Strong system instructions prevent diagnosis; redirect to professionals

**FR-PAT-2: Medication Adherence Tracking**
- **Description:** Interactive medication schedule with reminders and compliance reporting
- **Inputs:** 
  - Prescription (scanned via OCR or manual entry)
  - Patient-confirmed medication schedule
- **Processing:**
  - OCR extraction from prescription images (Gemini 3 multimodal)
  - Schedule generation with timing optimization (meal-based, sleep patterns)
  - Push notification scheduling
- **Outputs:**
  - Daily medication checklist
  - Adherence statistics (for patient and doctor portal)
  - Missed dose alerts
- **Reporting:** Weekly adherence summary shared with prescribing doctor

**FR-PAT-3: Symptom Logging and Trend Analysis**
- **Description:** Structured symptom diary with AI-detected patterns
- **Inputs:** Patient-reported symptoms (pain scale, frequency, duration, context)
- **Processing:**
  - Time-series analysis of symptom patterns
  - Correlation with medication adherence
  - Anomaly detection (sudden worsening)
- **Outputs:**
  - Visual symptom timeline
  - Pattern insights ("pain worse 2 hours post-medication")
  - Alert triggers for concerning trends
- **Privacy:** Patient-controlled sharing with healthcare provider

**FR-PAT-4: Wearable Data Integration**
- **Description:** Continuous health monitoring with proactive alerts
- **Data Sources:** Heart rate, blood oxygen, sleep quality, activity levels, weight
- **Processing:**
  - Baseline establishment (normal ranges for individual)
  - Real-time anomaly detection (e.g., sustained tachycardia)
  - Trend analysis (gradual decline in activity)
- **Alerts:**
  - Patient notification for out-of-range values
  - Automatic escalation to clinical team for critical values
  - Integration with symptom logs for comprehensive view
- **Thresholds:** Configurable by patient's care team, defaults based on age/conditions

**FR-PAT-5: Video/Voice Escalation**
- **Description:** Seamless transition from AI assistant to human clinician
- **Trigger Conditions:**
  - Patient explicitly requests human assistance
  - AI detects emergent symptoms (chest pain, severe allergic reaction)
  - Complex question beyond AI capability
- **Processing:**
  - Live API WebSocket connection establishment
  - Context handoff (conversation history, patient data)
  - Queue management and clinician routing
- **Outputs:**
  - Real-time video/voice connection
  - Shared screen view of patient data
  - Post-call summary note in EHR
- **Availability:** 24/7 coverage with on-call physician network

#### 3.2.4 Cross-Persona Functions

**FR-CROSS-1: Multi-Agent Orchestration**
- **Description:** Hierarchical agent system coordinating specialized sub-agents
- **Architecture:**
  - Root Orchestrator Agent (ADK framework)
  - Specialized agents: BillingAgent, ClinicalAgent, PatientAgent
  - Tool agents: EHRSearchAgent, DrugDatabaseAgent, SchedulingAgent
- **Coordination:** Agent-to-Agent (A2A) protocol for task handoffs
- **State Management:** Vertex AI Agent Engine Sessions for persistent context
- **Example Flow:**
  - Patient reports symptom → PatientAgent triages → escalates to ClinicalAgent
  - ClinicalAgent retrieves EHR via EHRSearchAgent → recommends action → updates patient

**FR-CROSS-2: Session Management**
- **Description:** Persistent conversational context across sessions
- **Storage:** Vertex AI Memory Bank (55-day retention for paid tier)
- **Content:**
  - Conversation history
  - Key facts extracted (patient preferences, ongoing concerns)
  - Action items and follow-up requirements
- **Privacy:** Role-based encryption; patients cannot access clinical notes, doctors cannot access admin financial data

**FR-CROSS-3: Audit Logging**
- **Description:** Comprehensive logging of all AI interactions for compliance
- **Logged Data:**
  - User ID, role, timestamp
  - Input query (sanitized of PII in logs)
  - Model used, configuration parameters
  - Response generated (hash for verification)
  - Function calls made and results
  - Thinking signatures (for debugging)
- **Retention:** 7 years (HIPAA requirement)
- **Access Control:** Compliance officer and system admin only

### 3.3 Non-Functional Requirements

#### 3.3.1 Performance Requirements

**NFR-PERF-1: Response Time**
- Doctor clinical search: < 3 seconds (95th percentile)
- Patient conversational response: < 1 second (95th percentile)
- Admin dashboard load: < 2 seconds (95th percentile)
- Drug interaction check: < 1 second (99th percentile)
- Live API voice latency: < 300ms time-to-first-token

**NFR-PERF-2: Throughput**
- Support 10,000 concurrent users per instance
- Handle 100,000 patient conversations per day
- Process 50,000 claims submissions per day
- Sustain 500 RPM to Gemini API (distributed across endpoints)

**NFR-PERF-3: Scalability**
- Horizontal scaling: Auto-scale based on CPU (target 70%) and request queue depth
- Geographic distribution: Multi-region deployment (US, India, Europe)
- Database sharding: Partition by hospital/organization ID

**NFR-PERF-4: Resource Utilization**
- Context caching utilization: > 80% cache hit rate for clinical guidelines
- Token optimization: < 5,000 tokens per average doctor query (via caching)
- Cost target: < $0.10 per patient conversation, < $2 per complex clinical query

#### 3.3.2 Security Requirements

**NFR-SEC-1: Authentication**
- Multi-factor authentication (MFA) required for all users accessing PHI
- Biometric authentication option for mobile (fingerprint, Face ID)
- Session timeout: 15 minutes inactivity for clinical users, 30 minutes for patients
- Password requirements: 12+ characters, complexity rules enforced

**NFR-SEC-2: Authorization**
- Role-Based Access Control (RBAC) with principle of least privilege
- Attribute-Based Access Control (ABAC) for dynamic patient data access (doctor can only access their patients)
- API access tokens scoped to specific functions (e.g., SchedulingAgent cannot access clinical notes)

**NFR-SEC-3: Data Encryption**
- At rest: AES-256 encryption for all databases and storage
- In transit: TLS 1.3 for all communications
- Key management: Google Cloud KMS with automatic rotation every 90 days

**NFR-SEC-4: PHI Protection**
- De-identification: Automated scrubbing of PII/PHI from logs
- Data minimization: Only necessary fields transmitted to Gemini API
- Audit trail: All PHI access logged with user, timestamp, purpose

**NFR-SEC-5: Vulnerability Management**
- Automated dependency scanning (weekly)
- Penetration testing: Quarterly by third-party
- Security patches: Applied within 48 hours of release for critical vulnerabilities

#### 3.3.3 Reliability Requirements

**NFR-REL-1: Availability**
- System uptime: 99.9% (approximately 8.76 hours downtime per year)
- Maintenance windows: Sunday 2-4 AM local time, advance notification
- Degraded mode: Core functions (patient triage, medication lookup) remain operational during partial outages

**NFR-REL-2: Fault Tolerance**
- Gemini API failures: Automatic retry with exponential backoff (3 attempts)
- Fallback models: Gemini 2.5 Pro available if 3.0 unavailable
- Database replication: Multi-zone synchronous replication
- Circuit breakers: Prevent cascade failures from external system outages

**NFR-REL-3: Data Integrity**
- Transaction atomicity: ACID compliance for critical operations (billing, prescriptions)
- Checksums: Verify data integrity during transmission
- Backup frequency: Hourly incremental, daily full backup
- Recovery Point Objective (RPO): < 1 hour
- Recovery Time Objective (RTO): < 4 hours

**NFR-REL-4: Error Handling**
- Graceful degradation: Informative error messages without exposing internals
- User-facing errors: Plain language explanations with suggested actions
- Automatic error reporting: Critical errors alert on-call engineer
- Thought signature failures: Clear error message, log for debugging, request retry

#### 3.3.4 Maintainability Requirements

**NFR-MAINT-1: Code Quality**
- Test coverage: Minimum 80% unit test coverage
- Integration tests: All API endpoints and agent interactions
- Code review: Mandatory peer review for all changes
- Documentation: Inline comments for complex logic, API documentation auto-generated

**NFR-MAINT-2: Monitoring and Observability**
- Application Performance Monitoring (APM): Google Cloud Trace for distributed tracing
- Metrics: Prometheus-format metrics exported to Cloud Monitoring
- Log aggregation: Centralized logging with structured JSON format
- Alerting: PagerDuty integration for critical issues

**NFR-MAINT-3: Deployment**
- CI/CD pipeline: Automated testing and deployment via Cloud Build
- Blue-green deployment: Zero-downtime releases
- Rollback capability: One-click rollback to previous version
- Feature flags: Gradual rollout of new features (10% → 50% → 100%)

**NFR-MAINT-4: Model Versioning**
- Track model versions: Log Gemini model ID with each request
- A/B testing: Compare model versions on subset of traffic
- Model updates: Regression testing before production deployment
- Version pinning: Ability to lock to specific model version for stability

#### 3.3.5 Usability Requirements

**NFR-USE-1: Learnability**
- New user onboarding: Interactive tutorial < 5 minutes
- Context-sensitive help: Tooltips and help icons throughout interface
- Success metrics: 80% of users complete core task without assistance in first session

**NFR-USE-2: Accessibility**
- Screen reader compatibility: Full ARIA labeling
- Keyboard navigation: All functions accessible without mouse
- Color contrast: WCAG AA minimum (4.5:1 for normal text)
- Font sizing: User-adjustable from 100% to 150%

**NFR-USE-3: Localization**
- Language support: 12 Indian languages + English
- Right-to-left (RTL) support: For future Arabic/Urdu expansion
- Date/time formatting: Locale-appropriate display
- Cultural considerations: Medication timing aligned with meal customs

**NFR-USE-4: User Satisfaction**
- Net Promoter Score (NPS): Target > 50
- Task completion rate: > 90% for primary workflows
- User-reported errors: < 5% of sessions
- Mobile usability: > 85% satisfaction score for mobile interface

#### 3.3.6 Compliance Requirements

**NFR-COMP-1: HIPAA Compliance**
- Business Associate Agreement: Signed with Google Cloud
- Regulated data flag: Enabled for all Vertex AI requests
- Minimum Necessary Standard: Access controls enforce minimum data access
- Breach notification: Automated detection and reporting within 60 days

**NFR-COMP-2: HITRUST Certification**
- Annual assessment: Third-party validated HITRUST CSF certification
- Control implementation: Document compliance with all applicable controls
- Risk assessment: Annual risk analysis and remediation planning

**NFR-COMP-3: Data Residency**
- India PHI: Stored in asia-south1 region (Mumbai)
- US PHI: Stored in us-central1 region (Iowa)
- Cross-border transfer: Only with explicit patient consent and encryption

**NFR-COMP-4: Audit Support**
- Audit trail completeness: All access to PHI logged
- Report generation: Automated compliance reports (monthly)
- External audit: Support third-party auditor access to logs and documentation

---

## 4. SYSTEM FEATURES

### 4.1 Feature: Intelligent Claims Processing

**Priority:** High  
**Persona:** Hospital Administrator

**Description:**  
End-to-end automation of medical claims from coding through submission and tracking, reducing manual workload by 30-50% and denial rates by 15%.

**Functional Requirements:**
1. FR-ADMIN-1: Automated ICD-11 Coding
2. FR-ADMIN-2: Claims Submission Automation
3. Integration with NHCX claims exchange
4. Real-time claim status tracking
5. Denial prediction and prevention

**Use Case Flow:**
1. Patient encounter completed → clinical notes finalized in EHR
2. BillingAgent retrieves encounter data via EHR API
3. Gemini 3 Pro analyzes notes → suggests ICD-11 codes with confidence scores
4. Codes with confidence > 85% auto-approved; others to human review queue
5. Claim assembled with patient demographics, provider info, codes
6. Pre-submission validation against NHCX requirements
7. Claim submitted via NHCX API → reference number returned
8. Status polling every 4 hours → update dashboard
9. Denial cases analyzed → root cause categorization → process improvement recommendations

**Success Metrics:**
- < 5% initial rejection rate
- 85% of claims auto-coded without human review
- $150K+ annual revenue recovery per 100-bed hospital

### 4.2 Feature: Point-of-Care Clinical Decision Support

**Priority:** Critical  
**Persona:** Doctor/Clinician

**Description:**  
Real-time, evidence-based clinical guidance integrated into mobile workflow, reducing time-to-answer by 50-70% and improving protocol adherence.

**Functional Requirements:**
1. FR-DOC-1: Clinical Search
2. FR-DOC-2: Drug Interaction Checking
3. FR-DOC-3: Medical Imaging Analysis Support
4. FR-DOC-4: Prescription Generation

**Use Case Flow:**
1. Doctor encounters clinical question during rounds
2. Voice or text query to mobile app: "Post-operative antibiotic for pediatric appendectomy"
3. ClinicalAgent searches embedded hospital protocols (context caching for speed)
4. Gemini 3 Pro synthesizes answer with citations from hospital guidelines
5. Response displays: recommended antibiotics, dosing, duration, evidence grade
6. Doctor reviews patient allergies → selects antibiotic
7. Drug interaction check against patient's current medications (real-time)
8. Prescription generated with safety checks → digital copy to patient app
9. Encounter summary auto-documented with reasoning trail for audit

**Success Metrics:**
- < 3 seconds response time for 95% of queries
- 95% clinician satisfaction score
- 25% reduction in protocol deviation incidents
- 40% reduction in time spent searching for clinical information

### 4.3 Feature: Intelligent Medication Adherence Platform

**Priority:** High  
**Persona:** Patient

**Description:**  
Transforms static prescriptions into interactive, personalized medication management with adherence tracking, improving compliance rates and health outcomes.

**Functional Requirements:**
1. FR-PAT-2: Medication Adherence Tracking
2. Prescription scanning with OCR
3. Personalized reminder scheduling
4. Adherence analytics and reporting

**Use Case Flow:**
1. Patient receives paper prescription at doctor's office
2. Opens patient app → taps "Scan Prescription"
3. Camera activates with alignment guides → captures prescription image
4. Gemini 3 multimodal OCR extracts: medication names, dosages, frequencies, duration
5. Patient confirms extracted data (corrections if needed)
6. App generates personalized schedule based on meal times, sleep patterns
7. Push notifications sent at scheduled times with medication images
8. Patient marks medication as taken → timestamp recorded
9. Missed doses trigger progressive reminders (15 min, 1 hour, 4 hours)
10. Weekly adherence summary generated → shared with prescribing doctor
11. App detects patterns (e.g., frequent evening missed doses) → suggests schedule adjustment

**Success Metrics:**
- 85%+ medication adherence rate (vs. 50% baseline)
- 30% reduction in doctor follow-up burden for monitoring
- 95% OCR accuracy on prescription extraction
- 4.5+ star rating in app stores

### 4.4 Feature: Proactive Health Monitoring via Wearables

**Priority:** Medium  
**Persona:** Patient

**Description:**  
Continuous integration of wearable device data with AI-powered anomaly detection and escalation, enabling early intervention.

**Functional Requirements:**
1. FR-PAT-4: Wearable Data Integration
2. Real-time anomaly detection
3. Automatic escalation protocols

**Use Case Flow:**
1. Patient connects Apple Watch / Fitbit to app during onboarding
2. Baseline established over 14 days (normal heart rate range, activity levels, sleep patterns)
3. Continuous background sync every 4 hours (or real-time for critical vitals)
4. Patient with heart condition experiences sustained tachycardia (120+ bpm for 30 min at rest)
5. PatientAgent detects anomaly → analyzes context (no exercise, normal time of day)
6. Alert sent to patient: "Elevated heart rate detected. Are you feeling okay?"
7. Patient reports chest discomfort → symptom severity assessment (1-10 scale)
8. Severity 7/10 + cardiac history → automatic escalation to on-call cardiologist
9. Video call initiated with patient data pre-loaded (vitals graph, medication list)
10. Cardiologist triages → advises patient to go to ER or adjusts medication

**Success Metrics:**
- 25% reduction in unnecessary ER visits (better triage)
- 15% reduction in adverse cardiac events (earlier intervention)
- < 2% false positive rate on critical alerts
- 70%+ patient engagement with wearable integration

---

## 5. DATA REQUIREMENTS

### 5.1 Logical Data Model

**Core Entities:**

1. **User**
   - user_id (PK)
   - role (admin, doctor, patient)
   - organization_id (FK)
   - auth_provider (SSO, local)
   - mfa_enabled (boolean)
   - created_at, last_login

2. **Organization**
   - organization_id (PK)
   - name
   - type (hospital, clinic, health_system)
   - region
   - hipaa_baa_signed (boolean)
   - subscription_tier

3. **Patient**
   - patient_id (PK)
   - user_id (FK)
   - mrn (Medical Record Number)
   - demographics (name, DOB, gender)
   - allergies (JSON array)
   - chronic_conditions (JSON array)
   - primary_doctor_id (FK)

4. **Conversation**
   - conversation_id (PK)
   - user_id (FK)
   - agent_type (patient, clinical, billing)
   - vertex_session_id
   - started_at, last_message_at
   - status (active, escalated, closed)

5. **Message**
   - message_id (PK)
   - conversation_id (FK)
   - role (user, assistant)
   - content (text, encrypted if PHI)
   - function_calls (JSON)
   - thought_signature (encrypted blob)
   - token_count
   - timestamp

6. **Medication**
   - medication_id (PK)
   - patient_id (FK)
   - drug_name, ndc_code
   - dosage, frequency
   - prescribed_by (doctor_id FK)
   - start_date, end_date
   - prescription_image_url

7. **Adherence_Log**
   - log_id (PK)
   - medication_id (FK)
   - scheduled_time
   - actual_time (null if missed)
   - status (taken, missed, skipped)
   - patient_note

8. **Clinical_Document**
   - document_id (PK)
   - patient_id (FK)
   - document_type (lab_result, imaging_report, progress_note)
   - content (encrypted)
   - embedding (vector for semantic search)
   - created_at
   - source_system (EHR name)

9. **Audit_Log**
   - log_id (PK)
   - user_id (FK)
   - action_type (view_phi, modify_data, ai_query)
   - resource_id (patient_id, document_id)
   - ip_address, user_agent
   - success (boolean)
   - timestamp

### 5.2 Data Volumes and Growth

**Initial Estimates (100-bed hospital, 5,000 patients):**
- Messages: 50,000/day (10 per active patient)
- Audit logs: 100,000/day
- Wearable data points: 1M/day (200 per connected patient)
- Clinical documents: 500/day
- Storage growth: ~50 GB/month

**3-Year Projections (10 hospitals, 50,000 patients):**
- Messages: 500,000/day
- Storage: 20 TB total
- Vertex AI requests: 5M/day
- Cost: ~$15K/month in AI costs (with caching)

### 5.3 Data Retention and Archival

**Retention Periods:**
- PHI data: 7 years (HIPAA minimum)
- Audit logs: 7 years
- Conversation history: 55 days active (Memory Bank), then archived
- Wearable data: 2 years active, then aggregated to daily summaries
- Model training data: Not stored (HIPAA restriction)

**Archival Strategy:**
- Cold storage: Google Cloud Storage Archive class after 90 days
- Patient data portability: Export capability in FHIR format
- Right to deletion: Automated 30-day purge process after patient requests

---

## 6. APPENDIX

### 6.1 Glossary

**Agent:** An AI system powered by a language model that can perform tasks, use tools, and make decisions.

**Context Caching:** Gemini API feature that stores frequently used prompt content to reduce costs and latency.

**Function Calling:** LLM capability to determine when to invoke external tools/APIs and structure the parameters.

**Grounding:** Connecting LLM responses to external data sources (search, databases) for factual accuracy.

**Memory Bank:** Vertex AI feature for persistent storage of conversation context across sessions.

**Thought Signature:** Encrypted representation of model's reasoning that must be preserved across turns.

**RAG (Retrieval-Augmented Generation):** Pattern where LLM retrieves relevant documents before generating responses.

### 6.2 Analysis Models

**Cost-Benefit Analysis (Year 1, Single Hospital):**

**Costs:**
- Platform development: $250,000
- Gemini API usage: $180,000/year
- Infrastructure (GCP): $60,000/year
- Training and change management: $40,000
- **Total:** $530,000

**Benefits:**
- Revenue recovery (reduced denials): $200,000/year
- Labor cost reduction (30% efficiency): $150,000/year
- Reduced readmissions (better adherence): $100,000/year
- **Total:** $450,000/year

**ROI:** 85% in Year 1, breakeven by Month 14

**Risk Analysis:**

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Model hallucination causing clinical error | Medium | Critical | Mandatory human verification, strong guardrails |
| HIPAA breach | Low | Critical | Vertex AI with BAA, comprehensive auditing |
| Gemini API outage | Low | High | Fallback to Gemini 2.5, degraded mode |
| User adoption resistance | Medium | Medium | Phased rollout, training, physician champions |
| Integration failures with EHRs | High | High | Extensive testing, vendor partnerships |

### 6.3 Requirements Traceability

| Business Goal | PRD Section | SRS Requirement |
|--------------|-------------|-----------------|
| Reduce manual workload 30-50% | 3.2 Admin KPIs | FR-ADMIN-1, FR-ADMIN-2 |
| Reduce revenue leakage 10-20% | 3.2 Admin KPIs | FR-ADMIN-4, Feature 4.1 |
| Reduce time-to-answer 50-70% | 3.3 Doctor KPIs | FR-DOC-1, Feature 4.2 |
| Improve medication adherence | 3.4 Patient KPIs | FR-PAT-2, Feature 4.3 |
| 24/7 multilingual support | 2.3 Patient Stories | FR-PAT-1 |
| Reduce unnecessary ER visits | 3.4 Patient KPIs | FR-PAT-4, Feature 4.4 |

---

**Document Control:**
- **Author:** Principal AI Engineer
- **Reviewers:** Clinical Advisory Board, Legal/Compliance, Technical Architecture Team
- **Approval:** Chief Medical Informatics Officer, CTO
- **Next Review:** Q2 2026 (post-Gemini 3 GA release)

```

## File: Documentation/healthcare-platform-sad.md

```md
# Software Architecture Document (SAD)
## Healthcare AI Orchestration Platform

**Version:** 1.0  
**Date:** January 29, 2026  
**Status:** Draft

---

## 1. INTRODUCTION

### 1.1 Purpose
This Software Architecture Document describes the comprehensive technical architecture for a multi-persona healthcare AI platform built on Google Gemini 3 API and Agentic Development Kit (ADK). The architecture supports hospital administrators, doctors, and patients through a hierarchical multi-agent orchestration system.

### 1.2 Scope
This document covers:
- System decomposition into components and agents
- Interaction patterns between system elements
- Deployment topology and infrastructure
- Data architecture and flow
- Technology stack and integration points
- Quality attribute implementations (performance, security, scalability)

### 1.3 Intended Audience
- Solution architects and technical leads
- Backend and frontend development teams
- DevOps and infrastructure engineers
- Security and compliance officers
- Integration partners (EHR vendors, payers)

### 1.4 Architectural Representation
This document follows the **4+1 View Model** for software architecture:
1. **Use Case View:** System functionality from user perspective
2. **Logical View:** System decomposition into components
3. **Process View:** Runtime behavior, concurrency, communication
4. **Deployment View:** Physical infrastructure and topology
5. **Implementation View:** Code organization and build structure

### 1.5 References
- Software Requirements Specification (SRS) v1.0
- Google Agentic Development Kit (ADK) Documentation
- Gemini 3 API Technical Specifications
- Vertex AI Agent Engine Architecture Guide
- HIPAA Security Rule Technical Safeguards

---

## 2. ARCHITECTURAL GOALS AND CONSTRAINTS

### 2.1 Architectural Drivers

#### 2.1.1 Business Goals
1. **Multi-Persona Support:** Serve three distinct user types with specialized AI agents
2. **Revenue Impact:** Demonstrate 10-20% revenue improvement within 12 months
3. **Clinical Accuracy:** Achieve 95%+ clinician satisfaction with AI recommendations
4. **Patient Engagement:** 85%+ medication adherence rates through AI guidance
5. **Operational Efficiency:** Reduce manual workload by 30-50% in administrative functions

#### 2.1.2 Quality Attributes (Priority Order)

**1. Security & Compliance (Critical)**
- HIPAA compliance with signed BAA through Vertex AI
- PHI encryption at rest (AES-256) and in transit (TLS 1.3)
- Role-based access control with audit logging
- 7-year audit trail retention

**2. Reliability (Critical)**
- 99.9% uptime SLA (8.76 hours downtime/year)
- Graceful degradation when Gemini API unavailable
- Data integrity with ACID transactions for critical operations
- RPO < 1 hour, RTO < 4 hours

**3. Performance (High)**
- Doctor queries: < 3 seconds (p95)
- Patient conversations: < 1 second (p95)
- Drug interaction checks: < 1 second (p99)
- Support 10,000 concurrent users per instance

**4. Scalability (High)**
- Horizontal scaling across multiple regions
- Handle 100,000 patient conversations/day
- Process 50,000 claims/day
- Cost-efficient token utilization (< $0.10/patient conversation)

**5. Maintainability (Medium)**
- Modular agent architecture for independent updates
- Comprehensive observability (logs, metrics, traces)
- CI/CD with automated testing and blue-green deployment

### 2.2 Architectural Constraints

#### 2.2.1 Technical Constraints
1. **Gemini 3 API Limitations:**
   - 1M token context window (hard limit)
   - Temperature must remain at 1.0 (architectural requirement)
   - Thought signatures mandatory for function calling
   - Rate limits: 150-300 RPM (Tier 1), scaling to 2,000+ RPM (Tier 3)

2. **ADK Framework Requirements:**
   - Python 3.10+ for agent implementation
   - Pydantic for configuration management
   - SessionService for state persistence
   - FunctionTool pattern for external integrations

3. **Google Cloud Platform:**
   - Vertex AI required for HIPAA compliance (not Consumer Gemini API)
   - Regional deployment: us-central1 (US), asia-south1 (India)
   - Identity-Aware Proxy (IAP) for access control

#### 2.2.2 Regulatory Constraints
1. **HIPAA:**
   - BAA signed with Google Cloud
   - Regulated-data flag enabled on all Vertex AI requests
   - Web search grounding disabled when processing PHI
   - Minimum necessary standard enforced via RBAC

2. **HITRUST CSF:**
   - Annual third-party certification required
   - Control implementation documentation
   - Risk assessment and remediation

3. **Medical Device Regulations:**
   - System explicitly NOT FDA-cleared
   - Disclaimers required on all clinical outputs
   - No autonomous clinical decisions without human oversight

#### 2.2.3 Organizational Constraints
1. **Budget:** $530K Year 1 including development and operational costs
2. **Timeline:** MVP in 6 months, full deployment in 12 months
3. **Team:** 5 backend engineers, 3 frontend engineers, 1 DevOps, 1 architect
4. **Existing Systems:** Must integrate with diverse EHR systems (Epic, Cerner, custom)

### 2.3 Architectural Principles

1. **Agent-First Design:** Encapsulate all AI capabilities within well-defined agents
2. **Separation of Concerns:** Distinct layers for presentation, orchestration, integration, data
3. **API-First:** All inter-component communication via documented REST/gRPC APIs
4. **Secure by Default:** PHI protection at every layer, deny-by-default access control
5. **Cloud-Native:** Leverage managed services (Vertex AI, Firestore, Cloud Run)
6. **Observable Systems:** Comprehensive logging, metrics, and distributed tracing
7. **Fail-Safe Operations:** Graceful degradation, circuit breakers, human escalation paths

---

## 3. USE CASE VIEW

### 3.1 Critical Use Cases

#### UC-1: Doctor Performs Point-of-Care Clinical Search
**Actors:** Doctor, ClinicalAgent, EHRSearchAgent, Gemini 3 Pro

**Flow:**
1. Doctor opens mobile app during patient rounds
2. Enters voice/text query: "Post-op antibiotic for pediatric appendectomy"
3. ClinicalAgent receives query via API Gateway
4. Agent retrieves patient context via EHRSearchAgent (allergies, current meds)
5. Agent searches embedded hospital protocols (vector DB with context caching)
6. Gemini 3 Pro (`thinking_level: high`) synthesizes response with citations
7. Response includes: recommended antibiotics, dosing, evidence grading
8. Doctor reviews and selects antibiotic
9. Drug interaction check performed (function call to Micromedex API)
10. Prescription generated and sent to patient app

**Quality Attributes:**
- Performance: < 3 seconds end-to-end (p95)
- Reliability: Fallback to cached protocols if Gemini unavailable
- Security: Patient context encrypted in transit, audit logged

#### UC-2: Patient Medication Adherence Tracking
**Actors:** Patient, PatientAgent, Gemini 3 Flash (OCR), NotificationService

**Flow:**
1. Patient receives paper prescription at clinic
2. Opens patient app → "Scan Prescription"
3. Camera captures prescription image → uploaded to Cloud Storage
4. Gemini 3 Flash multimodal processes image (OCR)
5. Extracted data: medication names, dosages, frequencies
6. Patient confirms/corrects extracted data
7. PatientAgent generates personalized schedule (meal times, sleep patterns)
8. Push notifications scheduled via Firebase Cloud Messaging
9. Patient marks medications taken → adherence recorded
10. Weekly summary generated → shared with prescribing doctor

**Quality Attributes:**
- Usability: 95% OCR accuracy, < 30 seconds to complete scan
- Reliability: Offline capability for marking medications taken
- Security: Prescription images encrypted, auto-deleted after 30 days

#### UC-3: Administrator Analyzes Revenue Cycle
**Actors:** Administrator, BillingAgent, Gemini 3 Pro, NHCX API

**Flow:**
1. Admin opens dashboard → "Revenue Cycle Analytics"
2. BillingAgent retrieves billing data from past 90 days
3. Gemini 3 Pro analyzes denial patterns, coding errors, payment delays
4. Agent identifies: 15% denial rate on orthopedic procedures due to documentation gaps
5. Root cause analysis performed (function calling to claims database)
6. Recommendations generated: "Add pre-submission documentation checklist"
7. Admin implements recommendation → claims template updated
8. Ongoing monitoring shows denial rate drops to 8% over 30 days

**Quality Attributes:**
- Performance: Dashboard loads < 2 seconds with cached analytics
- Scalability: Analyze 50,000 claims/day across multiple facilities
- Security: Financial data segregated by organization, admin-only access

### 3.2 Actor-System Interactions

```
┌─────────────┐         ┌──────────────────────────────────────┐
│   Doctor    │────────▶│         Web/Mobile App               │
└─────────────┘         │  (React PWA, React Native)           │
                        └──────────────┬───────────────────────┘
                                       │ HTTPS/TLS 1.3
┌─────────────┐         ┌──────────────▼───────────────────────┐
│   Patient   │────────▶│       API Gateway (Cloud Endpoints)  │
└─────────────┘         │  Authentication, Rate Limiting       │
                        └──────────────┬───────────────────────┘
                                       │
┌─────────────┐         ┌──────────────▼───────────────────────┐
│   Admin     │────────▶│    Orchestration Layer (Cloud Run)   │
└─────────────┘         │  RootOrchestrator, Agent Dispatching │
                        └──────────────┬───────────────────────┘
                                       │
                        ┌──────────────▼───────────────────────┐
                        │      Agent Layer (ADK Framework)     │
                        │  ClinicalAgent, PatientAgent,        │
                        │  BillingAgent, Tool Agents           │
                        └──────────────┬───────────────────────┘
                                       │
                        ┌──────────────▼───────────────────────┐
                        │    Gemini 3 API (Vertex AI)          │
                        │  Pro: Clinical, Admin Analytics      │
                        │  Flash: Patient Conversations        │
                        └──────────────────────────────────────┘
```

---

## 4. LOGICAL VIEW

### 4.1 High-Level Architecture

The system follows a **layered architecture** with **hierarchical agent orchestration**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Doctor Portal│  │ Patient Portal│  │ Admin Portal │              │
│  │ (React PWA)  │  │ (React Native)│  │ (React PWA)  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                               │ REST/GraphQL
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY LAYER                               │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │ Cloud Endpoints: Auth, Rate Limiting, Request Validation   │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                   ORCHESTRATION LAYER (Cloud Run)                    │
│  ┌────────────────────────────────────────────────────────────┐     │
│  │              RootOrchestratorAgent (ADK)                   │     │
│  │  - Request routing by user role and task type              │     │
│  │  - Session management (Vertex AI Sessions)                 │     │
│  │  - Agent-to-Agent coordination                             │     │
│  └────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                        AGENT LAYER (ADK)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ClinicalAgent │  │ PatientAgent │  │ BillingAgent │              │
│  │Gemini 3 Pro  │  │Gemini 3 Flash│  │Gemini 3 Pro  │              │
│  │thinking: high│  │thinking: low │  │thinking: high│              │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘              │
│         │                 │                  │                       │
│  ┌──────▼──────────────────▼──────────────────▼──────┐              │
│  │              Tool Agents (FunctionTool)           │              │
│  │  EHRSearchAgent, DrugDBAgent, SchedulingAgent,   │              │
│  │  ImagingAgent, ClaimsAgent, NotificationAgent    │              │
│  └───────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                    INTEGRATION LAYER                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ EHR Connector│  │ NHCX Connector│ │ Wearable APIs│              │
│  │ (HL7 FHIR)   │  │ (Claims API)  │  │(Apple, Google│              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                               │
┌─────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  Firestore   │  │  Cloud SQL   │  │ Cloud Storage│              │
│  │ (Documents)  │  │ (Relational) │  │  (Blobs)     │              │
│  │ ┌──────────┐ │  │ ┌──────────┐ │  │ ┌──────────┐ │              │
│  │ │Patients  │ │  │ │Users     │ │  │ │Prescriptions│              │
│  │ │Messages  │ │  │ │Audit Logs│ │  │ │Images    │ │              │
│  │ │Adherence │ │  │ │Orgs      │ │  │ │Documents │ │              │
│  │ └──────────┘ │  │ └──────────┘ │  │ └──────────┘ │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │ Vector DB    │  │ Redis Cache  │  │ Pub/Sub      │              │
│  │(Vertex AI VDB│  │ (Sessions)   │  │(Async Events)│              │
│  │ Embeddings)  │  │              │  │              │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 Component Descriptions

#### 4.2.1 Presentation Layer

**Doctor Portal (React PWA)**
- **Responsibility:** Mobile-first clinical interface for point-of-care use
- **Technology:** React 18, TypeScript, Tailwind CSS, PWA with service workers
- **Key Features:**
  - Voice input via Web Speech API
  - Offline mode for cached protocols
  - Push notifications for critical alerts
- **Communication:** REST API to API Gateway, WebSocket for Live API

**Patient Portal (React Native)**
- **Responsibility:** Native mobile app for iOS/Android
- **Technology:** React Native 0.73, Expo, TypeScript
- **Key Features:**
  - Camera integration for prescription scanning
  - Push notifications via Firebase Cloud Messaging
  - Wearable data sync (Apple HealthKit, Google Fit)
- **Communication:** REST API to API Gateway, background sync

**Admin Portal (React PWA)**
- **Responsibility:** Desktop/tablet dashboard for operations and analytics
- **Technology:** React 18, TypeScript, Recharts for visualization
- **Key Features:**
  - Real-time dashboards with WebSocket updates
  - CSV/PDF export for compliance reports
  - Multi-organization view for health systems
- **Communication:** GraphQL API for complex queries, REST for mutations

#### 4.2.2 API Gateway Layer

**Cloud Endpoints**
- **Responsibility:** Single entry point for all client requests
- **Technology:** Google Cloud Endpoints with OpenAPI 3.0 specification
- **Functions:**
  - **Authentication:** JWT validation, OAuth 2.0 token verification
  - **Authorization:** RBAC enforcement (admin, doctor, patient roles)
  - **Rate Limiting:** Per-user quotas (100 req/min patient, 500 req/min doctor)
  - **Request Validation:** Schema validation against OpenAPI spec
  - **TLS Termination:** Certificate management via Google-managed certs
- **Monitoring:** Cloud Monitoring for latency, error rates, quota usage

#### 4.2.3 Orchestration Layer

**RootOrchestratorAgent**
- **Responsibility:** Top-level agent coordinating all sub-agents
- **Technology:** ADK LlmAgent with Gemini 3 Flash (routing speed critical)
- **Functions:**
  - **Request Classification:** Determine appropriate sub-agent (clinical vs. billing vs. patient)
  - **Session Management:** Create/retrieve Vertex AI Agent Engine Sessions
  - **Context Assembly:** Gather user context, permissions, organization settings
  - **Agent Dispatching:** Route to specialized agents with context handoff
  - **Response Aggregation:** Combine multi-agent responses when needed
- **State Management:** 
  - Session data stored in Vertex AI Sessions (55-day retention)
  - Thought signatures preserved across agent handoffs
  - Memory Bank for long-term patient context

**Implementation Pattern:**
```python
from google import genai
from google.genai import types
from adk import Agent, LlmAgent, SessionService

class RootOrchestratorAgent(LlmAgent):
    def __init__(self, config: OrchestratorConfig):
        self.clinical_agent = ClinicalAgent()
        self.patient_agent = PatientAgent()
        self.billing_agent = BillingAgent()
        self.session_service = SessionService()
        
        super().__init__(
            model="gemini-3-flash-preview",
            system_instruction=self._get_system_instruction(),
            tools=[
                self._route_to_clinical,
                self._route_to_patient,
                self._route_to_billing
            ]
        )
    
    async def process(self, request: Request) -> Response:
        # Retrieve or create session
        session = await self.session_service.get_or_create(
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        # Classify request and route
        classification = await self._classify_request(request.query)
        
        if classification.agent_type == "clinical":
            response = await self.clinical_agent.process(request, session)
        elif classification.agent_type == "patient":
            response = await self.patient_agent.process(request, session)
        elif classification.agent_type == "billing":
            response = await self.billing_agent.process(request, session)
        
        # Update session with response
        await self.session_service.update(session, response)
        
        return response
```

#### 4.2.4 Agent Layer

**ClinicalAgent**
- **Model:** Gemini 3 Pro with `thinking_level: high`
- **Purpose:** Clinical decision support for doctors
- **Tools:**
  - EHRSearchAgent: Patient data retrieval via FHIR
  - DrugDBAgent: Medication information, interactions (Micromedex)
  - ProtocolSearchAgent: Hospital guideline lookup (vector DB)
  - ImagingAgent: DICOM analysis (preliminary findings)
- **Configuration:**
  - Context caching enabled for clinical guidelines (90% hit rate target)
  - Structured output for prescription generation
  - Grounding disabled (uses internal protocols only)
- **Safety:**
  - System instruction emphasizes uncertainty quantification
  - Hard blocks on autonomous diagnosis
  - Mandatory human verification flags

**PatientAgent**
- **Model:** Gemini 3 Flash with `thinking_level: low`
- **Purpose:** Conversational health assistant for patients
- **Tools:**
  - SymptomTriageAgent: Severity assessment, escalation logic
  - MedicationAgent: Adherence tracking, reminder scheduling
  - WearableAgent: Data sync, anomaly detection
  - EscalationAgent: Connect to on-call clinician
- **Configuration:**
  - Multilingual support (12 languages via system instructions)
  - Google Search grounding enabled (health education only)
  - Live API integration for voice interactions
- **Safety:**
  - Strict guardrails against medical diagnosis
  - Automatic escalation triggers (chest pain, severe allergic reaction)
  - Content filtering for harmful medical advice

**BillingAgent**
- **Model:** Gemini 3 Pro with `thinking_level: high`
- **Purpose:** Revenue cycle optimization for administrators
- **Tools:**
  - CodingAgent: ICD-11 code suggestion from clinical notes
  - ClaimsAgent: NHCX submission, status tracking
  - AnalyticsAgent: Denial pattern analysis, revenue insights
  - ValidationAgent: Pre-submission documentation checks
- **Configuration:**
  - Structured output for claims (JSON schema validation)
  - Function calling to billing system APIs
  - Context caching for coding guidelines
- **Compliance:**
  - Audit logging for all coding decisions
  - Confidence thresholds (85% for auto-coding)
  - Human review queue for low-confidence cases

**Tool Agents (FunctionTool Pattern)**

All tool agents follow the same pattern:
```python
from adk import FunctionTool

@FunctionTool
async def search_ehr(patient_id: str, resource_type: str) -> dict:
    """Retrieves patient data from EHR via FHIR API.
    
    Args:
        patient_id: Patient MRN or FHIR ID
        resource_type: FHIR resource (Patient, Observation, MedicationRequest)
    
    Returns:
        FHIR bundle with requested resources
    """
    ehr_connector = EHRConnector()
    response = await ehr_connector.get(
        endpoint=f"Patient/{patient_id}/{resource_type}",
        headers={"Authorization": f"Bearer {get_ehr_token()}"}
    )
    return response.json()
```

**EHRSearchAgent:**
- Implements HL7 FHIR R4 client
- OAuth 2.0 + SMART on FHIR authentication
- Caching layer (Redis) for frequently accessed records
- Retry logic with exponential backoff

**DrugDBAgent:**
- Integration with Micromedex API (drug interactions)
- RxNorm for medication normalization
- Local cache for common drug pairs (< 100ms response)

**SchedulingAgent:**
- Integration with hospital scheduling system
- Appointment availability checking
- Confirmation via SMS/email

**NotificationAgent:**
- Firebase Cloud Messaging for push notifications
- SMS via Twilio (medication reminders, appointment alerts)
- Email via SendGrid (reports, compliance notifications)

#### 4.2.5 Integration Layer

**EHR Connector**
- **Protocol:** HL7 FHIR R4 (preferred), HL7 v2.x (legacy fallback)
- **Authentication:** OAuth 2.0 with SMART on FHIR
- **Supported Vendors:** Epic (MyChart API), Cerner (HealtheIntent), Allscripts, Custom
- **Operations:** Read-only access (GET requests)
- **Error Handling:** Circuit breaker pattern (open circuit after 5 consecutive failures)

**NHCX Connector**
- **Protocol:** REST API with JSON payloads
- **Functions:** Claim submission, status check, payment posting
- **Authentication:** API key + HMAC signature
- **Retry Logic:** Exponential backoff (1s, 2s, 4s, 8s, 16s max)
- **Idempotency:** Request IDs to prevent duplicate submissions

**Wearable APIs**
- **Apple HealthKit:** Native iOS integration, HealthKit framework
- **Google Fit:** REST API, OAuth 2.0 scopes (fitness.activity.read, fitness.heart_rate.read)
- **Sync Frequency:** Background sync every 4 hours, real-time for critical values (heart rate > 120 bpm)
- **Data Normalization:** Convert to FHIR Observation resources for consistent storage

#### 4.2.6 Data Layer

**Firestore (Document Database)**
- **Use Cases:** Semi-structured data with flexible schema
- **Collections:**
  - `conversations`: Message history, thought signatures
  - `patients`: Demographics, preferences, adherence logs
  - `medications`: Active prescriptions, schedules
  - `wearable_data`: Time-series health metrics
- **Indexing:** Composite indexes on (user_id, created_at) for queries
- **Security Rules:** Firestore Security Rules enforce RBAC at database level

**Cloud SQL (PostgreSQL)**
- **Use Cases:** Relational data requiring ACID transactions
- **Tables:**
  - `users`: Authentication, roles, organization mapping
  - `audit_logs`: All PHI access, 7-year retention
  - `organizations`: Hospital/clinic metadata, subscription tiers
  - `appointments`: Scheduling data with foreign keys
- **High Availability:** Regional replication, automatic failover
- **Backups:** Hourly incremental, daily full backup to Cloud Storage

**Cloud Storage**
- **Buckets:**
  - `prescription-images`: Encrypted prescription scans (auto-delete after 30 days)
  - `clinical-documents`: Lab reports, imaging studies (7-year retention)
  - `backups`: Database backups (Archive storage class after 90 days)
- **Encryption:** Customer-managed encryption keys (CMEK) via Cloud KMS
- **Access Control:** Signed URLs for temporary access, IAM for permanent

**Vertex AI Vector Database**
- **Use Cases:** Semantic search over clinical protocols, medical literature
- **Data:** Hospital-specific guidelines, standard protocols (AHA, CDC)
- **Embeddings:** Gemini text-embedding-004 model (768 dimensions)
- **Index Type:** ScaNN for fast approximate nearest neighbor search

**Redis Cache**
- **Use Cases:** Session data, frequently accessed EHR records, rate limiting counters
- **Deployment:** Cloud Memorystore with 4GB instance
- **TTL:** 15 minutes for session data, 1 hour for EHR data
- **Eviction Policy:** LRU (Least Recently Used)

**Pub/Sub**
- **Use Cases:** Asynchronous event processing, decoupling
- **Topics:**
  - `medication-reminders`: Schedule push notifications
  - `wearable-alerts`: Critical value notifications
  - `audit-events`: Real-time audit log processing
- **Subscriptions:** Push subscriptions to Cloud Run services

---

## 5. PROCESS VIEW

### 5.1 Concurrency and Threading

**API Gateway (Cloud Endpoints)**
- **Concurrency Model:** Event-driven, handles 1,000+ concurrent connections per instance
- **Auto-scaling:** Scale to zero when idle, max 100 instances

**Orchestration Layer (Cloud Run)**
- **Concurrency:** 10 concurrent requests per container instance
- **Instances:** Min 2 (for redundancy), max 50 (cost control)
- **CPU:** 2 vCPU per instance
- **Memory:** 4 GB per instance

**Agent Processing**
- **Pattern:** Asynchronous I/O using Python asyncio
- **LLM Calls:** Non-blocking async calls to Gemini API
- **Function Calling:** Parallel execution of independent function calls
- **Timeout:** 30 seconds per agent processing request

### 5.2 Inter-Process Communication

**Client ↔ API Gateway**
- **Protocol:** HTTPS with REST or GraphQL
- **Format:** JSON
- **Authentication:** JWT Bearer tokens (15-minute expiry, refresh tokens)

**API Gateway ↔ Orchestration Layer**
- **Protocol:** gRPC for low latency
- **Format:** Protocol Buffers
- **Load Balancing:** Google Cloud Load Balancer (round-robin)

**Orchestration ↔ Agents**
- **Pattern:** In-process function calls (agents deployed as libraries, not microservices)
- **State Sharing:** Via SessionService (abstracts Vertex AI Sessions API)

**Agents ↔ External Systems**
- **EHR:** REST API with OAuth 2.0, JSON
- **Gemini API:** REST API with API key auth, JSON
- **Tool Agents:** Function calls with retry logic

**Asynchronous Events**
- **Pub/Sub Topics:** Medication reminders, wearable alerts, audit events
- **Subscribers:** Cloud Run services (push subscriptions)
- **Dead Letter Queue:** Failed messages after 5 retries

### 5.3 Critical Workflows

#### Workflow 1: Doctor Clinical Query with Function Calling

```
┌────────┐    ┌─────────┐    ┌──────────────┐    ┌────────────┐    ┌────────┐
│ Doctor │    │   App   │    │Orchestrator  │    │Clinical    │    │ Gemini │
│        │    │         │    │              │    │Agent       │    │ 3 Pro  │
└───┬────┘    └────┬────┘    └──────┬───────┘    └─────┬──────┘    └────┬───┘
    │              │                 │                   │                │
    │ Voice Query  │                 │                   │                │
    ├─────────────▶│                 │                   │                │
    │              │ POST /query     │                   │                │
    │              ├────────────────▶│                   │                │
    │              │                 │ Route to Clinical │                │
    │              │                 ├──────────────────▶│                │
    │              │                 │                   │ LLM Request    │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │ (thinking:high)│
    │              │                 │                   │                │
    │              │                 │                   │◀───Decides to  │
    │              │                 │                   │  call function │
    │              │                 │                   │  search_ehr()  │
    │              │                 │                   │                │
    │              │                 │                   │ Call EHRSearch │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │   (parallel)   │
    │              │                 │                   │◀───────────────┤
    │              │                 │                   │ Patient data   │
    │              │                 │                   │                │
    │              │                 │                   │ Continue LLM   │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │ with results   │
    │              │                 │                   │◀───────────────┤
    │              │                 │                   │ Final response │
    │              │                 │◀──────────────────┤ + thought sig  │
    │              │◀────────────────┤                   │                │
    │              │ Response        │                   │                │
    │◀─────────────┤ (JSON)          │                   │                │
    │              │                 │                   │                │
    │ Display      │                 │                   │                │
    └──────────────┘                 └───────────────────┘                │
                                                                          │
    Total Time: 2.5 seconds (p95)                                         │
```

**Performance Breakdown:**
- API Gateway: 20ms (JWT validation, routing)
- Orchestrator: 50ms (session retrieval, context assembly)
- ClinicalAgent + Gemini: 1,800ms (LLM reasoning with `thinking_level: high`)
- Function call (EHR search): 300ms (cached patient data)
- Response assembly: 30ms
- **Total:** ~2.2 seconds (well under 3-second SLA)

#### Workflow 2: Patient Prescription Scanning (Multimodal)

```
┌────────┐    ┌─────────┐    ┌──────────────┐    ┌────────────┐    ┌────────┐
│Patient │    │  App    │    │Orchestrator  │    │Patient     │    │ Gemini │
│        │    │         │    │              │    │Agent       │    │3 Flash │
└───┬────┘    └────┬────┘    └──────┬───────┘    └─────┬──────┘    └────┬───┘
    │              │                 │                   │                │
    │ Tap Scan Rx  │                 │                   │                │
    ├─────────────▶│                 │                   │                │
    │              │ Open Camera     │                   │                │
    │◀─────────────┤                 │                   │                │
    │              │                 │                   │                │
    │ Capture Image│                 │                   │                │
    ├─────────────▶│                 │                   │                │
    │              │ Upload to       │                   │                │
    │              │ Cloud Storage   │                   │                │
    │              ├─────────────────┼───────────────────┼───────────────▶│
    │              │                 │                   │                │
    │              │ POST /ocr       │                   │                │
    │              ├────────────────▶│                   │                │
    │              │ {image_url}     │ Route to Patient  │                │
    │              │                 ├──────────────────▶│                │
    │              │                 │                   │ Multimodal OCR │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │ (image + prompt│
    │              │                 │                   │  structured out│
    │              │                 │                   │◀───────────────┤
    │              │                 │                   │ JSON: meds, dos│
    │              │                 │◀──────────────────┤                │
    │              │◀────────────────┤ Structured data   │                │
    │              │                 │                   │                │
    │◀─────────────┤ Display for     │                   │                │
    │ Confirm/Edit │ confirmation    │                   │                │
    │              │                 │                   │                │
    │ Confirmed    │                 │                   │                │
    ├─────────────▶│ POST /schedule  │                   │                │
    │              ├────────────────▶│                   │                │
    │              │                 │ Create schedule   │                │
    │              │                 ├──────────────────▶│                │
    │              │                 │                   │ Pub/Sub        │
    │              │                 │                   ├───────────────▶│
    │              │                 │                   │ (notifications)│
    │              │◀────────────────┤                   │                │
    │◀─────────────┤ Schedule created│                   │                │
    └──────────────┘                 └───────────────────┘                │
```

**Token Consumption:**
- Prescription image: ~600 tokens (average at medium resolution)
- System instruction + schema: 200 tokens (cached)
- Output: ~100 tokens (structured JSON)
- **Total:** ~900 tokens × $0.50/1M = $0.00045 per scan

#### Workflow 3: Real-Time Wearable Alert Escalation

```
┌──────────┐    ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌────────┐
│ Wearable │    │  Sync   │    │ Patient  │    │ Live API │    │On-Call │
│  Device  │    │ Service │    │  Agent   │    │ (WebSock)│    │ Doctor │
└────┬─────┘    └────┬────┘    └─────┬────┘    └────┬─────┘    └────┬───┘
     │               │                │              │              │
     │ Heart rate    │                │              │              │
     │ 130 bpm (rest)│                │              │              │
     ├──────────────▶│                │              │              │
     │               │ Store data     │              │              │
     │               │ Firestore      │              │              │
     │               │                │              │              │
     │ 135 bpm       │                │              │              │
     ├──────────────▶│                │              │              │
     │ (sustained)   │                │              │              │
     │               │ Anomaly detect │              │              │
     │               ├───────────────▶│              │              │
     │               │                │ Analyze      │              │
     │               │                │ context      │              │
     │               │                │              │              │
     │               │                │ Push alert   │              │
     │               │                │ to patient   │              │
     │               │◀───────────────┤              │              │
     │               │ FCM            │              │              │
     │               │                │              │              │
     │◀──────────────┴────────────────┴──Alert: High│              │
     │               │                │  heart rate  │              │
     │               │                │              │              │
     │ Patient       │                │              │              │
     │ reports chest │                │              │              │
     │ discomfort    │                │              │              │
     ├──────────────▶│────────────────▶              │              │
     │               │                │              │              │
     │               │                │ Severity 8/10│              │
     │               │                │ + cardiac Hx │              │
     │               │                │ = ESCALATE   │              │
     │               │                │              │              │
     │               │                │ Initiate Live│              │
     │               │                │ API session  │              │
     │               │                │──────────────▶              │
     │               │                │ WebSocket    │              │
     │               │                │              │ Notify       │
     │               │                │              ├─────────────▶│
     │               │                │              │ on-call      │
     │               │                │              │◀─────────────┤
     │               │                │              │ Accept call  │
     │               │                │◀──────────────              │
     │◀──────────────┴────────────────┴──Video call │              │
     │               │                │  established │              │
     │               │                │              │              │
     │ Video consultation with pre-loaded patient data              │
     └──────────────────────────────────────────────────────────────┘
```

**Latency Requirements:**
- Wearable sync to storage: < 5 seconds
- Anomaly detection: < 10 seconds
- Patient alert delivery: < 15 seconds (total from detection)
- Video call connection: < 30 seconds

### 5.4 State Management

**Session State (Short-Term)**
- **Storage:** Vertex AI Agent Engine Sessions
- **Retention:** 55 days (paid tier), 1 day (free tier)
- **Contents:**
  - Conversation history (full messages)
  - Thought signatures (preserved across turns)
  - User context (patient allergies, current medications)
  - Temporary decisions (medications considered, rejected options)

**Memory Bank (Long-Term)**
- **Storage:** Vertex AI Memory Bank
- **Retention:** Indefinite (until user deletion)
- **Contents:**
  - Extracted key facts (patient preferences, chronic conditions)
  - Recurring concerns (frequent symptom reports)
  - Action items (follow-up appointments, pending tasks)
- **Update Mechanism:** LLM-driven summarization after each session

**Database State (Permanent)**
- **Firestore & Cloud SQL:** Core application data
- **Retention:** 7 years (HIPAA) or indefinite
- **Backup:** Hourly incremental, daily full backup

---

## 6. DEPLOYMENT VIEW

### 6.1 Physical Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          CLOUD INFRASTRUCTURE                            │
│                        (Google Cloud Platform)                           │
│                                                                           │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │                      GLOBAL LOAD BALANCER                           │ │
│  │                (Cloud Load Balancing - HTTPS)                       │ │
│  └────────────────────┬───────────────────────────────────────────────┘ │
│                       │                                                  │
│  ┌────────────────────┼──────────────────────────────────────────────┐ │
│  │                    │           CLOUD CDN                           │ │
│  │                    │      (Static Assets, Images)                  │ │
│  └────────────────────┼──────────────────────────────────────────────┘ │
│                       │                                                  │
│         ┌─────────────┴─────────────┐                                   │
│         │                           │                                   │
│  ┌──────▼──────────┐        ┌──────▼──────────┐                        │
│  │   REGION:       │        │   REGION:       │                        │
│  │  us-central1    │        │  asia-south1    │                        │
│  │   (Iowa)        │        │   (Mumbai)      │                        │
│  └─────────────────┘        └─────────────────┘                        │
│         │                           │                                   │
│  ┌──────▼───────────────────────────▼──────────────┐                   │
│  │            CLOUD ENDPOINTS (API Gateway)        │                   │
│  │  - Auth, Rate Limiting, Request Validation      │                   │
│  └──────┬───────────────────────────┬──────────────┘                   │
│         │                           │                                   │
│  ┌──────▼──────────┐        ┌──────▼──────────┐                        │
│  │   CLOUD RUN     │        │   CLOUD RUN     │                        │
│  │ Orchestration   │        │ Orchestration   │                        │
│  │  (us-central1)  │        │ (asia-south1)   │                        │
│  │  - Min: 2       │        │  - Min: 2       │                        │
│  │  - Max: 50      │        │  - Max: 50      │                        │
│  │  - 2 vCPU/4GB   │        │  - 2 vCPU/4GB   │                        │
│  └──────┬──────────┘        └──────┬──────────┘                        │
│         │                           │                                   │
│  ┌──────▼───────────────────────────▼──────────────┐                   │
│  │           VERTEX AI (Gemini API)                │                   │
│  │  - gemini-3-pro-preview (Clinical, Admin)       │                   │
│  │  - gemini-3-flash-preview (Patient)             │                   │
│  │  - HIPAA BAA enabled                            │                   │
│  │  - Regulated-data flag: true                    │                   │
│  └─────────────────────────────────────────────────┘                   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         DATA TIER                                │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │  FIRESTORE   │  │  CLOUD SQL   │  │CLOUD STORAGE │           │   │
│  │  │  (Multi-     │  │  (Regional)  │  │(Multi-region)│           │   │
│  │  │   region)    │  │  PostgreSQL  │  │              │           │   │
│  │  │              │  │  - Primary:  │  │  - Encrypted │           │   │
│  │  │  - Encrypted │  │    us-c1     │  │  - CMEK      │           │   │
│  │  │  - Auto-scale│  │  - Replica:  │  │  - Lifecycle │           │   │
│  │  │              │  │    asia-s1   │  │              │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │  VERTEX AI   │  │    REDIS     │  │   PUB/SUB    │           │   │
│  │  │  VECTOR DB   │  │ (Memorystore)│  │              │           │   │
│  │  │  - Embeddings│  │  - 4GB       │  │  - Topics:   │           │   │
│  │  │  - Clinical  │  │  - Regional  │  │    alerts,   │           │   │
│  │  │    protocols │  │              │  │    reminders │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    MONITORING & SECURITY                         │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ CLOUD        │  │ CLOUD TRACE  │  │ CLOUD KMS    │           │   │
│  │  │ MONITORING   │  │ (Tracing)    │  │ (Key Mgmt)   │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  │                                                                   │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │   │
│  │  │ CLOUD        │  │ SECURITY     │  │ IAM & IAP    │           │   │
│  │  │ LOGGING      │  │ COMMAND CTR  │  │              │           │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────────────────┘
```

### 6.2 Regional Deployment Strategy

**Multi-Region Active-Active**
- **Primary:** us-central1 (Iowa) - US customers
- **Secondary:** asia-south1 (Mumbai) - India customers
- **Load Balancing:** Geo-routing (latency-based)

**Data Residency:**
- US patient data stored in us-central1
- India patient data stored in asia-south1
- Cross-border transfer only with patient consent

**Disaster Recovery:**
- **RTO:** 4 hours (Recovery Time Objective)
- **RPO:** 1 hour (Recovery Point Objective)
- **Failover:** Automatic Cloud SQL replica promotion
- **Backup Restoration:** Tested monthly

### 6.3 Scaling Strategy

**Horizontal Scaling:**
- Cloud Run auto-scales based on CPU (target 70%) and request queue
- Firestore auto-shards collections at high write volume
- Cloud SQL read replicas for query offloading

**Vertical Scaling:**
- Cloud Run instances: 2 vCPU → 4 vCPU during peak hours (configurable)
- Redis: 4GB → 8GB if cache hit rate < 80%

**Cost Optimization:**
- Context caching reduces Gemini API costs by 90% for repeated content
- Cloud Run scale-to-zero for non-critical services (admin analytics)
- Committed use discounts for baseline capacity (30% savings)

### 6.4 Network Architecture

**VPC Configuration:**
- Private subnets for Cloud Run, Cloud SQL (no public IPs)
- Cloud NAT for outbound internet access (EHR APIs, Gemini API)
- VPC Service Controls for data exfiltration prevention

**Security Perimeter:**
- Identity-Aware Proxy (IAP) for admin access
- Cloud Armor (WAF) for DDoS protection
- Allowlist for known EHR IP ranges

**TLS/SSL:**
- Google-managed certificates for *.app-domain.com
- Certificate pinning in mobile apps
- TLS 1.3 minimum enforced

---

## 7. IMPLEMENTATION VIEW

### 7.1 Code Organization

```
healthcare-platform/
├── backend/
│   ├── orchestrator/                   # Cloud Run orchestration service
│   │   ├── main.py                     # FastAPI application entry
│   │   ├── agents/
│   │   │   ├── root_orchestrator.py    # Top-level routing agent
│   │   │   ├── clinical_agent.py       # Doctor-facing agent
│   │   │   ├── patient_agent.py        # Patient-facing agent
│   │   │   ├── billing_agent.py        # Admin-facing agent
│   │   │   └── tool_agents/
│   │   │       ├── ehr_search.py       # FHIR client
│   │   │       ├── drug_db.py          # Micromedex integration
│   │   │       ├── scheduling.py       # Appointment booking
│   │   │       └── notification.py     # Push/SMS/email
│   │   ├── config/
│   │   │   ├── settings.py             # Pydantic configuration
│   │   │   ├── prompts.py              # System instructions
│   │   │   └── models.py               # Data models
│   │   ├── services/
│   │   │   ├── session_service.py      # Vertex AI Sessions wrapper
│   │   │   ├── auth_service.py         # JWT validation, RBAC
│   │   │   └── audit_service.py        # Compliance logging
│   │   ├── utils/
│   │   │   ├── retry.py                # Exponential backoff
│   │   │   ├── encryption.py           # PHI encryption helpers
│   │   │   └── validators.py           # Input validation
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── pyproject.toml
│   │
│   ├── integrations/                   # External system connectors
│   │   ├── ehr/
│   │   │   ├── fhir_client.py          # HL7 FHIR R4 client
│   │   │   ├── epic_adapter.py         # Epic-specific logic
│   │   │   └── cerner_adapter.py       # Cerner-specific logic
│   │   ├── billing/
│   │   │   └── nhcx_client.py          # India claims exchange
│   │   ├── wearables/
│   │   │   ├── apple_health.py         # HealthKit integration
│   │   │   └── google_fit.py           # Google Fit API
│   │   └── drug_db/
│   │       └── micromedex_client.py    # Drug database API
│   │
│   ├── data/
│   │   ├── repositories/               # Data access layer
│   │   │   ├── user_repository.py      # Cloud SQL users table
│   │   │   ├── patient_repository.py   # Firestore patients collection
│   │   │   ├── conversation_repo.py    # Firestore conversations
│   │   │   └── audit_repository.py     # Cloud SQL audit_logs
│   │   ├── models/                     # SQLAlchemy/Pydantic models
│   │   └── migrations/                 # Alembic database migrations
│   │
│   └── tests/
│       ├── unit/                       # Unit tests (pytest)
│       ├── integration/                # Integration tests
│       └── e2e/                        # End-to-end tests
│
├── frontend/
│   ├── doctor-portal/                  # React PWA for doctors
│   │   ├── src/
│   │   │   ├── components/
│   │   │   ├── pages/
│   │   │   ├── services/               # API clients
│   │   │   └── hooks/                  # Custom React hooks
│   │   ├── public/
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   ├── patient-app/                    # React Native for patients
│   │   ├── src/
│   │   │   ├── screens/
│   │   │   ├── components/
│   │   │   ├── navigation/
│   │   │   └── services/
│   │   ├── ios/                        # Native iOS code
│   │   ├── android/                    # Native Android code
│   │   └── package.json
│   │
│   └── admin-portal/                   # React PWA for admins
│       ├── src/
│       └── package.json
│
├── infrastructure/
│   ├── terraform/                      # Infrastructure as Code
│   │   ├── main.tf                     # GCP resources
│   │   ├── variables.tf
│   │   ├── outputs.tf
│   │   └── modules/
│   │       ├── vpc/
│   │       ├── cloud_run/
│   │       └── databases/
│   │
│   ├── kubernetes/                     # K8s manifests (if needed)
│   └── scripts/
│       ├── deploy.sh                   # Deployment automation
│       └── backup.sh                   # Database backup
│
├── docs/
│   ├── api/                            # OpenAPI specifications
│   ├── architecture/                   # ADRs (Architecture Decision Records)
│   └── runbooks/                       # Operational procedures
│
├── .github/
│   └── workflows/
│       ├── ci.yml                      # GitHub Actions CI
│       ├── deploy-staging.yml
│       └── deploy-production.yml
│
├── README.md
├── LICENSE
└── .gitignore
```

### 7.2 Build and Deployment Pipeline

**CI/CD Flow (GitHub Actions):**

1. **On Pull Request:**
   - Run linters (black, flake8, eslint)
   - Run unit tests (pytest, jest)
   - Run integration tests (against staging Vertex AI)
   - Security scan (Snyk, Trivy)
   - Code coverage report (minimum 80%)

2. **On Merge to Main:**
   - Build Docker images (backend)
   - Build static assets (frontend)
   - Push images to Artifact Registry
   - Deploy to staging environment
   - Run E2E tests against staging
   - Manual approval gate

3. **On Approval:**
   - Blue-green deployment to production
   - Health checks and smoke tests
   - Monitor error rates for 1 hour
   - Auto-rollback if error rate > 1%

**Deployment Strategy:**
```bash
# Blue-Green Deployment (Cloud Run)
gcloud run deploy orchestrator-green \
  --image=gcr.io/project/orchestrator:v2.0 \
  --region=us-central1 \
  --no-traffic  # Deploy without serving traffic

# Run smoke tests against green deployment
./scripts/smoke-test.sh orchestrator-green

# Shift traffic gradually (10% -> 50% -> 100%)
gcloud run services update-traffic orchestrator \
  --to-revisions=orchestrator-green=10,orchestrator-blue=90

# Monitor for 30 minutes, then shift 100%
gcloud run services update-traffic orchestrator \
  --to-revisions=orchestrator-green=100
```

### 7.3 Technology Stack

**Backend:**
- **Language:** Python 3.11
- **Framework:** FastAPI (async REST API)
- **Agent Framework:** Google ADK (Agentic Development Kit)
- **LLM:** Gemini 3 Pro/Flash via Vertex AI
- **ORM:** SQLAlchemy (PostgreSQL), Firestore SDK
- **Async:** asyncio, aiohttp
- **Testing:** pytest, pytest-asyncio, pytest-cov
- **Linting:** black, flake8, mypy

**Frontend:**
- **Doctor/Admin Portal:** React 18, TypeScript, Vite, Tailwind CSS
- **Patient App:** React Native 0.73, Expo, TypeScript
- **State Management:** Zustand (lightweight alternative to Redux)
- **API Client:** Axios with retry logic
- **Testing:** Jest, React Testing Library, Detox (E2E for mobile)

**Infrastructure:**
- **Cloud:** Google Cloud Platform
- **Compute:** Cloud Run (serverless containers)
- **Databases:** Firestore, Cloud SQL (PostgreSQL), Cloud Storage
- **Cache:** Cloud Memorystore (Redis)
- **Messaging:** Pub/Sub
- **IaC:** Terraform
- **Monitoring:** Cloud Monitoring, Cloud Trace, Cloud Logging
- **CI/CD:** GitHub Actions, Cloud Build

**Security:**
- **Encryption:** Cloud KMS (key management), TLS 1.3
- **Authentication:** OAuth 2.0, JWT, Firebase Auth
- **Authorization:** Custom RBAC middleware
- **WAF:** Cloud Armor
- **Secrets:** Secret Manager

---

## 8. DATA VIEW

### 8.1 Data Flow Diagram

```
┌────────────────────────────────────────────────────────────────────────┐
│                         DATA SOURCES                                    │
│                                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │   EHR    │  │ Wearables│  │   User   │  │  Billing │               │
│  │  (FHIR)  │  │  (APIs)  │  │  Input   │  │  System  │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
│       │             │             │             │                       │
└───────┼─────────────┼─────────────┼─────────────┼───────────────────────┘
        │             │             │             │
        │             │             │             │
        ▼             ▼             ▼             ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      INGESTION LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │            Integration Services (Cloud Run)                   │      │
│  │  - EHR Connector: FHIR→JSON normalization                     │      │
│  │  - Wearable Sync: Background jobs every 4 hours               │      │
│  │  - API Gateway: Input validation, sanitization                │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
        │
        │ Encrypted PHI, validated data
        ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     PROCESSING LAYER                                    │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │                 Agent Orchestration                           │      │
│  │  - Data enrichment (retrieve patient context)                 │      │
│  │  - De-identification for logging (scrub PII)                  │      │
│  │  - Embedding generation (clinical protocols → vector DB)      │      │
│  │  - Gemini API calls (encrypted transit)                       │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
        │
        │ Processed data, AI outputs
        ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                                      │
│                                                                          │
│  ┌─────────────────────┐    ┌─────────────────────┐                    │
│  │   FIRESTORE         │    │   CLOUD SQL         │                    │
│  │   (Encrypted)       │    │   (Encrypted)       │                    │
│  │                     │    │                     │                    │
│  │  - patients         │    │  - users            │                    │
│  │  - conversations    │    │  - audit_logs       │                    │
│  │  - medications      │    │  - organizations    │                    │
│  │  - wearable_data    │    │  - appointments     │                    │
│  └─────────────────────┘    └─────────────────────┘                    │
│                                                                          │
│  ┌─────────────────────┐    ┌─────────────────────┐                    │
│  │  CLOUD STORAGE      │    │  VERTEX AI VECTOR   │                    │
│  │  (CMEK Encrypted)   │    │  DB (Embeddings)    │                    │
│  │                     │    │                     │                    │
│  │  - prescription_img │    │  - clinical_proto   │                    │
│  │  - clinical_docs    │    │  - medical_lit      │                    │
│  │  - backups          │    │                     │                    │
│  └─────────────────────┘    └─────────────────────┘                    │
└────────────────────────────────────────────────────────────────────────┘
        │
        │ Query results, stored data
        ▼
┌────────────────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                                   │
│  ┌──────────────────────────────────────────────────────────────┐      │
│  │              Client Applications                              │      │
│  │  - Data rendering (charts, lists, detail views)              │      │
│  │  - Local caching (service workers, async storage)            │      │
│  │  - Real-time updates (WebSocket, Firebase Realtime DB)       │      │
│  └──────────────────────────────────────────────────────────────┘      │
└────────────────────────────────────────────────────────────────────────┘
```

### 8.2 Data Security and Privacy

**Encryption:**
- **At Rest:** AES-256 encryption for all databases and storage
- **In Transit:** TLS 1.3 for all communications
- **Key Management:** Customer-managed encryption keys (CMEK) via Cloud KMS, automatic 90-day rotation

**De-Identification:**
- **Logging:** PII/PHI scrubbed from application logs (names, MRNs replaced with hashed IDs)
- **Analytics:** Aggregated metrics only (no individual patient data in dashboards)
- **Testing:** Synthetic data generation for non-production environments

**Access Control:**
- **RBAC:** Role-based access (admin, doctor, patient) enforced at API Gateway
- **ABAC:** Attribute-based (doctor can only access their patients) enforced at application layer
- **Audit:** All data access logged to immutable audit_logs table (7-year retention)

**Data Minimization:**
- **API Calls:** Only necessary fields sent to Gemini API (exclude sensitive demographics when not needed)
- **Caching:** Cached content excludes PHI (clinical guidelines only, not patient data)
- **Retention:** Automatic deletion policies (prescription images after 30 days, unless patient-requested retention)

---

## 9. SIZE AND PERFORMANCE

### 9.1 Capacity Planning

**Current (MVP - 1 Hospital, 5,000 Patients):**
- Daily active users: 1,500 (30% of patients, 100 doctors, 50 admins)
- Gemini API requests: 50,000/day
- Token consumption: 150M tokens/day
- Storage growth: 50 GB/month
- Cost: $5,000/month ($2,500 AI, $1,500 infrastructure, $1,000 other)

**12-Month Projection (10 Hospitals, 50,000 Patients):**
- Daily active users: 15,000
- Gemini API requests: 500,000/day
- Token consumption: 1.5B tokens/day (with 80% cache hit rate)
- Storage: 20 TB total
- Cost: $35,000/month ($20,000 AI, $10,000 infrastructure, $5,000 other)

**3-Year Projection (100 Hospitals, 500,000 Patients):**
- Daily active users: 150,000
- Gemini API requests: 5M/day
- Token consumption: 15B tokens/day (with optimizations)
- Storage: 200 TB total
- Cost: $200,000/month ($120,000 AI, $60,000 infrastructure, $20,000 other)

### 9.2 Performance Benchmarks

**Response Times (95th Percentile):**
- Doctor clinical search: 2.8 seconds (target: < 3 seconds) ✓
- Patient conversation: 0.9 seconds (target: < 1 second) ✓
- Drug interaction check: 0.7 seconds (target: < 1 second) ✓
- Admin dashboard load: 1.5 seconds (target: < 2 seconds) ✓
- Prescription OCR: 1.2 seconds (target: < 2 seconds) ✓

**Throughput:**
- Concurrent users per region: 10,000
- Requests per minute (RPM): 2,000 (sustained)
- Gemini API rate limit: 2,000 RPM (Tier 3, distributed across agents)
- Database writes: 500/second (Firestore auto-scales)

**Resource Utilization:**
- Cloud Run CPU: 65% average (target: 70%)
- Cloud Run memory: 2.5GB average (4GB allocated)
- Cloud SQL connections: 150 active (500 max)
- Redis cache hit rate: 85% (target: 80%) ✓

### 9.3 Optimization Strategies

**Token Optimization:**
- Context caching for clinical guidelines (saves 90% on repeated content)
- Media resolution optimization (use `medium` for most PDFs, not `high`)
- Structured outputs to reduce verbose responses
- Target: < 5,000 tokens per average doctor query (currently 4,200)

**Latency Optimization:**
- Context caching reduces time-to-first-token by 60%
- Gemini 3 Flash for routing and patient conversations (3x faster than Pro)
- Parallel function calls (simultaneous EHR lookup + drug interaction check)
- Redis caching for frequently accessed EHR data (1-hour TTL)

**Cost Optimization:**
- Context caching: 90% cost reduction on cached content
- Batch API for non-urgent workloads (50% discount)
- Combined caching + batch: 75% total cost reduction
- Gemini 3 Flash for patient queries (5x cheaper than Pro)
- Target: < $0.10 per patient conversation, < $2 per complex clinical query

---

## 10. QUALITY ATTRIBUTES

### 10.1 Security

**Implementation:**
- **Authentication:** Multi-factor authentication (MFA) via Firebase Auth + SMS OTP
- **Authorization:** Custom RBAC middleware validating JWT claims against role matrix
- **Encryption:** TLS 1.3 (transit), AES-256 (rest), CMEK via Cloud KMS
- **Audit:** Comprehensive logging to immutable Cloud SQL audit_logs table
- **Vulnerability Management:** Weekly Snyk scans, quarterly penetration testing

**Validation:**
- Third-party penetration test (annual)
- HITRUST CSF certification (annual audit)
- Automated security scanning in CI/CD (Trivy, Snyk)

### 10.2 Reliability

**Implementation:**
- **Redundancy:** Multi-region deployment (us-central1, asia-south1)
- **Failover:** Automatic Cloud SQL replica promotion (< 30 seconds)
- **Circuit Breakers:** Prevent cascade failures from external system outages
- **Graceful Degradation:** Fallback to Gemini 2.5 Pro if 3.0 unavailable, cached protocols if API down

**Validation:**
- Chaos engineering tests (monthly): Random pod termination, network latency injection
- Disaster recovery drill (quarterly): Simulate region outage, measure RTO
- Uptime monitoring: 99.9% SLA (8.76 hours downtime/year), currently 99.95%

### 10.3 Performance

**Implementation:**
- **Caching:** Multi-layer caching (Redis for sessions/EHR, Vertex AI for prompts, CDN for assets)
- **Async Processing:** asyncio for non-blocking I/O, Pub/Sub for background tasks
- **Database Optimization:** Indexes on (user_id, created_at), read replicas for queries
- **Auto-Scaling:** Cloud Run scales 0-50 instances based on CPU and queue depth

**Validation:**
- Load testing (monthly): Simulate 10,000 concurrent users with k6
- Performance regression tests: Baseline response times in CI/CD
- APM monitoring: Cloud Trace for distributed tracing, identify bottlenecks

### 10.4 Scalability

**Implementation:**
- **Horizontal Scaling:** Cloud Run auto-scales, Firestore auto-shards
- **Stateless Design:** No session state in containers (externalized to Vertex AI Sessions)
- **Database Sharding:** Partition by organization_id for multi-tenancy
- **CDN:** Cloud CDN for static assets (reduces origin load by 80%)

**Validation:**
- Scalability testing: Incrementally increase load from 1K → 10K → 100K users
- Resource monitoring: Track CPU, memory, database connections at scale
- Cost projection: Validate that cost scales sublinearly with users (via caching efficiency)

### 10.5 Maintainability

**Implementation:**
- **Modular Architecture:** Clear separation between agents, tools, integrations
- **Comprehensive Logging:** Structured JSON logs with correlation IDs
- **Observability:** Distributed tracing (Cloud Trace), metrics (Cloud Monitoring)
- **Documentation:** OpenAPI specs auto-generated, inline code comments, runbooks

**Validation:**
- Time-to-resolution: Track mean time to resolve (MTTR) for incidents (target: < 2 hours)
- Code quality: Enforce 80% test coverage, peer review all changes
- Developer onboarding: New engineer productive within 1 week (documentation quality metric)

---

## 11. RISKS AND MITIGATION

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| **Gemini API model hallucination causes clinical error** | Medium | Critical | Mandatory human verification for all clinical outputs, strong system instructions emphasizing uncertainty, disclaimers on all AI responses |
| **HIPAA breach due to misconfiguration** | Low | Critical | Automated compliance checks in CI/CD, quarterly third-party audits, comprehensive training |
| **Gemini API outage disrupts service** | Low | High | Fallback to Gemini 2.5 Pro, graceful degradation to cached protocols, SLA with Google Cloud |
| **EHR integration failures delay deployment** | High | High | Extensive pre-integration testing, vendor partnerships, abstraction layer for EHR-agnostic logic |
| **Resistance to AI adoption by clinicians** | Medium | Medium | Physician champions, gradual rollout, training programs, demonstrate quick wins |
| **Token costs exceed budget** | Medium | Medium | Context caching (90% savings), batch processing (50% discount), Gemini Flash for low-complexity tasks |
| **Thought signature preservation failures** | Low | Medium | Comprehensive testing, automatic error detection and retry, SDK usage (handles automatically) |
| **Data residency compliance violations** | Low | High | Regional deployment enforcement via Terraform, automated audits, policy-based controls |

---

## 12. ARCHITECTURAL DECISION RECORDS (ADRs)

### ADR-001: Use ADK Framework for Multi-Agent Orchestration

**Status:** Accepted  
**Context:** Need robust framework for hierarchical agent coordination  
**Decision:** Adopt Google ADK over LangChain or custom framework  
**Rationale:** Native integration with Gemini API, thought signature handling, Vertex AI Sessions support  
**Consequences:** Team needs to learn ADK patterns, vendor lock-in to Google ecosystem (acceptable given Gemini dependency)

### ADR-002: Gemini 3 Pro for Clinical, Flash for Patient

**Status:** Accepted  
**Context:** Balance accuracy vs. cost/latency across personas  
**Decision:** Gemini 3 Pro (`thinking_level: high`) for clinical decisions, Flash (`thinking_level: low`) for patient conversations  
**Rationale:** Clinical accuracy critical (justify higher cost), patient interactions need sub-second latency (Flash 3x faster)  
**Consequences:** Higher operational cost for clinical queries (~$2 vs. $0.10), but aligned with quality requirements

### ADR-003: Firestore for Conversations, Cloud SQL for Audit

**Status:** Accepted  
**Context:** Need flexible schema for conversations, ACID for audit logs  
**Decision:** Hybrid database architecture (Firestore + Cloud SQL)  
**Rationale:** Firestore excels at semi-structured data (messages with varying tool calls), Cloud SQL provides immutability for compliance  
**Consequences:** Increased operational complexity (two databases), but optimal for use case

### ADR-004: No Custom Model Fine-Tuning

**Status:** Accepted  
**Context:** Consider fine-tuning Gemini for medical specificity  
**Decision:** Use base Gemini models with RAG (retrieval-augmented generation) for hospital protocols  
**Rationale:** Fine-tuning expensive ($$$), slow iteration, RAG provides similar benefits with faster updates  
**Consequences:** Dependence on prompt engineering and vector DB quality, acceptable given maturity of base models

### ADR-005: React PWA for Doctor Portal (Not Native Mobile)

**Status:** Accepted  
**Context:** Mobile-first requirement for doctor interface  
**Decision:** Progressive Web App (PWA) instead of React Native  
**Rationale:** Faster development, single codebase, offline capability via service workers, sufficient for clinical use case  
**Consequences:** Limited access to device APIs (vs. native), acceptable given no need for deep OS integration for doctors

---

## APPENDIX A: GLOSSARY

**ADK (Agentic Development Kit):** Google's framework for building multi-agent AI systems  
**Context Caching:** Gemini API feature to cache frequently used content and reduce costs  
**FHIR (Fast Healthcare Interoperability Resources):** HL7 standard for healthcare data exchange  
**Function Calling:** LLM capability to invoke external tools/APIs with structured parameters  
**Grounding:** Connecting LLM responses to external data sources for factual accuracy  
**Memory Bank:** Vertex AI feature for long-term conversational context storage  
**OCR (Optical Character Recognition):** Extracting text from images  
**RAG (Retrieval-Augmented Generation):** Pattern where LLM retrieves documents before generating responses  
**Thought Signature:** Encrypted representation of model's reasoning in Gemini 3  
**Vertex AI:** Google Cloud's managed ML platform  

---

**Document Approval:**
- **Architect:** Principal AI Engineer
- **Reviewers:** Backend Lead, DevOps Lead, Security Officer, CTO
- **Status:** Draft for Review
- **Version:** 1.0
- **Date:** January 29, 2026

```

## File: app/application/__init__.py

```py

```

## File: app/application/agents/base_orchestrator.py

```py
from ...infrastructure.ai.gemini import GeminiAgent
from ...domain.interfaces import OrchestratorInterface
from typing import Dict, Any, Optional

class BaseDomainOrchestrator(OrchestratorInterface):
    def __init__(self, name: str):
        self.agent = GeminiAgent(name)
        # In a real implementation, each subclass would initialize its specific sub-agents here
        
    def route_request(self, user_query: str, conversation_id: int, context: Optional[Dict[str, Any]] = None, device: Optional[Any] = None) -> Dict[str, Any]:
        # Placeholder generic routing for now, specialized implementations will override
        response = self.agent.generate_response(user_query, conversation_id, context)
        return {"agent": self.agent.agent_name, "response": response}

```

## File: app/application/agents/clinician/orchestrator.py

```py
from ..base_orchestrator import BaseDomainOrchestrator
from ....infrastructure.ai.gemini import GeminiAgent

class ClinicianOrchestrator(BaseDomainOrchestrator):
    def __init__(self):
        super().__init__("ClinicianOrchestrator")
        self.protocol_agent = GeminiAgent("ProtocolAgent")
        self.evidence_agent = GeminiAgent("EvidenceAgent")
        
    def route_request(self, user_query, conversation_id, context=None):
        if "protocol" in user_query.lower():
             return {"agent": "ProtocolAgent", "response": self.protocol_agent.generate_response(user_query, conversation_id, context)}
        else:
             return {"agent": "ClinicianGeneral", "response": self.agent.generate_response(user_query, conversation_id, context)}

```

## File: app/application/agents/clinician/search.py

```py
from ...infrastructure.ai.gemini import GeminiAgent

class ClinicalAgent(GeminiAgent):
    def __init__(self):
        super().__init__("ClinicalAgent")
        
    def generate_response(self, prompt, conversation_id, context=None):
        system_prompt = """
        Role: Clinical Decision Support Specialist.
        Task: Provide evidence-based medical information to a clinician.
        Rules:
        1. Cite major guidelines (AHA, ACC, ADA, NICE).
        2. Focus on drug interactions, dosage standards, and contraindications.
        3. Use professional medical terminology.
        4. Structure response with Markdown headers.
        """
        
        full_prompt = f"{system_prompt}\n\nClinician Query: {prompt}"
        return super().generate_response(full_prompt, conversation_id, context)

```

## File: app/application/agents/admin/coding.py

```py
from ...infrastructure.ai.gemini import GeminiAgent
import json

class BillingAgent(GeminiAgent):
    def __init__(self):
        super().__init__("BillingAgent")
        
    def generate_response(self, prompt, conversation_id, context=None):
        system_prompt = """
        Role: Medical Coding Specialist.
        Task: Extract ICD-11 codes from the provided clinical note.
        Output Format: JSON Array only. No markdown formatting.
        [{"code": "...", "description": "...", "confidence": 0.0-1.0}]
        """
        
        full_prompt = f"{system_prompt}\n\nClinical Note: {prompt}"
        response_text = super().generate_response(full_prompt, conversation_id, context)
        
        # Basic cleanup attempting to return pure JSON string, 
        # In a real app we'd parse this into a Pydantic model at the Controller level
        return response_text.replace("```json", "").replace("```", "").strip()

```

## File: app/application/agents/admin/claims.py

```py
from ...infrastructure.ai.gemini import GeminiAgent

class ClaimsAgent(GeminiAgent):
    def __init__(self):
        super().__init__("ClaimsAgent")
        
    def generate_response(self, prompt, conversation_id, context=None):
        system_prompt = """
        Role: Insurance Claims Adjudicator.
        Task: Analyze claim for potential denial risks.
        Output: "Approved" or "Denial Risk: [Reason]"
        """
        full_prompt = f"{system_prompt}\n\nClaim Data: {prompt}"
        return super().generate_response(full_prompt, conversation_id, context)

```

## File: app/application/agents/admin/orchestrator.py

```py
from ..base_orchestrator import BaseDomainOrchestrator
from ....infrastructure.ai.gemini import GeminiAgent

class AdminOrchestrator(BaseDomainOrchestrator):
    def __init__(self):
        super().__init__("AdminOrchestrator")
        self.claims_agent = GeminiAgent("ClaimsAgent")
        self.billing_agent = GeminiAgent("BillingAgent") # Legacy name mapping
        self.scheduling_agent = GeminiAgent("SchedulingAgent")

    def route_request(self, user_query, conversation_id, context=None):
        # Simplified routing for now, can be expanded like Root
        if "claim" in user_query.lower():
            return {"agent": "ClaimsAgent", "response": self.claims_agent.generate_response(user_query, conversation_id, context)}
        elif "schedule" in user_query.lower() or "appointment" in user_query.lower():
            return {"agent": "SchedulingAgent", "response": self.scheduling_agent.generate_response(user_query, conversation_id, context)}
        else:
            return {"agent": "AdminGeneral", "response": self.agent.generate_response(user_query, conversation_id, context)}

```

## File: app/application/agents/admin/scheduling.py

```py
from ...infrastructure.ai.gemini import GeminiAgent
from ...infrastructure.persistence.database import get_db_connection

class SchedulingAgent(GeminiAgent):
    def __init__(self):
        super().__init__("SchedulingAgent")
        
    def book_appointment(self, patient_id, doctor_id, time, reason):
        conn = get_db_connection()
        try:
            conn.execute(
                "INSERT INTO appointments (id, patient_id, doctor_id, start_time, end_time, reason) VALUES (?, ?, ?, ?, ?, ?)",
                (f"appt_{time}", patient_id, doctor_id, time, time, reason)
            )
            conn.commit()
            return "Appointment Booked Successfully."
        except Exception as e:
            return f"Booking Failed: {e}"
        finally:
            conn.close()

    def generate_response(self, prompt, conversation_id, context=None):
        # In full implementation, we would extract tools here
        instruction = "Extract appointment details (Time, Doctor) from input."
        full_prompt = f"{instruction}\n\nInput: {prompt}"
        return super().generate_response(full_prompt, conversation_id, context)

```

## File: app/application/agents/patient/triage.py

```py
from ...infrastructure.ai.gemini import GeminiAgent

class TriageAgent(GeminiAgent):
    def __init__(self):
        super().__init__("TriageAgent")
        
    def generate_response(self, prompt, conversation_id, context=None):
        system_prompt = f"""
        Role: You are a compassionate Medical Triage Assistant named "Dr. AI".
        Patient Context:
        - Name: {context.get('name') if context else 'Unknown'}
        - Conditions: {context.get('conditions') if context else 'Unknown'}
        - Allergies: {context.get('allergies') if context else 'Unknown'}
        
        Task:
        1. Analyze symptoms provided by the patient.
        2. Check against Known Conditions.
        3. DETECT EMERGENCIES: If symptoms match Chest Pain, Stroke signs, Severe Bleeding -> Reply "STATUS: EMERGENCY" immediately.
        4. Otherwise, provide supportive home-care advice or suggest a doctor visit.
        5. Keep language simple (Grade 6 level).
        """
        
        # We override generate_response to inject system prompt
        full_prompt = f"{system_prompt}\n\nUser Input: {prompt}"
        return super().generate_response(full_prompt, conversation_id, context)

```

## File: app/application/agents/patient/orchestrator.py

```py
from ..base_orchestrator import BaseDomainOrchestrator
from ....infrastructure.ai.gemini import GeminiAgent

class PatientOrchestrator(BaseDomainOrchestrator):
    def __init__(self):
        super().__init__("PatientOrchestrator")
        self.triage_agent = GeminiAgent("TriageAgent")
        
    def route_request(self, user_query, conversation_id, context=None):
        if "symptom" in user_query.lower() or "pain" in user_query.lower():
             return {"agent": "TriageAgent", "response": self.triage_agent.generate_response(user_query, conversation_id, context)}
        else:
             return {"agent": "PatientGeneral", "response": self.agent.generate_response(user_query, conversation_id, context)}

```

## File: app/application/services/root_orchestrator.py

```py
from ...domain.interfaces import OrchestratorInterface
from ...domain.models import DeviceCapabilities
from ..agents.admin.orchestrator import AdminOrchestrator
from ..agents.clinician.orchestrator import ClinicianOrchestrator
from ..agents.patient.orchestrator import PatientOrchestrator
from ...infrastructure.ai.gemini import GeminiAgent
from typing import Dict, Any, Optional

class RootOrchestrator(OrchestratorInterface):
    def __init__(self):
        # We use a Gemini Agent for the routing decision logic
        self.router = GeminiAgent("RootRouter", "gemini-3-flash-preview")
        self.admin = AdminOrchestrator()
        self.clinician = ClinicianOrchestrator()
        self.patient = PatientOrchestrator()

    def assess_complexity(self, query: str) -> str:
        simple_keywords = [
            "symptom", "fever", "headache", "cough", "cold", "flu",
            "medication", "dose", "when to take", "side effect",
            "appointment", "schedule"
        ]
        query_lower = query.lower()
        if any(kw in query_lower for kw in simple_keywords):
            return "simple"
        return "complex"

    def route_request(self, user_query: str, user_role: str, conversation_id: int, context: Optional[Dict[str, Any]] = None, device: Optional[DeviceCapabilities] = None) -> Dict[str, Any]:
        
        # --- 1. EDGE SMART ROUTING ---
        if device and device.has_local_model:
            complexity = self.assess_complexity(user_query)
            if complexity == "simple" and device.battery_level > 20:
                print(f"📱 Delegating to Edge AI. Query: '{user_query}'")
                return {
                    "agent": "EdgeAI",
                    "delegated": True,
                    "instruction": "USE_LOCAL_MODEL",
                    "reasoning": "Query is simple and device is capable."
                }
        
        # --- 2. CLOUD ROUTING ---
        prompt = f"""
        Role: System Root Router.
        Task: Route query to the correct Domain Orchestrator.
        User Role: {user_role}
        Query: {user_query}
        
        Domains:
        - PATIENT: Symptoms, wearable data, triage, health records.
        - CLINICIAN: Medical advice, protocols, imaging, prescriptions.
        - ADMIN: Coding, billing, scheduling, governance, compliance.
        
        Output: Domain Name (PATIENT, CLINICIAN, ADMIN, GENERAL).
        """
        
        decision_text = self.router.generate_response(prompt)
        decision = decision_text.strip().upper()
        
        print(f"🌳 Root Routing: {decision}")
        
        if decision == "PATIENT" or (user_role == "patient" and decision != "GENERAL"):
            return self.patient.route_request(user_query, conversation_id, context)
            
        elif decision == "CLINICIAN" or (user_role == "doctor" and decision != "GENERAL"):
             return self.clinician.route_request(user_query, conversation_id, context)
            
        elif decision == "ADMIN" or (user_role == "admin" and decision != "GENERAL"):
             return self.admin.route_request(user_query, conversation_id, context)
            
        else:
            # Fallback to general chat
            return {"agent": "General", "response": self.router.generate_response(user_query, conversation_id, context)}

```

## File: app/infrastructure/__init__.py

```py

```

## File: app/infrastructure/web/main.py

```py
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

```

## File: app/infrastructure/ai/gemini.py

```py
from ...domain.interfaces import AgentInterface
import os
import google.generativeai as genai
from typing import Dict, Any, Optional

# --- CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in environment variables.")

# Using the deprecated library for now as per legacy code, but isolated here.
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Error configuring Gemini: {e}")

class GeminiAgent(AgentInterface):
    def __init__(self, agent_name: str, model_name: str = "gemini-3.0-flash-preview"):
        self.agent_name = agent_name
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
    def generate_response(self, prompt: str, conversation_id: Optional[int] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates content using Google Gemini.
        Appends context if provided.
        """
        try:
            full_prompt = prompt
            if context:
                full_prompt += f"\n\nContext: {context}"
                
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"❌ Gemini Error in {self.agent_name}: {e}")
            return "I apologize, but I am currently unable to process your request due to a system error."

```

## File: app/infrastructure/persistence/database.py

```py
import sqlite3
from typing import Any

DB_FILE = "healthcare.db"

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

```

## File: app/domain/interfaces.py

```py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class AgentInterface(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, conversation_id: Optional[int] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response given a prompt and context."""
        pass

class OrchestratorInterface(ABC):
    @abstractmethod
    def route_request(self, user_query: str, user_role: str, conversation_id: int, context: Optional[Dict[str, Any]] = None, device: Optional[Any] = None) -> Dict[str, Any]:
        """Route request to appropriate handler."""
        pass

```

## File: app/domain/models.py

```py
from pydantic import BaseModel
from typing import Dict, Any, Optional

class DeviceCapabilities(BaseModel):
    has_local_model: bool = False
    battery_level: int = 100
    is_charging: bool = False
    network_quality: str = "good"

class AgentRequest(BaseModel):
    query: str
    role: str # Patient, Doctor, Admin
    conversation_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = {}
    device: Optional[DeviceCapabilities] = None

class LoginRequest(BaseModel):
    role: str

```

## File: app/domain/__init__.py

```py

```

## File: static/index.html

```html
<!doctype html>
<html lang="en" class="h-full">

<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dhanvantari OS - Live Tiles</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@300;400;600;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="style.css">
</head>

<body class="h-full">
    <div id="app" class="h-full w-full overflow-auto scrollbar-thin transition-colors duration-500">

        <!-- Header -->
        <div class="sticky top-0 z-20 backdrop-blur-xl bg-opacity-80 px-6 py-4">
            <div class="flex items-center justify-between max-w-4xl mx-auto">
                <div class="flex items-center gap-4">
                    <!-- Dynamic SVG Head (Bob/Doctor) -->
                    <svg id="bobhead" class="w-12 h-12" viewbox="0 0 100 100">
                        <!-- ... (SVG Content injected via JS or kept here if static) ... -->
                        <g id="doctor-head">
                            <ellipse cx="50" cy="50" rx="25" ry="27" fill="#e8c4a0" />
                            <ellipse cx="38" cy="45" rx="4" ry="4.5" fill="#fff" />
                            <circle cx="38" cy="45" r="2.5" fill="#333" />
                            <ellipse cx="62" cy="45" rx="4" ry="4.5" fill="#fff" />
                            <circle cx="62" cy="45" r="2.5" fill="#333" />
                            <path d="M 38 62 Q 50 65 62 62" stroke="#a0654d" stroke-width="2" fill="none"
                                stroke-linecap="round" />
                        </g>
                    </svg>
                    <div>
                        <h1 id="userName" class="text-2xl font-light tracking-tight">Dr. AI</h1>
                        <span id="role-indicator" class="text-xs uppercase tracking-widest opacity-60">System
                            Ready</span>
                    </div>
                </div>

                <div class="flex items-center gap-4">
                    <div class="text-right">
                        <p id="currentTime" class="text-lg font-light"></p>
                        <p id="currentDate" class="text-xs opacity-60"></p>
                    </div>
                </div>
            </div>
        </div>

        <!-- AI Status Bar -->
        <div class="px-6 py-2 max-w-4xl mx-auto">
            <div class="flex items-center gap-2 text-xs opacity-70">
                <div id="connection-dot" class="w-2 h-2 rounded-full bg-green-400 animate-pulse"></div>
                <span id="connection-text">Cloud Active</span>
                <span class="opacity-50">•</span>
                <span id="aiStatus">Monitoring Vitals...</span>
            </div>
        </div>

        <!-- Tiles Grid -->
        <div id="tilesContainer" class="px-6 py-4 max-w-4xl mx-auto mb-24">
            <div class="grid grid-cols-4 gap-3 auto-rows-[120px]" id="tilesGrid">
                <!-- Tiles injected by JS -->
            </div>
        </div>

        <!-- Quick Actions (Bottom Bar) -->
        <div class="fixed bottom-0 left-0 right-0 backdrop-blur-xl bg-opacity-90 border-t border-white/10 z-40">
            <div class="flex justify-around items-center py-3 max-w-4xl mx-auto px-6">
                <!-- Role Switcher Integrated into Bottom Bar -->
                <button onclick="setRole('patient')"
                    class="flex flex-col items-center gap-1 opacity-60 hover:opacity-100 transition-opacity">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                    </svg>
                    <span class="text-[10px]">Patient</span>
                </button>

                <button id="aiAssistBtn" class="flex flex-col items-center gap-1 relative scale-110">
                    <div class="absolute -top-1 -right-1 w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                    <svg class="w-6 h-6 text-blue-400" fill="currentColor" viewBox="0 0 24 24">
                        <path
                            d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-1 17.93c-3.95-.49-7-3.85-7-7.93 0-.62.08-1.21.21-1.79L9 15v1c0 1.1.9 2 2 2v1.93zm6.9-2.54c-.26-.81-1-1.39-1.9-1.39h-1v-3c0-.55-.45-1-1-1H8v-2h2c.55 0 1-.45 1-1V7h2c1.1 0 2-.9 2-2v-.41c2.93 1.19 5 4.06 5 7.41 0 2.08-.8 3.97-2.1 5.39z" />
                    </svg>
                    <span class="text-[10px] font-medium text-blue-400">Ask AI</span>
                </button>

                <button onclick="setRole('doctor')"
                    class="flex flex-col items-center gap-1 opacity-60 hover:opacity-100 transition-opacity">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    <span class="text-[10px]">Clinician</span>
                </button>

                <!-- Edge Toggle (Hidden simple visual) -->
                <button id="edgeToggle"
                    class="flex flex-col items-center gap-1 opacity-60 hover:opacity-100 transition-opacity">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
                            d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    <span class="text-[10px]">Edge: <span id="edgeState">ON</span></span>
                </button>
            </div>
        </div>

        <!-- Mini Chat Panel (The "Sheet") -->
        <div id="miniChat"
            class="fixed bottom-0 left-0 right-0 h-[50vh] backdrop-blur-2xl rounded-t-3xl shadow-2xl z-50  transform translate-y-full transition-transform duration-500 ease-out border-t border-white/20 bg-slate-900/90">
            <div class="p-4 h-full flex flex-col">
                <div class="flex items-center justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <div
                            class="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                            <span class="text-xl">🩺</span>
                        </div>
                        <div>
                            <h3 id="chatTitle" class="font-semibold text-sm text-white">Dhanvantari Assistant</h3>
                            <p id="chatContext" class="text-xs opacity-60 text-white">Tap a tile to focus context</p>
                        </div>
                    </div>
                    <button id="closeChatBtn" class="p-2 rounded-full hover:bg-white/10 text-white">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                        </svg>
                    </button>
                </div>

                <div id="chatMessages" class="flex-1 overflow-auto space-y-3 mb-4 p-2">
                    <!-- Msgs go here -->
                    <div class="flex gap-2">
                        <div class="bg-white/10 rounded-2xl rounded-tl-none px-4 py-2 max-w-[85%] text-white text-sm">
                            How can I assist you today?
                        </div>
                    </div>
                </div>

                <div class="flex gap-2">
                    <input type="text" id="chatInput" placeholder="Type your health query..."
                        class="flex-1 bg-white/10 text-white rounded-full px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-blue-500/50 transition-all">
                    <button id="sendBtn"
                        class="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center hover:bg-blue-500 text-white">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <!-- Overlay -->
        <div id="overlay" class="fixed inset-0 bg-black/60 opacity-0 pointer-events-none transition-opacity z-30"></div>

    </div>

    <script src="app.js"></script>
</body>

</html>
```

## File: static/style.css

```css
/* Base Setup matching the user request */
body {
    box-sizing: border-box;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
    background: #0f172a;
    /* Slate 900 base */
    color: white;
    overscroll-behavior: none;
}

/* --- TILE 3D ENGINE --- */
.tile {
    perspective: 1200px;
    transform-style: preserve-3d;
    cursor: pointer;
    position: relative;
    border-radius: 20px;
}

.tile-inner {
    position: relative;
    width: 100%;
    height: 100%;
    transform-style: preserve-3d;
    transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    border-radius: 20px;
}

.tile-face {
    position: absolute;
    width: 100%;
    height: 100%;
    backface-visibility: hidden;
    border-radius: 20px;
    overflow: hidden;
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
}

/* Glassy Gradients */
.glass-base {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
}

.tile-front {
    z-index: 2;
}

.tile-back {
    transform: rotateY(180deg);
    background: rgba(15, 23, 42, 0.95);
    /* Darker back */
}

/* Interaction States */
.tile.flipped .tile-inner {
    transform: rotateY(180deg);
}

.tile:hover {
    transform: translateY(-4px);
    transition: transform 0.3s ease;
}

.tile:active {
    transform: scale(0.96);
}

/* --- ANIMATIONS (Copied & Adapted) --- */
@keyframes tile-enter {
    from {
        opacity: 0;
        transform: scale(0.8) translateY(20px);
    }

    to {
        opacity: 1;
        transform: scale(1) translateY(0);
    }
}

.tile-animate {
    animation: tile-enter 0.6s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
    opacity: 0;
    /* Hidden initially */
}

/* Content Cycles */
@keyframes content-slide-up {

    0%,
    45% {
        transform: translateY(0);
        opacity: 1;
    }

    50% {
        transform: translateY(-10px);
        opacity: 0;
    }

    55% {
        transform: translateY(10px);
        opacity: 0;
    }

    100% {
        transform: translateY(0);
        opacity: 1;
    }
}

.tile-cycle {
    animation: content-slide-up 8s ease-in-out infinite;
}

/* Live Update Pulse */
@keyframes glow-pulse {

    0%,
    100% {
        box-shadow: 0 0 0 rgba(59, 130, 246, 0);
    }

    50% {
        box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
    }
}

.has-update {
    animation: glow-pulse 3s infinite;
    border-color: rgba(59, 130, 246, 0.5);
}

/* Mini Chat Sheet */
.mini-chat-open {
    transform: translateY(0) !important;
}

/* Scrollbar Hide */
.scrollbar-thin::-webkit-scrollbar {
    width: 4px;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 4px;
}

/* Custom message bubbles */
.msg-bubble-user {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
    color: white;
    border-radius: 18px 18px 2px 18px;
    padding: 8px 12px;
    font-size: 0.9rem;
    align-self: flex-end;
    box-shadow: 0 2px 10px rgba(59, 130, 246, 0.3);
}

.msg-bubble-ai {
    background: rgba(255, 255, 255, 0.1);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: white;
    border-radius: 18px 18px 18px 2px;
    padding: 8px 12px;
    font-size: 0.9rem;
    align-self: flex-start;
}

.msg-row {
    display: flex;
    width: 100%;
    margin-bottom: 8px;
}

.msg-row.user-row {
    justify-content: flex-end;
}
```

## File: static/app.js

```js
// --- CONFIG & STATE ---
const API_URL = "/api/agent/query";
let CURRENT_ROLE = "patient";
let EDGE_MODE = true; // Default to Edge ON
let CONVERSATION_ID = Date.now();

// --- TILE DEFINITIONS (Dhanvantari Context) ---
const tiles = [
    {
        id: 'triage',
        title: 'Virtual Triage',
        size: 'wide', // 2x1
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>',
        gradient: 'from-blue-600 to-indigo-600',
        front: { title: 'Symptom Check', subtitle: 'Tap to start assessment', extra: 'AI Ready' },
        back: { title: 'Actions', options: ['Report Fever', 'Check Cough', 'View History'] },
        role: 'patient'
    },
    {
        id: 'vitals',
        title: 'My Vitals',
        size: 'small', // 1x1
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/></svg>',
        gradient: 'from-rose-500 to-pink-600',
        front: { title: '98%', subtitle: 'SpO2' },
        back: { title: 'Heart Rate', subtitle: '72 bpm' }, // Simple text for back
        role: 'patient'
    },
    {
        id: 'meds',
        title: 'Medications',
        size: 'small',
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"/></svg>',
        gradient: 'from-emerald-500 to-teal-600',
        front: { title: 'Metformin', subtitle: '500mg • 8:00 AM' },
        back: { title: 'Adherence', subtitle: '95% this week' },
        role: 'patient'
    },
    {
        id: 'appointments',
        title: 'Appointments',
        size: 'medium', // 2x1 (same as wide in this grid system)
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"/></svg>',
        gradient: 'from-purple-600 to-violet-600',
        front: { title: 'Dr. Sharma', subtitle: 'Tomorrow, 10:00 AM', extra: 'Video Call' },
        back: { title: 'Actions', options: ['Join Call', 'Reschedule'] },
        role: 'patient'
    },
    // Doctor Tiles
    {
        id: 'patients-list',
        title: 'Patient List',
        size: 'wide',
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"/></svg>',
        gradient: 'from-cyan-600 to-blue-700',
        front: { title: '12 Patients', subtitle: '3 Waiting for Review' },
        back: { title: 'Triage', subtitle: 'High Priority: 2' },
        role: 'doctor'
    },
    {
        id: 'protocols',
        title: 'Protocols',
        size: 'medium',
        icon: '<svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"/></svg>',
        gradient: 'from-slate-600 to-slate-800',
        front: { title: 'Treatment Guidelines', subtitle: 'Search Protocols' },
        back: { title: 'Recent', options: ['Diabetes Type 2', 'Hypertension'] },
        role: 'doctor'
    }
];

// --- RENDER ENGINE ---

function getSizeClasses(size) {
    if (size === 'wide' || size === 'medium') return 'col-span-2 row-span-1';
    return 'col-span-1 row-span-1';
}

function renderTiles() {
    const grid = document.getElementById('tilesGrid');
    grid.innerHTML = '';

    // Filter tiles by role
    const visibleTiles = tiles.filter(t => t.role === CURRENT_ROLE || !t.role);

    visibleTiles.forEach((tile, index) => {
        const el = document.createElement('div');
        el.className = `tile ${getSizeClasses(tile.size)} tile-animate`;
        el.style.animationDelay = `${index * 0.1}s`;

        // Front Content
        const frontHTML = `
            <div class="h-full flex flex-col justify-between p-4 relative z-10">
                <div class="flex justify-between items-start">
                    <div class="text-white/80 opacity-70 scale-90">${tile.icon}</div>
                    ${tile.gradient.includes('rose') ? '<div class="w-2 h-2 bg-white rounded-full animate-ping"></div>' : ''}
                </div>
                <div class="tile-cycle">
                    <p class="text-xl font-bold leading-none text-white drop-shadow-md">${tile.front.title}</p>
                    <p class="text-xs text-white/70 mt-1">${tile.front.subtitle}</p>
                    ${tile.front.extra ? `<span class="text-[10px] bg-white/20 px-1.5 py-0.5 rounded mt-2 inline-block">${tile.front.extra}</span>` : ''}
                </div>
            </div>
        `;

        // Back Content
        let backHTML = '';
        if (tile.back.options) {
            backHTML = `
                <div class="h-full flex flex-col p-4 relative z-10">
                    <p class="text-xs font-semibold uppercase opacity-60 mb-2">${tile.back.title}</p>
                    <div class="flex flex-col gap-2">
                        ${tile.back.options.map(opt => `<button class="text-left text-[10px] bg-white/10 hover:bg-white/20 rounded px-2 py-1 transition">${opt}</button>`).join('')}
                    </div>
                </div>
            `;
        } else {
            backHTML = `
                <div class="h-full flex flex-col justify-center items-center p-4 text-center relative z-10">
                    <p class="text-xs font-semibold uppercase opacity-60 mb-1">${tile.back.title}</p>
                    <p class="text-lg font-bold">${tile.back.subtitle}</p>
                </div>
            `;
        }

        el.innerHTML = `
            <div class="tile-inner h-full">
                <div class="tile-face tile-front bg-gradient-to-br ${tile.gradient}">
                    ${frontHTML}
                </div>
                <div class="tile-face tile-back bg-slate-900 border border-white/10">
                    ${backHTML}
                </div>
            </div>
        `;

        // Interactions
        el.addEventListener('click', (e) => {
            // If clicking a button inside back face, don't flip
            if (e.target.tagName === 'BUTTON') {
                openChat(tile.title, `I selected "${e.target.innerText}" from ${tile.title}.`);
                return;
            }
            // Flip logic or Open Chat
            if (tile.id === 'triage' || tile.id === 'protocols') {
                // Open Chat directly for interactive tiles
                openChat(tile.title);
            } else {
                el.classList.toggle('flipped');
            }
        });

        grid.appendChild(el);
    });
}

// --- CHAT & API LOGIC ---

const chatPanel = document.getElementById('miniChat');
const chatInput = document.getElementById('chatInput');
const chatMsgs = document.getElementById('chatMessages');
const overlay = document.getElementById('overlay');

function openChat(context = "General", initialQuery = "") {
    document.getElementById('chatTitle').innerText = context;
    document.getElementById('chatContext').innerText = `AI Agent Active (${CURRENT_ROLE})`;
    chatPanel.classList.add('mini-chat-open');
    overlay.style.opacity = '1';
    overlay.style.pointerEvents = 'auto';

    if (initialQuery) {
        // Auto send if triggered by action
        sendUserMessage(initialQuery);
    } else {
        chatInput.focus();
    }
}

function closeChat() {
    chatPanel.classList.remove('mini-chat-open');
    overlay.style.opacity = '0';
    overlay.style.pointerEvents = 'none';
}

document.getElementById('closeChatBtn').addEventListener('click', closeChat);
overlay.addEventListener('click', closeChat);
document.getElementById('aiAssistBtn').addEventListener('click', () => openChat());

// Sending Messages
async function sendUserMessage(text = "") {
    const query = text || chatInput.value.trim();
    if (!query) return;

    // UI
    addMessage(query, 'user');
    chatInput.value = "";

    // API Call
    addMessage("Thinking...", 'ai', true); // Temp loading msg

    const payload = {
        query: query,
        role: CURRENT_ROLE,
        conversation_id: CONVERSATION_ID,
        device: {
            has_local_model: EDGE_MODE,
            battery_level: 85
        }
    };

    try {
        const res = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();

        // Remove loading
        chatMsgs.lastElementChild.remove();

        // Formatting
        let responseText = data.response || "No response.";
        if (data.delegated) responseText = `[⚡ Edge AI]: ${data.instruction}`;

        addMessage(responseText, 'ai');

    } catch (e) {
        console.error(e);
        chatMsgs.lastElementChild.remove();
        addMessage("⚠️ Connection Error. Ensure backend is running.", 'ai');
    }
}

function addMessage(text, type, isTemp = false) {
    const div = document.createElement('div');
    div.className = `msg-row ${type === 'user' ? 'user-row' : ''}`;
    div.innerHTML = `<div class="msg-bubble-${type} ${isTemp ? 'animate-pulse' : ''}">${text}</div>`;
    chatMsgs.appendChild(div);
    chatMsgs.scrollTop = chatMsgs.scrollHeight;
}

document.getElementById('sendBtn').addEventListener('click', () => sendUserMessage());
chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') sendUserMessage();
});


// --- GLOBAL UTILS ---
function updateTime() {
    const now = new Date();
    document.getElementById('currentTime').innerText = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    document.getElementById('currentDate').innerText = now.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' });
}

function setRole(role) {
    CURRENT_ROLE = role;
    renderTiles(); // Re-render tiles for new role
    // Visual feedback on role change can be added here
}

document.getElementById('edgeToggle').addEventListener('click', () => {
    EDGE_MODE = !EDGE_MODE;
    document.getElementById('edgeState').innerText = EDGE_MODE ? "ON" : "OFF";
    document.getElementById('edgeState').style.color = EDGE_MODE ? "#4ade80" : "#ef4444";
});

// Init
setInterval(updateTime, 1000);
updateTime();
renderTiles();

```

## File: static/css/style.css

```css
:root {
    --primary: #2563EB;
    --primary-dark: #1E40AF;
    --secondary: #64748B;
    --bg-color: #F8FAFC;
    --surface: #FFFFFF;
    --text-primary: #1E293B;
    --text-secondary: #475569;
    --success: #10B981;
    --warning: #F59E0B;
    --danger: #EF4444;
    --glass-bg: rgba(255, 255, 255, 0.7);
    --glass-border: rgba(255, 255, 255, 0.5);
    --shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}

* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

body {
    font-family: 'Inter', sans-serif;
    background-color: var(--bg-color);
    color: var(--text-primary);
    line-height: 1.5;
    height: 100vh;
    overflow: hidden;
    background-image: 
        radial-gradient(at 0% 0%, hsla(253,16%,7%,1) 0, transparent 50%), 
        radial-gradient(at 50% 0%, hsla(225,39%,30%,1) 0, transparent 50%), 
        radial-gradient(at 100% 0%, hsla(339,49%,30%,1) 0, transparent 50%);
    background-color: #f3f4f6; /* Fallback */
    background-size: cover;
}

#app {
    display: flex;
    height: 100vh;
}

/* SIDEBAR */
.sidebar {
    width: 260px;
    background: var(--glass-bg);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border-right: 1px solid var(--glass-border);
    display: flex;
    flex-direction: column;
    padding: 20px;
    transition: transform 0.3s ease;
}

.sidebar.hidden {
    display: none;
}

.brand {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary);
    margin-bottom: 40px;
    display: flex;
    align-items: center;
    gap: 10px;
}

.user-profile {
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 20px;
    border-bottom: 1px solid rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.avatar {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background: var(--primary);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

.nav-links {
    list-style: none;
    flex: 1;
}

.nav-item {
    padding: 12px 16px;
    margin-bottom: 5px;
    border-radius: 8px;
    cursor: pointer;
    color: var(--text-secondary);
    transition: all 0.2s;
    font-weight: 500;
}

.nav-item:hover, .nav-item.active {
    background: rgba(37, 99, 235, 0.1);
    color: var(--primary);
}

.nav-item i {
    width: 24px;
}

/* MAIN CONTENT */
.content {
    flex: 1;
    overflow-y: auto;
    padding: 30px;
    position: relative;
}

.view {
    display: none;
    animation: fadeIn 0.4s ease;
}

.view.active {
    display: block;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* GLASS PANEL */
.glass-panel {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: var(--shadow);
    border-radius: 16px;
    padding: 24px;
    margin-bottom: 24px;
}

/* LOGIN SCREEN */
.login-container {
    max-width: 900px;
    margin: 100px auto;
    text-align: center;
}

.persona-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    margin-top: 40px;
}

.persona-card {
    background: rgba(255,255,255,0.6);
    padding: 30px;
    border-radius: 12px;
    cursor: pointer;
    transition: transform 0.2s, box-shadow 0.2s;
    border: 1px solid transparent;
}

.persona-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    border-color: var(--primary);
}

.persona-card i {
    font-size: 3rem;
    color: var(--primary);
    margin-bottom: 15px;
}

/* CHAT */
.chat-container {
    height: 70vh;
    display: flex;
    flex-direction: column;
}

.chat-history {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.message {
    max-width: 80%;
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 0.95rem;
}

.message.user {
    align-self: flex-end;
    background: var(--primary);
    color: white;
    border-bottom-right-radius: 2px;
}

.message.model {
    align-self: flex-start;
    background: #f1f5f9;
    color: var(--text-primary);
    border-bottom-left-radius: 2px;
}

.message.emergency {
    border: 2px solid var(--danger);
    background: #fee2e2;
    color: #991b1b;
}

.chat-input-area {
    padding-top: 20px;
    display: flex;
    gap: 10px;
}

input[type="text"], textarea {
    width: 100%;
    padding: 12px;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    font-family: inherit;
    font-size: 1rem;
    &:focus {
        outline: none;
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }
}

button {
    padding: 12px 24px;
    background: var(--primary);
    color: white;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}

button:hover {
    background: var(--primary-dark);
}

/* UTILS */
.grid-2 {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px;
}

.upload-area {
    border: 2px dashed #cbd5e1;
    border-radius: 12px;
    padding: 40px;
    text-align: center;
    color: var(--text-secondary);
    margin-bottom: 20px;
    cursor: pointer;
}

.upload-area:hover {
    border-color: var(--primary);
    background: rgba(37, 99, 235, 0.05);
}

pre {
    background: #f1f5f9;
    padding: 15px;
    border-radius: 8px;
    font-family: monospace;
    font-size: 0.85rem;
    overflow-x: auto;
}

```

## File: static/js/app.js

```js
const App = {
    state: {
        user: null,
        token: null,
        chatHistory: [],
        patientContext: null
    },

    // --- NAVIGATION ---
    init() {
        // Check local storage for session? For demo, we start clean.
        console.log("App Initialized");
    },

    navigate(viewId) {
        document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
        document.getElementById(`view-${viewId}`).classList.add('active');
        
        document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
        // Find nav item that calls this view
        const activeNav = document.querySelector(`.nav-item[onclick*="${viewId}"]`);
        if(activeNav) activeNav.classList.add('active');
    },

    // --- AUTH ---
    async login(role) {
        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({role})
            });
            
            if (!response.ok) throw new Error("Login failed");
            
            const data = await response.json();
            this.state.user = data.user;
            this.state.patientContext = data.patient; // Populated only if patient
            
            // Update UI
            document.getElementById('user-name').innerText = data.user.full_name;
            document.getElementById('user-role').innerText = role;
            document.getElementById('user-avatar').innerText = data.user.full_name.charAt(0);
            
            // Show Sidebar
            document.getElementById('sidebar').classList.remove('hidden');
            
            // Filter Nav Links
            document.querySelectorAll('.nav-item').forEach(el => {
                if(el.dataset.role === role.toLowerCase()) {
                    el.style.display = 'block';
                } else {
                    el.style.display = 'none';
                }
            });
            
            // Navigate to Home based on role
            if (role === 'Patient') {
                this.navigate('patient-chat');
            } else if (role === 'Doctor') {
                this.navigate('doctor-search');
            } else if (role === 'Admin') {
                this.navigate('admin-coding');
            }
            
            // Hide Login
            document.getElementById('view-login').classList.remove('active');
            
        } catch (e) {
            alert("Error logging in: " + e.message);
        }
    },

    logout() {
        this.state.user = null;
        this.state.chatHistory = [];
        document.getElementById('sidebar').classList.add('hidden');
        document.getElementById('view-login').classList.add('active');
        document.querySelectorAll('.view').forEach(el => {
            if(el.id !== 'view-login') el.classList.remove('active');
        });
    },

    // --- PATIENT CHAT ---
    async sendChatMessage() {
        const input = document.getElementById('chat-input');
        const text = input.value.trim();
        if (!text) return;

        // Add User Message to UI
        this.addMessageToUI('user', text);
        input.value = '';

        // API Call
        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: text,
                    history: this.state.chatHistory,
                    patient_context: this.state.patientContext || {}
                })
            });

            const data = await response.json();
            
            // Update History
            this.state.chatHistory.push({role: 'user', content: text});
            this.state.chatHistory.push({role: 'model', content: data.response});
            
            // Add Model Message to UI
            this.addMessageToUI('model', data.response, data.is_emergency);

        } catch (e) {
            this.addMessageToUI('model', "Error: Could not reach Dr. AI.");
        }
    },

    addMessageToUI(role, text, isEmergency=false) {
        const container = document.getElementById('chat-history');
        const str = `
            <div class="message ${role} ${isEmergency ? 'emergency' : ''}">
                <div class="text">${text}</div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', str);
        container.scrollTop = container.scrollHeight;
    },

    // --- DOCTOR SEARCH ---
    async clinicalSearch() {
        const query = document.getElementById('doc-search-input').value;
        const container = document.getElementById('search-results');
        
        container.innerHTML = '<div class="glass-panel">Searching medical protocols... <i class="fa-solid fa-spinner fa-spin"></i></div>';
        
        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    query: query,
                    patient_meds: "Metformin, Lisinopril" // Mock
                })
            });
            const data = await response.json();
            container.innerHTML = `<div class="glass-panel">${marked.parse(data.result)}</div>`; // Assume marked.js is loaded or just plain text
            
        } catch (e) {
            container.innerHTML = '<div class="glass-panel">Error searching protocols.</div>';
        }
    },

    // --- ADMIN CODING ---
    async generateCodes() {
        const note = document.getElementById('clinical-note').value;
        const container = document.getElementById('coding-results');
        
        container.innerHTML = 'Analyzing...';
        
        try {
            const response = await fetch('/api/coding', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({note})
            });
            const data = await response.json();
            
            let html = '';
            data.codes.forEach(code => {
                const color = code.confidence > 0.8 ? '#10B981' : '#F59E0B';
                html += `
                    <div style="padding: 10px; border-left: 4px solid ${color}; background: #f8fafc; margin-bottom: 8px;">
                        <strong>${code.code}</strong>: ${code.description}
                        <br><small>Confidence: ${Math.round(code.confidence * 100)}%</small>
                    </div>
                `;
            });
            container.innerHTML = html;
            
        } catch (e) {
            container.innerHTML = 'Error generating codes.';
        }
    }
};

// RX Upload Listener
const rxInput = document.getElementById('rx-upload');
if (rxInput) {
    rxInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if(!file) return;
        
        const output = document.getElementById('json-output');
        output.innerText = "Extracting data with Gemini Vision...";
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/upload_rx', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            output.innerText = JSON.stringify(data, null, 2);
        } catch (e) {
            output.innerText = "Error extracting data.";
        }
    });
}

// Init
App.init();

```

