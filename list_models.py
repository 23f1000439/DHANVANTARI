import google.generativeai as genai
import os

key = "AIzaSyDLQt-Yx4VK1v2z1qKErNd8iOAdjYQcGdI"
genai.configure(api_key=key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")
