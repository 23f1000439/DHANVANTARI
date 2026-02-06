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
    
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "Clinical Search", "Patient Rounds", "Imaging Triage ⚠️",
        "📚 Guideline RAG", "💊 Rx Digitalizer", "🩺 Bedside Monitor"
    ])
    
    # Fetch patients once
    conn = get_db_connection()
    patients = conn.execute("SELECT p.id, u.full_name, p.conditions FROM patients p JOIN users u ON p.user_id = u.id").fetchall()
    conn.close()
    
    with tab1:
        st.subheader("🧠 Evidence-Based Clinical Search")
        query = st.text_input("Ask a clinical question (e.g., 'Drug interactions for Metformin')")
        
        selected_p_id_search = st.selectbox("Context Patient (Optional):", [p['id'] for p in patients], format_func=lambda x: [p['full_name'] for p in patients if p['id'] == x][0], key="search_pat")
        
        if st.button("Search Protocols"):
            if query:
                p_ctx_meds = "Metformin, Lisinopril" 
                
                with st.spinner("Searching Medical Guidelines (Gemini 3 Pro)..."):
                    response = st.session_state.ai_service.get_clinical_search_response(query, p_ctx_meds)
                    st.markdown(response)
                    st.info("ℹ️ Information grounded in simulated medical database.")
    
    with tab2:
        st.write("Patient Rounds View (Mockup)")
        df = pd.DataFrame(patients, columns=["ID", "Name", "Conditions"])
        st.dataframe(df)

    with tab3:
        st.subheader("⚡️ AI Imaging Triage (Edge + Cloud)")
        
        img_file = st.file_uploader("Upload Scan (X-Ray/CT/MRI)", type=["png", "jpg", "dcm"])
        selected_p_id_img = st.selectbox("Select Patient:", [p['id'] for p in patients], format_func=lambda x: [p['full_name'] for p in patients if p['id'] == x][0], key="img_pat")
        st.markdown("**Simulated Vision Encoder Output:**")
        tags_input = st.text_input("Enter detected visual tags (comma separated):", value="large right-sided pneumothorax, midline shift, mediastinal deviation")
        
        if st.button("Process Scan"):
            from app.application.services.imaging_orchestrator import ImagingOrchestrator
            orch = ImagingOrchestrator()
            p_notes = "Patient complaining of sudden onset chest pain and shortness of breath."
            
            with st.status("Running Hybrid Triage Pipeline...", expanded=True) as status:
                st.write("1️⃣  Edge: Local MedGemma analyzing features...")
                time.sleep(1)
                tags = [t.strip() for t in tags_input.split(",")]
                results = orch.process_scan(selected_p_id_img, img_file, tags, p_notes)
                triage = results["stage_1_triage"]
                
                if triage["classification"] == "URGENT_ABNORMAL":
                    st.error(f"🚨 TRIAGE ALERT: {triage['classification']}")
                    st.write(f"Latency: {triage['latency_ms']}ms")
                    st.write("2️⃣  Cloud: Gemini 3 Pro generating preliminary report...")
                    report = results["stage_2_report"]
                    st.success("Report Generated Successfully!")
                    status.update(label="Triage Complete: URGENT", state="error", expanded=True)
                    st.divider()
                    st.markdown("### 📝 Preliminary AI Report")
                    st.markdown(f"**Impression:** {report.get('impression')}")
                    for f in report.get('findings', []):
                        st.markdown(f"- {f}")
                    st.warning(f"**Recommendation:** {report.get('recommendations', ['Review ASAP'])[0]}")
                else:
                    st.success(f"✅ TRIAGE STATUS: {triage['classification']}")
                    st.info("No urgent findings detected.")
                    status.update(label="Triage Complete: NORMAL", state="complete", expanded=False)

    # ============ NEW TAB: Guideline RAG ============
    with tab4:
        st.subheader("📚 Grounded Guideline Search (RAG)")
        st.caption("Hybrid Search (BM25 + Vector) → MedGemma Validation → Gemini 3 Synthesis")
        
        rag_query = st.text_input("Clinical Question:", value="What is the latest sepsis management protocol?", key="rag_q")
        
        if st.button("Search Guidelines", key="rag_btn"):
            from app.application.services.central_orchestrator import DhanvantariCentralOrchestrator
            orchestrator = DhanvantariCentralOrchestrator()
            
            with st.status("Running RAG Pipeline...", expanded=True) as status:
                st.write("🔍 Step 1: Hybrid Search (BM25 + Vector)...")
                time.sleep(0.5)
                st.write("🔬 Step 2: MedGemma validating protocol currency...")
                time.sleep(0.5)
                st.write("🧠 Step 3: Gemini 3 synthesizing answer...")
                
                result = orchestrator.route_request("GUIDELINE_SEARCH", {"query": rag_query})
                status.update(label="RAG Complete", state="complete")
            
            st.divider()
            st.markdown(f"**Answer:** {result.get('clinical_summary', 'No answer generated.')}")
            st.info(f"**Evidence Grade:** {result.get('evidence_grade', 'N/A')}")
            
            with st.expander("View Raw Response"):
                st.json(result.get('raw_response'))

    # ============ NEW TAB: Prescription Digitalizer ============
    with tab5:
        st.subheader("💊 Clinical Slip Digitalizer")
        st.caption("OCR → Drug Catalog Matching → MedGemma Validation → FHIR Bundle")
        
        rx_text = st.text_area("Prescription Text (or paste OCR output):", 
                               value="Rx: Amox 500mg TID x 7 days. Metformin 850 BD. Lisinopril 10mg OD.",
                               height=100, key="rx_input")
        
        if st.button("Digitize Prescription", key="rx_btn"):
            from app.application.services.central_orchestrator import DhanvantariCentralOrchestrator
            orchestrator = DhanvantariCentralOrchestrator()
            
            with st.status("Running Digitalizer Pipeline...", expanded=True) as status:
                st.write("📝 Step 1: OCR Extraction...")
                time.sleep(0.5)
                st.write("💊 Step 2: Drug Catalog Matching (RxNorm)...")
                time.sleep(0.5)
                st.write("🔬 Step 3: MedGemma Validation...")
                time.sleep(0.5)
                st.write("📦 Step 4: Generating FHIR Bundle...")
                
                result = orchestrator.route_request("PRESCRIPTION_DIGITIZE", {"prescription_text": rx_text})
                status.update(label="Digitization Complete", state="complete")
            
            st.divider()
            raw = result.get('raw_response', {})
            
            st.markdown("### Matched Drugs")
            for drug in raw.get('matched_drugs', []):
                conf_color = "green" if drug.get('match_confidence', 0) > 0.8 else "orange"
                st.markdown(f"""
                <div style="border-left: 5px solid {conf_color}; padding: 10px; background-color: #f1f1f1; margin-bottom: 5px;">
                    <strong>{drug.get('normalized_drug', 'Unknown')}</strong> - {drug.get('dose_raw', '')} {drug.get('frequency_raw', '')}
                    <br><small>RxNorm: {drug.get('rxnorm_code', 'N/A')} | Confidence: {int(drug.get('match_confidence', 0)*100)}%</small>
                </div>
                """, unsafe_allow_html=True)
            
            with st.expander("View FHIR Bundle"):
                st.json(raw.get('fhir_bundle'))

    # ============ NEW TAB: Bedside Monitor ============
    with tab6:
        st.subheader("🩺 Bedside Risk Stratification")
        st.caption("Vitals (LSTM) + Labs (MedGemma) + Triage (NB) → Gemini 3 Alert")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Vitals Input:**")
            hr = st.number_input("Heart Rate (bpm)", value=110, key="v_hr")
            bp_sys = st.number_input("BP Systolic (mmHg)", value=88, key="v_bps")
            bp_dia = st.number_input("BP Diastolic (mmHg)", value=55, key="v_bpd")
            spo2 = st.number_input("SpO2 (%)", value=89, key="v_spo2")
            temp = st.number_input("Temperature (°C)", value=39.2, key="v_temp")
            rr = st.number_input("Respiratory Rate", value=26, key="v_rr")
        
        with col2:
            st.markdown("**Lab Values:**")
            lactate = st.number_input("Lactate (mmol/L)", value=4.5, key="l_lac")
            wbc = st.number_input("WBC (k/μL)", value=15.0, key="l_wbc")
            bands = st.number_input("Bands (%)", value=12, key="l_bands")
            creatinine = st.number_input("Creatinine (mg/dL)", value=2.1, key="l_cr")
        
        chief_complaint = st.text_input("Chief Complaint:", value="Patient with fever, hypotension, and confusion", key="cc")
        
        if st.button("Run Risk Stratification", key="risk_btn"):
            from app.application.services.central_orchestrator import DhanvantariCentralOrchestrator
            orchestrator = DhanvantariCentralOrchestrator()
            
            vitals = {"heart_rate": hr, "bp_systolic": bp_sys, "bp_diastolic": bp_dia, 
                      "spo2": spo2, "temperature": temp, "respiratory_rate": rr}
            labs = {"lactate": lactate, "wbc": wbc, "bands_percent": bands, "creatinine": creatinine}
            
            with st.status("Running Risk Stratification Pipeline...", expanded=True) as status:
                st.write("⚡ Step 1: Triage Gate (NB)...")
                time.sleep(0.5)
                st.write("📊 Step 2: Vitals Anomaly Detection (LSTM)...")
                time.sleep(0.5)
                st.write("🔬 Step 3: MedGemma Lab Analysis...")
                time.sleep(0.5)
                st.write("🧠 Step 4: Gemini 3 Alert Synthesis...")
                
                result = orchestrator.route_request("BEDSIDE_MONITOR", {
                    "vitals": vitals, "labs": labs, "chief_complaint": chief_complaint
                })
                
                if result.get('emergency_status') in ['Critical', 'EMERGENCY', 'CRITICAL']:
                    status.update(label="🚨 CRITICAL ALERT", state="error", expanded=True)
                else:
                    status.update(label="Assessment Complete", state="complete")
            
            st.divider()
            
            # Display Alert
            em_status = result.get('emergency_status', 'Stable')
            if em_status in ['Critical', 'EMERGENCY', 'CRITICAL']:
                st.error(f"🚨 **EMERGENCY STATUS: {em_status}**")
            else:
                st.success(f"✅ Status: {em_status}")
            
            st.markdown(f"**Clinical Summary:** {result.get('clinical_summary', 'N/A')}")
            st.markdown(f"**Thinking Level:** {result.get('thinking_level', 'N/A')}")
            
            st.markdown("### Action Plan")
            for i, step in enumerate(result.get('action_plan', [])):
                st.markdown(f"{i+1}. {step}")
            
            st.info(f"**Evidence Grade:** {result.get('evidence_grade', 'N/A')}")
            
            with st.expander("View Raw Analysis"):
                st.json(result.get('raw_response'))


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
        # Import NER Service locally to avoid scope pollution if not needed elsewhere
        from app.application.services.clinical_ner import ClinicalNERService
        ner_service = ClinicalNERService()
        
        # Mock Context for Admin Demo
        patient_context = {
            "patient_age": 45,
            "conditions": ["Type 2 Diabetes"],
            "medications": ["Lisinopril"]
        }

        with st.spinner("Stage 1: Local MedGemma extracting entities..."):
            entities = ner_service.extract_entities(note)
            st.info(f"Found {len(entities)} clinical entities: {[e['text'] for e in entities]}")
        
        with st.spinner("Stage 2: Gemini 3 Pro reasoning through mappings..."):
            # Call the new reasoning method
            result = st.session_state.ai_service.generate_icd11_with_reasoning(
                entities, note, patient_context
            )
            
            codes = result.get("codes", [])
            reasoning = result.get("reasoning_summary", "No reasoning provided.")
            
            st.markdown(f"**Reasoning Summary:** {reasoning}")
            
            # Display results with audit justifications
            for code in codes:
                confidence = code.get("confidence", 0.0)
                color = "green" if confidence > 0.85 else "orange"
                st.markdown(f"""
                <div style="border-left: 5px solid {color}; padding: 10px; background-color: #f1f1f1; margin-bottom: 5px;">
                    <strong>{code.get('code')}</strong> - {code.get('description')} 
                    <br><small>Confidence: {int(confidence*100)}%</small>
                    <br><em>Justification:</em> {code.get('justification')}
                </div>
                """, unsafe_allow_html=True)
