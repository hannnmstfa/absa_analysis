import pandas as pd
from engine import analyze_dataset

df = pd.read_csv('audit_sentimen_untuk_excel.csv')
res = analyze_dataset(df, text_col='Komentar', usage_col='Apakah Anda pernah menggunakan LuxueXPerfume?')

seg = res.get('segment_views', {})
non_user = seg.get('non_user', {})
print("KEYS IN NON_USER:", non_user.keys())

insights = non_user.get('market_insights')
print("MARKET_INSIGHTS:", insights)
