from backend.inference.engine import LocalInferenceEngine
import time

def test_local_inference():
    print("🚀 Initializing Local Engine...")
    start_load = time.time()
    engine = LocalInferenceEngine()
    print(f"⏱️ Load Time: {time.time() - start_load:.2f}s")
    
    prompt = "Listing symptoms of diabetes:"
    print(f"\n📝 Prompt: {prompt}")
    
    start_gen = time.time()
    response = engine.generate(prompt, max_tokens=128)
    print(f"⏱️ Generation Time: {time.time() - start_gen:.2f}s")
    
    print(f"\n🤖 Response:\n{response}")
    
    if "Error" not in response:
        print("\n✅ Local Inference Verification PASSED")
    else:
        print("\n❌ Local Inference Verification FAILED")

if __name__ == "__main__":
    test_local_inference()
