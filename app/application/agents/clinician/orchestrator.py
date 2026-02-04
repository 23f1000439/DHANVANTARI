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
