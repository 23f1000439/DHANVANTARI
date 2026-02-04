from ...domain.interfaces import OrchestratorInterface
from ...domain.models import DeviceCapabilities
from ..agents.admin.orchestrator import AdminOrchestrator
from ..agents.clinician.orchestrator import ClinicianOrchestrator
from ..agents.patient.orchestrator import PatientOrchestrator
from ...infrastructure.ai.gemini import GeminiAgent
from typing import Dict, Any, Optional

class RootOrchestrator(OrchestratorInterface):
    def __init__(self):
        # We use a Gemini Agent for the routing decision logic
        self.router = GeminiAgent("RootRouter", "gemini-3-flash-preview")
        self.admin = AdminOrchestrator()
        self.clinician = ClinicianOrchestrator()
        self.patient = PatientOrchestrator()

    def assess_complexity(self, query: str) -> str:
        simple_keywords = [
            "symptom", "fever", "headache", "cough", "cold", "flu",
            "medication", "dose", "when to take", "side effect",
            "appointment", "schedule"
        ]
        query_lower = query.lower()
        if any(kw in query_lower for kw in simple_keywords):
            return "simple"
        return "complex"

    def route_request(self, user_query: str, user_role: str, conversation_id: int, context: Optional[Dict[str, Any]] = None, device: Optional[DeviceCapabilities] = None) -> Dict[str, Any]:
        
        # --- 1. EDGE SMART ROUTING ---
        if device and device.has_local_model:
            complexity = self.assess_complexity(user_query)
            if complexity == "simple" and device.battery_level > 20:
                print(f"📱 Delegating to Edge AI. Query: '{user_query}'")
                return {
                    "agent": "EdgeAI",
                    "delegated": True,
                    "instruction": "USE_LOCAL_MODEL",
                    "reasoning": "Query is simple and device is capable."
                }
        
        # --- 2. CLOUD ROUTING ---
        prompt = f"""
        Role: System Root Router.
        Task: Route query to the correct Domain Orchestrator.
        User Role: {user_role}
        Query: {user_query}
        
        Domains:
        - PATIENT: Symptoms, wearable data, triage, health records.
        - CLINICIAN: Medical advice, protocols, imaging, prescriptions.
        - ADMIN: Coding, billing, scheduling, governance, compliance.
        
        Output: Domain Name (PATIENT, CLINICIAN, ADMIN, GENERAL).
        """
        
        decision_text = self.router.generate_response(prompt)
        decision = decision_text.strip().upper()
        
        print(f"🌳 Root Routing: {decision}")
        
        if decision == "PATIENT" or (user_role == "patient" and decision != "GENERAL"):
            return self.patient.route_request(user_query, conversation_id, context)
            
        elif decision == "CLINICIAN" or (user_role == "doctor" and decision != "GENERAL"):
             return self.clinician.route_request(user_query, conversation_id, context)
            
        elif decision == "ADMIN" or (user_role == "admin" and decision != "GENERAL"):
             return self.admin.route_request(user_query, conversation_id, context)
            
        else:
            # Fallback to general chat
            return {"agent": "General", "response": self.router.generate_response(user_query, conversation_id, context)}
