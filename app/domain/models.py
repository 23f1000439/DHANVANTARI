from pydantic import BaseModel
from typing import Dict, Any, Optional

class DeviceCapabilities(BaseModel):
    has_local_model: bool = False
    battery_level: int = 100
    is_charging: bool = False
    network_quality: str = "good"

class AgentRequest(BaseModel):
    query: str
    role: str # Patient, Doctor, Admin
    conversation_id: Optional[int] = None
    context: Optional[Dict[str, Any]] = {}
    device: Optional[DeviceCapabilities] = None

class LoginRequest(BaseModel):
    role: str
