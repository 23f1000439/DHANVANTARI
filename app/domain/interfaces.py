from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class AgentInterface(ABC):
    @abstractmethod
    def generate_response(self, prompt: str, conversation_id: Optional[int] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """Generate response given a prompt and context."""
        pass

class OrchestratorInterface(ABC):
    @abstractmethod
    def route_request(self, user_query: str, user_role: str, conversation_id: int, context: Optional[Dict[str, Any]] = None, device: Optional[Any] = None) -> Dict[str, Any]:
        """Route request to appropriate handler."""
        pass
