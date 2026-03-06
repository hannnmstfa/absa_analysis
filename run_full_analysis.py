import re
import json
import pandas as pd
from io import StringIO
import requests
from collections import Counter

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.pipeline import Pipeline


URL = "https://docs.google.com/spreadsheets/d/1kZhMZ1PezsznYVfe3eLoH1UZKRdnOJKHzMDfR78sE_w/export?format=csv&gid=729413622"

# --- helpers ---

def download_csv_text(csv_url: str, timeout_sec: int = 25) -> str:
    headers = {"User-Agent": "Mozilla/5.0", "Accept": "text/csv,text/plain,*/*"}
    r = requests.get(csv_url, headers=headers, timeout=timeout_sec)
    r.raise_for_status()
    text = r.text
    if "<html" in text[:200].lower():
        raise ValueError("URL tidak menghasilkan CSV. Pastikan publik & format export?format=csv")
    return text


def clean_text_basic(s: str) -> str:
    if pd.isna(s):
        return ""
    t = str(s)
    t = re.sub(r'https?://\S+|www\.\S+', '', t)
    t = re.sub(r'@\w+', '', t)
    t = re.sub(r"[^a-zA-Z0-9\s]", ' ', t)
    t = re.sub(r"\d+", ' ', t)
    return re.sub(r"\s+", ' ', t).strip().lower()


def tokenize(text: str):
    text = str(text).lower()
    text = re.sub(r"[^a-z\s]", ' ', text)
    toks = [t for t in text.split() if len(t) > 2]
    return toks


# aspect keywords (from Colab script)
aspek_dict_final = {
    "Aroma": [
        "aroma", "wangi", "wanginya", "harum", "bau",
        "manis", "fresh", "segar", "maskulin", "feminin",
        "lembut", "elegan", "menyengat", "pusing"
    ],
    "Ketahanan": [
        "tahan", "tahan lama", "awet", "lama", "ketahanan",
        "cepat hilang", "cepet hilang", "gampang hilang", "cepat pudar"
    ],
    "Kemasan": [
        "kemasan", "botol", "packaging",
        "tutup", "nozzle", "spray", "semprot", "sprayer",
        "longgar", "bocor", "travel", "kecil", "besar"
    ]
}

RECO_RULES = {
    "Kemasan": {
        "bocor": "Perkuat sealing & material botol/tutup. Tambahkan leak test dan drop test sebelum distribusi.",
        "tutup": "Perbaiki desain tutup (klik-lock/ulir lebih rapat) dan QC toleransi tutup.",
        "nozzle": "Upgrade nozzle/sprayer agar semprotan stabil. Uji semprot berulang per botol.",
        "spray": "Kalibrasi sprayer (debit & pola semprot) dan perketat QC komponen sprayer.",
        "rusak": "Gunakan material kemasan lebih kuat + protective packaging saat pengiriman."
    },
    "Ketahanan": {
        "cepat": "Optimalkan konsentrasi & fixative agar performa tahan lama meningkat (uji 4–8 jam).",
        "hilang": "Reformulasi base notes/fixative dan uji daya tahan indoor/outdoor.",
        "pudar": "Evaluasi stabilitas formula dan sesuaikan komposisi untuk memperlambat fading."
    },
    "Aroma": {
        "menyengat": "Haluskan top notes, kurangi bahan terlalu tajam; lakukan uji panel kenyamanan aroma.",
        "pusing": "Kurangi intensitas aroma tajam/menyengat dan lakukan uji sensitivitas pada responden.",
        "tajam": "Rebalance komposisi agar tidak ‘sharp’; uji preferensi konsumen untuk varian lebih soft.",
        "bau": "Periksa bahan baku & stabilitas; pastikan tidak ada off-odor dari batch."
    }
}

# summary fallback per-aspect (string) untuk rekomendasi final
RECO_SUMMARY = {
    "Kemasan": "Perkuat kualitas botol & sealing. Tambahkan leak test dan drop test sebelum distribusi.",
    "Ketahanan": "Optimalkan konsentrasi dan fixative agar parfum lebih tahan lama (uji 4–8 jam).",
    "Aroma": "Lakukan reformulasi komposisi aroma agar tidak terlalu tajam/menyengat dan lebih nyaman digunakan."
}


print('Download CSV...')
csv_text = download_csv_text(URL)
print('Parsing CSV...')
df = pd.read_csv(StringIO(csv_text), on_bad_lines='skip')
df.columns = [c.strip() for c in df.columns]
print('Shape:', df.shape)

# detect text column
from statistics import mean

possible_text = None
candidates = []
for c in df.columns:
    cl = c.lower()
    if any(k in cl for k in ['komentar','ulasan','review','saran','masukan','text','kata','alasan']):
        candidates.append(c)
if candidates:
    possible_text = candidates[0]
else:
    obj_cols = [c for c in df.columns if df[c].dtype == 'object']
    if obj_cols:
        possible_text = sorted(obj_cols, key=lambda c: df[c].astype(str).str.len().mean(), reverse=True)[0]

print('Using text column:', possible_text)

# create clean_text
if possible_text:
    df['clean_text'] = df[possible_text].astype(str).fillna('').apply(clean_text_basic)
else:
    df['clean_text'] = ''

# detect likert columns
def is_likert_series_local(s: pd.Series) -> bool:
    x = pd.to_numeric(s, errors='coerce').dropna()
    if len(x) == 0:
        return False
    return (x.between(1,5).mean() >= 0.8)

likert_cols = [c for c in df.columns if c != possible_text and is_likert_series_local(df[c])]
print('Likert cols found:', len(likert_cols))

# choose a LABEL_COL: prefer keywords
keywords_priority = ["keseluruhan","puas","kepuasan","penilaian","overall","secara keseluruhan"]
LABEL_COL = None
for kw in keywords_priority:
    for c in likert_cols:
        if kw in c.lower():
            LABEL_COL = c
            break
    if LABEL_COL:
        break
if LABEL_COL is None and likert_cols:
    LABEL_COL = likert_cols[0]

print('Selected LABEL_COL:', LABEL_COL)

# label mapping
import numpy as np

def likert_to_label_val(v):
    v = pd.to_numeric(v, errors='coerce')
    if pd.isna(v):
        return None
    if v <= 2:
        return 'Negatif'
    if v == 3:
        return 'Netral'
    return 'Positif'

if LABEL_COL:
    df['likert_score'] = pd.to_numeric(df[LABEL_COL], errors='coerce')
    df['label'] = df['likert_score'].apply(likert_to_label_val)
else:
    df['label'] = None

# prepare df_model
df_model = df[['clean_text','label']].copy()
df_model = df_model[(df_model['clean_text'].str.len() > 0) & (df_model['label'].notna())].reset_index(drop=True)
print('Rows ready for modeling:', len(df_model))

# train models if possible
results = {}
if len(df_model) >= 5 and df_model['label'].nunique() >= 2:
    X = df_model['clean_text'].values
    y = df_model['label'].values

    def safe_split(X, y, test_size=0.2, random_state=42):
        counts = Counter(y)
        can_stratify = all(v >= 2 for v in counts.values()) and len(counts) >= 2
        if can_stratify:
            return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
        return train_test_split(X, y, test_size=test_size, random_state=random_state)

    X_train, X_test, y_train, y_test = safe_split(X, y, test_size=0.2)

    tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1,2))
    X_train_tfidf = tfidf.fit_transform(X_train)
    X_test_tfidf = tfidf.transform(X_test)

    nb = MultinomialNB()
    nb.fit(X_train_tfidf, y_train)
    y_pred_nb = nb.predict(X_test_tfidf)
    acc_nb = accuracy_score(y_test, y_pred_nb)

    svm = LinearSVC(random_state=42, max_iter=2000)
    svm.fit(X_train_tfidf, y_train)
    y_pred_svm = svm.predict(X_test_tfidf)
    acc_svm = accuracy_score(y_test, y_pred_svm)

    best = 'Naive Bayes' if acc_nb >= acc_svm else 'SVM'
    best_acc = max(acc_nb, acc_svm)

    # cross validation scores
    pipe_nb = Pipeline([('tfidf', tfidf),('clf', MultinomialNB())])
    pipe_svm = Pipeline([('tfidf', tfidf),('clf', LinearSVC(random_state=42, max_iter=2000))])
    try:
        cv_nb = cross_val_score(pipe_nb, X, y, cv=5, scoring='accuracy', n_jobs=-1)
        cv_svm = cross_val_score(pipe_svm, X, y, cv=5, scoring='accuracy', n_jobs=-1)
    except Exception:
        cv_nb = cv_svm = []


    results['models'] = {
        'accuracy_nb': acc_nb,
        'accuracy_svm': acc_svm,
        'best_model': best,
        'best_acc': best_acc,
        'classification_nb': classification_report(y_test, y_pred_nb, zero_division=0, output_dict=True),
        'classification_svm': classification_report(y_test, y_pred_svm, zero_division=0, output_dict=True),
        'cv_nb_mean': float(cv_nb.mean()) if len(cv_nb) else None,
        'cv_nb_std': float(cv_nb.std()) if len(cv_nb) else None,
        'cv_svm_mean': float(cv_svm.mean()) if len(cv_svm) else None,
        'cv_svm_std': float(cv_svm.std()) if len(cv_svm) else None,
    }
else:
    results['models'] = {'note': 'Not enough data to train or single class present', 'rows': len(df_model), 'n_classes': df_model['label'].nunique()}

# --- ABSA: detect aspects by keywords and compute negative tokens per aspect ---
print('Running ABSA...')
df['aspek_detected'] = df['clean_text'].apply(lambda t: [a for a,kws in aspek_dict_final.items() if any(kw in t for kw in kws)])

# explode
df_absa = df.explode('aspek_detected').dropna(subset=['aspek_detected']).copy()
print('ABSA rows after explode:', len(df_absa))

# filter negative rows
NEG = 'Negatif'
if 'label' in df_absa.columns:
    df_neg = df_absa[df_absa['label'].astype(str).str.lower() == NEG.lower()].copy()
else:
    df_neg = pd.DataFrame()

print('Neg rows (ABSA):', len(df_neg))

# top tokens per desired aspects
TOP_N = 8
rows = []
for asp in ['Aroma','Kemasan','Ketahanan']:
    sub = df_neg[df_neg['aspek_detected']==asp]
    toks = []
    for t in sub['clean_text']:
        toks.extend([w for w in tokenize(t) if len(w)>2])
    freq = Counter(toks).most_common(TOP_N)
    rows.append({'aspek': asp, 'top_tokens': freq, 'total_neg': int(len(sub))})

results['absa'] = rows

# build recommendations for Aroma/Kemasan/Ketahanan
rekom = []
for r in rows:
    asp = r['aspek']
    tokens = [w for w,c in r['top_tokens']]
    # match tokens to issue rules
    issue_set = set()
    for k in aspek_dict_final.get(asp,[]):
        issue_set.add(k)
    matched = [t for t in tokens if t in issue_set]
    recs = []
    for m in matched:
        rule = RECO_RULES.get(asp, {}).get(m)
        if rule and rule not in recs:
            recs.append(rule)
    if not recs:
        # fallback template
        recs = [
            f"Fokus perbaikan pada aspek {asp}; isu utama: {', '.join(tokens[:3]) if tokens else '-'}.",
            RECO_SUMMARY.get(asp, f"Evaluasi lanjutan untuk aspek {asp}.")
        ]
    rekom.append({'aspek': asp, 'rekomendasi': ' | '.join(recs), 'total_neg': r['total_neg']})

results['rekom'] = sorted(rekom, key=lambda x: x['total_neg'], reverse=True)

print(json.dumps(results, ensure_ascii=False, indent=2))
