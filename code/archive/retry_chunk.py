import os
import json
import pandas as pd
from google import genai
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv(r"c:\Users\chira\Desktop\orchestrate-agent\code\.env")

class MessageFact(BaseModel):
    message_id: str
    effect: str
    related_event_id: Optional[str] = None
    new_amount: Optional[float] = None
    new_date: Optional[str] = None

class MessageBatch(BaseModel):
    facts: List[MessageFact]

def run():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    df = pd.read_csv(r"c:\Users\chira\Desktop\orchestrate-agent\dataset\messages.csv")
    
    with open(r"c:\Users\chira\Desktop\orchestrate-agent\code\notes\resolved_facts.json", "r") as f:
        existing = json.load(f)
        
    chunk = df.iloc[90:120]
    prompt = "Parse the following messages into the structured format. Extract any explicit new numeric amounts (no currency) and new dates (YYYY-MM-DD).\n\n"
    for _, row in chunk.iterrows():
        rel = row['related_event_id'] if pd.notna(row['related_event_id']) else "None"
        prompt += f"ID: {row['message_id']} | Related: {rel} | Text: {row['message_text']}\n"
        
    print(f"Processing missing chunk 90...")
    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[prompt],
            config=genai.types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=MessageBatch,
            ),
        )
        data = json.loads(response.text)
        for f in data.get('facts', []):
            existing['message_facts'][f['message_id']] = {
                "effect": f['effect'],
                "related_event_id": f['related_event_id'],
                "new_amount": f['new_amount'],
                "new_date": f['new_date']
            }
            
        with open(r"c:\Users\chira\Desktop\orchestrate-agent\code\notes\resolved_facts.json", "w") as f:
            json.dump(existing, f, indent=2)
        print("Missing chunk appended successfully.")
    except Exception as e:
        print(f"Failed chunk 90 again: {e}")

if __name__ == "__main__":
    run()
