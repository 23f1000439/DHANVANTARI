import google.generativeai as genai
import os
import json
from datetime import datetime
import time
# Load .env file manually to avoid dependency on python-dotenv for this demo
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value

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

    def get_enhanced_denial_analysis(self, claim_data, ml_results, clinical_notes):
        """
        Utilizes Gemini 3.0 Thinking to synthesize ML risk factors 
        with clinical reality.
        """
        prompt = f"""
        ROLE: Senior Clinical Auditor & RCM Specialist.
        
        ML MODEL OUTPUT:
        - Denial Probability: {ml_results.get('probability')}
        - Top Risk Factors (SHAP): {ml_results.get('risk_factors')}
        
        CLINICAL CONTEXT:
        - Encounter Notes: {clinical_notes}
        - Billed Codes: {claim_data.get('codes')}
        - Total Amount: {claim_data.get('total_amount')}
        
        TASK:
        Perform a 'Thinking' analysis. Use your reasoning capability to:
        1. Cross-reference the SHAP risk factors against the actual clinical narrative.
        2. Identify if the 'Denial Risk' is a documentation error (fixable) or a medical necessity issue (likely denial).
        3. Check for specific NHCX (National Health Claims Exchange) compliance issues.
        4. Provide a 'Corrective Action Plan' for the billing staff.
        
        OUTPUT FORMAT (JSON ONLY):
        {{
          "clinical_validation": "Does the note support the billed code?",
          "reasoning_summary": "Short explanation of why the ML model is correct/incorrect",
          "remediation_steps": ["Step 1", "Step 2"],
          "denial_prevention_score": 0.0 to 1.0 (confidence score)
        }}
        """
        
        try:
            # Utilizing the 'gemini-3-flash-preview' for thinking/reasoning
            response = self.flash_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2 # Low temperature for precision
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Enhanced Analysis Error: {e}")
            return {
                "clinical_validation": "Error performing analysis",
                "reasoning_summary": str(e),
                "remediation_steps": ["Manual Review Required"],
                "denial_prevention_score": 0.0
            }

    def generate_icd11_with_reasoning(self, entities: list, clinical_note: str, encounter_context: dict) -> dict:
        """
        Uses Gemini 3 Pro 'Thinking' mode to:
        1. Map BERT entities to ICD-11 codes
        2. Resolve ambiguities
        3. Apply coding hierarchy rules
        4. Generate audit justification
        """
        prompt = f"""
        ROLE: Senior Medical Coding Auditor (AAPC Certified).

        EXTRACTED CLINICAL ENTITIES (from BERT NER):
        {json.dumps(entities, indent=2)}

        FULL CLINICAL NOTE:
        {clinical_note}

        PATIENT CONTEXT:
        - Age: {encounter_context.get('patient_age')}
        - Existing Conditions: {encounter_context.get('conditions')}
        - Current Medications: {encounter_context.get('medications')}

        ICD-11 CODING TASK:
        1. For each extracted DIAGNOSIS entity, determine the most specific ICD-11 code
        2. Use the ICD-11 hierarchy to verify parent-child relationships
        3. Check for contradictions
        4. Provide justification suitable for audit defense

        COMPLIANCE RULES:
        - Must follow NHCX (National Health Claims Exchange) standards
        - Confidence threshold: 0.85 minimum for auto-coding

        OUTPUT FORMAT (Strict JSON):
        {{
          "codes": [
            {{
              "code": "ICD-11 Code",
              "description": "Description",
              "confidence": 0.0-1.0,
              "justification": "Medical reasoning",
              "supporting_entities": ["list of BERT entities that support this code"],
              "requires_human_review": boolean
            }}
          ],
          "reasoning_summary": "Explanation of coding logic",
          "audit_trail": "Trace for documentation"
        }}
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
            print(f"ICD-11 Coding Error: {e}")
            return {"codes": [], "reasoning_summary": f"Error: {e}", "audit_trail": ""}

    def validate_local_entities(self, entities: list, clinical_note: str) -> dict:
        """
        Uses Gemini 3 Thinking to validate and enhance Local/MedGemma extractions.
        """
        prompt = f"""
        ROLE: Clinical NLP Validator.
        
        LOCALLY EXTRACTED ENTITIES (MedGemma):
        {json.dumps(entities, indent=2)}
        
        ORIGINAL CLINICAL NOTE:
        {clinical_note}
        
        TASK:
        1. Verify if the local model missed any critical qualifiers (acute/chronic, Type 1/Type 2)
        2. Identify ambiguous entities that need disambiguation
        3. Suggest additional entities the local model should have caught
        
        OUTPUT (JSON):
        {{
          "validated_entities": [enhanced entity list],
          "corrections": ["List of local model errors found"],
          "confidence_adjustments": {{"entity_index": new_confidence}}
        }}
        """
        
        try:
            response = self.flash_model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            return json.loads(response.text)
        except Exception as e:
             return {"validated_entities": entities, "corrections": [f"Error: {e}"]}

    def translate_shap_to_actionable_steps(self, shap_values: dict, claim_data: dict) -> str:
        """
        Gemini 3 converts ML outputs into human-readable remediation plans.
        """
        prompt = f"""
        ROLE: Billing Manager Advisor.
        
        MACHINE LEARNING ANALYSIS:
        The XGBoost model flagged this claim.
        
        TOP RISK FACTORS (SHAP Values):
        {json.dumps(shap_values)}
        
        CLAIM DETAILS:
        {json.dumps(claim_data)}
        
        TASK FOR BILLING STAFF:
        Translate these technical risk factors into a 3-step action plan 
        that a non-technical billing clerk can execute.
        
        OUTPUT FORMAT (JSON):
        {{
          "plain_language_summary": "The claim is at risk because...",
          "action_steps": [
            "Step 1: ...",
            "Step 2: ...",
            "Step 3: ..."
          ],
          "estimated_risk_reduction": "Following these steps should reduce denial risk..."
        }}
        """
        
        try:
           response = self.flash_model.generate_content(
               prompt,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json"
                )
           )
           return response.text
        except Exception as e:
            return json.dumps({"plain_language_summary": f"Error translating SHAP: {e}", "action_steps": []})

    def generate_preliminary_report(self, image_data, triage_flag, clinical_context):
        """
        Stage 2: Gemini 3 Pro generates a detailed radiological report.
        """
        prompt = f"""
        ROLE: Virtual Radiologist (Preliminary Assistant).
        
        LOCAL TRIAGE FLAG: {triage_flag}
        CLINICAL CONTEXT: {clinical_context.get('notes', 'N/A')}
        PAST HISTORY: {clinical_context.get('history', 'N/A')}
        
        TASK:
        1. Analyze the attached image (or description if image upload simulated) in the context of the URGENT flag from the edge-AI.
        2. Use your 'Thinking' mode to correlate visual findings with the patient's clinical symptoms (e.g., if dyspnea is mentioned, look specifically at the lung fields).
        3. Draft a structured preliminary report.
        
        REPORT STRUCTURE (Strict JSON):
        {{
          "priority": "STAT / Urgent / Routine",
          "findings": ["Point 1", "Point 2"],
          "impression": "Primary diagnosis or suspicion",
          "clinical_correlation": "How findings match/contradict patient notes",
          "recommendations": ["Immediate next steps"],
          "disclaimer": "AI-generated preliminary report. Requires human radiologist sign-off."
        }}
        """
        
        try:
            # Check if image_data is a PIL Image or similar supported type
            content = [prompt]
            if image_data:
                content.append(image_data)
                
            response = self.pro_model.generate_content(
                content,
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2
                )
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"Reporting Error: {e}")
            return {
                "priority": "Urgent (Fallback)",
                "findings": ["Error generating report"],
                "impression": "Manual review required",
                "disclaimer": str(e)
            }

if __name__ == "__main__":
    # Simple test
    print("AI Service initialized.")
