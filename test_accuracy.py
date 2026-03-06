from engine import run_analysis_from_csv_url
import pandas as pd
from io import StringIO
import requests
from engine import _download_csv_text, build_csv_export_url, guess_text_column, is_likert_series

# First, let's see what columns are being detected
url = 'https://docs.google.com/spreadsheets/d/1kZhMZ1PezsznYVfe3eLoH1UZKRdnOJKHzMDfR78sE_w/export?format=csv&gid=729413622'
url = build_csv_export_url(url)
csv_text = _download_csv_text(url, timeout_sec=25)
df = pd.read_csv(StringIO(csv_text), on_bad_lines="skip")
df.columns = [c.strip() for c in df.columns]

print(f"Total columns: {len(df.columns)}")
print(f"Total rows: {len(df)}")

# Detect likert columns
likert_cols = []
for c in df.columns:
    if is_likert_series(df[c]):
        likert_cols.append(c)
        
print(f"\nLikert columns found ({len(likert_cols)}):")
for col in likert_cols:
    print(f"  - {col}")

# Select LABEL_COL
LABEL_COL = None
keywords_priority = ["keseluruhan", "puas", "kepuasan", "penilaian", "overall", "secara keseluruhan"]
for kw in keywords_priority:
    for c in likert_cols:
        if kw in c.lower():
            LABEL_COL = c
            break
    if LABEL_COL:
        break
if LABEL_COL is None and likert_cols:
    LABEL_COL = likert_cols[0]

print(f"\nSelected LABEL_COL: {LABEL_COL}")

# Now run full analysis
result = run_analysis_from_csv_url(url)
models = result.get('kpi', {})
print(f"\nNB Accuracy: {models.get('accuracy_nb', 0)*100:.1f}%")
print(f"SVM Accuracy: {models.get('accuracy_svm', 0)*100:.1f}%")
print(f"Overall Accuracy (best model): {models.get('akurasi_model', 0)*100:.1f}%")

