"""
MedGemma Local Inference Service
Runs medgemma-1.5-4b-it GGUF model locally using llama-cpp-python
"""
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

# Model configuration
MODEL_PATH = Path(__file__).parent / "models" / "medgemma" / "medgemma-1.5-4b-it.Q4_K_M.gguf"


class MedGemmaLocalService:
    """
    Local MedGemma inference service using llama.cpp.
    Provides medical AI capabilities without cloud API calls.
    """
    
    def __init__(self, model_path: Optional[str] = None, n_ctx: int = 4096, n_gpu_layers: int = 0):
        """
        Initialize MedGemma local inference.
        
        Args:
            model_path: Path to GGUF model file
            n_ctx: Context window size
            n_gpu_layers: Number of layers to offload to GPU (0 for CPU only)
        """
        self.model_path = model_path or str(MODEL_PATH)
        self.n_ctx = n_ctx
        self.n_gpu_layers = n_gpu_layers
        self.llm = None
        
        print(f"[MedGemma Local] Initializing with model: {self.model_path}")
    
    def load_model(self):
        """Load the GGUF model into memory."""
        try:
            from llama_cpp import Llama
            
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model not found at {self.model_path}")
            
            print("[MedGemma Local] Loading model... (this may take a moment)")
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_gpu_layers=self.n_gpu_layers,
                verbose=False
            )
            print("[MedGemma Local] Model loaded successfully!")
            return True
            
        except ImportError:
            print("[MedGemma Local] Error: llama-cpp-python not installed")
            print("Install with: pip install llama-cpp-python")
            return False
        except Exception as e:
            print(f"[MedGemma Local] Error loading model: {e}")
            return False
    
    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.3,
                 stop: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generate a response from MedGemma.
        
        Args:
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (lower = more deterministic)
            stop: Stop sequences
        
        Returns:
            Dict with generated text and metadata
        """
        if self.llm is None:
            if not self.load_model():
                return {"error": "Model not loaded", "text": ""}
        
        try:
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or ["</s>", "\n\n\n"],
                echo=False
            )
            
            generated_text = response["choices"][0]["text"].strip()
            
            return {
                "text": generated_text,
                "tokens_used": response.get("usage", {}).get("total_tokens", 0),
                "model": "medgemma-1.5-4b-it-Q4_K_M",
                "status": "success"
            }
            
        except Exception as e:
            return {"error": str(e), "text": "", "status": "error"}
    
    def analyze_clinical_text(self, text: str) -> Dict[str, Any]:
        """
        Analyze clinical text for medical insights.
        """
        prompt = f"""<start_of_turn>user
You are MedGemma, a medical AI assistant. Analyze the following clinical text and provide key findings:

{text}

Provide:
1. Key clinical findings
2. Possible diagnoses to consider
3. Recommended next steps
<end_of_turn>
<start_of_turn>model
"""
        return self.generate(prompt, max_tokens=1024)
    
    def analyze_symptoms(self, symptoms: List[str], patient_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze patient symptoms and provide differential diagnosis.
        """
        patient_context = ""
        if patient_info:
            patient_context = f"Patient: {patient_info.get('age', 'Unknown')} year old {patient_info.get('gender', 'patient')}"
        
        symptoms_text = ", ".join(symptoms)
        
        prompt = f"""<start_of_turn>user
You are MedGemma, a medical AI assistant. {patient_context}

Presenting symptoms: {symptoms_text}

Provide:
1. Most likely differential diagnoses (ranked by probability)
2. Red flags to watch for
3. Suggested workup
<end_of_turn>
<start_of_turn>model
"""
        return self.generate(prompt, max_tokens=1024)
    
    def validate_prescription(self, medications: List[Dict]) -> Dict[str, Any]:
        """
        Validate prescription for drug interactions and dosing.
        """
        meds_text = "\n".join([f"- {m.get('drug', 'Unknown')}: {m.get('dose', 'Unknown')}" 
                               for m in medications])
        
        prompt = f"""<start_of_turn>user
You are MedGemma, a medical AI assistant. Review this prescription for safety:

{meds_text}

Check for:
1. Drug-drug interactions
2. Dosing appropriateness
3. Contraindications to consider
4. Overall safety assessment
<end_of_turn>
<start_of_turn>model
"""
        return self.generate(prompt, max_tokens=1024)
    
    def interpret_lab_results(self, labs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret laboratory results.
        """
        labs_text = "\n".join([f"- {k}: {v}" for k, v in labs.items()])
        
        prompt = f"""<start_of_turn>user
You are MedGemma, a medical AI assistant. Interpret these lab results:

{labs_text}

Provide:
1. Abnormal findings
2. Clinical significance
3. Suggested follow-up tests
<end_of_turn>
<start_of_turn>model
"""
        return self.generate(prompt, max_tokens=1024)
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self.llm is not None
    
    def unload(self):
        """Unload model from memory."""
        if self.llm is not None:
            del self.llm
            self.llm = None
            print("[MedGemma Local] Model unloaded")


# Singleton instance for easy access
_instance: Optional[MedGemmaLocalService] = None

def get_medgemma_service() -> MedGemmaLocalService:
    """Get or create MedGemma service instance."""
    global _instance
    if _instance is None:
        _instance = MedGemmaLocalService()
    return _instance


if __name__ == "__main__":
    # Test the service
    print("Testing MedGemma Local Service...")
    
    service = MedGemmaLocalService()
    
    # Check if model exists
    if os.path.exists(service.model_path):
        print(f"✅ Model found at: {service.model_path}")
        
        # Test loading (optional - takes time)
        # response = service.analyze_symptoms(["chest pain", "shortness of breath"])
        # print(response)
    else:
        print(f"❌ Model not found at: {service.model_path}")
        print("Download using huggingface_hub or manually place the model file.")
