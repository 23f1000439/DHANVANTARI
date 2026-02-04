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
