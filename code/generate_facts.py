import os
import json
import pandas as pd
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv(r"c:\Users\chira\Desktop\orchestrate-agent\code\.env")

class MessageFact(BaseModel):
    message_id: str
    effect: str # 'confirm', 'amend', 'cancel', 'delay', 'irrelevant'
    related_event_id: Optional[str] = None
    new_amount: Optional[float] = None
    new_date: Optional[str] = None

class MessageBatch(BaseModel):
    facts: List[MessageFact]

def run():
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    df = pd.read_csv(r"c:\Users\chira\Desktop\orchestrate-agent\dataset\messages.csv")
    
    message_facts = {}
    chunk_size = 30
    
    for i in range(0, len(df), chunk_size):
        chunk = df.iloc[i:i+chunk_size]
        prompt = "Parse the following messages into the structured format. Extract any explicit new numeric amounts (no currency) and new dates (YYYY-MM-DD).\n\n"
        for _, row in chunk.iterrows():
            rel = row['related_event_id'] if pd.notna(row['related_event_id']) else "None"
            prompt += f"ID: {row['message_id']} | Related: {rel} | Text: {row['message_text']}\n"
            
        print(f"Processing chunk {i}...")
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
                message_facts[f['message_id']] = {
                    "effect": f['effect'],
                    "related_event_id": f['related_event_id'],
                    "new_amount": f['new_amount'],
                    "new_date": f['new_date']
                }
        except Exception as e:
            print(f"Failed chunk {i}: {e}")

    # Hardcoded image facts from Phase 0
    image_facts = {
      "event_253": 4365000,
      "event_1442": 200000.00,
      "event_1545": 41272.00,
      "event_1700": 2854.00,
      "event_1786": 704.05,
      "event_3051": 1995.00,
      "event_5170": 723.00,
      "event_6033": 79679.26,
      "event_6859": 3650.00,
      "event_7307": 33.50,
      "event_7941": 2298,
      "event_9421": 4543.00
    }

    final_out = {
        "image_facts": image_facts,
        "message_facts": message_facts
    }

    with open(r"c:\Users\chira\Desktop\orchestrate-agent\code\notes\resolved_facts.json", "w") as f:
        json.dump(final_out, f, indent=2)
        
    print("Facts saved to notes/resolved_facts.json")

if __name__ == "__main__":
    run()
