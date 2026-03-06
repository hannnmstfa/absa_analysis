import pandas as pd
from io import StringIO
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score
from engine import _download_csv_text, build_csv_export_url, guess_text_column, is_likert_series, build_clean_text_column

# Download CSV
url = 'https://docs.google.com/spreadsheets/d/1kZhMZ1PezsznYVfe3eLoH1UZKRdnOJKHzMDfR78sE_w/export?format=csv&gid=729413622'
url = build_csv_export_url(url)
csv_text = _download_csv_text(url, timeout_sec=25)
df = pd.read_csv(StringIO(csv_text), on_bad_lines="skip")
df.columns = [c.strip() for c in df.columns]

print(f"Shape: {df.shape}")

# Detect text column
text_col = guess_text_column(df)
print(f"Text column: {text_col}")

# Clean text
if text_col:
    build_clean_text_column(df, text_col, "clean_text")
    modeling_text_col = "clean_text"
else:
    modeling_text_col = None

# Detect likert columns
likert_cols = []
for c in df.columns:
    if c == text_col:
        continue
    if is_likert_series(df[c]):
        likert_cols.append(c)

print(f"Likert columns: {len(likert_cols)}")

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

print(f"Selected LABEL_COL: {LABEL_COL}")

# Build df_model
df_model = df[[modeling_text_col, LABEL_COL]].copy()

def _likert_label(v):
    if pd.isna(v):
        return None
    v = pd.to_numeric(v, errors='coerce')
    if pd.isna(v):
        return None
    if v <= 2:
        return "Negatif"
    if v == 3:
        return "Netral"
    return "Positif"

df_model[modeling_text_col] = df_model[modeling_text_col].astype(str).fillna("").str.strip()
df_model["label"] = pd.to_numeric(df_model[LABEL_COL], errors='coerce').apply(_likert_label)
df_model = df_model[(df_model[modeling_text_col].str.len() > 0) & (df_model["label"].notna())].reset_index(drop=True)

print(f"Rows ready for modeling: {len(df_model)}")
print(f"Label distribution:")
print(df_model["label"].value_counts())

# Train models
X = df_model[modeling_text_col].astype(str).values
y = df_model["label"].values

def safe_train_test_split(Xi, yi, test_size=0.2, random_state=42):
    counts = Counter(yi)
    can_stratify = all(v >= 2 for v in counts.values()) and len(counts) >= 2
    if can_stratify:
        return train_test_split(Xi, yi, test_size=test_size, random_state=random_state, stratify=yi)
    return train_test_split(Xi, yi, test_size=test_size, random_state=random_state)

X_train, X_test, y_train, y_test = safe_train_test_split(X, y, test_size=0.2, random_state=42)

print(f"\nTrain set: {len(X_train)}")
print(f"Test set: {len(X_test)}")
print(f"Test set labels:")
print(pd.Series(y_test).value_counts())

tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf = tfidf.transform(X_test)

# Train NB
nb = MultinomialNB()
nb.fit(X_train_tfidf, y_train)
y_pred_nb = nb.predict(X_test_tfidf)
acc_nb = accuracy_score(y_test, y_pred_nb)

# Train SVM
svm = LinearSVC(random_state=42, max_iter=2000)
svm.fit(X_train_tfidf, y_train)
y_pred_svm = svm.predict(X_test_tfidf)
acc_svm = accuracy_score(y_test, y_pred_svm)

print(f"\nNB Accuracy: {acc_nb*100:.1f}%")
print(f"SVM Accuracy: {acc_svm*100:.1f}%")

print(f"\nNB predictions:")
print(pd.Series(y_pred_nb).value_counts())
print(f"\nSVM predictions:")
print(pd.Series(y_pred_svm).value_counts())
