import pandas as pd
import os
import glob

DATA_DIR = r"c:\Users\chira\Desktop\orchestrate-agent\dataset"

def inspect():
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    print("=== SCHEMAS ===")
    data = {}
    for f in csv_files:
        name = os.path.basename(f)
        df = pd.read_csv(f)
        data[name] = df
        print(f"\n--- {name} ---")
        print(f"Shape: {df.shape}")
        print("Dtypes & Nulls:")
        info_df = pd.DataFrame({'dtype': df.dtypes, 'nulls': df.isnull().sum()})
        print(info_df)
    
    print("\n=== SAMPLE USERS ===")
    profiles = data.get('financial_profiles.csv')
    events = data.get('financial_events.csv')
    images = data.get('images.csv')
    
    if profiles is not None and events is not None:
        sample_users = profiles['user_id'].head(3).tolist()
        print(f"Selected Users: {sample_users}")
        for uid in sample_users:
            print(f"\n--- User: {uid} ---")
            user_events = events[events['user_id'] == uid].sort_values('event_date')
            for _, row in user_events.iterrows():
                amt = row['amount']
                flag = ""
                if pd.isna(amt):
                    flag = " (BLANK AMOUNT)"
                    if images is not None:
                        img_match = images[images['related_event_id'] == row['event_id']]
                        if not img_match.empty:
                            flag += f" -> Image: {img_match.iloc[0]['image_id']}.png"
                        else:
                            flag += " -> Image: NOT FOUND"
                print(f"{row['event_date']} | {row['event_id']} | {row['event_type']} | {amt}{flag} | linked_to: {row['linked_event_id']}")
    
    print("\n=== LINKED EVENT CHAINS ===")
    if events is not None:
        linked = events[events['linked_event_id'].notna()]
        print(f"Found {len(linked)} linked events.")
        for _, row in linked.iterrows():
            parent_id = row['linked_event_id']
            parent = events[events['event_id'] == parent_id]
            parent_type = parent.iloc[0]['event_type'] if not parent.empty else "UNKNOWN"
            print(f"Child: {row['event_id']} ({row['event_type']}) -> Parent: {parent_id} ({parent_type})")
            
    print("\n=== MESSAGES ===")
    msgs = data.get('messages.csv')
    if msgs is not None:
        for _, row in msgs.iterrows():
            print(f"Msg ID: {row['message_id']} | User: {row['user_id']} | Date: {row['sent_at']}")
            print(f"Content: {row['message_text']}\n")
            
    print("\n=== SAMPLE REQUESTS ===")
    reqs = data.get('sample_requests.csv')
    if reqs is not None:
        for _, row in reqs.iterrows():
            print(dict(row))

if __name__ == "__main__":
    inspect()
