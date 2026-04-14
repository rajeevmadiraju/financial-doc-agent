import httpx
import os
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("QDRANT_URL")
api_key = os.getenv("QDRANT_API_KEY")

response = httpx.get(
    f"{url}/collections",
    headers={"api-key": api_key}
)
print(f"Qdrant ping: {response.status_code}")