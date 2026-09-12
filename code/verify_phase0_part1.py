import os
import glob
import pandas as pd
# pyrefly: ignore [missing-import]
from google import genai
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv(r"c:\Users\chira\Desktop\orchestrate-agent\code\.env")

DATA_DIR = r"c:\Users\chira\Desktop\orchestrate-agent\dataset"
OUT_FILE = r"c:\Users\chira\Desktop\orchestrate-agent\code\notes\part1_report.md"

def run_checks():
    out = []
    
    # 1. Schema Check
    out.append("## 1. Schema Check\n")
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    data = {}
    for f in sorted(csv_files):
        name = os.path.basename(f)
        df = pd.read_csv(f)
        data[name] = df
        out.append(f"### {name}")
        out.append(f"- **Shape**: {df.shape}")
        out.append("- **Columns, Dtypes, and Nulls**:\n")
        out.append("| Column | Dtype | Null Count |")
        out.append("|---|---|---|")
        for col in df.columns:
            out.append(f"| {col} | {df[col].dtype} | {df[col].isnull().sum()} |")
        out.append("\n")

    events = data.get("financial_events.csv")
    images = data.get("images.csv")
    messages = data.get("messages.csv")

    # 2. Blank Amount Resolution
    out.append("## 2. Blank-Amount Resolution\n")
    if events is not None and images is not None:
        blank_events = events[events['amount'].isna()]
        if len(blank_events) == 0:
            out.append("No blank amounts found.\n")
        else:
            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            for _, row in blank_events.iterrows():
                eid = row['event_id']
                # Trace to image
                img_row = images[images['related_event_id'] == eid]
                if img_row.empty:
                    out.append(f"- **{eid}**: ❌ Could not be traced to an image in images.csv\n")
                    continue
                img_id = img_row.iloc[0]['image_id']
                img_path = os.path.join(DATA_DIR, "media", "images", f"{img_id}.png")
                if not os.path.exists(img_path):
                    out.append(f"- **{eid}**: ❌ Traced to {img_id}.png, but file does not exist in media/images/.\n")
                    continue
                
                try:
                    # Upload and extract
                    upload = client.files.upload(file=img_path)
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=['Extract the final total amount from this image. Return ONLY the numeric value (no currency symbols or commas).', upload]
                    )
                    amount_val = response.text.strip()
                    out.append(f"- **{eid}**: ✅ Traced to `{img_id}.png`. Extracted Amount: **{amount_val}**")
                except Exception as e:
                    out.append(f"- **{eid}**: ❌ Traced to `{img_id}.png`, but OCR failed: {str(e)}")
    out.append("\n")

    # 3. Linked-event chains
    out.append("## 3. Linked-Event Chains\n")
    if events is not None:
        linked = events[events['linked_event_id'].notna()]
        for _, row in linked.iterrows():
            parent_id = row['linked_event_id']
            parent = events[events['event_id'] == parent_id]
            parent_type = parent.iloc[0]['event_type'] if not parent.empty else "unknown"
            
            # Simple lifecycle mapping logic
            c_type = row['event_type']
            p_type = parent_type
            lifecycle = "unknown lifecycle"
            if c_type == 'refund' and p_type == 'expense': lifecycle = "partial or full reversal"
            elif c_type == 'expense' and p_type == 'expense': lifecycle = "subsequent fee or adjustment"
            elif c_type == 'investment_valuation' and p_type == 'investment_purchase': lifecycle = "unrealized market value update"
            elif c_type == 'investment_sale' and p_type == 'investment_purchase': lifecycle = "realized sale proceeds"
            elif c_type == 'debt_payment' and p_type == 'debt_payment': lifecycle = "subsequent installment or fee"
            
            out.append(f"- {row['event_id']} ({c_type}) -> {parent_id} ({p_type}): {lifecycle}")
    out.append("\n")

    # 4. Message classification
    out.append("## 4. Message Classification\n")
    if messages is not None:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        # We process in chunks of 50 to avoid massive prompts
        chunk_size = 50
        for i in range(0, len(messages), chunk_size):
            chunk = messages.iloc[i:i+chunk_size]
            prompt = "Classify the following messages into ONE of these categories: confirm, amend, cancel, delay, irrelevant.\n"
            prompt += "Also provide a brief 1-line reason.\n"
            prompt += "Return in format: message_id | category | reason\n\n"
            for _, row in chunk.iterrows():
                prompt += f"{row['message_id']}: {row['message_text']}\n"
            
            try:
                response = client.models.generate_content(
                    model='gemini-3.6-flash',
                    contents=[prompt]
                )
                out.append(response.text)
            except Exception as e:
                out.append(f"Failed to classify chunk starting at {i}: {str(e)}")

    with open(OUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(out))

if __name__ == "__main__":
    run_checks()
