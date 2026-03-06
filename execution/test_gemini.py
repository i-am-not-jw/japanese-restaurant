import requests
import os

def load_env():
    env_paths = [
        "/tmp/japanese_restaurant_data/.env",
        "/Users/jw/Desktop/japanese-restaurant/.env"
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        os.environ[k] = v

load_env()
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
print(f"Testing key: {GEMINI_KEY[:10]}...")

prompt = "Hello, can you hear me? Answer in Korean."
models = ["gemini-flash-latest", "gemini-2.0-flash-001", "gemini-2.0-flash-lite", "gemini-1.5-flash-latest", "gemini-1.5-pro-latest"]
for model in models:
    print(f"\n--- Testing model: {model} ---")
    url_pro = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}

    try:
        resp = requests.post(url_pro, json=payload, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Response: {resp.json()['candidates'][0]['content']['parts'][0]['text']}")
            break
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Failed: {e}")
