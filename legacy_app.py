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
