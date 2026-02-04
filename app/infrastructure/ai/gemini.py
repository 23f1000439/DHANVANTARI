from ...domain.interfaces import AgentInterface
import os
import google.generativeai as genai
from typing import Dict, Any, Optional

# --- CONFIGURATION ---
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("⚠️ WARNING: GEMINI_API_KEY not found in environment variables.")

# Using the deprecated library for now as per legacy code, but isolated here.
try:
    genai.configure(api_key=API_KEY)
except Exception as e:
    print(f"Error configuring Gemini: {e}")

class GeminiAgent(AgentInterface):
    def __init__(self, agent_name: str, model_name: str = "gemini-3.0-flash-preview"):
        self.agent_name = agent_name
        self.model_name = model_name
        self.model = genai.GenerativeModel(model_name)
        
    def generate_response(self, prompt: str, conversation_id: Optional[int] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates content using Google Gemini.
        Appends context if provided.
        """
        try:
            full_prompt = prompt
            if context:
                full_prompt += f"\n\nContext: {context}"
                
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            print(f"❌ Gemini Error in {self.agent_name}: {e}")
            return "I apologize, but I am currently unable to process your request due to a system error."
