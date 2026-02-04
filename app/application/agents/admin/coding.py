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
