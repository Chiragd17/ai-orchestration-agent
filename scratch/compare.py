import pandas as pd
df1 = pd.read_csv('dataset/output.csv')
df2 = pd.read_csv('dataset/sample_requests.csv')
merged = df1.merge(df2, on='request_id', suffixes=('_pred', '_target'))
for _, r in merged.iterrows():
    if str(r['amount_safe_to_pay_pred']) != str(r['amount_safe_to_pay_target']):
        print(f"{r['request_id']}: pred {r['amount_safe_to_pay_pred']} != target {r['amount_safe_to_pay_target']}")
