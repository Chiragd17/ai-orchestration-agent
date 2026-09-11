import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

try:
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents='Say "API connection successful."',
    )
    print("\nSUCCESS!")
    print("LLM Response:", response.text)
except Exception as e:
    print("\nERROR: Failed to connect to Gemini API.")
    print(e)