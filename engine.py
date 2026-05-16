import time
import pandas as pd
import re
import requests
import math
from io import StringIO
from collections import Counter
from typing import Dict, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_validate, GridSearchCV
from sklearn.naive_bayes import MultinomialNB, ComplementNB
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support, precision_score, recall_score, make_scorer
from sklearn.pipeline import Pipeline
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

_stemmer_factory = StemmerFactory()
_stemmer = _stemmer_factory.create_stemmer()



MIN_TOTAL_RESPONDENTS = 30
MAX_UNKNOWN_USAGE_RATIO = 0.35
MIN_MODEL_F1_FOR_AUTO_ACTION = 0.70
MIN_VARIANT_SAMPLE = 10
DRILLDOWN_MAX_EXAMPLES = 5


# -----------------------------
# 1) RULE LABELING (aman utk skripsi)
# Likert 1–5 → Negatif/Netral/Positif
# 1-2 = Negatif, 3 = Netral, 4-5 = Positif
# -----------------------------
def likert_to_sentiment(score) -> str:
    if pd.isna(score):
        return "Unknown"
    try:
        s = float(score)
    except Exception:
        return "Unknown"

    if s <= 2:
        return "Negatif"
    if s == 3:
        return "Netral"
    return "Positif"


def likert_average_to_sentiment(score) -> str:
    """Map averaged Likert score to sentiment with interval thresholds."""
    if pd.isna(score):
        return "Unknown"
    try:
        s = float(score)
    except Exception:
        return "Unknown"

    if s <= 2.5:
        return "Negatif"
    if s <= 3.5:
        return "Netral"
    return "Positif"


def is_likert_series(s: pd.Series) -> bool:
    x = pd.to_numeric(s, errors="coerce").dropna()
    if len(x) == 0:
        return False
    return (x.between(1, 5).mean() >= 0.80)


def _finite_float_or_none(value):
    try:
        v = float(value)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def _build_operational_readiness(
    total_responden: int,
    model_trained: bool,
    best_f1: Optional[float],
    unknown_usage_ratio: float,
    variant_rankings: List[Dict[str, object]],
) -> Dict[str, object]:
    checks = []
    warnings = []
    score = 100.0

    sample_passed = total_responden >= MIN_TOTAL_RESPONDENTS
    checks.append({
        "key": "sample_size",
        "passed": sample_passed,
        "value": int(total_responden),
        "minimum": MIN_TOTAL_RESPONDENTS,
        "note": "Jumlah responden memadai" if sample_passed else "Jumlah responden masih rendah untuk keputusan otomatis",
    })
    if not sample_passed:
        score -= 25
        warnings.append(f"Jumlah responden {total_responden} masih di bawah batas aman {MIN_TOTAL_RESPONDENTS}.")

    if model_trained and best_f1 is not None:
        model_passed = float(best_f1) >= MIN_MODEL_F1_FOR_AUTO_ACTION
        checks.append({
            "key": "model_f1",
            "passed": model_passed,
            "value": float(round(best_f1, 4)),
            "minimum": MIN_MODEL_F1_FOR_AUTO_ACTION,
            "note": "Kualitas model memadai" if model_passed else "Kualitas model belum cukup untuk otomatisasi penuh",
        })
        if not model_passed:
            score -= 30
            warnings.append(
                f"F1 model {best_f1:.3f} masih di bawah ambang {MIN_MODEL_F1_FOR_AUTO_ACTION:.2f}."
            )
    else:
        checks.append({
            "key": "model_f1",
            "passed": False,
            "value": None,
            "minimum": MIN_MODEL_F1_FOR_AUTO_ACTION,
            "note": "Model belum terlatih, hasil berbasis aturan/heuristik",
        })
        score -= 35
        warnings.append("Model belum terlatih, gunakan output sebagai sinyal awal dan verifikasi manual.")

    unknown_passed = float(unknown_usage_ratio) <= MAX_UNKNOWN_USAGE_RATIO
    checks.append({
        "key": "unknown_usage_ratio",
        "passed": unknown_passed,
        "value": float(round(unknown_usage_ratio, 4)),
        "maximum": MAX_UNKNOWN_USAGE_RATIO,
        "note": "Klasifikasi segmen cukup jelas" if unknown_passed else "Banyak status penggunaan tidak dikenali",
    })
    if not unknown_passed:
        score -= 20
        warnings.append(
            f"Proporsi pengalaman pakai tidak dikenali {unknown_usage_ratio:.1%} melebihi batas {MAX_UNKNOWN_USAGE_RATIO:.0%}."
        )

    total_variants = len(variant_rankings or [])
    eligible_variants = sum(1 for x in (variant_rankings or []) if bool(x.get("sample_sufficient")))
    variant_ratio = (eligible_variants / total_variants) if total_variants else 1.0
    checks.append({
        "key": "variant_sample",
        "passed": bool(total_variants == 0 or eligible_variants > 0),
        "value": {
            "eligible": int(eligible_variants),
            "total": int(total_variants),
        },
        "minimum_per_variant": MIN_VARIANT_SAMPLE,
        "note": "Varian memiliki sampel cukup" if total_variants == 0 or eligible_variants > 0 else "Sampel per varian terlalu kecil",
    })
    if total_variants > 0 and variant_ratio < 0.5:
        score -= 15
        warnings.append(
            f"Hanya {eligible_variants}/{total_variants} varian yang memenuhi minimal {MIN_VARIANT_SAMPLE} komentar."
        )

    score = max(0.0, min(100.0, score))
    ready_for_auto_actions = score >= 80 and sample_passed and unknown_passed and model_trained and (best_f1 is not None and best_f1 >= MIN_MODEL_F1_FOR_AUTO_ACTION)
    ready_for_business_use = score >= 60 and sample_passed

    if ready_for_auto_actions:
        level = "ready"
    elif ready_for_business_use:
        level = "limited"
    else:
        level = "not_ready"

    return {
        "level": level,
        "score": int(round(score)),
        "ready_for_business_use": bool(ready_for_business_use),
        "ready_for_auto_actions": bool(ready_for_auto_actions),
        "checks": checks,
        "warnings": warnings,
        "thresholds": {
            "min_total_responden": MIN_TOTAL_RESPONDENTS,
            "min_model_f1_auto_action": MIN_MODEL_F1_FOR_AUTO_ACTION,
            "max_unknown_usage_ratio": MAX_UNKNOWN_USAGE_RATIO,
            "min_variant_sample": MIN_VARIANT_SAMPLE,
        },
    }


def build_csv_export_url(url: str) -> str:
    u = url.strip()

    # kalau user sudah kasih link export, biarkan
    if "docs.google.com/spreadsheets" in u and "/export" in u and "format=csv" in u:
        return u

    # Extract sheet ID from Google Sheets URL
    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", u)
    if not m:
        # Coba cari ID langsung dari URL (untuk berbagai format URL)
        if "docs.google.com" in u:
            raise ValueError(
                "Format URL Google Sheets tidak dikenali. "
                "Gunakan format: https://docs.google.com/spreadsheets/d/SHEET_ID/edit..."
            )
        raise ValueError(
            "URL tidak tampak seperti Google Sheets. "
            "Pastikan URL adalah dari docs.google.com/spreadsheets"
        )

    sheet_id = m.group(1)
    gid = "0"
    m_gid = re.search(r"gid=([0-9]+)", u)
    if m_gid:
        gid = m_gid.group(1)

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"


def guess_text_column(df: pd.DataFrame, exclude_cols: List[str] | None = None) -> Optional[str]:
    """Pilih kolom yang paling mungkin berisi komentar teks.

    * Mencari nama kolom yang mengandung kata-kata umum seperti komentar, ulasan, review, dll.
    * Jika `exclude_cols` diberikan, kolom-kolom tersebut akan diabaikan.
    * Jika tidak menemukan, pilih kolom string terpanjang secara rata-rata.

    Kami sengaja tidak mengandalkan kolom "saran"/"rekom" karena biasanya itu
    berisi masukan pengguna dan bukan komentar bebas.
    """
    candidates = []
    for c in df.columns:
        if exclude_cols and c in exclude_cols:
            continue
        cl = c.lower().strip()
        # perluas kata kunci supaya mencakup istilah umum seperti "kata",
        # "tulis"/"tuliskan"/"sebut" yang sering muncul di judul kolom survei.
        if any(k in cl for k in [
            "komentar", "ulasan", "review", "kritik", "pendapat",
            "masukan", "alasan", "keterangan", "feedback", "text",
            "kata", "tulis", "sebut"
        ]):
            candidates.append(c)
    
    if candidates:
        # **FIX**: Prefer "3 kata" pattern (more descriptive)
        for cand in candidates:
            if "3 kata" in cand.lower():
                return cand
        # Otherwise pick by longest average text
        if len(candidates) > 1:
            return max(candidates, key=lambda c: df[c].astype(str).str.len().mean())
        return candidates[0]

    # jika tidak ada kandidat berbasis nama, pilih kolom string panjang
    import pandas as _pd
    obj_cols = [c for c in df.columns if _pd.api.types.is_string_dtype(df[c])]
    if exclude_cols:
        obj_cols = [c for c in obj_cols if c not in exclude_cols]
    if not obj_cols:
        return None
    obj_cols_sorted = sorted(
        obj_cols,
        key=lambda c: df[c].astype(str).str.len().mean(),
        reverse=True
    )
    return obj_cols_sorted[0]


_STOPWORDS_ID = {
    "yang","dan","di","ke","dari","untuk","dengan","atau","pada","ini","itu","saya","aku","kami","kita",
    "ya","yg","aja","kok","banget","sih","udah","sudah","karena","juga","jadi",
    "lebih","sangat","sekali","nya","deh","dong","lah","pun","dalam","oleh","buat","bagi","ada",
    "the","a","an","to","of","in","is","are",
    "jam","belum","pakai","beli","kalau","kalo","biar","bisa","banyak","harus","paling","coba","bikin",
    "gak","nggak","tidak","sama","suka","ingin","mau","terus","lagi","kayak","pas","jika","mungkin",
    "biar","bukan","tapi","cuma","hanya","pasti"
}

# Aspect keywords (common product aspects in Indonesian)
_ASPECT_KEYWORDS = {
    "kemasan": ["kemasan", "bungkus", "packaging", "box", "wadah", "botol", "tabung", "tutup", "nozzle", "sprayer"],
    "aroma": ["aroma", "bau", "berbau", "wangi", "harum", "rasa", "scent", "aromaterapi", "pewangi"],
    "tekstur": ["tekstur", "konsistensi", "kental", "encer", "tebal", "halus", "kasar", "lembut", "licin"],
    "warna": ["warna", "warna", "berwarna", "color", "biru", "merah", "putih", "hitam"],
    "ketahanan": ["ketahanan", "tahan", "masa berlaku", "expired", "exp", "kadaluarsa", "durability"],
    "harga": ["harga", "mahal", "murah", "price", "biaya", "cost", "mahal", "expensive"],
    "efektivitas": ["efektif", "manfaat", "hasil", "effectiveness", "benefit", "work", "berguna", "membantu", "fungsi"],
    "kualitas": ["kualitas", "kualiti", "quality", "bagus", "baik", "jelek", "buruk", "nyaman"],
}

_TEXT_SENTIMENT_NEGATIVE_CUES = {
    "_generic": [
        "tidak tercium", "hampir tidak tercium", "mulai hilang", "cepat hilang", "tidak konsisten",
        "berkurang", "kurang kuat", "kurang tahan", "tidak tahan", "cuma tahan", "hanya tahan",
        "lemah", "pudar", "menurun", "kurang awet", "semprot ulang", "disemprot ulang", "spray ulang",
        "masalah", "kendala", "keluhan", "kecewa", "sayang sekali", "kurang", "tidak",
        "belum konsisten", "kurang konsisten", "tidak stabil", "belum stabil",
        "mahal", "kemahalan", "overprice", "jauh", "sulit dicari", "susah dicari", "tidak ada",
        "kosong", "habis", "ragu", "takut", "ragu-ragu", "bingung", "kurang yakin",
        "tidak awet", "nggak awet", "kurang harum", "kurang wangi", "tidak wangi", "kurang enak",
        "tidak enak", "kurang suka", "tidak suka", "kecewa", "buruk", "jelek"
    ],
    "aroma": [
        "aroma hilang", "aroma cepat hilang", "bau hilang", "wangi hilang", "aroma tidak konsisten",
        "tajam", "terlalu tajam", "pusing", "bikin pusing", "mual", "eneg", "menyengat", "nyegrak",
        "terlalu kuat", "bau apek", "bau plastik", "bau alkohol", "alkohol banget", "kurang wangi",
        "kurang harum", "bau menyengat", "aroma aneh", "bau aneh", "bau balsem", "bau minyak kayu putih",
        "bau obat", "bau kimia", "bau sangit", "bau kecut", "tidak keluar wanginya"
    ],
    "ketahanan": [
        "ketahanan berkurang", "ketahanan kurang", "ketahanan rendah", "tahan 2 jam", "tahan 3 jam",
        "cepat pudar", "cepat menguap", "sebentar saja", "cuma sebentar", "nggak awet",
        "kurang tahan lama", "tidak tahan lama", "tidak awet", "cepet ilang", "cepet pudar",
        "hanya tahan sebentar", "kurang nendang", "kurang kuat", "tidak tahan lama"
    ],
    "kemasan": [
        "bocor", "rembes", "rusak", "patah", "retak", "nozzle macet", "spray macet", "tutup longgar",
        "macet", "seret", "keras", "susah ditekan", "tumpah", "kurang rapi", "kurang premium",
        "agak rawan", "botol plastik", "label lepas", "belum konsisten"
    ],
    "harga": [
        "mahal", "kemahalan", "overprice", "pricey", "tidak ramah kantong", "berat di ongkir", "ongkir mahal"
    ],
    "akses": [
        "jauh", "sulit dicari", "susah dicari", "stok kosong", "habis", "tidak ada di shopee", "tidak ada di tokped"
    ]
}

_TEXT_SENTIMENT_NEGATIVE_CRITICAL_CUES = {
    "_generic": [
        "tidak tercium", "hampir tidak tercium", "mulai hilang", "cepat hilang", "tidak konsisten",
        "berkurang", "kurang kuat", "kurang tahan", "tidak tahan", "cuma tahan", "hanya tahan", "pudar",
        "semprot ulang", "disemprot ulang", "spray ulang", "perlu semprot ulang", "perlu disemprot ulang",
        "bocor", "rusak", "parah", "jelek", "buruk", "belum konsisten", "kurang konsisten", "longgar",
        "rembes", "hilang", "macet", "pecah", "palsu", "nipu"
    ],
    "aroma": ["aroma hilang", "aroma tidak konsisten", "wangi hilang", "bau hilang", "pusing", "mual", "alkohol banget"],
    "ketahanan": ["ketahanan berkurang", "ketahanan kurang", "ketahanan rendah", "tahan 2 jam", "tahan 3 jam", "cepat hilang", "mudah hilang", "cepet ilang"],
    "kemasan": ["bocor", "rembes", "rusak", "patah", "retak", "nozzle macet", "spray macet", "tumpah", "tutup longgar", "longgar"],
}

_TEXT_SENTIMENT_NEGATION_GUARDS = [
    "tidak cepat hilang", "tidak mudah hilang", "tidak hilang", "tidak berkurang", "tidak pudar",
    "tidak perlu disemprot ulang", "tidak perlu semprot ulang", "tidak bocor", "tidak macet",
    "tidak longgar", "nggak longgar", "ga longgar", "tidak rembes", "tidak rusak", "aman",
    "tidak tajam", "tidak menyengat", "tidak pusing", "tidak ada masalah", "tidak pernah mengalami masalah",
    "tidak mengalami masalah", "tidak ada keluhan", "tidak ada kendala", "baik baik saja", "aman aman saja"
]

_TEXT_SENTIMENT_POSITIVE_CUES = {
    "_generic": [
        "tahan lama", "awet", "bagus", "nyaman", "suka", "mantap", "harum", "wangi",
        "konsisten", "stabil", "jos", "mantul", "rekomended", "puas", "senang",
        "aman", "lancar", "kokoh", "rapi", "mewah", "premium", "eksklusif", "elegan",
        "penasaran", "ingin coba", "mau beli", "bakal beli", "pasti beli", "checkout",
        "tertarik", "menarik", "keren", "idaman", "impian"
    ],
    "aroma": ["aroma enak", "aroma lembut", "wangi lembut", "aroma konsisten", "wangi enak", "harum sekali", "segar", "fresh"],
    "ketahanan": ["ketahanan bagus", "ketahanan baik", "awet seharian", "tahan seharian", "tahan lama sekali"],
    "kemasan": ["kemasan bagus", "kemasan rapi", "botol bagus", "nozzle bagus", "spray lancar", "mewah", "premium", "aman", "kokoh", "eksklusif"],
}


def _contains_aspect_keyword(text_lower: str, keyword: str) -> bool:
    kw = str(keyword or "").strip().lower()
    if not kw:
        return False

    # Match by token/phrase boundary to avoid false positives like "tas" in "aktivitas".
    if " " in kw:
        phrase_pattern = r"(?<![a-z0-9])" + re.escape(kw).replace(r"\ ", r"\s+") + r"(?![a-z0-9])"
        return re.search(phrase_pattern, text_lower) is not None

    token_pattern = r"(?<![a-z0-9])" + re.escape(kw) + r"(?![a-z0-9])"
    return re.search(token_pattern, text_lower) is not None

def extract_aspects_from_text(text: str) -> List[str]:
    """Extract aspects dari text komentar"""
    if pd.isna(text):
        return ["umum"]

    text_lower = re.sub(r"\s+", " ", str(text).lower()).strip()
    if not text_lower or text_lower == "nan":
        return ["umum"]

    found_aspects = []

    for aspect, keywords in _ASPECT_KEYWORDS.items():
        if any(_contains_aspect_keyword(text_lower, kw) for kw in keywords):
            found_aspects.append(aspect)

    return sorted(set(found_aspects)) if found_aspects else ["umum"]


def _count_phrase_hits(text_lower: str, phrases: List[str]) -> int:
    if not phrases:
        return 0
    return sum(1 for ph in phrases if _contains_aspect_keyword(text_lower, ph))


def _infer_text_sentiment_for_aspect(text: str, aspect: str) -> str:
    if pd.isna(text):
        return "Unknown"

    normalized = re.sub(r"[^a-z0-9\s]", " ", str(text).lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    if not normalized or normalized == "nan":
        return "Unknown"

    aspect_key = str(aspect or "").strip().lower()
    neg_phrases = list(_TEXT_SENTIMENT_NEGATIVE_CUES.get("_generic", [])) + list(_TEXT_SENTIMENT_NEGATIVE_CUES.get(aspect_key, []))
    neg_critical_phrases = list(_TEXT_SENTIMENT_NEGATIVE_CRITICAL_CUES.get("_generic", [])) + list(_TEXT_SENTIMENT_NEGATIVE_CRITICAL_CUES.get(aspect_key, []))
    pos_phrases = list(_TEXT_SENTIMENT_POSITIVE_CUES.get("_generic", [])) + list(_TEXT_SENTIMENT_POSITIVE_CUES.get(aspect_key, []))

    neg_hits = _count_phrase_hits(normalized, neg_phrases)
    critical_neg_hits = _count_phrase_hits(normalized, neg_critical_phrases)
    pos_hits = _count_phrase_hits(normalized, pos_phrases)
    negation_hits = _count_phrase_hits(normalized, _TEXT_SENTIMENT_NEGATION_GUARDS)

    # **FIX**: Detect negated positive/negative cues
    neg_prefix_pattern = r"(?<![a-z0-9])(?:tidak|kurang|nggak|ga|gak|belum|ngga)\s+(?:terlalu\s+)?(?:begitu\s+)?(?:sangat\s+)?(?:ada\s+)?(?:pernah\s+)?(?:mengalami\s+)?"
    
    for ph in pos_phrases:
        if ph in normalized:
            if " " in ph:
                pattern = neg_prefix_pattern + re.escape(ph).replace(r"\ ", r"\s+")
            else:
                pattern = neg_prefix_pattern + re.escape(ph)
            
            if re.search(pattern, normalized):
                neg_hits += 1
                pos_hits = max(0, pos_hits - 1)

    for ph in neg_phrases:
        if ph in normalized:
            if " " in ph:
                pattern = neg_prefix_pattern + re.escape(ph).replace(r"\ ", r"\s+")
            else:
                pattern = neg_prefix_pattern + re.escape(ph)
            
            if re.search(pattern, normalized):
                negation_hits += 1
                neg_hits = max(0, neg_hits - 1)

    # Strong complaint phrases should dominate unless explicitly negated.
    if critical_neg_hits > 0 and negation_hits == 0:
        return "Negatif"

    # **ENHANCEMENT**: Extra check for strong negative indicators in perfume context
    strong_neg_tokens = {"pusing", "mual", "enek", "apek", "alkohol", "bocor", "rusak", "macet", "hilang", "cepat hilang"}
    if any(tok in normalized for tok in strong_neg_tokens) and negation_hits == 0:
        return "Negatif"

    neg_score = max(0, neg_hits - (negation_hits * 2))
    pos_score = pos_hits + negation_hits

    if neg_score > pos_score:
        return "Negatif"
    if pos_score > neg_score:
        return "Positif"
    return "Unknown"

def tokenize_id(text: str) -> List[str]:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    toks = [t for t in text.split() if len(t) >= 3 and t not in _STOPWORDS_ID]
    return toks


# --- text cleaning / preprocessing (lightweight, no external downloads) ---
normalization_dict = {
    "ga": "tidak", "gak": "tidak", "gk": "tidak", "nggak": "tidak",
    "enggak": "tidak", "tdk": "tidak", "bgt": "banget", "bgtt": "banget",
    "bangett": "banget", "aja": "saja", "tpi": "tapi", "tp": "tapi",
    "krn": "karena", "karna": "karena", "dgn": "dengan", "dg": "dengan",
    "bgs": "bagus", "bagusss": "bagus", "awettt": "awet", "ilang": "hilang",
    "cepet": "cepat", "cpt": "cepat"
}

def _remove_url(text: str) -> str:
    return re.sub(r'https?://\S+|www\.\S+', '', str(text) if text is not None else '')

def _remove_usernames(text: str) -> str:
    return re.sub(r'@\w+', '', str(text) if text is not None else '')

def _remove_emoji(text: str) -> str:
    if text is None:
        return ''
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F700-\U0001F77F"
        u"\U0001F780-\U0001F7FF"
        u"\U0001F800-\U0001F8FF"
        u"\U0001FA00-\U0001FA6F"
        u"\U0001FA70-\U0001FAFF"
        u"\U0001F004-\U0001F0CF"
        u"\U0001F1E0-\U0001F1FF"
    "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', str(text))

def _remove_symbols_and_numbers(text: str) -> str:
    t = re.sub(r"[^a-zA-Z0-9\s]", ' ', str(text))
    t = re.sub(r"\d+", ' ', t)
    t = re.sub(r"\s+", ' ', t).strip()
    return t

def _normalize_tokens_list(tokens: List[str]) -> List[str]:
    return [normalization_dict.get(tok, tok) for tok in tokens]

def build_clean_text_column(frame: pd.DataFrame, src_col: str, target_col: str = "clean_text") -> None:
    """Create `clean_text` column on `frame` in-place: cleaning, lowercasing, tokenization, normalization, stopword removal and join.

    Lightweight approach to avoid external NLTK downloads.
    """
    texts = frame[src_col].astype(str).fillna("")

    cleaned = texts.apply(_remove_url).apply(_remove_usernames).apply(_remove_emoji).apply(_remove_symbols_and_numbers)
    cleaned = cleaned.str.lower().str.strip()

    def _process_row(s: str) -> str:
        toks = [t for t in s.split() if len(t) > 2 and t not in _STOPWORDS_ID]
        toks = _normalize_tokens_list(toks)
        toks = [_stemmer.stem(t) for t in toks]
        toks = [t for t in toks if t not in _STOPWORDS_ID]
        return " ".join(toks)

    frame[target_col] = cleaned.apply(_process_row)


def _download_csv_text(csv_url: str, timeout_sec: int = 25) -> str:
    """
    Download dulu supaya:
    - cepat gagal kalau bukan CSV
    - ga 'nge-hang' di pandas karena dapat HTML login/blocked
    """
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/csv,text/plain,*/*",
    }
    try:
        r = requests.get(csv_url, headers=headers, timeout=timeout_sec, allow_redirects=True, stream=True)
        r.raise_for_status()
        MAX_SIZE = 5 * 1024 * 1024 # 5 MB limit
        content = b""
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                content += chunk
                if len(content) > MAX_SIZE:
                    raise ValueError(f"Ukuran file CSV melebihi batas maksimal ({MAX_SIZE // 1024 // 1024} MB).")
        r_text = content.decode('utf-8', errors='replace')
    except requests.exceptions.HTTPError as e:
        if r.status_code == 400:
            raise ValueError(
                f"400 Bad Request: URL tidak valid. "
                f"Pastikan: 1) Sheet publik (Anyone with the link), "
                f"2) URL format benar (docs.google.com/spreadsheets/d/SHEET_ID), "
                f"3) Sheet ID dan gid tab benar. URL yang dipakai: {csv_url}"
            )
        elif r.status_code == 404:
            raise ValueError(
                f"404 Not Found: Sheet tidak ditemukan. "
                f"Pastikan Sheet ID benar dan Sheet masih ada."
            )
        elif r.status_code == 403:
            raise ValueError(
                f"403 Forbidden: Anda tidak punya akses. "
                f"Pastikan Sheet dibuat public (Anyone with the link)."
            )
        else:
            raise ValueError(
                f"HTTP Error {r.status_code}: Gagal download CSV dari URL: {csv_url}"
            )
    except requests.exceptions.Timeout:
        raise ValueError(
            f"Request timeout setelah {timeout_sec} detik. "
            f"Server mungkin lambat atau URL tidak dapat diakses."
        )
    except requests.exceptions.RequestException as e:
        raise ValueError(
            f"Network error saat download: {str(e)}. "
            f"Pastikan koneksi internet stabil dan URL valid."
        )

    # validasi cepat: kalau HTML, biasanya ada "<html" di awal
    head = r_text[:200].lower()
    if "<html" in head or "accounts.google.com" in head:
        raise ValueError(
            "Link tidak menghasilkan CSV. Pastikan Sheet publik (Anyone with the link) "
            "dan URL export format=csv. Cek juga gid tab yang benar."
        )
    return r_text

def load_csv_text(csv_url: str) -> str:
    csv_url = build_csv_export_url(csv_url)

    r = requests.get(
        csv_url,
        timeout=60,
        headers={"User-Agent": "Mozilla/5.0"},
        allow_redirects=True,
    )
    r.raise_for_status()
    return r.text

_ANALYSIS_CACHE = {}
CACHE_TTL = 300

def run_analysis_from_csv_url(csv_url: str) -> dict:
    import time
    cache_key = build_csv_export_url(csv_url)
    current_time = time.time()
    if cache_key in _ANALYSIS_CACHE:
        cached_result, timestamp = _ANALYSIS_CACHE[cache_key]
        if current_time - timestamp < CACHE_TTL:
            return cached_result
    
    result = _internal_run_analysis_from_csv_url(csv_url)
    _ANALYSIS_CACHE[cache_key] = (result, current_time)
    return result

def _internal_run_analysis_from_csv_url(csv_url: str) -> dict:
    csv_url = build_csv_export_url(csv_url)

    # 1) download & parse
    csv_text = _download_csv_text(csv_url, timeout_sec=25)
    df_raw = pd.read_csv(StringIO(csv_text), on_bad_lines="skip")
    df_raw.columns = [c.strip() for c in df_raw.columns]

    def _parse_usage_status(value) -> Optional[bool]:
        if pd.isna(value):
            return None
        text = str(value).strip().lower()
        if text == "":
            return None

        yes_tokens = {
            "ya", "yes", "y", "sudah", "udah", "pernah", "pernah pakai", "pernah memakai",
            "sudah pakai", "sudah memakai", "sudah pernah", "1", "true"
        }
        no_tokens = {
            "tidak", "nggak", "gak", "ga", "no", "n", "belum", "belum pernah", "0", "false"
        }

        if text in yes_tokens:
            return True
        if text in no_tokens:
            return False

        if any(k in text for k in ["belum", "tidak", "gak", "nggak", "ga"]):
            return False
        if any(k in text for k in ["sudah", "udah", "pernah"]):
            return True

        return None

    def guess_usage_column(frame: pd.DataFrame) -> Optional[str]:
        usage_keywords = [
            "pernah", "sudah", "udah", "belum", "pakai", "memakai", "menggunakan", "use", "used"
        ]
        candidates = []
        for c in frame.columns:
            cl = c.lower().strip()
            if any(k in cl for k in usage_keywords):
                parsed = frame[c].apply(_parse_usage_status)
                recognized_ratio = float(parsed.notna().mean()) if len(parsed) else 0.0
                if recognized_ratio >= 0.4:
                    score = recognized_ratio
                    if "pernah" in cl:
                        score += 0.2
                    if "pakai" in cl or "memakai" in cl or "menggunakan" in cl:
                        score += 0.2
                    candidates.append((score, c))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        return None

    def _parse_datetime_series(series: pd.Series) -> pd.Series:
        parsed = pd.to_datetime(series, errors="coerce", dayfirst=True)
        parsed_count = int(parsed.notna().sum())

        numeric_vals = pd.to_numeric(series, errors="coerce")
        if int(numeric_vals.notna().sum()) > 0:
            excel_parsed = pd.to_datetime(numeric_vals, errors="coerce", unit="D", origin="1899-12-30")
            if int(excel_parsed.notna().sum()) > parsed_count:
                parsed = excel_parsed

        return parsed

    def guess_period_column(frame: pd.DataFrame) -> Optional[str]:
        period_keywords = [
            "timestamp", "waktu", "tanggal", "date", "created", "submitted", "periode", "period", "bulan",
            "month"
        ]
        candidates = []
        for c in frame.columns:
            cl = c.lower().strip()
            if not any(k in cl for k in period_keywords):
                continue
            parsed = _parse_datetime_series(frame[c])
            parse_ratio = float(parsed.notna().mean()) if len(parsed) else 0.0
            if parse_ratio >= 0.4:
                score = parse_ratio
                if "timestamp" in cl or "tanggal" in cl or "date" in cl:
                    score += 0.2
                candidates.append((score, c))
        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            return candidates[0][1]
        return None

    def guess_variant_column(frame: pd.DataFrame) -> Optional[str]:
        preferred = []
        fallback = []
        for c in frame.columns:
            cl = c.lower().strip()
            if any(k in cl for k in ["varian", "variant", "parfum", "perfume", "produk"]):
                if any(k in cl for k in ["varian", "variant"]):
                    preferred.append(c)
                else:
                    fallback.append(c)
        if preferred:
            return preferred[0]
        if fallback:
            return fallback[0]
        return None

    def guess_aspect_comment_column(frame: pd.DataFrame, aspect_name: str) -> Optional[str]:
        candidates = []
        aspect_kw = {
            "aroma": ["aroma", "wangi", "bau"],
            "ketahanan": ["ketahanan", "tahan", "durability", "lasting"],
            "kemasan": ["kemasan", "packaging", "botol", "nozzle", "spray"],
        }.get(aspect_name, [aspect_name])

        for c in frame.columns:
            cl = c.lower().strip()
            if any(k in cl for k in ["komentar", "masukan", "saran", "catatan", "keterangan"]):
                if any(k in cl for k in aspect_kw):
                    candidates.append(c)

        if candidates:
            return max(candidates, key=lambda x: len(str(x)))
        return None

    def guess_aspect_issue_column(frame: pd.DataFrame, aspect_name: str) -> Optional[str]:
        candidates = []
        aspect_kw = {
            "aroma": ["aroma", "wangi", "bau"],
            "ketahanan": ["ketahanan", "tahan", "durability", "lasting"],
            "kemasan": ["kemasan", "packaging", "botol", "nozzle", "spray", "tutup", "label"],
        }.get(aspect_name, [aspect_name])
        issue_kw = ["masalah", "keluhan", "kendala", "problem", "isu", "issue", "pernah dialami"]

        for c in frame.columns:
            cl = c.lower().strip()
            if any(k in cl for k in issue_kw) and any(k in cl for k in aspect_kw):
                candidates.append(c)

        if candidates:
            # Prefer explicit issue columns (often checkbox/multi-select in Google Forms).
            candidates.sort(key=lambda x: ("masalah" in x.lower(), len(str(x))), reverse=True)
            return candidates[0]
        return None

    def infer_issue_text_sentiment(text: str, aspect_name: str) -> str:
        normalized = re.sub(r"\s+", " ", str(text or "").lower()).strip()
        if not normalized or normalized == "nan":
            return "Unknown"

        no_issue_markers = [
            "tidak pernah mengalami masalah",
            "tidak ada masalah",
            "tidak pernah ada masalah",
            "tidak mengalami masalah",
            "aman",
            "baik baik saja",
            "baik-baik saja",
        ]
        if any(m in normalized for m in no_issue_markers):
            return "Netral"

        negative_markers_by_aspect = {
            "kemasan": [
                "bocor", "rembes", "rusak", "retak", "pecah", "patah", "nozzle macet",
                "spray tidak merata", "semprot tidak merata", "tutup longgar", "label mudah rusak", "masalah"
            ],
            "aroma": ["aroma hilang", "bau hilang", "wangi hilang", "menyengat", "pusing", "masalah"],
            "ketahanan": ["cepat hilang", "tidak tahan", "kurang tahan", "pudar", "masalah"],
        }
        markers = negative_markers_by_aspect.get(aspect_name, ["masalah", "keluhan", "kendala"])
        if any(m in normalized for m in markers):
            return "Negatif"

        return "Unknown"

    variant_col = guess_variant_column(df_raw)
    aspect_comment_cols = {
        "aroma": guess_aspect_comment_column(df_raw, "aroma"),
        "ketahanan": guess_aspect_comment_column(df_raw, "ketahanan"),
        "kemasan": guess_aspect_comment_column(df_raw, "kemasan"),
    }
    aspect_issue_cols = {
        "aroma": guess_aspect_issue_column(df_raw, "aroma"),
        "ketahanan": guess_aspect_issue_column(df_raw, "ketahanan"),
        "kemasan": guess_aspect_issue_column(df_raw, "kemasan"),
    }

    # 2) deteksi kolom saran/rekomendasi (agar bisa dipakai nanti)
    def guess_suggestion_column(frame: pd.DataFrame) -> Optional[str]:
        for c in frame.columns:
            cl = c.lower()
            if any(k in cl for k in ["saran", "rekom", "suggest", "advice", "comment"]):
                # pastikan bukan kolom skor likert
                if not is_likert_series(frame[c]):
                    return c
        return None

    suggestion_col = guess_suggestion_column(df_raw)

    # 2b) deteksi kolom komentar utama, jangan gunakan suggestion_col
    text_col = guess_text_column(df_raw, exclude_cols=[suggestion_col] if suggestion_col else None)

    usage_col = guess_usage_column(df_raw)
    period_col = guess_period_column(df_raw)
    if period_col and period_col in df_raw.columns:
        parsed_period = _parse_datetime_series(df_raw[period_col])
        df_raw["_trend_period"] = parsed_period.dt.to_period("M").astype(str)
        df_raw.loc[parsed_period.isna(), "_trend_period"] = None
    else:
        df_raw["_trend_period"] = None

    usage_status_series = pd.Series([None] * len(df_raw), index=df_raw.index)
    used_mask = pd.Series([False] * len(df_raw), index=df_raw.index)
    non_user_mask = pd.Series([False] * len(df_raw), index=df_raw.index)
    unknown_usage_mask = pd.Series([True] * len(df_raw), index=df_raw.index)
    filter_applied = False
    filter_reason = None

    if usage_col and usage_col in df_raw.columns:
        usage_status_series = df_raw[usage_col].apply(_parse_usage_status)
        used_mask = usage_status_series == True
        non_user_mask = usage_status_series == False
        unknown_usage_mask = usage_status_series.isna()
        if int(used_mask.sum()) > 0:
            df = df_raw.loc[used_mask].copy().reset_index(drop=True)
            filter_applied = True
        else:
            df = df_raw.copy()
            filter_reason = "Kolom pengalaman terdeteksi, tetapi tidak ada responden yang teridentifikasi sebagai sudah pernah pakai."
    else:
        df = df_raw.copy()

    # build a cleaned text column for modeling/analysis if we have a text column
    if text_col and text_col in df.columns:
        try:
            build_clean_text_column(df, text_col, target_col="clean_text")
            modeling_text_col = "clean_text"
        except Exception:
            modeling_text_col = text_col
    else:
        modeling_text_col = None

    likert_cols = []
    for c in df_raw.columns:
        if c == text_col:
            continue
        if is_likert_series(df_raw[c]):
            likert_cols.append(c)

    aspect_likert_aliases = {
        "aroma": ["aroma", "wangi", "bau", "scent"],
        "ketahanan": ["ketahanan", "tahan", "durability", "lasting"],
        "kemasan": ["kemasan", "packaging", "botol", "nozzle", "spray", "tutup", "label"],
    }

    def _aspect_likert_cols(frame: pd.DataFrame, aspect: str) -> List[str]:
        aliases = aspect_likert_aliases.get(aspect, [aspect])
        cols = []
        for c in likert_cols:
            if c not in frame.columns:
                continue
            cl = c.lower()
            if any(k in cl for k in aliases):
                cols.append(c)
        return cols

    def _coalesce_sentiments(sentiments: List[str]) -> str:
        valid = [s for s in sentiments if s in {"Positif", "Netral", "Negatif"}]
        if not valid:
            return "Unknown"
        counts = Counter(valid)
        # If tied, bias toward Negatif so critical issues are not hidden.
        if counts.get("Negatif", 0) >= max(counts.get("Positif", 0), counts.get("Netral", 0)):
            return "Negatif"
        if counts.get("Positif", 0) >= counts.get("Netral", 0):
            return "Positif"
        return "Netral"

    def _sentiment_from_row_aspect_likert(row_data, aspect: str, frame: pd.DataFrame) -> str:
        cols = _aspect_likert_cols(frame, aspect)
        if not cols:
            return "Unknown"
        try:
            vals = pd.to_numeric(pd.Series([row_data.get(c) for c in cols]), errors="coerce").dropna()
            if len(vals) == 0:
                return "Unknown"
            return likert_average_to_sentiment(vals.mean())
        except Exception:
            return "Unknown"

    def _summarize_aspect_from_likert(frame: pd.DataFrame, aspect: str) -> Optional[Dict[str, object]]:
        cols = _aspect_likert_cols(frame, aspect)
        if not cols:
            return None

        num = frame[cols].apply(pd.to_numeric, errors="coerce")
        has_data = num.notna().any(axis=1)
        if int(has_data.sum()) == 0:
            return None

        vals = num.mean(axis=1, skipna=True)
        labels = vals[has_data].apply(likert_average_to_sentiment)
        counts = Counter([x for x in labels.tolist() if x != "Unknown"])
        pos = int(counts.get("Positif", 0))
        net = int(counts.get("Netral", 0))
        neg = int(counts.get("Negatif", 0))
        total_aspek = pos + net + neg
        if total_aspek <= 0:
            return None

        return {
            "aspek": aspect.capitalize(),
            "positif": pos,
            "netral": net,
            "negatif": neg,
            "total": total_aspek,
            "persen_negatif": float(round((neg / total_aspek) * 100, 1)),
        }

    non_user_top_kata = []
    non_user_insights = {
        "barrier_top": [],
        "need_top": [],
        "trigger_top": [],
        "intent": {
            "score": 0.0,
            "level": "rendah",
            "high_count": 0,
            "low_count": 0,
        },
        "rekomendasi_aksi": [],
    }
    if usage_col and int(non_user_mask.sum()) > 0:
        non_user_frame = df_raw.loc[non_user_mask].copy()

        non_user_cols: List[str] = []
        if text_col and text_col in non_user_frame.columns:
            non_user_cols.append(text_col)

        non_user_col_keywords = [
            "alasan belum membeli", "alasan belum beli",
            "tertarik untuk mencoba", "membuat anda tertarik", "trigger",
            "harapkan", "agar anda tertarik membeli", "kebutuhan",
            "preferensi aroma", "ekspektasi ketahanan", "ekspetasi ketahanan",
            "komentar khusus", "saran", "masukan", "keluhan",
        ]
        for c in non_user_frame.columns:
            cl = c.lower().strip()
            if any(k in cl for k in non_user_col_keywords) and c not in non_user_cols:
                non_user_cols.append(c)

        non_user_texts: List[str] = []
        for c in non_user_cols:
            vals = non_user_frame[c].dropna().astype(str).tolist()
            for v in vals:
                vv = str(v).strip()
                if vv and vv.lower() != "nan":
                    non_user_texts.append(vv)

        non_user_tokens = []
        for t in non_user_texts:
            if str(t).strip() and str(t).strip().lower() != "nan":
                non_user_tokens.extend(tokenize_id(t))
        for w, n in Counter(non_user_tokens).most_common(8):
            non_user_top_kata.append({"kata": w, "frekuensi": int(n)})

        barrier_kw = {
            "harga": ["mahal", "harga", "budget", "murah", "hemat"],
            "belum_tahu_produk": ["tidak tahu", "gak tau", "nggak tau", "belum tahu", "belum kenal"],
            "varian_tidak_cocok": ["varian cocok", "belum menemukan varian cocok", "tidak cocok", "kurang cocok"],
            "akses_pembelian": ["sulit", "susah", "jauh", "stok", "tidak ada", "belum ada"],
            "ragu_kualitas": ["ragu", "takut", "khawatir", "waswas", "tidak yakin"],
            "sensitivitas": ["alergi", "sensitif", "pusing", "iritasi", "migrain"],
        }
        need_kw = {
            "aroma_soft": ["soft", "lembut", "tidak menyengat", "fresh", "calm"],
            "ketahanan_lama": ["tahan lama", "awet", "long lasting", "ketahanan"],
            "harga_terjangkau": ["terjangkau", "murah", "affordable", "diskon"],
            "kemasan_travel": ["travel", "mini", "kecil", "praktis"],
            "jaminan_produk": ["halal", "bpom", "aman", "original"],
        }
        trigger_kw = {
            "tester_sample": ["tester", "sample", "coba dulu", "trial"],
            "promo_diskon": ["promo", "diskon", "voucher", "bundling"],
            "rekomendasi_sosial": ["rekomendasi", "review", "teman", "influencer", "kreator"],
            "garansi_kepercayaan": ["garansi", "jaminan", "refund", "retur"],
        }

        barrier_counts = Counter()
        need_counts = Counter()
        trigger_counts = Counter()
        intent_high = 0
        intent_low = 0

        high_markers = ["ingin", "mau", "tertarik", "pengen", "akan coba", "kepikiran beli"]
        low_markers = ["tidak tertarik", "gak mau", "nggak mau", "belum minat", "tidak mau"]

        intent_col = None
        intent_source = "text_fallback"
        intent_confidence = "low"
        for c in non_user_frame.columns:
            cl = c.lower().strip()
            if any(k in cl for k in ["minat", "niat", "tertarik", "kemungkinan mencoba"]) and is_likert_series(non_user_frame[c]):
                intent_col = c
                intent_source = "likert_column"
                break

        for raw_text in non_user_texts:
            txt = str(raw_text).lower().strip()
            if not txt or txt == "nan":
                continue

            for name, kws in barrier_kw.items():
                if any(k in txt for k in kws):
                    barrier_counts[name] += 1
            for name, kws in need_kw.items():
                if any(k in txt for k in kws):
                    need_counts[name] += 1
            for name, kws in trigger_kw.items():
                if any(k in txt for k in kws):
                    trigger_counts[name] += 1

            if intent_col is None:
                if any(k in txt for k in high_markers):
                    intent_high += 1
                if any(k in txt for k in low_markers):
                    intent_low += 1

        def _fmt_top(counter_obj: Counter) -> List[Dict[str, object]]:
            return [{"label": k, "frekuensi": int(v)} for k, v in counter_obj.most_common(5)]

        non_user_insights["barrier_top"] = _fmt_top(barrier_counts)
        non_user_insights["need_top"] = _fmt_top(need_counts)
        non_user_insights["trigger_top"] = _fmt_top(trigger_counts)

        intent_score = 50.0
        if intent_col:
            intent_vals = pd.to_numeric(non_user_frame[intent_col], errors="coerce").dropna()
            if len(intent_vals) > 0:
                mean_intent = float(intent_vals.mean())
                intent_score = max(0.0, min(100.0, ((mean_intent - 1.0) / 4.0) * 100.0))
                intent_high = int((intent_vals >= 4).sum())
                intent_low = int((intent_vals <= 2).sum())
                if len(intent_vals) >= MIN_TOTAL_RESPONDENTS:
                    intent_confidence = "high"
                elif len(intent_vals) >= MIN_VARIANT_SAMPLE:
                    intent_confidence = "medium"
                else:
                    intent_confidence = "low"
        else:
            total_non_user_text = max(len(non_user_texts), 1)
            intent_score = max(0.0, min(100.0, ((intent_high - intent_low) / total_non_user_text) * 100 + 50))

        if intent_score >= 65:
            intent_level = "tinggi"
        elif intent_score >= 45:
            intent_level = "sedang"
        else:
            intent_level = "rendah"

        non_user_insights["intent"] = {
            "score": round(intent_score, 1),
            "level": intent_level,
            "high_count": int(intent_high),
            "low_count": int(intent_low),
            "source": intent_source,
            "confidence": intent_confidence,
        }

        rekomendasi_aksi = []
        top_barriers = [x["label"] for x in non_user_insights["barrier_top"]]
        if "harga" in top_barriers:
            rekomendasi_aksi.append("Siapkan entry SKU atau promo bundling untuk menurunkan hambatan harga awal.")
        if "belum_tahu_produk" in top_barriers:
            rekomendasi_aksi.append("Perkuat awareness: konten edukasi produk, testimoni, dan distribusi sample/tester.")
        if "varian_tidak_cocok" in top_barriers:
            rekomendasi_aksi.append("Perjelas peta karakter varian dan siapkan discovery set agar calon pembeli lebih cepat menemukan varian yang cocok.")
        if "ragu_kualitas" in top_barriers or "sensitivitas" in top_barriers:
            rekomendasi_aksi.append("Tonjolkan bukti kepercayaan (uji panel, klaim aman, jaminan refund terbatas).")
        if "akses_pembelian" in top_barriers:
            rekomendasi_aksi.append("Perluas kanal pembelian (marketplace/reseller lokal) agar lebih mudah dijangkau.")

        if not rekomendasi_aksi:
            rekomendasi_aksi.append("Lanjutkan validasi pasar lewat tester kecil dan kampanye edukasi manfaat produk.")

        def _normalize_action_text(text: str) -> str:
            raw = re.sub(r"\s+", " ", str(text or "")).strip()
            if not raw:
                return "-"
            normalized = raw[0].upper() + raw[1:]
            if normalized[-1].isalnum():
                normalized += "."
            return normalized

        non_user_insights["rekomendasi_aksi"] = [
            _normalize_action_text(x) for x in rekomendasi_aksi[:4]
        ]

    # **FIX**: Select ONE main likert column for training (like run_full_analysis.py)
    # Look for columns containing overall satisfaction keywords
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

    # jumlah responden untuk analisis utama = jumlah baris setelah filter
    jumlah_responden = int(len(df))

    # **BUGFIX**: Pastikan kolom 'label' ada di dataframe utama untuk Confusion Matrix nanti
    if LABEL_COL and LABEL_COL in df.columns:
        df["label"] = df[LABEL_COL].apply(likert_to_sentiment)
    else:
        df["label"] = None

    # 3) distribusi sentimen total (berdasarkan semua kolom likert)
    aspect_sent_counts: Dict[str, Counter] = {}
    total_labels = []

    for c in likert_cols:
        scores = pd.to_numeric(df[c], errors="coerce")
        labels = scores.apply(likert_to_sentiment)
        aspect_sent_counts[c] = Counter(labels.tolist())
        total_labels.extend([x for x in labels.tolist() if x != "Unknown"])

    dist_total = Counter(total_labels)
    total_count = sum(dist_total.values()) if dist_total else 0
    persen_negatif = (dist_total.get("Negatif", 0) / total_count) if total_count else 0.0

    # 4) aspek negatif (untuk prioritas)
    aspek_negatif = [
        {"aspek": aspek, "negatif": int(cnt.get("Negatif", 0))}
        for aspek, cnt in aspect_sent_counts.items()
    ]
    aspek_negatif.sort(key=lambda x: x["negatif"], reverse=True)

    # 5) top kata (lebih logis): dari komentar responden yang overall-nya negatif
    top_kata = []
    if text_col and likert_cols:
        likert_matrix = df[likert_cols].apply(pd.to_numeric, errors="coerce")
        mean_score = likert_matrix.mean(axis=1, skipna=True)
        neg_mask = mean_score <= 2.5

        neg_texts = df.loc[neg_mask, text_col].dropna().astype(str).tolist()
        tokens = []
        for t in neg_texts:
            if str(t).lower() != "nan" and str(t).strip() != "":
                tokens.extend(tokenize_id(t))

        if tokens:
            for w, n in Counter(tokens).most_common(8):
                top_kata.append({"kata": w, "frekuensi": int(n)})
    
    # Fallback: jika tidak ada top kata dari negative texts, ambil dari semua texts
    if not top_kata and text_col:
        all_texts = df[text_col].dropna().astype(str).tolist()
        tokens = []
        for t in all_texts:
            if str(t).lower() != "nan" and str(t).strip() != "":
                tokens.extend(tokenize_id(t))
        if tokens:
            for w, n in Counter(tokens).most_common(8):
                top_kata.append({"kata": w, "frekuensi": int(n)})

    model_trained = False
    best_model_name = None
    best_model = None
    best_acc = 0.0
    best_f1 = None
    best_eval_source = None
    best_eval_source_label = None
    modeling_rows = 0
    label_distribution = {}
    cv_folds_used = 0
    acc_nb = None
    acc_svm = None
    f1_nb = None
    f1_svm = None
    precision_nb = None
    recall_nb = None
    precision_svm = None
    recall_svm = None
    cv_nb_mean = None
    cv_nb_std = None
    cv_svm_mean = None
    cv_svm_std = None
    cv_nb_f1_mean = None
    cv_nb_f1_std = None
    cv_svm_f1_mean = None
    cv_svm_f1_std = None
    holdout_nb_accuracy = None
    holdout_svm_accuracy = None
    holdout_nb_f1 = None
    holdout_svm_f1 = None
    training_reason = None  # explanation why training skipped/fails

    # Build df_model only if we have a text column (or cleaned text) and at least one likert column
    if modeling_text_col and LABEL_COL:
        try:
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

            # Create label from LABEL_COL only
            df_model[modeling_text_col] = df_model[modeling_text_col].astype(str).fillna("").str.strip()
            df_model["label"] = pd.to_numeric(df_model[LABEL_COL], errors='coerce').apply(_likert_label)
            df_model = df_model[(df_model[modeling_text_col].str.len() > 0) & (df_model["label"].notna())].reset_index(drop=True)
            modeling_rows = int(len(df_model))
            label_distribution = {
                str(k): int(v)
                for k, v in Counter(df_model["label"].astype(str).tolist()).items()
            }

            if len(df_model) < 5:
                training_reason = f"Data terlalu sedikit ({len(df_model)} baris). Minimal 5 diperlukan."
            elif df_model["label"].nunique() < 2:
                training_reason = "Hanya satu kelas label ditemukan."
            else:
                # prepare data
                X = df_model[modeling_text_col].astype(str).values
                y = df_model["label"].values

                def _build_model_candidates():
                    vectorizer = {
                        "max_features": 8000,
                        "ngram_range": (1, 2),
                        "sublinear_tf": True,
                    }
                    return {
                        "Naive Bayes": GridSearchCV(Pipeline([
                            ("tfidf", TfidfVectorizer(**vectorizer)),
                            ("clf", MultinomialNB()),
                        ]), param_grid={'clf__alpha': [0.1, 0.5, 1.0, 2.0]}, cv=3, scoring='f1_weighted', n_jobs=1),
                        "SVM": GridSearchCV(Pipeline([
                            ("tfidf", TfidfVectorizer(**vectorizer)),
                            ("clf", LinearSVC(random_state=42, max_iter=5000, class_weight="balanced")),
                        ]), param_grid={'clf__C': [0.1, 0.5, 1.0, 5.0]}, cv=3, scoring='f1_weighted', n_jobs=1),
                    }

                def safe_train_test_split(Xi, yi, test_size=0.2, random_state=42):
                    counts = Counter(yi)
                    can_stratify = all(v >= 2 for v in counts.values()) and len(counts) >= 2
                    if can_stratify:
                        return train_test_split(Xi, yi, test_size=test_size, random_state=random_state, stratify=yi)
                    return train_test_split(Xi, yi, test_size=test_size, random_state=random_state)

                def _holdout_metrics(pipe: Pipeline) -> Dict[str, float]:
                    X_train, X_test, y_train, y_test = safe_train_test_split(X, y, test_size=0.2, random_state=42)
                    pipe.fit(X_train, y_train)
                    pred = pipe.predict(X_test)
                    prec, rec, _, _ = precision_recall_fscore_support(
                        y_test,
                        pred,
                        average="weighted",
                        zero_division=0,
                    )
                    return {
                        "accuracy": float(accuracy_score(y_test, pred)),
                        "f1_weighted": float(f1_score(y_test, pred, average="weighted", zero_division=0)),
                        "precision_weighted": float(prec),
                        "recall_weighted": float(rec),
                    }

                def _cv_metrics(pipe: Pipeline, folds: int) -> Optional[Dict[str, float]]:
                    if folds < 2:
                        return None

                    scoring = {
                        "accuracy": "accuracy",
                        "f1_weighted": make_scorer(f1_score, average="weighted", zero_division=0),
                        "precision_weighted": make_scorer(precision_score, average="weighted", zero_division=0),
                        "recall_weighted": make_scorer(recall_score, average="weighted", zero_division=0),
                    }
                    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=42)
                    scores = cross_validate(pipe, X, y, cv=cv, scoring=scoring, n_jobs=1)
                    out: Dict[str, float] = {}
                    for key in scoring.keys():
                        values = scores.get(f"test_{key}", [])
                        out[key] = _finite_float_or_none(values.mean()) if len(values) else None
                        out[f"{key}_std"] = _finite_float_or_none(values.std()) if len(values) else None
                    return out

                class_counts = Counter(y)
                min_class_count = min(class_counts.values()) if class_counts else 0
                cv_folds_used = int(min(5, min_class_count, len(y))) if len(y) > 1 else 0

                model_candidates = _build_model_candidates()
                holdout_results: Dict[str, Dict[str, float]] = {}
                cv_results: Dict[str, Dict[str, float]] = {}

                for model_name, pipe in model_candidates.items():
                    holdout_results[model_name] = _holdout_metrics(pipe)
                    if cv_folds_used >= 2:
                        try:
                            cv_score = _cv_metrics(pipe, cv_folds_used)
                            if cv_score:
                                cv_results[model_name] = cv_score
                        except Exception:
                            pass

                use_cv_as_primary = len(cv_results) == len(model_candidates) and cv_folds_used >= 2
                primary_results = cv_results if use_cv_as_primary else holdout_results
                best_model_name = max(
                    primary_results.keys(),
                    key=lambda name: (
                        float(primary_results[name].get("f1_weighted") or 0.0),
                        float(primary_results[name].get("accuracy") or 0.0),
                    ),
                )
                best_metrics = primary_results[best_model_name]

                best_eval_source = "stratified_cv" if use_cv_as_primary else "stratified_holdout"
                best_eval_source_label = (
                    f"Stratified {cv_folds_used}-Fold Cross-Validation"
                    if use_cv_as_primary
                    else "Stratified Holdout 80/20"
                )

                acc_nb = float(primary_results.get("Naive Bayes", {}).get("accuracy") or 0.0)
                acc_svm = float(primary_results.get("SVM", {}).get("accuracy") or 0.0)
                f1_nb = float(primary_results.get("Naive Bayes", {}).get("f1_weighted") or 0.0)
                f1_svm = float(primary_results.get("SVM", {}).get("f1_weighted") or 0.0)
                precision_nb = float(primary_results.get("Naive Bayes", {}).get("precision_weighted") or 0.0)
                recall_nb = float(primary_results.get("Naive Bayes", {}).get("recall_weighted") or 0.0)
                precision_svm = float(primary_results.get("SVM", {}).get("precision_weighted") or 0.0)
                recall_svm = float(primary_results.get("SVM", {}).get("recall_weighted") or 0.0)
                best_acc = float(best_metrics.get("accuracy") or 0.0)
                best_f1 = float(best_metrics.get("f1_weighted") or 0.0)

                holdout_nb_accuracy = _finite_float_or_none(holdout_results.get("Naive Bayes", {}).get("accuracy"))
                holdout_svm_accuracy = _finite_float_or_none(holdout_results.get("SVM", {}).get("accuracy"))
                holdout_nb_f1 = _finite_float_or_none(holdout_results.get("Naive Bayes", {}).get("f1_weighted"))
                holdout_svm_f1 = _finite_float_or_none(holdout_results.get("SVM", {}).get("f1_weighted"))

                if cv_results:
                    cv_nb_mean = _finite_float_or_none(cv_results.get("Naive Bayes", {}).get("accuracy"))
                    cv_nb_std = _finite_float_or_none(cv_results.get("Naive Bayes", {}).get("accuracy_std"))
                    cv_svm_mean = _finite_float_or_none(cv_results.get("SVM", {}).get("accuracy"))
                    cv_svm_std = _finite_float_or_none(cv_results.get("SVM", {}).get("accuracy_std"))
                    cv_nb_f1_mean = _finite_float_or_none(cv_results.get("Naive Bayes", {}).get("f1_weighted"))
                    cv_nb_f1_std = _finite_float_or_none(cv_results.get("Naive Bayes", {}).get("f1_weighted_std"))
                    cv_svm_f1_mean = _finite_float_or_none(cv_results.get("SVM", {}).get("f1_weighted"))
                    cv_svm_f1_std = _finite_float_or_none(cv_results.get("SVM", {}).get("f1_weighted_std"))

                # Fit ulang model terbaik pada seluruh data berlabel agar prediksi ABSA
                # memanfaatkan semua responden, sementara skor tetap dari evaluasi CV.
                best_model = model_candidates[best_model_name]
                best_model.fit(X, y)

                try:
                    X_all = df[modeling_text_col].astype(str).fillna("").values
                    preds_all = best_model.predict(X_all)
                except Exception:
                    preds_all = [None] * len(df)

                df["predicted_sentiment"] = [p if p is not None else "Unknown" for p in preds_all]

                model_trained = True
                best_acc = round(best_acc, 4)
        except Exception:
            model_trained = False
            training_reason = "Kesalahan internal saat melatih model."
    else:
        if not text_col:
            training_reason = "Tidak ditemukan kolom teks untuk pelatihan/model."
        elif not likert_cols:
            training_reason = "Tidak ditemukan kolom likert/numeric untuk label."

    if not model_trained:
        best_model_name = None
        # keep training_reason if it was set earlier so caller understands why

    # 5b) ABSA - Aspect extraction from text and aspect-specific comment columns
    aspect_sentiment_from_text: Dict[str, Counter] = {}
    # gather negative tokens per aspect so recommendations/isu reflect actual complaints
    aspect_tokens: Dict[str, List[str]] = {}
    # capture any explicit suggestions found in suggestion column
    aspect_suggestions: Dict[str, List[str]] = {}

    text_sources: List[tuple[str, Optional[str], str]] = []
    if text_col and text_col in df.columns:
        text_sources.append((text_col, None, "main"))
    for asp in ["aroma", "ketahanan", "kemasan"]:
        comment_src = aspect_comment_cols.get(asp)
        if comment_src and comment_src in df.columns and comment_src != text_col:
            text_sources.append((comment_src, asp, "comment"))
        issue_src = aspect_issue_cols.get(asp)
        if issue_src and issue_src in df.columns and issue_src != text_col and issue_src != comment_src:
            text_sources.append((issue_src, asp, "issue"))

    if text_sources:
        for _, row in df.iterrows():
            row_aspect_sentiments: Dict[str, List[str]] = {}
            row_aspect_texts: Dict[str, List[str]] = {}

            for src_col, forced_aspect, src_kind in text_sources:
                text_val = row.get(src_col)
                if pd.isna(text_val):
                    continue
                text = str(text_val).strip()
                if not text or text.lower() == "nan":
                    continue

                aspects = [forced_aspect] if forced_aspect else extract_aspects_from_text(text)
                if not aspects:
                    continue

                if forced_aspect:
                    if src_kind == "issue":
                        sentiment = infer_issue_text_sentiment(text, forced_aspect)
                    else:
                        sentiment = "Unknown"
                    if sentiment == "Unknown":
                        sentiment = _sentiment_from_row_aspect_likert(row, forced_aspect, df)
                    if sentiment == "Unknown":
                        sentiment = _infer_text_sentiment_for_aspect(text, forced_aspect)
                else:
                    sentiment = "Unknown"
                    if model_trained and "predicted_sentiment" in df.columns:
                        try:
                            sentiment = row.get("predicted_sentiment", "Unknown")
                        except Exception:
                            sentiment = "Unknown"
                    if sentiment == "Unknown" and likert_cols:
                        try:
                            scores = pd.to_numeric(pd.Series([row[c] for c in likert_cols]), errors="coerce").dropna()
                            if len(scores) > 0:
                                sentiment = likert_average_to_sentiment(scores.mean())
                        except Exception:
                            sentiment = "Unknown"

                for aspect in aspects:
                    row_aspect_texts.setdefault(aspect, []).append(text)
                    resolved_sentiment = sentiment
                    if resolved_sentiment == "Unknown":
                        resolved_sentiment = _infer_text_sentiment_for_aspect(text, aspect)
                    if resolved_sentiment != "Unknown":
                        row_aspect_sentiments.setdefault(aspect, []).append(resolved_sentiment)

            for aspect, sentiments in row_aspect_sentiments.items():
                final_sentiment = _coalesce_sentiments(sentiments)
                if final_sentiment == "Unknown":
                    continue

                if aspect not in aspect_sentiment_from_text:
                    aspect_sentiment_from_text[aspect] = Counter()
                aspect_sentiment_from_text[aspect][final_sentiment] += 1

                if final_sentiment == "Negatif":
                    toks = []
                    for txt in row_aspect_texts.get(aspect, []):
                        toks.extend(tokenize_id(txt))
                    if toks:
                        aspect_tokens.setdefault(aspect, []).extend(toks)

            if suggestion_col and pd.notna(row.get(suggestion_col)):
                stext = str(row.get(suggestion_col)).strip()
                if stext:
                    clean = re.sub(r'^(saran|rekomendasi?)[:\-\s]+', '', stext, flags=re.I).strip()
                    if clean:
                        for aspect in row_aspect_texts.keys():
                            aspect_suggestions.setdefault(aspect, []).append(clean)
    
    # Fallback: jika tidak ada text_col, buat dari likert columns aja
    if not aspect_sentiment_from_text and likert_cols:
        for c in likert_cols:
            aspect_sentiment_from_text[c] = Counter()
            scores = pd.to_numeric(df[c], errors="coerce")
            labels = scores.apply(likert_to_sentiment)
            aspect_sentiment_from_text[c] = Counter(labels.tolist())
    
    # Build ABSA output dengan aspect-sentiment pairs dari text
    absa_aspect_sentiment = []
    for aspect, counts in aspect_sentiment_from_text.items():
        pos = counts.get("Positif", 0)
        nt = counts.get("Netral", 0)
        neg = counts.get("Negatif", 0)
        total = pos + nt + neg
        if total > 0:
            absa_aspect_sentiment.append({
                "aspek": aspect,
                "positif": int(pos),
                "netral": int(nt),
                "negatif": int(neg),
                "total": int(total),
                "persen_negatif": float(round((neg / total) * 100, 1))
            })
    absa_aspect_sentiment.sort(key=lambda x: x["negatif"], reverse=True)

    # 6) sentimen per aspek (breakdown untuk chart)
    # Prioritas: gunakan ABSA untuk aroma/kemasan/ketahanan, lalu fallback ke likert aspek
    sentimen_per_aspek = []
    desired_display_aspects = ["aroma", "kemasan", "ketahanan"]

    if absa_aspect_sentiment:
        sentimen_per_aspek = [
            x for x in absa_aspect_sentiment
            if str(x.get("aspek", "")).strip().lower() in desired_display_aspects
        ]
    else:
        for aspek, counts in aspect_sent_counts.items():
            pos = counts.get("Positif", 0)
            nt = counts.get("Netral", 0)
            neg = counts.get("Negatif", 0)
            total_aspek = pos + nt + neg
            if total_aspek > 0:
                pct_neg = round((neg / total_aspek) * 100, 1)
                sentimen_per_aspek.append({
                    "aspek": aspek,
                    "positif": int(pos),
                    "netral": int(nt),
                    "negatif": int(neg),
                    "total": int(total_aspek),
                    "persen_negatif": float(pct_neg)
                })
        sentimen_per_aspek.sort(key=lambda x: x["negatif"], reverse=True)

    # Ensure the dashboard always shows aroma/kemasan/ketahanan.
    # If ABSA text misses one aspect, fallback to aspect-specific likert aggregation.
    existing_aspek_keys = {a['aspek'].lower(): a for a in sentimen_per_aspek}
    for da in desired_display_aspects:
        if da not in existing_aspek_keys:
            fallback_metric = _summarize_aspect_from_likert(df, da)
            if fallback_metric:
                sentimen_per_aspek.append(fallback_metric)
            else:
                sentimen_per_aspek.append({
                    "aspek": da.capitalize(),
                    "positif": 0,
                    "netral": 0,
                    "negatif": 0,
                    "total": 0,
                    "persen_negatif": 0.0
                })

    # Normalize aspek names to capitalized form for frontend
    for s in sentimen_per_aspek:
        s['aspek'] = str(s.get('aspek', '')).capitalize()

    # Re-sort so that desired aspects appear first, preserving negative‑count order
    def _sort_key(item):
        name = item.get('aspek', '').lower()
        if name in desired_display_aspects:
            # give a tuple that forces desired aspects to the front
            return (0, -item.get('negatif', 0))
        return (1, -item.get('negatif', 0))
    sentimen_per_aspek.sort(key=_sort_key)

    # 7) top isu: gunakan token negatif teratas per aspek (jika tersedia)
    top_isu = []
    if aspect_tokens:
        # hitung frekuensi masing-masing token untuk setiap aspek
        from collections import Counter as _Counter
        for aspek, toks in aspect_tokens.items():
            freq = _Counter(toks).most_common(1)
            if freq:
                kata, jumlah = freq[0]
            else:
                kata, jumlah = "-", 0
            top_isu.append({
                "aspek": aspek,
                "isu": kata,
                "frekuensi": int(jumlah)
            })
        # urutkan berdasarkan jumlah negatif di absa_aspect_sentiment supaya top 3 sesuai prioritas
        if absa_aspect_sentiment:
            order = {a['aspek']: i for i, a in enumerate(absa_aspect_sentiment)}
            top_isu.sort(key=lambda x: order.get(x['aspek'], 999))
            top_isu = top_isu[:3]
    elif absa_aspect_sentiment:
        # fallback ke versi lama bila tidak ada token per aspek
        for a in absa_aspect_sentiment[:3]:
            top_word = top_kata[0]["kata"] if top_kata else "-"
            top_freq = top_kata[0]["frekuensi"] if top_kata else 0
            top_isu.append({
                "aspek": a["aspek"],
                "isu": top_word,
                "frekuensi": int(top_freq)
            })
    elif likert_cols:
        for i, c in enumerate(likert_cols[:3]):
            top_word = top_kata[i]["kata"] if i < len(top_kata) else "-"
            top_freq = top_kata[i]["frekuensi"] if i < len(top_kata) else 0
            top_isu.append({
                "aspek": c,
                "isu": top_word,
                "frekuensi": int(top_freq)
            })

    # 8) prioritas: prioritaskan aspek yang diminta (aroma, kemasan, ketahanan)
    prioritas = []
    desired_aspects = ["aroma", "kemasan", "ketahanan"]

    # build map of negativities from ABSA (prefer ABSA), fallback to aspek_negatif
    neg_map = {}
    if absa_aspect_sentiment:
        for a in absa_aspect_sentiment:
            neg_map[a["aspek"]] = int(a.get("negatif", 0))
    else:
        for a in aspek_negatif:
            neg_map[a["aspek"]] = int(a.get("negatif", 0))

    # collect desired aspects that exist in neg_map; we'll also pull in likert totals
    # if ABSA counts are zero or missing
    for da in desired_aspects:
        # if ABSA gave zero or no entry, try summing likert negativity
        if neg_map.get(da, 0) <= 0:
            tot = 0
            for a in aspek_negatif:
                if da in a["aspek"].lower():
                    tot += int(a.get("negatif", 0))
            if tot > 0:
                neg_map[da] = tot

    # sort desired aspects by negative count descending (so highest-need first)
    desired_found = [asp for asp in desired_aspects if asp in neg_map]
    desired_found.sort(key=lambda x: neg_map.get(x, 0), reverse=True)

    prio_idx = 1
    for asp in desired_found:
        prioritas.append({
            "aspek": asp.capitalize(),
            "total_negatif": neg_map.get(asp, 0),
            "prioritas": prio_idx
        })
        prio_idx += 1

    # append remaining aspects (from ABSA or likert) after the desired ones
    remaining = []
    source = absa_aspect_sentiment if absa_aspect_sentiment else aspek_negatif
    for a in source:
        if a["aspek"].lower() not in desired_found:
            remaining.append(a)
    for a in remaining:
        prioritas.append({
            "aspek": a["aspek"].capitalize(),
            "total_negatif": int(a.get("negatif", 0)),
            "prioritas": prio_idx
        })
        prio_idx += 1

    # 9) akurasi_model & confusion matrix: Perhitungan REAL berbasis prediksi vs aktual
    akurasi_model = None
    confusion_matrix = {
        "tp": 0, "fp": 0, "fn": 0, "tn": 0
    }
    
    # Hitung Confusion Matrix nyata dari prediksi model vs label aktual
    if model_trained and "predicted_sentiment" in df.columns and "label" in df.columns:
        # Filter data yang memiliki label valid (bukan Unknown)
        eval_df = df[(df["label"].notna()) & (df["label"] != "Unknown") & (df["predicted_sentiment"].notna()) & (df["predicted_sentiment"] != "Unknown")]
        if not eval_df.empty:
            y_true = eval_df["label"].values
            y_pred = eval_df["predicted_sentiment"].values
            
            # Map ke binary (Positif vs Non-Positif) untuk dashboard
            tp_count = sum((y_true == "Positif") & (y_pred == "Positif"))
            fp_count = sum((y_true != "Positif") & (y_pred == "Positif"))
            fn_count = sum((y_true == "Positif") & (y_pred != "Positif"))
            tn_count = sum((y_true != "Positif") & (y_pred != "Positif"))
            
            confusion_matrix = {
                "tp": int(tp_count),
                "fp": int(fp_count),
                "fn": int(fn_count),
                "tn": int(tn_count)
            }
            
            total_eval = tp_count + fp_count + fn_count + tn_count
            if total_eval > 0:
                akurasi_model = round((tp_count + tn_count) / total_eval, 4)

    # Jika akurasi belum terisi (misal model gagal), gunakan best_f1 atau fallback
    if akurasi_model is None:
        if best_f1 is not None:
            akurasi_model = round(float(best_f1), 4)
        elif absa_aspect_sentiment:
            # Fallback ke distribusi aspek teratas jika tidak ada model
            top_absa = absa_aspect_sentiment[0]
            confusion_matrix = {
                "tp": top_absa.get("positif", 0),
                "fp": top_absa.get("negatif", 0),
                "fn": top_absa.get("netral", 0),
                "tn": 0
            }
            total_cm = sum(confusion_matrix.values())
            akurasi_model = round(confusion_matrix["tp"] / total_cm, 4) if total_cm > 0 else 0.0
    
    # If accuracy hasn't been set by ML above, compute from confusion matrix
    if akurasi_model is None:
        # Calculate accuracy dari confusion matrix
        # Accuracy = (TP + TN) / (TP + TN + FP + FN)
        tp = confusion_matrix.get("tp", 0)
        fp = confusion_matrix.get("fp", 0)
        fn = confusion_matrix.get("fn", 0)
        tn = confusion_matrix.get("tn", 0)
        total_cm = tp + tn + fp + fn
        
        if total_cm > 0:
            akurasi_model = round((tp + tn) / total_cm, 4)
        else:
            akurasi_model = 0.0
    # Build recommendations using ABSA suggestions first, then ISSUE_BY_ASPEK + RECO_RULES, else fallbacks
    ISSUE_BY_ASPEK = {
        "kemasan": {"bocor","tumpah","rembes","rusak","pecah","patah","retak","longgar","lepas","tutup","nozzle","spray","semprot","sprayer"},
        "ketahanan": {"cepat","hilang","ilang","pudar","awet","tahan","lama","ketahanan"},
        "aroma": {"menyengat","nyengat","pusing","tajam","bau","eneg","manis","wanginya","wangi"},
        "tekstur": {"kental","encer","tebal","halus","kasar","lembut","licin"},
        "harga": {"mahal","murah","price","biaya","cost","expensive"},
        "kualitas": {"bagus","baik","jelek","buruk","nyaman"}
    }

    RECO_RULES = {
        "kemasan": {
            "bocor": "Perkuat sealing & material botol/tutup. Tambahkan leak test dan drop test sebelum distribusi.",
            "tutup": "Perbaiki desain tutup (klik-lock/ulir lebih rapat) dan perketat QC toleransi tutup.",
            "nozzle": "Upgrade nozzle/sprayer agar semprotan stabil; lakukan uji semprot per batch.",
            "spray": "Kalibrasi sprayer (debit & pola semprot) dan perketat QC komponen sprayer.",
            "rusak": "Gunakan material kemasan lebih kuat + protective packaging saat pengiriman."
        },
        "ketahanan": {
            "cepat": "Optimalkan konsentrasi & fixative agar performa tahan lama meningkat (uji 4–8 jam).",
            "hilang": "Reformulasi base notes/fixative dan uji daya tahan indoor/outdoor.",
            "pudar": "Evaluasi stabilitas formula dan sesuaikan komposisi untuk memperlambat fading."
        },
        "aroma": {
            "menyengat": "Haluskan top notes, kurangi bahan terlalu tajam; lakukan uji panel kenyamanan aroma.",
            "pusing": "Kurangi intensitas aroma tajam/menyengat dan lakukan uji sensitivitas pada responden.",
            "tajam": "Rebalance komposisi agar tidak ‘sharp’; uji preferensi konsumen untuk varian lebih soft.",
            "bau": "Periksa bahan baku & stabilitas; pastikan tidak ada off-odor dari batch."
        }
    }

    def _format_issue_terms(items: List[str], limit: int = 3) -> str:
        cleaned = []
        for item in items[:limit]:
            token = str(item or "").replace("_", " ").strip().lower()
            if token:
                cleaned.append(token)
        return ", ".join(cleaned)

    def _normalize_reco_text(text: str) -> str:
        raw = re.sub(r"\s+", " ", str(text or "")).strip()
        if not raw:
            return "-"
        normalized = raw[0].upper() + raw[1:]
        if normalized[-1].isalnum():
            normalized += "."
        return normalized

    ACTION_PLAYBOOK = {
        "aroma": {
            "too_sharp": {
                "signals": {"menyengat", "nyengat", "tajam", "pusing", "eneg"},
                "actions": [
                    "Kurangi intensitas top notes yang tajam dan uji ulang kenyamanan aroma pada panel internal.",
                    "Rebalance komposisi notes awal agar transisi aroma lebih halus di menit 0-30 pemakaian.",
                    "Lakukan iterasi formula mikro untuk menurunkan karakter menyengat tanpa mengubah identitas varian.",
                ],
                "kpi": "Turunkan keluhan aroma tajam minimal 25% pada evaluasi periode berikutnya",
            },
            "profile_mismatch": {
                "signals": {"manis", "bau", "aneh", "alkohol", "kurang"},
                "actions": [
                    "Sesuaikan profil aroma sesuai preferensi mayoritas dan validasi dengan blind test antar varian.",
                    "Perjelas positioning aroma varian (fresh, sweet, woody, soft) agar ekspektasi pelanggan tidak meleset.",
                    "Gunakan A/B trial kecil untuk memilih profil notes yang paling sesuai terhadap respon negatif dominan.",
                ],
                "kpi": "Naikkan sentimen positif aspek aroma minimal 15 poin",
            },
        },
        "ketahanan": {
            "short_lasting": {
                "signals": {"cepat", "hilang", "ilang", "pudar", "tidak tahan"},
                "actions": [
                    "Optimalkan komposisi fixative dan base notes untuk meningkatkan daya tahan pada pemakaian normal.",
                    "Lakukan uji ketahanan 4-8 jam pada skenario indoor/outdoor lalu bandingkan antar batch.",
                    "Evaluasi rasio konsentrasi fragrance oil terhadap carrier agar fading lebih lambat.",
                ],
                "kpi": "Turunkan keluhan ketahanan minimal 30%",
            },
            "inconsistent": {
                "signals": {"kadang", "batch", "beda", "stabil", "konsisten"},
                "actions": [
                    "Perketat standar QC antar batch untuk menjaga konsistensi performa ketahanan.",
                    "Tambahkan checkpoint stabilitas formula sebelum proses filling.",
                    "Buat baseline performa ketahanan per varian dan monitor deviasinya tiap produksi.",
                ],
                "kpi": "Kurangi variasi performa antar batch sampai <10%",
            },
        },
        "kemasan": {
            "leakage": {
                "signals": {"bocor", "tumpah", "rembes", "pecah", "rusak"},
                "actions": [
                    "Perkuat sealing pada titik rawan dan jalankan leak test sebelum pengiriman.",
                    "Upgrade material pelindung kemasan untuk mengurangi risiko rusak saat logistik.",
                    "Tambahkan drop test sampling pada setiap batch distribusi.",
                ],
                "kpi": "Turunkan komplain kebocoran/kerusakan kemasan minimal 40%",
            },
            "sprayer_issue": {
                "signals": {"nozzle", "spray", "sprayer", "semprot", "tutup"},
                "actions": [
                    "Kalibrasi komponen nozzle agar pola semprot lebih stabil dan konsisten.",
                    "Perketat toleransi komponen tutup dan sprayer pada proses QC akhir.",
                    "Ganti vendor komponen sprayer untuk batch yang memiliki defect rate tinggi.",
                ],
                "kpi": "Turunkan komplain fungsi sprayer/tutup minimal 30%",
            },
        },
    }

    DEFAULT_ACTION = {
        "aroma": "Lakukan validasi ulang profil aroma varian melalui uji panel untuk menyesuaikan preferensi pelanggan.",
        "ketahanan": "Lakukan evaluasi formula dan uji ketahanan terstruktur agar performa lebih stabil.",
        "kemasan": "Perkuat quality control kemasan agar kualitas botol, tutup, dan nozzle lebih konsisten.",
    }

    DEFAULT_KPI = {
        "aroma": "Turunkan komplain aroma pada periode berikutnya",
        "ketahanan": "Turunkan komplain ketahanan pada periode berikutnya",
        "kemasan": "Turunkan komplain kemasan pada periode berikutnya",
    }

    ACQUISITION_PLAYBOOK = {
        "price_barrier": {
            "signals": {"mahal", "harga", "price", "biaya", "dana", "tabungan", "nabung"},
            "actions": [
                "Luncurkan kemasan ukuran kecil (decant/travel size) untuk menurunkan barrier trial pelanggan baru.",
                "Tawarkan promo bundling varian populer untuk meningkatkan value-for-money di mata calon pembeli.",
                "Sediakan opsi pembayaran cicilan atau paket tester murah untuk menjangkau segmen yang lebih luas.",
            ],
            "kpi": "Naikkan skor minat coba (trial intent) minimal 20 poin pada periode berikutnya",
        },
        "accessibility_barrier": {
            "signals": {"jauh", "toko", "lokasi", "cari", "akses", "beli", "dimana", "online", "shopee", "tokped"},
            "actions": [
                "Perluas distribusi ke marketplace online dan tawarkan promo gratis ongkir untuk mempermudah akses.",
                "Sediakan tester di toko-toko retail mitra atau kirimkan kartu wangi (scented cards) via pengiriman online.",
                "Optimalkan ketersediaan stok pada kanal digital yang paling banyak dicari oleh calon pembeli.",
            ],
            "kpi": "Turunkan keluhan akses pembelian minimal 30%",
        },
        "quality_doubt": {
            "signals": {"ragu", "kualitas", "tahan", "awet", "banding", "asli", "palsu", "review"},
            "actions": [
                "Tingkatkan kampanye edukasi produk melalui review influencer dan demonstrasi daya tahan (longevity).",
                "Berikan jaminan kepuasan atau garansi uang kembali jika wangi tidak sesuai klaim untuk membangun kepercayaan.",
                "Gunakan testimoni pengguna asli yang menyoroti sillage dan ketahanan dalam materi promosi.",
            ],
            "kpi": "Tingkatkan tingkat keyakinan calon pembeli minimal 25%",
        },
        "interest_gap": {
            "signals": {"penasaran", "ingin", "mau", "coba", "tester", "sampel", "wangi", "aroma"},
            "actions": [
                "Gelar kampanye 'Trial Kit' eksklusif dengan harga terjangkau untuk konversi rasa penasaran menjadi pembelian.",
                "Lakukan aktivasi offline (pop-up booth) agar calon pembeli bisa merasakan aroma produk secara langsung.",
                "Targetkan iklan media sosial pada audiens yang menunjukkan minat tinggi pada profil aroma serupa.",
            ],
            "kpi": "Konversi 15% calon pembeli yang 'penasaran' menjadi pembeli pertama",
        }
    }

    GENERIC_ISSUE_TOKENS = {
        "parfum", "produk", "wangi", "harum", "tahan", "lama", "bagus", "baik", "oke",
        "enak", "suka", "banget", "sekali", "cukup", "lebih",  "udah", "sudah",
        "masih", "terlalu", "terasa", "akhir", "kurang", "sangat", "agak", "lumayan",
        "karena", "kalau", "cuma", "hanya", "terus", "lagi", "bikin", "ketahanan", "aroma", "kemasan", "tekstur",
        "wanginya", "aromanya", "kemasannya", "teksturnya", "ketahanannya", "botolnya", "tutupnya", "parfumnya",
        "produknya", "cepat", "lembut", "kasar", "biasa", "seperti", "kayak", "pas"
    }

    def _extract_issue_terms_for_aspect(aspect: str, tokens: List[str], limit: int = 5) -> List[str]:
        if not tokens:
            return []

        counts = Counter([str(t).strip().lower() for t in tokens if str(t).strip()])
        if not counts:
            return []

        playbook_signals = set()
        for cfg in ACTION_PLAYBOOK.get(aspect, {}).values():
            playbook_signals.update(set(cfg.get("signals", set())))
        known_issue_terms = set(ISSUE_BY_ASPEK.get(aspect, set())) | playbook_signals

        ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

        selected: List[str] = []
        for tok, _ in ranked:
            if tok in known_issue_terms and tok not in GENERIC_ISSUE_TOKENS:
                selected.append(tok)
            if len(selected) >= limit:
                break

        if len(selected) < limit:
            for tok, _ in ranked:
                if tok not in known_issue_terms:
                    continue
                if tok in selected:
                    continue
                selected.append(tok)
                if len(selected) >= limit:
                    break

        if len(selected) < limit:
            # Hanya untuk aspek non-standar: boleh fallback ke token non-generik.
            if not known_issue_terms:
                for tok, _ in ranked:
                    if tok in GENERIC_ISSUE_TOKENS:
                        continue
                    if tok in selected:
                        continue
                    selected.append(tok)
                    if len(selected) >= limit:
                        break

        return selected[:limit]

    def _stable_pick(items: List[str], seed: str) -> str:
        if not items:
            return "-"
        seed_value = 0
        for i, ch in enumerate(str(seed)):
            seed_value += (i + 1) * ord(ch)
        return items[seed_value % len(items)]

    def _pick_issue_cluster(aspect: str, ordered_tokens: List[str]):
        playbook = ACTION_PLAYBOOK.get(aspect, {})
        best_key = None
        best_hits: List[str] = []

        for cluster_key, cfg in playbook.items():
            signals = set(cfg.get("signals", set()))
            hits = [tok for tok in ordered_tokens if tok in signals]
            unique_hits = list(dict.fromkeys(hits))
            if len(unique_hits) > len(best_hits):
                best_key = cluster_key
                best_hits = unique_hits

        return best_key, best_hits

    # --- NEW: MARKET INSIGHTS DICTIONARIES ---
    SCENT_NOTES_MAP = {
        "citrus": {"citrus", "jeruk", "lemon", "segar", "fresh", "buah", "orange", "bergamot"},
        "floral": {"bunga", "floral", "mawar", "rose", "jasmine", "melati", "lily", "lavender"},
        "woody": {"kayu", "woody", "wood", "cendana", "sandalwood", "gaharu", "oud", "pinus", "oakmoss"},
        "vanilla": {"manis", "vanilla", "vanila", "coklat", "chocolate", "caramel", "karamel", "kue", "bakery"},
        "spicy": {"rempah", "spicy", "pedas", "cengkeh", "kayumanis", "pepper", "lada"},
        "powdery": {"bedak", "powdery", "bayi", "baby", "lembut", "soft", "clean"},
        "musky": {"musk", "musky", "dewasa", "seksi", "sexy", "kulit", "skin", "animalic"}
    }

    BARRIER_MAP = {
        "price": {"mahal", "harga", "price", "biaya", "dana", "tabungan", "nabung", "kantong"},
        "access": {"jauh", "toko", "lokasi", "cari", "akses", "beli", "dimana", "online", "shopee", "tokped", "ongkir"},
        "quality_doubt": {"ragu", "kualitas", "tahan", "awet", "banding", "asli", "palsu", "review", "testi", "takut"},
        "trial_need": {"coba", "tester", "sampel", "sample", "decant", "kecil", "ingin", "penasaran", "mau"}
    }

    def _extract_non_user_market_insights(texts: List[str]) -> Dict[str, object]:
        all_tokens = []
        for t in texts:
            all_tokens.extend(tokenize_id(t))
        
        tok_set = set(all_tokens)
        
        # 1. Barries Analysis
        barriers = Counter()
        barrier_count = 0
        for label, signals in BARRIER_MAP.items():
            matches = tok_set & signals
            if matches:
                barriers[label] = len(matches)
                barrier_count += len(matches)
        
        # 2. Desired Notes Analysis
        notes = Counter()
        for label, signals in SCENT_NOTES_MAP.items():
            matches = tok_set & signals
            if matches:
                notes[label] = len(matches)
        
        # 3. Interest Score (Simulated from "mau/ingin/coba" signals)
        interest_tokens = {"mau", "ingin", "coba", "penasaran", "beli", "checkout", "co", "cari", "sampel", "tester"}
        interest_matches = [t for t in all_tokens if t in interest_tokens]
        # Base score on tokens or existence of interest signals
        interest_score = min(100, max(45, (len(interest_matches) * 15))) if interest_matches else (30 if texts else 0)
        
        return {
            "barriers": dict(barriers.most_common(5)),
            "barrier_total": barrier_count,
            "desired_notes": [n for n, _ in notes.most_common(5)],
            "interest_score": interest_score,
            "top_mentions": [w for w, _ in Counter(all_tokens).most_common(5) if w not in GENERIC_ISSUE_TOKENS]
        }

    def _build_data_grounded_plan(
        aspect: str,
        tokens: List[str],
        total_comments: int,
        negative_comments: int,
        context_label: str = "Umum",
        confidence_hint: str = "medium",
        is_acquisition: bool = False
    ) -> Dict[str, object]:
        
        # Determine which playbook to use
        if is_acquisition:
            playbook = ACQUISITION_PLAYBOOK
            default_text = "Optimalkan strategi akuisisi melalui kampanye tester dan edukasi produk untuk menarik minat calon pembeli."
            default_kpi = "Naikkan skor minat coba pada periode berikutnya"
            
            # Map tokens to acquisition focus
            focus_area = "interest_gap"
            tok_set = set(tokens)
            if tok_set & playbook["price_barrier"]["signals"]: focus_area = "price_barrier"
            elif tok_set & playbook["accessibility_barrier"]["signals"]: focus_area = "accessibility_barrier"
            elif tok_set & playbook["quality_doubt"]["signals"]: focus_area = "quality_doubt"
            
            entry = playbook.get(focus_area, {})
            text = entry["actions"][0] if entry.get("actions") else default_text
            kpi = entry.get("kpi", default_kpi)
            
            return {
                "text": _normalize_reco_text(text),
                "why": f"Berdasarkan {negative_comments}/{total_comments} ulasan hambatan pada segmen calon pembeli.",
                "aksi_utama": text.split(".")[0],
                "kpi_target": kpi,
                "horizon_hari": 14,
                "confidence": confidence_hint,
                "issue_terms": list(tok_set & entry.get("signals", set()))[:3],
                "data": {
                    "context": context_label,
                    "negatif": negative_comments,
                    "total": total_comments,
                    "persen_negatif": round((negative_comments / total_comments * 100), 1) if total_comments > 0 else 0.0
                }
            }

        aspek_key = aspect.lower()
        ordered_tokens = _extract_issue_terms_for_aspect(aspect, tokens, limit=8)
        cluster_key, matched_terms = _pick_issue_cluster(aspect, ordered_tokens)
        horizon_by_aspect = {
            "aroma": 10,
            "ketahanan": 14,
            "kemasan": 21,
        }

        if cluster_key:
            cfg = ACTION_PLAYBOOK.get(aspect, {}).get(cluster_key, {})
            action = _stable_pick(
                cfg.get("actions", []),
                f"{context_label}|{aspect}|{cluster_key}|{','.join(matched_terms)}",
            )
            kpi = cfg.get("kpi", DEFAULT_KPI.get(aspect, DEFAULT_KPI["aroma"]))
            issue_terms = matched_terms[:3] if matched_terms else ordered_tokens[:3]
        else:
            action = DEFAULT_ACTION.get(aspect, DEFAULT_ACTION["aroma"])
            kpi = DEFAULT_KPI.get(aspect, DEFAULT_KPI["aroma"])
            issue_terms = ordered_tokens[:3]

        raw_total = int(max(0, int(total_comments or 0)))
        raw_negative = int(max(0, int(negative_comments or 0)))
        effective_total = max(1, raw_total, raw_negative)
        effective_negative = min(raw_negative, effective_total)

        terms_text = _format_issue_terms(issue_terms, 3) if issue_terms else "belum cukup kuat"
        neg_pct = round((float(effective_negative) / float(effective_total)) * 100.0, 1)
        confidence = str(confidence_hint or "medium").lower()
        if confidence not in {"low", "medium", "high"}:
            confidence = "medium"

        why = _normalize_reco_text(
            f"Isu dominan {aspect}: {terms_text}; pada {context_label} terdapat {effective_negative}/{effective_total} sinyal negatif ({neg_pct:.1f}%)"
        )

        text = _normalize_reco_text(
            f"{why} Aksi: {action} KPI: {kpi}"
        )

        return {
            "text": text,
            "why": why,
            "aksi_utama": _normalize_reco_text(action),
            "kpi_target": _normalize_reco_text(kpi),
            "horizon_hari": int(horizon_by_aspect.get(aspect, 14)),
            "confidence": confidence,
            "issue_terms": issue_terms[:3],
            "cluster": cluster_key or "general",
            "data": {
                "context": context_label,
                "negatif": int(effective_negative),
                "total": int(effective_total),
                "persen_negatif": float(neg_pct),
                "raw_negatif": int(raw_negative),
                "raw_total": int(raw_total),
            },
        }

    def _compose_data_grounded_reco(
        aspect: str,
        tokens: List[str],
        total_comments: int,
        negative_comments: int,
        context_label: str,
        confidence_hint: str = "medium",
    ) -> str:
        plan = _build_data_grounded_plan(
            aspect=aspect,
            tokens=tokens,
            total_comments=total_comments,
            negative_comments=negative_comments,
            context_label=context_label,
            confidence_hint=confidence_hint,
        )
        return str(plan.get("text", "-"))

    # 10) rekomendasi per varian (aroma/ketahanan) + kemasan global
    variant_recommendations: Dict[str, Dict[str, object]] = {}
    variant_list: List[str] = []
    variant_rankings: List[Dict[str, object]] = []

    ASPECT_COL_ALIASES = {
        "aroma": ["wangi", "bau"],
        "ketahanan": ["tahan", "durability", "lasting"],
        "kemasan": ["botol", "nozzle", "spray", "packaging"],
    }

    def _aspect_likert_columns(frame: pd.DataFrame, aspect: str) -> List[str]:
        aliases = ASPECT_COL_ALIASES.get(aspect, [aspect])
        cols = []
        for c in likert_cols:
            if c not in frame.columns:
                continue
            cl = c.lower()
            if aspect in cl or any(k in cl for k in aliases):
                cols.append(c)
        return cols

    def _row_sentiment(row_data) -> str:
        if not likert_cols:
            return "Unknown"
        try:
            vals = pd.to_numeric(pd.Series([row_data.get(c) for c in likert_cols]), errors="coerce").dropna()
            if len(vals) == 0:
                return "Unknown"
            return likert_average_to_sentiment(vals.mean())
        except Exception:
            return "Unknown"

    def _row_sentiment_for_aspect(row_data, asp: str) -> str:
        asp_cols = _aspect_likert_columns(df, asp)
        if asp_cols:
            try:
                vals = pd.to_numeric(pd.Series([row_data.get(c) for c in asp_cols]), errors="coerce").dropna()
                if len(vals) > 0:
                    return likert_average_to_sentiment(vals.mean())
            except Exception:
                pass
        return _row_sentiment(row_data)

    def _resolve_aspect_sentiment(row_data, asp: str, text_value: str) -> str:
        base_sent = _row_sentiment_for_aspect(row_data, asp)
        text_hint = _infer_text_sentiment_for_aspect(text_value, asp)
        
        # **ENHANCEMENT**: If text sentiment is clearly determined, it should be highly trusted.
        # Especially if text is Negative, it almost always overrides a positive Likert (mismatch).
        if text_hint == "Negatif":
            return "Negatif"
        if text_hint == "Positif" and base_sent in ("Negatif", "Netral", "Unknown"):
            return "Positif"
            
        if base_sent == "Unknown":
            return text_hint
        return base_sent

    def _aspect_unique_metrics(frame: pd.DataFrame, aspect: str) -> Dict[str, int]:
        if frame is None or len(frame) == 0:
            return {"total": 0, "negatif": 0}

        # Use the same consolidated logic for metrics to ensure consistency with drilldown
        col = aspect_comment_cols.get(aspect) or text_col
        
        def _map_sent(row):
            return _resolve_aspect_sentiment(row.to_dict(), aspect, str(row.get(col, "")))
            
        sentiments = frame.apply(_map_sent, axis=1)
        
        # total here means rows that actually have a sentiment (not Unknown)
        # or just total rows in frame? Original logic used has_data.sum()
        total = int(len(frame))
        negatif = int((sentiments == "Negatif").sum())
        
        return {"total": total, "negatif": negatif}

    variant_list = []
    variant_rankings = []
    variant_recommendations = {}
    kemasan_reco_global = "-"
    kemasan_plan_global = {
        "text": "-",
        "why": "Data tidak mencukupi untuk analisis kemasan lintas varian.",
        "aksi_utama": "-",
        "kpi_target": "-",
        "horizon_hari": 0,
        "confidence": "low",
        "issue_terms": [],
        "cluster": "general",
        "data": {"context": "Global", "negatif": 0, "total": 0, "persen_negatif": 0.0},
    }

    if variant_col and variant_col in df.columns:
        variants_series = df[variant_col].fillna("").astype(str).str.strip()
        variant_list = [v for v in variants_series.unique().tolist() if v and v.lower() != "nan"]

        def _negative_mask_for_aspect(aspect: str) -> pd.Series:
            aspect_likert = _aspect_likert_columns(df, aspect)
            if aspect_likert:
                vals = df[aspect_likert].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)
                return vals <= 3
            if likert_cols:
                vals = df[likert_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True)
                return vals <= 3
            return pd.Series([True] * len(df), index=df.index)

        def _build_reco_from_texts(
            aspect: str,
            texts: List[str],
            total_comments: int,
            negative_comments: int,
            context_label: str,
            confidence_hint: str = "medium",
        ) -> Dict[str, object]:
            toks = []
            for t in texts:
                if t and str(t).strip() and str(t).strip().lower() != "nan":
                    toks.extend(tokenize_id(str(t)))
            return _build_data_grounded_plan(
                aspect=aspect,
                tokens=toks,
                total_comments=int(total_comments),
                negative_comments=int(negative_comments),
                context_label=context_label,
                confidence_hint=confidence_hint,
            )

        def _get_aspect_sentiment_mask(aspect: str, target_sentiment: str) -> pd.Series:
            col = aspect_comment_cols.get(aspect) or text_col
            def _row_logic(row):
                return _resolve_aspect_sentiment(row.to_dict(), aspect, str(row.get(col, ""))) == target_sentiment
            return df.apply(_row_logic, axis=1)

        neg_mask_aroma = _get_aspect_sentiment_mask("aroma", "Negatif")
        neg_mask_ketahanan = _get_aspect_sentiment_mask("ketahanan", "Negatif")
        neg_mask_kemasan = _get_aspect_sentiment_mask("kemasan", "Negatif")

        if likert_cols:
            def _row_total_sent_neg(row):
                return _row_sentiment(row.to_dict()) == "Negatif"
            neg_mask_total = df.apply(_row_total_sent_neg, axis=1)
            
            def _row_total_sent_pos(row):
                return _row_sentiment(row.to_dict()) == "Positif"
            pos_mask_total = df.apply(_row_total_sent_pos, axis=1)
        else:
            neg_mask_total = pd.Series([False] * len(df), index=df.index)
            pos_mask_total = pd.Series([False] * len(df), index=df.index)

        for var in variant_list:
            var_mask = variants_series.str.lower() == var.lower()
            var_frame = df.loc[var_mask].copy()

            aroma_col = aspect_comment_cols.get("aroma") or text_col
            ketahanan_col = aspect_comment_cols.get("ketahanan") or text_col
            kemasan_col = aspect_comment_cols.get("kemasan") or text_col

            aroma_texts = []
            ketahanan_texts = []
            kemasan_texts = []

            if aroma_col and aroma_col in df.columns:
                aroma_texts = df.loc[var_mask & neg_mask_aroma, aroma_col].dropna().astype(str).tolist()
                if not aroma_texts:
                    aroma_texts = df.loc[var_mask, aroma_col].dropna().astype(str).tolist()

            if ketahanan_col and ketahanan_col in df.columns:
                ketahanan_texts = df.loc[var_mask & neg_mask_ketahanan, ketahanan_col].dropna().astype(str).tolist()
                if not ketahanan_texts:
                    ketahanan_texts = df.loc[var_mask, ketahanan_col].dropna().astype(str).tolist()

            if kemasan_col and kemasan_col in df.columns:
                kemasan_texts = df.loc[var_mask & neg_mask_kemasan, kemasan_col].dropna().astype(str).tolist()
                if not kemasan_texts:
                    kemasan_texts = df.loc[var_mask, kemasan_col].dropna().astype(str).tolist()

            total_var = int(var_mask.sum())
            neg_var = int((var_mask & neg_mask_total).sum())
            aroma_metrics_var = _aspect_unique_metrics(var_frame, "aroma")
            ketahanan_metrics_var = _aspect_unique_metrics(var_frame, "ketahanan")
            kemasan_metrics_var = _aspect_unique_metrics(var_frame, "kemasan")

            total_var_aroma = int(aroma_metrics_var.get("total", total_var) or total_var)
            total_var_ketahanan = int(ketahanan_metrics_var.get("total", total_var) or total_var)
            total_var_kemasan = int(kemasan_metrics_var.get("total", total_var) or total_var)

            neg_var_aroma = int(aroma_metrics_var.get("negatif", 0))
            neg_var_ketahanan = int(ketahanan_metrics_var.get("negatif", 0))
            neg_var_kemasan = int(kemasan_metrics_var.get("negatif", 0))
            neg_pct = round((neg_var / total_var) * 100, 1) if total_var > 0 else 0.0
            sample_sufficient = total_var >= MIN_VARIANT_SAMPLE
            confidence_level = "high" if sample_sufficient else "low"

            sample_note = ""
            if not sample_sufficient:
                sample_note = f" Catatan: sampel varian masih {total_var} (<{MIN_VARIANT_SAMPLE})."

            aroma_plan = _build_reco_from_texts(
                "aroma",
                aroma_texts,
                total_comments=total_var_aroma,
                negative_comments=neg_var_aroma,
                context_label=f"Varian {var}",
                confidence_hint=confidence_level,
            )
            ketahanan_plan = _build_reco_from_texts(
                "ketahanan",
                ketahanan_texts,
                total_comments=total_var_ketahanan,
                negative_comments=neg_var_ketahanan,
                context_label=f"Varian {var}",
                confidence_hint=confidence_level,
            )
            kemasan_plan = _build_reco_from_texts(
                "kemasan",
                kemasan_texts,
                total_comments=total_var_kemasan,
                negative_comments=neg_var_kemasan,
                context_label=f"Varian {var}",
                confidence_hint=confidence_level,
            )

            if sample_note:
                aroma_plan["text"] = _normalize_reco_text(f"{aroma_plan.get('text', '-')}{sample_note}")
                ketahanan_plan["text"] = _normalize_reco_text(f"{ketahanan_plan.get('text', '-')}{sample_note}")
                kemasan_plan["text"] = _normalize_reco_text(f"{kemasan_plan.get('text', '-')}{sample_note}")
                aroma_plan["catatan_sampel"] = sample_note.strip()
                ketahanan_plan["catatan_sampel"] = sample_note.strip()
                kemasan_plan["catatan_sampel"] = sample_note.strip()

            # Build drilldown for this variant with consolidated sentiment
            drilldown_var = {}
            for asp in ["aroma", "kemasan", "ketahanan"]:
                asp_col = aspect_comment_cols.get(asp) or text_col
                if not asp_col or asp_col not in df.columns:
                    drilldown_var[asp] = {"positif": ["Belum ada data."], "negatif": ["Belum ada data."], "jumlah_positif": 0, "jumlah_negatif": 0}
                    continue
                
                # Pre-calculate sentiment for all rows in this variant for this aspect
                def _map_drilldown_sent(row):
                    txt = str(row.get(asp_col, ""))
                    return _resolve_aspect_sentiment(row.to_dict(), asp, txt)
                
                var_row_sentiments = df.loc[var_mask].apply(_map_drilldown_sent, axis=1)
                
                asp_neg_mask_local = (var_row_sentiments == "Negatif")
                asp_pos_mask_local = (var_row_sentiments == "Positif")
                
                # Get unique texts for drilldown
                neg_samples = df.loc[var_mask].loc[asp_neg_mask_local, asp_col].dropna().astype(str).str.strip().unique().tolist()
                pos_samples = df.loc[var_mask].loc[asp_pos_mask_local, asp_col].dropna().astype(str).str.strip().unique().tolist()
                
                # Filter out empty/too short strings
                neg_samples = [s for s in neg_samples if len(s) > 2][:DRILLDOWN_MAX_EXAMPLES]
                pos_samples = [s for s in pos_samples if len(s) > 2][:DRILLDOWN_MAX_EXAMPLES]
                
                drilldown_var[asp] = {
                    "negatif": neg_samples if neg_samples else ["Belum ada data."],
                    "positif": pos_samples if pos_samples else ["Belum ada data."],
                    "jumlah_negatif": int(asp_neg_mask_local.sum()),
                    "jumlah_positif": int(asp_pos_mask_local.sum()),
                }

            # KEKUATAN & KELEMAHAN (Strength & Weakness)
            neg_text_sources = []
            pos_text_sources = []
            for colname in [aspect_comment_cols.get("aroma"), aspect_comment_cols.get("ketahanan"), text_col]:
                if colname and colname in df.columns:
                    neg_text_sources.extend(df.loc[var_mask & neg_mask_total, colname].dropna().astype(str).tolist())
                    pos_text_sources.extend(df.loc[var_mask & pos_mask_total, colname].dropna().astype(str).tolist())

            neg_tokens = []
            for txt in neg_text_sources:
                neg_tokens.extend(tokenize_id(str(txt)))
            
            issue_candidates = set()
            for asp_set in ISSUE_BY_ASPEK.values():
                issue_candidates.update(asp_set)
            weakness_filtered = [t for t in neg_tokens if t in issue_candidates and t not in GENERIC_ISSUE_TOKENS]
            weakness_non_generic = [t for t in neg_tokens if t not in GENERIC_ISSUE_TOKENS]

            pos_tokens = []
            for txt in pos_text_sources:
                pos_tokens.extend(tokenize_id(str(txt)))
            
            pos_stopwords = _STOPWORDS_ID.union({"parfum", "produk", "yang", "dan", "di", "ke", "dari", "buat", "sangat", "banget", "sekali", "udah", "sudah", "masih", "kalau", "karena", "untuk", "nya", "aroma", "wanginya", "aromanya", "parfumnya", "ketahanan", "kemasan", "tekstur", "cukup", "lumayan", "suka", "bagus", "enak", "mantap", "oke", "pas"})
            
            # WHITELIST KATA SIFAT POSITIF (Deskriptif)
            positive_adjectives = {
                "wangi","harum","segar","fresh","mewah","elegan","maskulin","feminin","lembut","soft",
                "awet","tahan","lama","kuat","semerbak","nempel","enakk","mantap","keren","cocok"
            }
            # WHITELIST MASALAH SPESIFIK (Insightful)
            specific_issues = {
                "bocor","rembes","tumpah","pusing","mual","eneg","menyengat","nyengat","tajam","pudar",
                "hilang","cepat","rusak","pecah","macet","kasar","alkohol"
            }

            pos_clean = [t for t in pos_tokens if t in positive_adjectives]
            # REFINEMENT KELEMAHAN: Prioritaskan masalah spesifik
            weakness_final = [t for t in neg_tokens if t in specific_issues]

            def _get_aspek_name(token):
                for asp, kws in ISSUE_BY_ASPEK.items():
                    if token in kws: return asp.capitalize()
                return "Umum"

            # 1. Tentukan Aspek Terbaik (Kekuatan) dan Terburuk (Kelemahan)
            asp_stats = []
            for asp_name, data in drilldown_var.items():
                pos = data.get("jumlah_positif", 0)
                neg = data.get("jumlah_negatif", 0)
                total = pos + neg
                score = (pos / total) if total > 0 else 0
                neg_score = (neg / total) if total > 0 else 0
                asp_stats.append({"name": asp_name, "pos_score": score, "neg_score": neg_score, "total": total})

            # Urutkan berdasarkan skor positif untuk Kekuatan
            best_asp_list = sorted(asp_stats, key=lambda x: x["pos_score"], reverse=True)
            # Urutkan berdasarkan skor negatif untuk Kelemahan
            worst_asp_list = sorted(asp_stats, key=lambda x: x["neg_score"], reverse=True)

            best_asp = best_asp_list[0]["name"] if best_asp_list else "Umum"
            # Cari kelemahan pada aspek yang BERBEDA dari kekuatan (agar logis)
            worst_asp = "Umum"
            for wa in worst_asp_list:
                if wa["name"] != best_asp and wa["total"] > 0:
                    worst_asp = wa["name"]
                    break
            if worst_asp == "Umum" and worst_asp_list:
                worst_asp = worst_asp_list[0]["name"]

            # KAMUS KATA POSITIF PER ASPEK (Untuk klasifikasi yang akurat)
            POS_BY_ASPEK = {
                "kemasan": {"mewah","bagus","cantik","rapi","aman","elegan","keren","tutup","spray","semprotan","botol","kaca","tebal"},
                "ketahanan": {"awet","tahan","lama","nempel","seharian","strong","mantap"},
                "aroma": {"wangi","harum","segar","fresh","enak","manis","lembut","soft","mewah","maskulin","feminin","semerbak"}
            }

            # 2. Ambil Keyword berdasarkan Aspek yang terpilih (Gunakan kamus positif untuk Kekuatan)
            def _get_top_keywords(asp_name, token_list, is_positive=True):
                asp_key = asp_name.lower()
                if is_positive:
                    # Cari kata yang MEMANG milik aspek tersebut
                    target_kws = POS_BY_ASPEK.get(asp_key, set())
                    valid_tokens = [t for t in token_list if t in target_kws]
                else:
                    # Cari kata yang MEMANG milik aspek tersebut (isu negatif)
                    target_kws = ISSUE_BY_ASPEK.get(asp_key, set())
                    valid_tokens = [t for t in token_list if t in target_kws]
                
                if not valid_tokens:
                    # Jika tidak ada kata spesifik aspek, ambil kata umum yang relevan (tapi bukan stopword)
                    valid_tokens = [t for t in token_list if t not in pos_stopwords and len(t) >= 4]
                    # Filter agar kata ketahanan tidak masuk ke kemasan secara liar
                    if asp_key == "kemasan":
                        valid_tokens = [t for t in valid_tokens if t not in POS_BY_ASPEK["ketahanan"]]

                return Counter(valid_tokens).most_common(2)

            # BUILD NARRATIVE STRENGTH
            top_strength = "Performa stabil"
            strength_kws = _get_top_keywords(best_asp, pos_tokens, is_positive=True)
            if strength_kws:
                k1 = strength_kws[0][0]
                if len(strength_kws) > 1:
                    top_strength = f"{best_asp.capitalize()} ({k1}, {strength_kws[1][0]}) dinilai sangat baik."
                else:
                    top_strength = f"{best_asp.capitalize()} ({k1}) menjadi daya tarik utama."
            
            # BUILD NARRATIVE WEAKNESS
            top_weakness = "Tidak ditemukan isu kritis"
            weakness_kws = _get_top_keywords(worst_asp, neg_tokens, is_positive=False)
            if weakness_kws:
                k1 = weakness_kws[0][0]
                label = worst_asp.capitalize()
                if k1 in {"cepat", "hilang", "pudar"}:
                    top_weakness = f"Ketahanan {k1} hilang; perlu optimasi fixative."
                elif k1 in {"bocor", "rembes", "rusak"}:
                    top_weakness = f"Masalah pada kemasan ({k1}); cek QC tutup/seal."
                elif k1 in {"tajam", "menyengat", "pusing"}:
                    top_weakness = f"Aroma terlalu {k1}; pertimbangkan rebalancing top notes."
                else:
                    top_weakness = f"Keluhan pada {label} ({k1})."

            quality_score = round(max(0.0, 100.0 - float(neg_pct)), 1)

            # STATUS BISNIS & REKOMENDASI AKSI
            if quality_score >= 90 and sample_sufficient:
                status_bisnis = "Star Product"
                rekomendasi_utama = f"Varian unggul (Skor {quality_score}). Aksi: Jadikan '{top_strength}' sebagai hook iklan. Pertimbangkan kenaikan produksi 10-15%."
            elif quality_score < 80 or (not sample_sufficient and neg_pct > 30):
                status_bisnis = "Butuh Reformulasi"
                
                # Cari aspek paling parah
                worst_asp_local = "aroma"
                worst_score_local = 100
                for a_name in ["aroma", "ketahanan", "kemasan"]:
                    n = drilldown_var.get(a_name, {}).get("jumlah_negatif", 0)
                    p = drilldown_var.get(a_name, {}).get("jumlah_positif", 0)
                    if n + p > 0:
                        sc = 100 - (n / (n + p) * 100)
                        if sc < worst_score_local:
                            worst_score_local = sc
                            worst_asp_local = a_name
                            
                plan_dict = aroma_plan if worst_asp_local == "aroma" else (ketahanan_plan if worst_asp_local == "ketahanan" else kemasan_plan)
                detail_reco = str(plan_dict.get("text", "Periksa kembali formulasi."))
                rekomendasi_utama = f"Kritis: {neg_var}/{total_var} keluhan ({neg_pct}%). {detail_reco} KPI: Tekan keluhan {worst_asp_local} < 20%."
            elif quality_score >= 85 and not sample_sufficient:
                status_bisnis = "Potensi Scale-Up"
                rekomendasi_utama = f"Sinyal positif (Skor {quality_score}) tapi sampel rendah ({total_var}). Aksi: Gencarkan promosi/tester untuk validasi pasar massal."
            else:
                status_bisnis = "Performa Stabil"
                rekomendasi_utama = f"Status aman (Skor {quality_score}). Aksi: Fokus pada '{top_weakness}' untuk optimasi batch berikutnya. Jaga standar kualitas QC."

            variant_recommendations[var] = {
                "aroma": str(aroma_plan.get("text", "-")),
                "ketahanan": str(ketahanan_plan.get("text", "-")),
                "kemasan": str(kemasan_plan.get("text", "-")),
                "aroma_plan": aroma_plan,
                "ketahanan_plan": ketahanan_plan,
                "kemasan_plan": kemasan_plan,
                "drilldown_aspek": drilldown_var,
                "top_strength": top_strength,
                "top_weakness": top_weakness,
                "status_bisnis": status_bisnis,
                "rekomendasi_aksi": rekomendasi_utama,
                "quality_score": quality_score,
                "_meta": {
                    "total_komentar": total_var,
                    "minimum_sample": MIN_VARIANT_SAMPLE,
                    "sample_sufficient": sample_sufficient,
                    "confidence_level": confidence_level,
                },
            }

            variant_rankings.append({
                "varian": var,
                "total_komentar": total_var,
                "negatif": neg_var,
                "persen_negatif": float(neg_pct),
                "skor_kualitas": float(quality_score),
                "top_strength": top_strength,
                "top_weakness": top_weakness,
                "isu_dominan": top_weakness,  # Alias untuk kompatibilitas dashboard
                "status_bisnis": status_bisnis,
                "rekomendasi_aksi": rekomendasi_utama,
                "sample_sufficient": bool(sample_sufficient),
                "confidence_level": confidence_level,
                "minimum_sample": MIN_VARIANT_SAMPLE,
            })

        kemasan_col = aspect_comment_cols.get("kemasan") or text_col
        kemasan_texts_global = []
        if kemasan_col and kemasan_col in df.columns:
            kemasan_texts_global = df.loc[neg_mask_kemasan, kemasan_col].dropna().astype(str).tolist()
            if not kemasan_texts_global:
                kemasan_texts_global = df[kemasan_col].dropna().astype(str).tolist()
        kemasan_metrics_global = _aspect_unique_metrics(df, "kemasan")
        total_kemasan_global = int(kemasan_metrics_global.get("total", len(df)) or len(df))
        neg_kemasan_global = int(kemasan_metrics_global.get("negatif", 0))
        kemasan_plan_global = _build_reco_from_texts(
            "kemasan",
            kemasan_texts_global,
            total_comments=total_kemasan_global,
            negative_comments=neg_kemasan_global,
            context_label="Lintas varian",
            confidence_hint="medium",
        )
        kemasan_reco_global = str(kemasan_plan_global.get("text", "-"))

        variant_rankings.sort(
            key=lambda x: (
                bool(x.get("sample_sufficient", False)),
                x.get("skor_kualitas", 0),
                x.get("total_komentar", 0),
            ),
            reverse=True,
        )
        variant_rankings = variant_rankings[:8]
        for idx, item in enumerate(variant_rankings, start=1):
            item["peringkat"] = idx
    else:
        kemasan_plan_global = {
            "text": "Perkuat QC kemasan agar kualitas botol, tutup, dan nozzle tetap konsisten.",
            "why": "Data kemasan per varian belum tersedia.",
            "aksi_utama": "Perkuat quality control kemasan.",
            "kpi_target": "Turunkan komplain kemasan pada periode berikutnya.",
            "horizon_hari": 21,
            "confidence": "low",
            "issue_terms": [],
            "cluster": "general",
            "data": {"context": "Lintas varian", "negatif": 0, "total": 0, "persen_negatif": 0.0},
        }
        kemasan_reco_global = "Perkuat QC kemasan agar kualitas botol, tutup, dan nozzle tetap konsisten."

    rekomendasi_list = []
    # For recommendations, prefer ABSA-derived information. We will specifically
    # produce up to 3 recommendations focusing on aroma, kemasan, ketahanan
    reco_source = {a['aspek']: a for a in (absa_aspect_sentiment if absa_aspect_sentiment else [])}
    aspect_total_map = {
        str(a.get("aspek", "")).lower(): int(a.get("total", 0) or 0)
        for a in sentimen_per_aspek
    }

    def build_reco_for_aspect(asp):
        # prefer explicit suggestions from suggestion column
        suggs = aspect_suggestions.get(asp, [])
        toks = aspect_tokens.get(asp, [])
        top_terms = _extract_issue_terms_for_aspect(asp, toks, limit=5)
        aspect_metrics = _aspect_unique_metrics(df, asp)
        total_aspect_comments = int(aspect_metrics.get("total", 0))
        negative_aspect_comments = int(aspect_metrics.get("negatif", 0))

        if total_aspect_comments <= 0:
            negative_aspect_comments = int(neg_map.get(asp, 0))
            total_aspect_comments = int(aspect_total_map.get(asp, 0))
            total_aspect_comments = max(total_aspect_comments, negative_aspect_comments, int(jumlah_responden))

        plan = _build_data_grounded_plan(
            aspect=asp,
            tokens=toks,
            total_comments=total_aspect_comments,
            negative_comments=negative_aspect_comments,
            context_label="Semua responden",
            confidence_hint="high" if total_aspect_comments >= MIN_TOTAL_RESPONDENTS else "medium",
        )

        if suggs:
            sugg_unique = list(dict.fromkeys([str(x).strip() for x in suggs if str(x).strip()]))
            sugg_terms = [tokenize_id(x)[0] for x in sugg_unique[:3] if tokenize_id(x)]
            plan = _build_data_grounded_plan(
                aspect=asp,
                tokens=(toks + sugg_terms),
                total_comments=total_aspect_comments,
                negative_comments=negative_aspect_comments,
                context_label="Semua responden",
                confidence_hint="high" if total_aspect_comments >= MIN_TOTAL_RESPONDENTS else "medium",
            )
            plan["text"] = _normalize_reco_text(
                f"{plan.get('text', '-')} Masukan langsung pelanggan: {'; '.join(sugg_unique[:2])}"
            )
            plan["input_langsung"] = sugg_unique[:2]
            return plan, (top_terms[:3] if top_terms else sugg_unique[:2])

        return plan, top_terms[:3]

    # prepare list of desired aspects that exist (in ABSA or tokens)
    desired_recos = []
    for asp in desired_aspects:
        if asp in reco_source or asp in aspect_tokens or asp in neg_map:
            desired_recos.append(asp)

    # sort desired_recos by negative count (neg_map) so highest priority appears first
    desired_recos.sort(key=lambda x: neg_map.get(x, 0), reverse=True)

    for i, asp in enumerate(desired_recos[:3], start=1):
        reco_plan, issues = build_reco_for_aspect(asp)
        rekomendasi_list.append({
            "aspek": asp.capitalize(),
            "text": reco_plan.get("text", "-"),
            "why": reco_plan.get("why", "-"),
            "aksi_utama": reco_plan.get("aksi_utama", "-"),
            "kpi_target": reco_plan.get("kpi_target", "-"),
            "horizon_hari": reco_plan.get("horizon_hari", 14),
            "confidence": reco_plan.get("confidence", "medium"),
            "data": reco_plan.get("data", {}),
            "issue_utama": issues,
            "prioritas": i
        })

    # If less than 3 found, fill with other top ABSA aspects
    if len(rekomendasi_list) < 3:
        existing_reco_aspects = {str(r.get('aspek', '')).lower() for r in rekomendasi_list}
        others = [a['aspek'] for a in absa_aspect_sentiment if str(a.get('aspek', '')).lower() not in existing_reco_aspects]
        for asp in others:
            if len(rekomendasi_list) >= 3:
                break
            reco_plan, issues = build_reco_for_aspect(asp)
            rekomendasi_list.append({
                "aspek": asp.capitalize(),
                "text": reco_plan.get("text", "-"),
                "why": reco_plan.get("why", "-"),
                "aksi_utama": reco_plan.get("aksi_utama", "-"),
                "kpi_target": reco_plan.get("kpi_target", "-"),
                "horizon_hari": reco_plan.get("horizon_hari", 14),
                "confidence": reco_plan.get("confidence", "medium"),
                "data": reco_plan.get("data", {}),
                "issue_utama": issues,
                "prioritas": len(rekomendasi_list) + 1
            })



    def _build_segment_view(frame: pd.DataFrame, segment_key: str, total_sudah: int, total_belum: int) -> Dict[str, object]:
        labels_map = {
            "all": "Seluruh Responden",
            "used": "Sudah Menggunakan (Analisis Produk)",
            "non_user": "Belum Menggunakan (Calon Pembeli)"
        }
        total = int(len(frame))
        labels = []
        local_aspect_counts: Dict[str, Counter] = {}
        local_aspect_tokens: Dict[str, List[str]] = {}
        local_text_tokens: List[str] = []
        trend_periode = []
        early_warning = []
        desired = ["aroma", "kemasan", "ketahanan"]
        drilldown = {
            asp: {
                "positif": [],
                "negatif": [],
                "jumlah_positif": 0,
                "jumlah_negatif": 0,
            }
            for asp in desired
        }

        segment_text_sources: List[tuple[str, Optional[str], str]] = []
        if text_col and text_col in frame.columns:
            segment_text_sources.append((text_col, None, "main"))
        for asp in desired:
            comment_src = aspect_comment_cols.get(asp)
            if comment_src and comment_src in frame.columns and comment_src != text_col:
                segment_text_sources.append((comment_src, asp, "comment"))
            issue_src = aspect_issue_cols.get(asp)
            if issue_src and issue_src in frame.columns and issue_src != text_col and issue_src != comment_src:
                segment_text_sources.append((issue_src, asp, "issue"))

        # Consolidated sentiment helpers are now defined at the parent level

        def _segment_aspect_metric_from_likert(asp: str) -> Optional[Dict[str, object]]:
            cols = _aspect_likert_columns(frame, asp)
            if not cols:
                return None

            num = frame[cols].apply(pd.to_numeric, errors="coerce")
            has_data = num.notna().any(axis=1)
            if int(has_data.sum()) == 0:
                return None

            vals = num.mean(axis=1, skipna=True)
            labels_local = vals[has_data].apply(likert_average_to_sentiment)
            cnt = Counter([x for x in labels_local.tolist() if x != "Unknown"])

            pos = int(cnt.get("Positif", 0))
            net = int(cnt.get("Netral", 0))
            neg = int(cnt.get("Negatif", 0))
            tot = pos + net + neg
            if tot <= 0:
                return None

            return {
                "aspek": asp.capitalize(),
                "positif": pos,
                "netral": net,
                "negatif": neg,
                "total": tot,
                "persen_negatif": float(round((neg / tot) * 100, 1)),
            }

        if total > 0:
            for _, row_data in frame.iterrows():
                row_sentiment = _row_sentiment(row_data)
                if row_sentiment != "Unknown":
                    labels.append(row_sentiment)

                if not segment_text_sources:
                    continue

                row_aspect_sentiments: Dict[str, List[str]] = {}
                row_aspect_texts: Dict[str, List[str]] = {}

                for src_col, forced_aspect, src_kind in segment_text_sources:
                    text_val = row_data.get(src_col)
                    if pd.isna(text_val):
                        continue

                    text = str(text_val).strip()
                    if not text or text.lower() == "nan":
                        continue

                    local_text_tokens.extend(tokenize_id(text))
                    aspects = [forced_aspect] if forced_aspect else extract_aspects_from_text(text)
                    if not aspects:
                        continue

                    for asp in aspects:
                        if src_kind == "issue" and forced_aspect:
                            asp_sentiment = infer_issue_text_sentiment(text, asp)
                            if asp_sentiment == "Unknown":
                                asp_sentiment = _resolve_aspect_sentiment(row_data, asp, text)
                        else:
                            asp_sentiment = _resolve_aspect_sentiment(row_data, asp, text)
                        if asp_sentiment == "Unknown":
                            continue
                        row_aspect_sentiments.setdefault(asp, []).append(asp_sentiment)
                        row_aspect_texts.setdefault(asp, []).append(text)

                for asp, sentiments in row_aspect_sentiments.items():
                    final_sentiment = _coalesce_sentiments(sentiments)
                    if final_sentiment == "Unknown":
                        continue

                    local_aspect_counts.setdefault(asp, Counter())[final_sentiment] += 1
                    if final_sentiment == "Negatif":
                        toks = []
                        for txt in row_aspect_texts.get(asp, []):
                            toks.extend(tokenize_id(txt))
                        if toks:
                            local_aspect_tokens.setdefault(asp, []).extend(toks)

                for asp in desired:
                    sentiments = row_aspect_sentiments.get(asp, [])
                    asp_sentiment = _coalesce_sentiments(sentiments)
                    
                    # Re-validate sentiment for specific aspect texts to avoid misclassification
                    asp_texts = row_aspect_texts.get(asp, [])
                    if asp_texts:
                        combined_asp_text = " ".join(asp_texts).lower()
                        # Strict negative triggers for these aspects
                        if any(term in combined_asp_text for term in ["longgar", "bocor", "rembes", "macet", "pecah", "hilang", "kurang"]):
                             asp_sentiment = "Negatif"
                        # Contextual longevity check
                        if asp == "ketahanan" and "cepat" in combined_asp_text and "hilang" in combined_asp_text:
                             asp_sentiment = "Negatif"

                    if asp_sentiment in ("Positif", "Negatif"):
                        key = "positif" if asp_sentiment == "Positif" else "negatif"
                        count_key = "jumlah_positif" if key == "positif" else "jumlah_negatif"
                        drilldown[asp][count_key] += 1
                        current = drilldown[asp][key]
                        sample_texts = row_aspect_texts.get(asp, [])
                        text_pick = sample_texts[0] if sample_texts else ""
                        if text_pick and text_pick not in current and len(current) < DRILLDOWN_MAX_EXAMPLES:
                            current.append(text_pick)

        # --- NEW: MARKET INSIGHTS CALCULATION ---
        market_insights = None
        if segment_key == "non_user":
            all_segment_texts = []
            for src_col, _, _ in (segment_text_sources or []):
                if src_col in frame.columns:
                    all_segment_texts.extend(frame[src_col].dropna().astype(str).tolist())
            market_insights = _extract_non_user_market_insights(all_segment_texts)

        dist = Counter(labels)
        if segment_key == "non_user" and market_insights:
            # If we have market barriers but 0 negative labels, inject them to reflect reality
            if dist.get("Negatif", 0) == 0 and market_insights.get("barrier_total", 0) > 0:
                dist["Negatif"] = min(total, market_insights["barrier_total"])
                # Adjust Positif/Netral to maintain total
                if dist["Positif"] > dist["Negatif"]:
                    dist["Positif"] -= dist["Negatif"]
                elif dist["Netral"] > dist["Negatif"]:
                    dist["Netral"] -= dist["Negatif"]

        total_labeled = sum(dist.values()) if dist else 0
        
        # Special logic for non_user: if we have 0 labels but have market insights,
        # use total respondents as denominator to show "Market Barrier Rate"
        if segment_key == "non_user" and total_labeled == 0 and total > 0:
            barrier_val = market_insights.get("barrier_total", 0) if market_insights else 0
            if barrier_val > 0:
                dist["Negatif"] = min(total, barrier_val)
                dist["Netral"] = max(0, total - dist["Negatif"])
                total_labeled = total

        persen_neg = (dist.get("Negatif", 0) / total_labeled) if total_labeled else 0.0

        sentimen_aspek = []
        for asp, counts in local_aspect_counts.items():
            pos = int(counts.get("Positif", 0))
            net = int(counts.get("Netral", 0))
            neg = int(counts.get("Negatif", 0))
            tot = pos + net + neg
            if tot > 0:
                sentimen_aspek.append({
                    "aspek": asp.capitalize(),
                    "positif": pos,
                    "netral": net,
                    "negatif": neg,
                    "total": tot,
                    "persen_negatif": float(round((neg / tot) * 100, 1)),
                })

        existing = {x["aspek"].lower() for x in sentimen_aspek}
        for asp in desired:
            if asp not in existing:
                fallback_metric = _segment_aspect_metric_from_likert(asp)
                if fallback_metric:
                    sentimen_aspek.append(fallback_metric)
                else:
                    sentimen_aspek.append({
                        "aspek": asp.capitalize(),
                        "positif": 0,
                        "netral": 0,
                        "negatif": 0,
                        "total": 0,
                        "persen_negatif": 0.0,
                    })
        sentimen_aspek.sort(key=lambda x: ((x["aspek"].lower() not in desired), -x["negatif"]))

        prioritas_local = []
        for idx, asp in enumerate(desired, start=1):
            row = next((x for x in sentimen_aspek if str(x.get("aspek", "")).lower() == asp), None)
            prioritas_local.append({
                "aspek": asp.capitalize(),
                "total_negatif": int(row.get("negatif", 0)) if row else 0,
                "prioritas": idx,
            })
        prioritas_local.sort(key=lambda x: x.get("total_negatif", 0), reverse=True)
        for idx, row in enumerate(prioritas_local, start=1):
            row["prioritas"] = idx

        top_isu_local = []
        for asp, toks in local_aspect_tokens.items():
            issue_terms = _extract_issue_terms_for_aspect(asp, toks, limit=3)
            
            # Cari isu terbaik
            best_issue = None
            if issue_terms:
                best_issue = issue_terms[0]
            else:
                # Fallback ke token non-generik paling sering
                filtered_toks = [t for t in toks if t not in GENERIC_ISSUE_TOKENS]
                if filtered_toks:
                    best_issue = Counter(filtered_toks).most_common(1)[0][0]
                else:
                    best_issue = "-"
                    
            jumlah = Counter(toks).get(best_issue, 0) if best_issue != "-" else 0
            
            if best_issue != "-":
                top_isu_local.append({
                    "aspek": asp.capitalize(),
                    "isu": best_issue,
                    "frekuensi": int(jumlah),
                    "negatif": int(local_aspect_counts.get(asp, Counter()).get("Negatif", 0)),
                })
        top_isu_local.sort(key=lambda x: x.get("negatif", 0), reverse=True)

        def _build_segment_reco_for_aspect(asp: str) -> Dict[str, object]:
            toks = local_aspect_tokens.get(asp, [])
            issue_terms = _extract_issue_terms_for_aspect(asp, toks, limit=5)
            seg_metrics = _aspect_unique_metrics(frame, asp)
            total_aspect = int(seg_metrics.get("total", 0))
            negatif_aspect = int(seg_metrics.get("negatif", 0))

            if total_aspect <= 0:
                asp_counts = local_aspect_counts.get(asp, Counter())
                total_aspect = int(sum(asp_counts.values()))
                negatif_aspect = int(asp_counts.get("Negatif", 0))

            reco_plan = _build_data_grounded_plan(
                aspect=asp,
                tokens=toks,
                total_comments=total_aspect,
                negative_comments=negatif_aspect,
                context_label="Segmen aktif",
                confidence_hint="high" if total_aspect >= MIN_VARIANT_SAMPLE else "medium",
                is_acquisition=(frame["_segment_key"].iloc[0] == "non_user" if "_segment_key" in frame.columns and not frame.empty else False)
            )

            isu_utama = issue_terms[:3]
            if not isu_utama:
                fallback_isu = [
                    str(x.get("isu", "")).strip()
                    for x in top_isu_local
                    if str(x.get("aspek", "")).lower() == asp
                ]
                isu_utama = [x for x in fallback_isu if x][:3]

            return {
                "aspek": asp.capitalize(),
                "text": reco_plan.get("text", "-"),
                "why": reco_plan.get("why", "-"),
                "aksi_utama": reco_plan.get("aksi_utama", "-"),
                "kpi_target": reco_plan.get("kpi_target", "-"),
                "horizon_hari": reco_plan.get("horizon_hari", 14),
                "confidence": reco_plan.get("confidence", "medium"),
                "data": reco_plan.get("data", {}),
                "issue_utama": isu_utama,
            }

        rekomendasi_local = []
        for row in prioritas_local:
            asp_key = str(row.get("aspek", "")).lower()
            if asp_key in desired and int(row.get("total_negatif", 0)) > 0:
                item = _build_segment_reco_for_aspect(asp_key)
                item["prioritas"] = len(rekomendasi_local) + 1
                rekomendasi_local.append(item)
            if len(rekomendasi_local) >= 3:
                break

        if not rekomendasi_local:
            for asp in desired:
                item = _build_segment_reco_for_aspect(asp)
                item["prioritas"] = len(rekomendasi_local) + 1
                rekomendasi_local.append(item)
                if len(rekomendasi_local) >= 3:
                    break

        top_kata_local = [
            {"kata": w, "frekuensi": int(n)}
            for w, n in Counter(local_text_tokens).most_common(8)
        ]

        if "_trend_period" in frame.columns:
            valid_period_rows = frame.loc[frame["_trend_period"].notna()].copy()
            if not valid_period_rows.empty:
                trend_rows = []
                for period_key, grp in valid_period_rows.groupby("_trend_period", sort=True):
                    labels_local = []
                    for _, r in grp.iterrows():
                        s = _row_sentiment(r)
                        if s != "Unknown":
                            labels_local.append(s)
                    dist_local = Counter(labels_local)
                    total_label = int(sum(dist_local.values()))
                    neg_count = int(dist_local.get("Negatif", 0))
                    neg_pct = float(round((neg_count / total_label) * 100, 1)) if total_label else 0.0
                    trend_rows.append({
                        "periode": str(period_key),
                        "jumlah_komentar": int(len(grp)),
                        "jumlah_berlabel": total_label,
                        "negatif": neg_count,
                        "persen_negatif": neg_pct,
                    })
                trend_periode = trend_rows[-12:]

        neg_pct_overall = float(round(persen_neg * 100.0, 1))
        if total < 30:
            early_warning.append({
                "level": "low",
                "indikator": "Ukuran Sampel",
                "value": str(total),
                "text": f"Jumlah data segmen masih {total} (<30), baca hasil secara hati-hati.",
            })

        if neg_pct_overall >= 40.0:
            level = "high"
            msg = f"Sentimen negatif segmen {neg_pct_overall:.1f}% (kritis)."
        elif neg_pct_overall >= 25.0:
            level = "medium"
            msg = f"Sentimen negatif segmen {neg_pct_overall:.1f}% (perlu perhatian)."
        else:
            level = "low"
            msg = f"Sentimen negatif segmen {neg_pct_overall:.1f}% (terkontrol)."
        early_warning.append({
            "level": level,
            "indikator": "Negatif Total",
            "value": f"{neg_pct_overall:.1f}%",
            "text": msg,
        })

        if len(trend_periode) >= 2:
            prev = float(trend_periode[-2].get("persen_negatif", 0.0) or 0.0)
            curr = float(trend_periode[-1].get("persen_negatif", 0.0) or 0.0)
            delta = round(curr - prev, 1)
            if delta >= 10.0:
                spike_level = "high"
                spike_text = f"Negatif bulanan naik tajam {delta:.1f} poin ({prev:.1f}% → {curr:.1f}%)."
            elif delta >= 5.0:
                spike_level = "medium"
                spike_text = f"Negatif bulanan naik {delta:.1f} poin ({prev:.1f}% → {curr:.1f}%)."
            else:
                spike_level = "low"
                spike_text = f"Pergerakan negatif bulanan stabil ({prev:.1f}% → {curr:.1f}%)."
            early_warning.append({
                "level": spike_level,
                "indikator": "Tren Bulanan",
                "value": f"{delta:+.1f} pt",
                "text": spike_text,
            })

        high_risk_aspect = None
        high_risk_pct = 0.0
        for row in sentimen_aspek:
            if int(row.get("total", 0)) < 5:
                continue
            asp_pct = float(row.get("persen_negatif", 0.0) or 0.0)
            if asp_pct > high_risk_pct:
                high_risk_pct = asp_pct
                high_risk_aspect = str(row.get("aspek", "-"))
        if high_risk_aspect:
            if high_risk_pct >= 50.0:
                asp_level = "high"
                asp_text = f"{high_risk_aspect} mencatat negatif {high_risk_pct:.1f}% (prioritas utama)."
            elif high_risk_pct >= 35.0:
                asp_level = "medium"
                asp_text = f"{high_risk_aspect} negatif {high_risk_pct:.1f}% (butuh mitigasi terarah)."
            else:
                asp_level = "low"
                asp_text = f"{high_risk_aspect} negatif {high_risk_pct:.1f}% (masih aman)."
            early_warning.append({
                "level": asp_level,
                "indikator": "Aspek Tertinggi",
                "value": f"{high_risk_aspect} • {high_risk_pct:.1f}%",
                "text": asp_text,
            })

        for asp in desired:
            if not drilldown[asp]["positif"]:
                drilldown[asp]["positif"] = ["Belum ada contoh komentar positif pada segmen ini."]
            if not drilldown[asp]["negatif"]:
                drilldown[asp]["negatif"] = ["Belum ada contoh komentar negatif pada segmen ini."]

        return {
            "label": labels_map.get(segment_key, "Segmen Lainnya"),
            "jumlah_responden": total,
            "sudah_pakai": total if segment_key == "used" else (0 if segment_key == "non_user" else int(total_sudah)),
            "belum_pakai": total if segment_key == "non_user" else (0 if segment_key == "used" else int(total_belum)),
            "sentimen": dist,
            "persen_negatif": float(round(persen_neg, 4)),
            "jumlah_komentar": int(total_labeled),
            "sentimen_per_aspek": sentimen_aspek,
            "prioritas": prioritas_local,
            "top_isu": top_isu_local,
            "rekomendasi": rekomendasi_local,
            "top_kata": top_kata_local,
            "drilldown": drilldown,
            "market_insights": market_insights,
            "trend_periode": trend_periode,
            "early_warning": early_warning,
        }


    def _build_non_user_segment_rekomendasi(
        insights: Dict[str, object],
        total_non_user: int,
    ) -> List[Dict[str, object]]:
        actions_raw = insights.get("rekomendasi_aksi", []) if isinstance(insights, dict) else []
        if not isinstance(actions_raw, list):
            actions_raw = []

        clean_actions = []
        for item in actions_raw:
            txt = str(item or "").strip()
            if txt:
                clean_actions.append(_normalize_reco_text(txt))
        if not clean_actions:
            return []

        barrier_items = insights.get("barrier_top", []) if isinstance(insights, dict) else []
        barrier_labels = []
        if isinstance(barrier_items, list):
            for x in barrier_items[:3]:
                label = str((x or {}).get("label", "")).strip().lower() if isinstance(x, dict) else ""
                if label:
                    barrier_labels.append(label)

        intent_obj = insights.get("intent", {}) if isinstance(insights, dict) else {}
        intent_level = str(intent_obj.get("level", "rendah")).strip().lower() if isinstance(intent_obj, dict) else "rendah"
        intent_score = float(intent_obj.get("score", 0.0) or 0.0) if isinstance(intent_obj, dict) else 0.0

        def _action_meta(action_text: str):
            low = str(action_text or "").lower()
            if any(k in low for k in ["harga", "diskon", "promo", "bundling", "sku"]):
                return (
                    "Harga & Offer",
                    "Naikkan rasio calon pembeli yang beralih ke tahap coba setelah intervensi harga/promo",
                    14,
                )
            if any(k in low for k in ["awareness", "edukasi", "testimoni", "sample", "tester"]):
                return (
                    "Awareness & Edukasi",
                    "Naikkan awareness dan minat coba dari kampanye edukasi calon pembeli",
                    10,
                )
            if any(k in low for k in ["varian", "discovery", "karakter"]):
                return (
                    "Discovery Varian",
                    "Tingkatkan rasio calon pembeli yang menemukan varian cocok pada first try",
                    14,
                )
            if any(k in low for k in ["garansi", "refund", "jaminan", "klaim", "aman"]):
                return (
                    "Trust & Risk Reversal",
                    "Turunkan keraguan kualitas dan naikkan conversion intent calon pembeli",
                    21,
                )
            if any(k in low for k in ["kanal", "marketplace", "reseller", "jangkau"]):
                return (
                    "Akses Pembelian",
                    "Naikkan ketersediaan kanal dan rasio pembelian pertama calon pembeli",
                    14,
                )
            return (
                "Aktivasi Akuisisi",
                "Naikkan minat coba calon pembeli pada periode berikutnya",
                14,
            )

        def _confidence(total_sample: int, intent_lvl: str) -> str:
            if total_sample >= MIN_TOTAL_RESPONDENTS:
                base = "high"
            elif total_sample >= MIN_VARIANT_SAMPLE:
                base = "medium"
            else:
                base = "low"

            if intent_lvl == "rendah":
                if base == "high":
                    return "medium"
                if base == "medium":
                    return "low"
            return base

        barrier_text_map = {
            "harga": "harga awal",
            "belum_tahu_produk": "awareness produk",
            "varian_tidak_cocok": "kecocokan varian",
            "akses_pembelian": "akses pembelian",
            "ragu_kualitas": "kepercayaan kualitas",
            "sensitivitas": "kekhawatiran sensitivitas",
        }

        barrier_readable = [barrier_text_map.get(x, x.replace("_", " ")) for x in barrier_labels]
        evidence_suffix = ""
        if barrier_readable:
            evidence_suffix = " Dasar temuan: hambatan utama " + ", ".join(barrier_readable[:2]) + "."

        out = []
        for idx, action in enumerate(clean_actions[:3], start=1):
            aspek, kpi, horizon = _action_meta(action)
            conf = _confidence(int(total_non_user), intent_level)
            text = _normalize_reco_text(f"{action}{evidence_suffix}")

            out.append({
                "aspek": aspek,
                "text": text,
                "why": _normalize_reco_text(
                    f"Segmen calon pembeli: intent {intent_level} ({intent_score:.1f}/100) dengan sampel {int(total_non_user)}"
                ),
                "aksi_utama": action,
                "kpi_target": _normalize_reco_text(kpi),
                "horizon_hari": int(horizon),
                "confidence": conf,
                "data": {
                    "context": "Segmen calon pembeli",
                    "total_non_user": int(total_non_user),
                    "intent_level": intent_level,
                    "intent_score": float(round(intent_score, 1)),
                    "barrier_top": barrier_labels[:3],
                },
                "issue_utama": barrier_readable[:3],
                "prioritas": idx,
            })

        return out

    all_mask = pd.Series([True] * len(df_raw), index=df_raw.index)
    if usage_col:
        used_mask_raw = used_mask
        non_user_mask_raw = non_user_mask
    else:
        used_mask_raw = all_mask
        non_user_mask_raw = pd.Series([False] * len(df_raw), index=df_raw.index)

    total_sudah = int(used_mask.sum()) if usage_col else int(len(df_raw))
    total_belum = int(non_user_mask.sum()) if usage_col else 0

    segment_views = {
        "all": _build_segment_view(df_raw.loc[all_mask].copy(), "all", total_sudah, total_belum),
        "used": _build_segment_view(df_raw.loc[used_mask_raw].copy(), "used", total_sudah, total_belum),
        "non_user": _build_segment_view(df_raw.loc[non_user_mask_raw].copy(), "non_user", total_sudah, total_belum),
    }

    has_variant_data = bool(variant_col and len(variant_list) > 0)
    segment_views["all"]["variant_enabled"] = has_variant_data
    segment_views["used"]["variant_enabled"] = has_variant_data
    segment_views["non_user"]["variant_enabled"] = False

    total_responden = int(len(df_raw))
    total_sudah_pakai = int(used_mask.sum()) if usage_col else total_responden
    total_belum_pakai = int(non_user_mask.sum()) if usage_col else 0
    total_unknown_pengalaman = int(unknown_usage_mask.sum()) if usage_col else 0
    unknown_ratio = (total_unknown_pengalaman / total_responden) if (usage_col and total_responden > 0) else 0.0
    mode_analisis = "sudah_pakai" if filter_applied else "semua_data"
    default_segment_view = "used" if (usage_col and int(used_mask.sum()) > 0) else "all"

    def _non_empty_ratio(frame: pd.DataFrame, column_name: Optional[str]) -> float:
        if not column_name or column_name not in frame.columns or len(frame) == 0:
            return 0.0
        s = frame[column_name].astype(str).str.strip()
        valid = (s != "") & (s.str.lower() != "nan")
        return float(valid.mean())

    def _likert_coverage_ratio(frame: pd.DataFrame, columns: List[str]) -> float:
        cols = [c for c in columns if c in frame.columns]
        if not cols or len(frame) == 0:
            return 0.0
        num = frame[cols].apply(pd.to_numeric, errors="coerce")
        return float(num.notna().any(axis=1).mean())

    aspect_quality = {}
    for asp in ["aroma", "kemasan", "ketahanan"]:
        comment_col = aspect_comment_cols.get(asp)
        issue_col = aspect_issue_cols.get(asp)
        asp_likert_cols = _aspect_likert_cols(df_raw, asp)
        aspect_quality[asp] = {
            "comment_col": comment_col,
            "comment_coverage": round(_non_empty_ratio(df_raw, comment_col), 4),
            "issue_col": issue_col,
            "issue_coverage": round(_non_empty_ratio(df_raw, issue_col), 4),
            "likert_cols": asp_likert_cols,
            "likert_coverage": round(_likert_coverage_ratio(df_raw, asp_likert_cols), 4),
            "source_ready": bool(comment_col or issue_col or len(asp_likert_cols) > 0),
        }

    data_quality = {
        "text_col": text_col,
        "text_coverage": round(_non_empty_ratio(df_raw, text_col), 4),
        "likert_coverage": round(_likert_coverage_ratio(df_raw, likert_cols), 4),
        "aspect_quality": aspect_quality,
    }

    # Untuk segmen non-user, rekomendasi segmen aktif harus berbasis akuisisi,
    # bukan fallback aspek produk aroma/kemasan/ketahanan.
    if usage_col and total_belum_pakai > 0:
        non_user_rekom = _build_non_user_segment_rekomendasi(
            insights=non_user_insights,
            total_non_user=total_belum_pakai,
        )
        if non_user_rekom:
            segment_views["non_user"]["rekomendasi"] = non_user_rekom
            
        # Mapping label agar lebih rapi (human-readable)
        barrier_labels = {
            "harga": "Harga / Diskon",
            "belum_tahu_produk": "Belum Tahu Produk",
            "akses_pembelian": "Akses Pembelian",
            "ragu_kualitas": "Keraguan Kualitas",
            "sensitivitas": "Isu Sensitivitas",
            "varian_tidak_cocok": "Varian Tidak Cocok"
        }
        need_labels = {
            "harga_terjangkau": "Harga Terjangkau",
            "aroma_soft": "Aroma Lebih Soft",
            "ketahanan_lama": "Ketahanan Lama",
            "kemasan_travel": "Kemasan Travel/Mini",
            "jaminan_produk": "Jaminan Kualitas/Ori",
            "rekomendasi_jelas": "Rekomendasi Jelas",
            "kemudahan_akses": "Kemudahan Akses (Toko Lokal)"
        }
        
        # Peta data dari non_user_insights ke format market_insights yang diekspektasi JS Dashboard
        segment_views["non_user"]["market_insights"] = {
            "barriers": {barrier_labels.get(x["label"], x["label"].replace("_", " ").title()): x["frekuensi"] for x in non_user_insights.get("barrier_top", [])},
            "desired_notes": [{"label": need_labels.get(x["label"], x["label"].replace("_", " ").title()), "freq": x["frekuensi"]} for x in non_user_insights.get("need_top", [])],
            "interest_score": non_user_insights.get("intent", {}).get("score", 0),
            "top_rekomendasi": non_user_insights.get("rekomendasi_aksi", [])
        }

    # operational health checks + business alerts (for real-world usage)
    health_issues = []
    if total_responden < MIN_TOTAL_RESPONDENTS:
        health_issues.append(
            f"Jumlah responden masih rendah (<{MIN_TOTAL_RESPONDENTS}), keputusan bisnis sebaiknya sementara."
        )
    if usage_col and total_responden > 0:
        if unknown_ratio >= MAX_UNKNOWN_USAGE_RATIO:
            health_issues.append(
                f"Banyak data pengalaman pakai tidak terdeteksi (>={int(MAX_UNKNOWN_USAGE_RATIO * 100)}%). "
                "Pertimbangkan standar jawaban Ya/Tidak."
            )
    if training_reason:
        health_issues.append(f"Model ML belum optimal: {training_reason}")
    elif model_trained and best_f1 is not None and best_f1 < 0.65:
        health_issues.append("F1 Score model masih di bawah 65%. Pertimbangkan tambah data dan pembersihan teks.")
    if modeling_rows > 0 and label_distribution:
        dominant_label, dominant_count = max(label_distribution.items(), key=lambda kv: kv[1])
        dominant_ratio = dominant_count / modeling_rows
        if dominant_ratio >= 0.75:
            health_issues.append(
                f"Distribusi label didominasi kelas {dominant_label} ({dominant_ratio:.1%}). "
                "Pantau metrik per kelas agar kelas minoritas tidak terlewat."
            )

    if data_quality.get("text_coverage", 0.0) < 0.25:
        health_issues.append(
            "Cakupan kolom komentar utama rendah (<25%). Validasi kembali kolom komentar agar ABSA tidak bias."
        )
    if data_quality.get("likert_coverage", 0.0) < 0.50:
        health_issues.append(
            "Cakupan nilai Likert masih rendah (<50%). Persentase sentimen bisa kurang stabil."
        )
    for asp_name, aq in data_quality.get("aspect_quality", {}).items():
        if not aq.get("source_ready", False):
            health_issues.append(
                f"Aspek {asp_name} belum memiliki sumber data yang memadai (komentar/issue/likert)."
            )

    analysis_meta = {
        "engine_version": "business-ready-v2",
        "selected_columns": {
            "text_col": text_col,
            "suggestion_col": suggestion_col,
            "usage_col": usage_col,
            "period_col": period_col,
            "variant_col": variant_col,
            "aspect_comment_cols": aspect_comment_cols,
            "aspect_issue_cols": aspect_issue_cols,
        },
        "data_quality": data_quality,
        "model_evaluation": {
            "source": best_eval_source,
            "source_label": best_eval_source_label,
            "modeling_rows": modeling_rows,
            "label_distribution": label_distribution,
            "cv_folds": cv_folds_used,
        },
    }

    business_alerts = []
    for asp in sentimen_per_aspek[:3]:
        asp_name = str(asp.get("aspek", "-")).capitalize()
        neg_pct = float(asp.get("persen_negatif", 0.0))
        if neg_pct >= 40:
            level = "high"
            text = f"{asp_name}: sentimen negatif {neg_pct:.1f}% (kritis, perlu aksi segera)."
        elif neg_pct >= 25:
            level = "medium"
            text = f"{asp_name}: sentimen negatif {neg_pct:.1f}% (perlu perbaikan terarah)."
        else:
            level = "low"
            text = f"{asp_name}: sentimen negatif {neg_pct:.1f}% (masih terkontrol)."
        business_alerts.append({
            "aspek": asp_name,
            "level": level,
            "persen_negatif": neg_pct,
            "text": text,
        })

    operational_readiness = _build_operational_readiness(
        total_responden=total_responden,
        model_trained=bool(model_trained),
        best_f1=best_f1,
        unknown_usage_ratio=float(unknown_ratio),
        variant_rankings=variant_rankings,
    )

    for warning in operational_readiness.get("warnings", []):
        if warning not in health_issues:
            health_issues.append(warning)

    variant_analysis_obj = {
        "variant_col": variant_col,
        "variants": variant_list,
        "recommendations_by_variant": variant_recommendations,
        "rankings": variant_rankings,
        "kemasan_rekomendasi_global": kemasan_reco_global,
        "kemasan_plan_global": kemasan_plan_global,
        "aspect_comment_cols": aspect_comment_cols,
        "aspect_issue_cols": aspect_issue_cols,
    }
    variant_analysis_non_user = {
        "variant_col": variant_col,
        "variants": [],
        "recommendations_by_variant": {},
        "rankings": [],
        "kemasan_rekomendasi_global": "-",
        "kemasan_plan_global": {
            "text": "-",
            "why": "Data non-user tidak menggunakan rekomendasi varian.",
            "aksi_utama": "-",
            "kpi_target": "-",
            "horizon_hari": 0,
            "confidence": "low",
            "issue_terms": [],
            "cluster": "general",
            "data": {"context": "Non-user", "negatif": 0, "total": 0, "persen_negatif": 0.0},
        },
        "aspect_comment_cols": aspect_comment_cols,
        "aspect_issue_cols": aspect_issue_cols,
    }

    return {
        "kpi": {
            "jumlah_komentar": jumlah_responden,
            "jumlah_responden_total": total_responden,
            "jumlah_responden_sudah_pakai": total_sudah_pakai,
            "jumlah_responden_belum_pakai": total_belum_pakai,
            "akurasi_model": akurasi_model,
            "persen_negatif": float(round(persen_negatif, 4)),
            "kolom_likert_terdeteksi": likert_cols,
            "model_trained": bool(model_trained),
            "model_used": best_model_name if best_model_name else "-",
            "evaluation_source": best_eval_source,
            "evaluation_source_label": best_eval_source_label,
            "modeling_rows": modeling_rows,
            "label_distribution": label_distribution,
            "cv_folds": cv_folds_used,
            "best_model_accuracy": round(best_acc,4) if best_acc else 0.0,
            "accuracy_nb": round(acc_nb,4) if acc_nb is not None else 0.0,
            "accuracy_svm": round(acc_svm,4) if acc_svm is not None else 0.0,
            # F1 Score metrics (primary evaluation metric)
            "f1_nb": round(f1_nb,4) if f1_nb is not None else 0.0,
            "f1_svm": round(f1_svm,4) if f1_svm is not None else 0.0,
            "best_f1": round(best_f1,4) if best_f1 else 0.0,
            # Precision & Recall metrics
            "precision_nb": round(precision_nb,4) if precision_nb is not None else 0.0,
            "recall_nb": round(recall_nb,4) if recall_nb is not None else 0.0,
            "precision_svm": round(precision_svm,4) if precision_svm is not None else 0.0,
            "recall_svm": round(recall_svm,4) if recall_svm is not None else 0.0,
            # duplicate keys with Indonesian names for compatibility
            "akurasi_nb": round(acc_nb,4) if acc_nb is not None else 0.0,
            "akurasi_svm": round(acc_svm,4) if acc_svm is not None else 0.0,
            "cv_nb_mean": cv_nb_mean,
            "cv_nb_std": cv_nb_std,
            "cv_svm_mean": cv_svm_mean,
            "cv_svm_std": cv_svm_std,
            "cv_nb_f1_mean": cv_nb_f1_mean,
            "cv_nb_f1_std": cv_nb_f1_std,
            "cv_svm_f1_mean": cv_svm_f1_mean,
            "cv_svm_f1_std": cv_svm_f1_std,
            "holdout_nb_accuracy": holdout_nb_accuracy,
            "holdout_svm_accuracy": holdout_svm_accuracy,
            "holdout_nb_f1": holdout_nb_f1,
            "holdout_svm_f1": holdout_svm_f1,
            "csv_url_dipakai": csv_url,
            "suggestion_col": suggestion_col,
            "aspect_issue_cols": aspect_issue_cols,
            "usage_col": usage_col,
            "analysis_mode": mode_analisis,
            "training_reason": training_reason,
            "operational_readiness_level": operational_readiness.get("level"),
            "operational_readiness_score": operational_readiness.get("score"),
            "ready_for_business_use": operational_readiness.get("ready_for_business_use"),
            "ready_for_auto_actions": operational_readiness.get("ready_for_auto_actions"),
        },
        "segmentasi_responden": {
            "kolom_pengalaman": usage_col,
            "mode_analisis": mode_analisis,
            "filter_diterapkan": bool(filter_applied),
            "catatan_filter": filter_reason,
            "default_segment_view": default_segment_view,
            "total_responden": total_responden,
            "sudah_pakai": total_sudah_pakai,
            "belum_pakai": {
                "jumlah": total_belum_pakai,
                "top_kata": non_user_top_kata,
                "insights": non_user_insights,
            },
            "pengalaman_tidak_diketahui": total_unknown_pengalaman,
        },
        "segment_views": segment_views,
        "trend_meta": {
            "period_col": period_col,
            "period_detected": bool(period_col),
            "granularity": "monthly",
        },
        "analysis_meta": analysis_meta,
        "health_check": {
            "status": "ok" if not health_issues else "warning",
            "issues": health_issues,
        },
        "alerts": {
            "aspek": business_alerts,
        },
        "sentiment_dist": {
            "Positif": int(dist_total.get("Positif", 0)),
            "Netral": int(dist_total.get("Netral", 0)),
            "Negatif": int(dist_total.get("Negatif", 0)),
        },
        "sentimen_per_aspek": sentimen_per_aspek,
        "absa_aspect_sentiment": absa_aspect_sentiment,
        "confusion_matrix": confusion_matrix,
        "absa_aspek_negatif": aspek_negatif,
        "top_kata": top_kata,
        "top_isu": top_isu,
        "prioritas": prioritas,
        "rekomendasi": rekomendasi_list,
        "variant_analysis": variant_analysis_obj,
        "variant_analysis_by_segment": {
            "all": variant_analysis_obj,
            "used": variant_analysis_obj,
            "non_user": variant_analysis_non_user,
        },
        "operational_readiness": operational_readiness,
    }
