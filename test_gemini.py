import requests

# Paste your EXACT API key here (temporarily for testing)
API_KEY = "AIzaSyA6B0Xk60r3tnX_TYm_8di81B5w4klAbxE"  # <-- Paste your key here

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={API_KEY}"

payload = {
    "contents": [{
        "parts": [{"text": "Say hello in one sentence"}]
    }]
}

response = requests.post(url, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
