import requests
import time

url = "http://localhost:8000/ask"
prompts = [
    "Hi there!",                          # Simple
    "What is 2+2?",                        # Simple
    "Summarize the history of the internet",# Medium
    "Write a complex FastAPI app with auth",# Hard
    "Hi there!"                           # This should hit the CACHE!
]

for p in prompts:
    print(f"Sending: {p}")
    response = requests.post(url, json={"prompt": p})
    data = response.json()
    print(f"Model: {data.get('model_used')} | Saved: {data.get('dollars_saved')}")
    print("-" * 30)
    time.sleep(1)