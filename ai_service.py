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
