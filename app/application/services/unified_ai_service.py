"""
Unified AI Service for Dhanvantr.ai
Combines Gemini 3 Pro (Cloud) + MedGemma 4B (Local) into single service.
"""
import os
import sys
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Add project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))


class AIModel(Enum):
    """Available AI models."""
    GEMINI_3_PRO = "gemini-3-pro"
    GEMINI_3_FLASH = "gemini-3-flash"
    MEDGEMMA_LOCAL = "medgemma-local"
    AUTO = "auto"  # Automatically choose based on task


class ThinkingLevel(Enum):
    """Gemini 3 thinking depth levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class UnifiedAIService:
    """
    Unified AI Service that orchestrates between:
    - Gemini 3 Pro/Flash (Cloud API)
    - MedGemma 4B (Local GGUF)
    
    Automatically selects appropriate model based on task complexity.
    """
    
    def __init__(self, use_local_medgemma: bool = True):
        """
        Initialize unified AI service.
        
        Args:
            use_local_medgemma: Whether to enable local MedGemma inference
        """
        self.use_local_medgemma = use_local_medgemma
        self.gemini_available = False
        self.medgemma_available = False
        
        self._init_gemini()
        if use_local_medgemma:
            self._init_medgemma()
        
        print(f"[UnifiedAI] Gemini: {'✅' if self.gemini_available else '❌'} | MedGemma: {'✅' if self.medgemma_available else '❌'}")
    
    def _init_gemini(self):
        """Initialize Gemini 3 models."""
        try:
            import google.generativeai as genai
            
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                # Try loading from .env
                env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), ".env")
                if os.path.exists(env_path):
                    with open(env_path) as f:
                        for line in f:
                            if line.startswith("GEMINI_API_KEY"):
                                api_key = line.strip().split("=", 1)[1].strip('"\'')
                                break
            
            if api_key:
                genai.configure(api_key=api_key)
                self.pro_model = genai.GenerativeModel('gemini-2.5-pro-preview-06-05')
                self.flash_model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
                
                # Generation configs
                self.analytical_config = genai.GenerationConfig(
                    temperature=0.2,
                    top_p=0.95,
                    max_output_tokens=4096
                )
                self.creative_config = genai.GenerationConfig(
                    temperature=0.7,
                    top_p=0.9,
                    max_output_tokens=2048
                )
                
                self.gemini_available = True
                print("[UnifiedAI] Gemini 3 initialized successfully")
            else:
                print("[UnifiedAI] Warning: GEMINI_API_KEY not found")
                
        except Exception as e:
            print(f"[UnifiedAI] Gemini init error: {e}")
    
    def _init_medgemma(self):
        """Initialize local MedGemma model."""
        try:
            from medgemma_local import MedGemmaLocalService
            
            self.medgemma_service = MedGemmaLocalService()
            model_path = self.medgemma_service.model_path
            
            if os.path.exists(model_path):
                self.medgemma_available = True
                print("[UnifiedAI] MedGemma local model available")
            else:
                print(f"[UnifiedAI] MedGemma model not found at {model_path}")
                
        except Exception as e:
            print(f"[UnifiedAI] MedGemma init error: {e}")
            self.medgemma_service = None

    # ============================================================
    # Model Selection Logic
    # ============================================================
    def _select_model(self, task_type: str, urgency: str = "routine") -> AIModel:
        """
        Automatically select best model for the task.
        
        Decision logic:
        - Clinical validation, drug checks → MedGemma (privacy + specialized)
        - Complex reasoning, coding → Gemini Pro
        - Quick triage, simple tasks → Gemini Flash / MedGemma
        - Critical/STAT → Gemini Pro (faster API response)
        """
        # Critical cases use cloud for reliability
        if urgency.upper() in ["STAT", "CRITICAL", "EMERGENCY"]:
            return AIModel.GEMINI_3_PRO
        
        # Clinical validation tasks prefer local MedGemma
        local_preferred_tasks = [
            "drug_interaction", "dose_validation", "symptom_analysis",
            "lab_interpretation", "clinical_entity_extraction"
        ]
        
        if task_type in local_preferred_tasks and self.medgemma_available:
            return AIModel.MEDGEMMA_LOCAL
        
        # Complex reasoning uses Pro
        complex_tasks = [
            "differential_diagnosis", "treatment_planning", "report_synthesis",
            "appeal_drafting", "icd_coding"
        ]
        
        if task_type in complex_tasks:
            return AIModel.GEMINI_3_PRO
        
        # Default to Flash for quick tasks
        return AIModel.GEMINI_3_FLASH

    # ============================================================
    # Core Generation Methods
    # ============================================================
    def generate(self, prompt: str, model: AIModel = AIModel.AUTO,
                 task_type: str = "general", urgency: str = "routine",
                 max_tokens: int = 1024, temperature: float = 0.3) -> Dict[str, Any]:
        """
        Generate response using appropriate model.
        
        Returns:
            Dict with 'text', 'model_used', 'tokens', 'latency_ms'
        """
        start_time = datetime.now()
        
        # Auto-select model if needed
        if model == AIModel.AUTO:
            model = self._select_model(task_type, urgency)
        
        result = {
            "text": "",
            "model_used": model.value,
            "task_type": task_type,
            "error": None
        }
        
        try:
            if model == AIModel.MEDGEMMA_LOCAL and self.medgemma_available:
                response = self.medgemma_service.generate(prompt, max_tokens, temperature)
                result["text"] = response.get("text", "")
                result["error"] = response.get("error")
                
            elif model in [AIModel.GEMINI_3_PRO, AIModel.GEMINI_3_FLASH] and self.gemini_available:
                gen_model = self.pro_model if model == AIModel.GEMINI_3_PRO else self.flash_model
                config = self.analytical_config if temperature < 0.5 else self.creative_config
                
                response = gen_model.generate_content(prompt, generation_config=config)
                result["text"] = response.text
                
            else:
                result["error"] = f"Model {model.value} not available"
                
        except Exception as e:
            result["error"] = str(e)
        
        # Calculate latency
        result["latency_ms"] = (datetime.now() - start_time).total_seconds() * 1000
        
        return result

    # ============================================================
    # Specialized Clinical Methods
    # ============================================================
    def analyze_symptoms(self, symptoms: List[str], patient_info: Dict = None,
                         use_local: bool = True) -> Dict[str, Any]:
        """Analyze symptoms and provide differential diagnosis."""
        model = AIModel.MEDGEMMA_LOCAL if use_local and self.medgemma_available else AIModel.GEMINI_3_PRO
        
        patient_context = ""
        if patient_info:
            patient_context = f"Patient: {patient_info.get('age', 'Unknown')}yo {patient_info.get('gender', '')}"
        
        prompt = f"""You are a clinical AI assistant. {patient_context}

Presenting symptoms: {', '.join(symptoms)}

Provide:
1. Top 3 differential diagnoses with reasoning
2. Red flags to watch for
3. Recommended workup
4. Urgency level (STAT/Urgent/Routine)

Output as JSON."""

        return self.generate(prompt, model, task_type="differential_diagnosis")
    
    def validate_prescription(self, medications: List[Dict]) -> Dict[str, Any]:
        """Validate prescription for interactions and dosing."""
        meds_text = "\n".join([f"- {m.get('drug')}: {m.get('dose')}, {m.get('frequency')}" 
                               for m in medications])
        
        prompt = f"""Review this prescription for safety:

{meds_text}

Check for:
1. Drug-drug interactions (severity: major/moderate/minor)
2. Dosing appropriateness
3. Contraindications
4. Overall safety: PASS/REVIEW_REQUIRED/REJECT

Output as JSON."""

        return self.generate(prompt, AIModel.MEDGEMMA_LOCAL if self.medgemma_available else AIModel.GEMINI_3_PRO,
                           task_type="drug_interaction", temperature=0.1)
    
    def interpret_labs(self, lab_results: Dict) -> Dict[str, Any]:
        """Interpret laboratory results."""
        labs_text = "\n".join([f"- {k}: {v}" for k, v in lab_results.items()])
        
        prompt = f"""Interpret these lab results:

{labs_text}

Provide:
1. Abnormal findings with clinical significance
2. Patterns suggesting specific conditions
3. Recommended follow-up tests
4. Overall assessment

Output as JSON."""

        return self.generate(prompt, AIModel.MEDGEMMA_LOCAL if self.medgemma_available else AIModel.GEMINI_3_PRO,
                           task_type="lab_interpretation", temperature=0.2)
    
    def generate_clinical_report(self, findings: Dict, report_type: str = "radiology") -> Dict[str, Any]:
        """Generate structured clinical report."""
        prompt = f"""Generate a structured {report_type} report.

Findings:
{json.dumps(findings, indent=2)}

Format:
1. TECHNIQUE
2. COMPARISON
3. FINDINGS (by region)
4. IMPRESSION (numbered, critical first)
5. RECOMMENDATIONS

Output as structured JSON."""

        return self.generate(prompt, AIModel.GEMINI_3_PRO, task_type="report_synthesis")
    
    def generate_icd_codes(self, clinical_text: str, entities: List[Dict] = None) -> Dict[str, Any]:
        """Generate ICD-11 codes from clinical text."""
        entities_text = ""
        if entities:
            entities_text = f"\nExtracted entities: {json.dumps(entities)}"
        
        prompt = f"""Map this clinical text to ICD-11 codes:

Clinical Text:
{clinical_text}
{entities_text}

For each diagnosis:
1. Primary ICD-11 code
2. Secondary codes if applicable
3. Confidence level
4. Coding justification

Output as JSON array."""

        return self.generate(prompt, AIModel.GEMINI_3_PRO, task_type="icd_coding", temperature=0.1)
    
    def draft_appeal_letter(self, denial_info: Dict, clinical_evidence: str) -> Dict[str, Any]:
        """Draft insurance appeal letter."""
        prompt = f"""Draft a formal insurance appeal letter.

Denial Information:
{json.dumps(denial_info, indent=2)}

Clinical Evidence:
{clinical_evidence}

Include:
1. Reference to specific policy language
2. Citation of clinical evidence proving medical necessity
3. Request for reconsideration
4. Professional, formal tone

Output the appeal letter text."""

        return self.generate(prompt, AIModel.GEMINI_3_PRO, task_type="appeal_drafting", temperature=0.3)
    
    def triage_text(self, text: str) -> Dict[str, Any]:
        """Quick triage classification of clinical text."""
        prompt = f"""Classify this clinical text for triage:

"{text}"

Output JSON:
{{
  "priority": "STAT|URGENT|ROUTINE",
  "esi_level": 1-5,
  "keywords": ["matched keywords"],
  "reasoning": "brief explanation"
}}"""

        return self.generate(prompt, AIModel.GEMINI_3_FLASH, task_type="triage", temperature=0.1)

    # ============================================================
    # Status Methods
    # ============================================================
    def get_status(self) -> Dict[str, Any]:
        """Get service status."""
        return {
            "gemini_available": self.gemini_available,
            "medgemma_available": self.medgemma_available,
            "medgemma_loaded": self.medgemma_service.is_loaded() if self.medgemma_available else False,
            "models": {
                "gemini_pro": "gemini-2.5-pro-preview-06-05" if self.gemini_available else None,
                "gemini_flash": "gemini-2.5-flash-preview-05-20" if self.gemini_available else None,
                "medgemma": "medgemma-1.5-4b-it-Q4_K_M" if self.medgemma_available else None
            }
        }
    
    def load_medgemma(self) -> bool:
        """Explicitly load MedGemma into memory."""
        if self.medgemma_available and not self.medgemma_service.is_loaded():
            return self.medgemma_service.load_model()
        return self.medgemma_service.is_loaded() if self.medgemma_available else False
    
    def unload_medgemma(self):
        """Unload MedGemma from memory."""
        if self.medgemma_available:
            self.medgemma_service.unload()


# Singleton instance
_unified_ai_service: Optional[UnifiedAIService] = None

def get_unified_ai_service() -> UnifiedAIService:
    """Get or create unified AI service instance."""
    global _unified_ai_service
    if _unified_ai_service is None:
        _unified_ai_service = UnifiedAIService()
    return _unified_ai_service


if __name__ == "__main__":
    service = UnifiedAIService()
    print(service.get_status())
