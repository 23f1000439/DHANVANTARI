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
