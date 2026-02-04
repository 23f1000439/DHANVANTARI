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
