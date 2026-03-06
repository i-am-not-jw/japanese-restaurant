import requests
import os
import json

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
print(f"Listing models with key: {GEMINI_KEY[:10]}...")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_KEY}"
resp = requests.get(url)
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    models = resp.json().get("models", [])
    for m in models:
        print(f" - {m['name']}")
else:
    print(f"Error: {resp.text}")
