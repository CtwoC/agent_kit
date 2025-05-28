import os
import requests
from dotenv import load_dotenv

load_dotenv()

# 获取环境变量
api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_API_BASE")

print(f"Base URL: {base_url}")
print(f"API Key: {api_key}")

# 构造请求
headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json"
}

data = {
    "model": "claude-3-sonnet-20240229",
    "max_tokens": 1024,
    "messages": [
        {
            "role": "user",
            "content": "Hello, how are you?"
        }
    ]
}

try:
    response = requests.post(f"{base_url}/v1/messages", headers=headers, json=data)
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {str(e)}")
