import requests
import os

API_KEY = "AIzaSyBrs5R3fTIeQXmzKce3wyhoxyz0XXjSZ3w"
MODELS = ["gemini-1.5-flash", "gemini-pro", "gemini-1.5-pro-latest", "gemini-1.0-pro"]

def test_model(model_name):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={API_KEY}"
    payload = {
        "contents": [{"parts": [{"text": "Hello, explain this is a test in 5 words."}]}]
    }
    try:
        print(f"Testing {model_name}...")
        resp = requests.post(url, json=payload, timeout=10)
        if resp.status_code == 200:
            print(f"✅ Success! Response: {resp.json()['candidates'][0]['content']['parts'][0]['text']}")
            return True
        else:
            print(f"❌ Failed: {resp.status_code} - {resp.text}")
            return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

print("--- Gemini API Test ---")
for m in MODELS:
    if test_model(m):
        break
