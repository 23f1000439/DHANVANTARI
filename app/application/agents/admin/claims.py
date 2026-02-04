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
