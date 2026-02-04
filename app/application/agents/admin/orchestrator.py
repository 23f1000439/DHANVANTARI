from ..base_orchestrator import BaseDomainOrchestrator
from ....infrastructure.ai.gemini import GeminiAgent

class AdminOrchestrator(BaseDomainOrchestrator):
    def __init__(self):
        super().__init__("AdminOrchestrator")
        self.claims_agent = GeminiAgent("ClaimsAgent")
        self.billing_agent = GeminiAgent("BillingAgent") # Legacy name mapping
        self.scheduling_agent = GeminiAgent("SchedulingAgent")

    def route_request(self, user_query, conversation_id, context=None):
        # Simplified routing for now, can be expanded like Root
        if "claim" in user_query.lower():
            return {"agent": "ClaimsAgent", "response": self.claims_agent.generate_response(user_query, conversation_id, context)}
        elif "schedule" in user_query.lower() or "appointment" in user_query.lower():
            return {"agent": "SchedulingAgent", "response": self.scheduling_agent.generate_response(user_query, conversation_id, context)}
        else:
            return {"agent": "AdminGeneral", "response": self.agent.generate_response(user_query, conversation_id, context)}
