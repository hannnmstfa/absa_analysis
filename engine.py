import pandas as pd
import re
import requests
import math
from io import StringIO
from collections import Counter
from typing import Dict, List, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, f1_score, precision_recall_fscore_support
from sklearn.pipeline import Pipeline


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
    "tidak","ga","gak","nggak","ya","yg","aja","kok","banget","sih","udah","sudah","karena","juga","jadi",
    "lebih","kurang","sangat","sekali","nya","deh","dong","lah","pun","dalam","oleh","buat","bagi","ada",
    "the","a","an","to","of","in","is","are"
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
    ],
    "aroma": ["aroma hilang", "aroma cepat hilang", "bau hilang", "wangi hilang", "aroma tidak konsisten"],
    "ketahanan": ["ketahanan berkurang", "ketahanan kurang", "ketahanan rendah", "tahan 2 jam", "tahan 3 jam"],
    "kemasan": ["bocor", "rembes", "rusak", "patah", "retak", "nozzle macet", "spray macet"],
}

_TEXT_SENTIMENT_NEGATIVE_CRITICAL_CUES = {
    "_generic": [
        "tidak tercium", "hampir tidak tercium", "mulai hilang", "cepat hilang", "tidak konsisten",
        "berkurang", "kurang kuat", "kurang tahan", "tidak tahan", "cuma tahan", "hanya tahan", "pudar",
        "semprot ulang", "disemprot ulang", "spray ulang", "perlu semprot ulang", "perlu disemprot ulang",
    ],
    "aroma": ["aroma hilang", "aroma tidak konsisten", "wangi hilang", "bau hilang"],
    "ketahanan": ["ketahanan berkurang", "ketahanan kurang", "ketahanan rendah", "tahan 2 jam", "tahan 3 jam"],
    "kemasan": ["bocor", "rembes", "rusak", "patah", "retak", "nozzle macet", "spray macet"],
}

_TEXT_SENTIMENT_NEGATION_GUARDS = [
    "tidak cepat hilang", "tidak mudah hilang", "tidak hilang", "tidak berkurang", "tidak pudar",
    "tidak perlu disemprot ulang", "tidak perlu semprot ulang",
]

_TEXT_SENTIMENT_POSITIVE_CUES = {
    "_generic": [
        "tahan lama", "awet", "bagus", "nyaman", "suka", "mantap", "harum", "wangi",
        "konsisten", "stabil",
    ],
    "aroma": ["aroma enak", "aroma lembut", "wangi lembut", "aroma konsisten"],
    "ketahanan": ["ketahanan bagus", "ketahanan baik", "awet seharian", "tahan seharian"],
    "kemasan": ["kemasan bagus", "kemasan rapi", "botol bagus", "nozzle bagus", "spray lancar"],
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

    # Strong complaint phrases should dominate unless explicitly negated.
    if critical_neg_hits > 0 and negation_hits == 0:
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
    "enggak": "tidak", "tdk": "tidak", "bgt": "banget", "aja": "saja",
    "tpi": "tapi", "tp": "tapi", "krn": "karena", "karna": "karena",
    "dgn": "dengan", "dg": "dengan"
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
        r = requests.get(csv_url, headers=headers, timeout=timeout_sec, allow_redirects=True)
        r.raise_for_status()
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
    head = r.text[:200].lower()
    if "<html" in head or "accounts.google.com" in head:
        raise ValueError(
            "Link tidak menghasilkan CSV. Pastikan Sheet publik (Anyone with the link) "
            "dan URL export format=csv. Cek juga gid tab yang benar."
        )
    return r.text

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

def run_analysis_from_csv_url(csv_url: str) -> dict:
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

    variant_col = guess_variant_column(df_raw)
    aspect_comment_cols = {
        "aroma": guess_aspect_comment_column(df_raw, "aroma"),
        "ketahanan": guess_aspect_comment_column(df_raw, "ketahanan"),
        "kemasan": guess_aspect_comment_column(df_raw, "kemasan"),
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
        for c in non_user_frame.columns:
            cl = c.lower().strip()
            if any(k in cl for k in ["minat", "niat", "tertarik", "kemungkinan mencoba"]) and is_likert_series(non_user_frame[c]):
                intent_col = c
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

            if len(df_model) < 5:
                training_reason = f"Data terlalu sedikit ({len(df_model)} baris). Minimal 5 diperlukan."
            elif df_model["label"].nunique() < 2:
                training_reason = "Hanya satu kelas label ditemukan."
            else:
                # prepare data
                X = df_model[modeling_text_col].astype(str).values
                y = df_model["label"].values

                # helper: safe split with stratify when possible
                def safe_train_test_split(Xi, yi, test_size=0.2, random_state=42):
                    counts = Counter(yi)
                    can_stratify = all(v >= 2 for v in counts.values()) and len(counts) >= 2
                    if can_stratify:
                        return train_test_split(Xi, yi, test_size=test_size, random_state=random_state, stratify=yi)
                    return train_test_split(Xi, yi, test_size=test_size, random_state=random_state)

                # perform split
                X_train, X_test, y_train, y_test = safe_train_test_split(X, y, test_size=0.2, random_state=42)

                # TF-IDF and train models
                tfidf = TfidfVectorizer(max_features=5000, ngram_range=(1, 2))
                X_train_tfidf = tfidf.fit_transform(X_train)
                X_test_tfidf = tfidf.transform(X_test)

                # Train NB
                nb_model = MultinomialNB()
                nb_model.fit(X_train_tfidf, y_train)
                y_pred_nb = nb_model.predict(X_test_tfidf)
                acc_nb = float(accuracy_score(y_test, y_pred_nb))
                f1_nb = float(f1_score(y_test, y_pred_nb, average='weighted', zero_division=0))
                
                # Calculate precision & recall for NB
                prec, rec, _, _ = precision_recall_fscore_support(y_test, y_pred_nb, average='weighted', zero_division=0)
                precision_nb = float(prec)
                recall_nb = float(rec)

                # Train SVM (LinearSVC)
                svm_model = LinearSVC(random_state=42, max_iter=2000)
                svm_model.fit(X_train_tfidf, y_train)
                y_pred_svm = svm_model.predict(X_test_tfidf)
                acc_svm = float(accuracy_score(y_test, y_pred_svm))
                f1_svm = float(f1_score(y_test, y_pred_svm, average='weighted', zero_division=0))
                
                # Calculate precision & recall for SVM
                prec, rec, _, _ = precision_recall_fscore_support(y_test, y_pred_svm, average='weighted', zero_division=0)
                precision_svm = float(prec)
                recall_svm = float(rec)

                # Choose best model (prioritize F1 Score as it's more robust)
                if f1_nb >= f1_svm:
                    best_model = nb_model
                    best_model_name = "Naive Bayes"
                    best_acc = acc_nb
                    best_f1 = f1_nb
                else:
                    best_model = svm_model
                    best_model_name = "SVM"
                    best_acc = acc_svm
                    best_f1 = f1_svm

                # cross-validation on full dataset for more reliable estimate
                try:
                    class_counts = Counter(y)
                    min_class_count = min(class_counts.values()) if class_counts else 0
                    cv_folds = min(5, min_class_count, len(y)) if len(y) > 1 else 0

                    pipe_nb = Pipeline([('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1,2))),
                                        ('clf', MultinomialNB())])
                    pipe_svm = Pipeline([('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1,2))),
                                         ('clf', LinearSVC(random_state=42, max_iter=2000))])

                    if cv_folds >= 2:
                        cv_nb_scores = cross_val_score(pipe_nb, X, y, cv=cv_folds, scoring='accuracy', n_jobs=-1)
                        cv_svm_scores = cross_val_score(pipe_svm, X, y, cv=cv_folds, scoring='accuracy', n_jobs=-1)
                    else:
                        cv_nb_scores = []
                        cv_svm_scores = []
                except Exception:
                    cv_nb_scores = []
                    cv_svm_scores = []

                cv_nb_mean = _finite_float_or_none(cv_nb_scores.mean()) if len(cv_nb_scores) else None
                cv_nb_std = _finite_float_or_none(cv_nb_scores.std()) if len(cv_nb_scores) else None
                cv_svm_mean = _finite_float_or_none(cv_svm_scores.mean()) if len(cv_svm_scores) else None
                cv_svm_std = _finite_float_or_none(cv_svm_scores.std()) if len(cv_svm_scores) else None

                # Predict labels for all available texts (use modeling column from original df)
                try:
                    X_all = df[modeling_text_col].astype(str).fillna("").values
                    X_all_tfidf = tfidf.transform(X_all)
                    preds_all = best_model.predict(X_all_tfidf)
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

    # 5b) ABSA - Aspect extraction dari text
    aspect_sentiment_from_text: Dict[str, Counter] = {}
    # we'll also gather negative tokens per aspect so recommendations/isu bisa realistis
    aspect_tokens: Dict[str, List[str]] = {}
    # and capture any explicit suggestions found in a suggestion column
    aspect_suggestions: Dict[str, List[str]] = {}
    
    if text_col:
        for idx, row in df.iterrows():
            text_val = row[text_col]
            # Skip if text is null/empty
            if pd.isna(text_val) or str(text_val).strip().lower() == "nan" or str(text_val).strip() == "":
                continue
            text = str(text_val).strip()

            # Extract aspects dari text
            aspects = extract_aspects_from_text(text)

            # Determine sentiment: prefer model prediction if available, otherwise likert rule
            sentiment = "Unknown"
            if model_trained and "predicted_sentiment" in df.columns:
                try:
                    sentiment = row.get("predicted_sentiment", "Unknown")
                except:
                    sentiment = "Unknown"
            else:
                if likert_cols:
                    try:
                        # convert to Series so dropna() works
                        scores = pd.to_numeric(pd.Series([row[c] for c in likert_cols]), errors="coerce").dropna()
                        if len(scores) > 0:
                            mean_score = scores.mean()
                            sentiment = likert_to_sentiment(mean_score)
                    except:
                        sentiment = "Unknown"


            # Add to aspect-sentiment counts
            if sentiment != "Unknown":
                for aspect in aspects:
                    if aspect not in aspect_sentiment_from_text:
                        aspect_sentiment_from_text[aspect] = Counter()
                    aspect_sentiment_from_text[aspect][sentiment] += 1

                    # if negative, capture tokens for that aspect
                    if sentiment == "Negatif":
                        toks = tokenize_id(text)
                        if toks:
                            aspect_tokens.setdefault(aspect, []).extend(toks)

                    # collect suggestion text if column exists
                    if suggestion_col and pd.notna(row.get(suggestion_col)):
                        stext = str(row.get(suggestion_col)).strip()
                        if stext:
                            # remove leading cue words like "saran:" or "rekomendasi"
                            clean = re.sub(r'^(saran|rekomendasi?)[:\-\s]+', '', stext, flags=re.I).strip()
                            if clean:
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
    # Prioritas: gunakan ABSA jika ada, kalau tidak gunakan likert
    sentimen_per_aspek = []
    
    # Jika ada ABSA data, gunakan itu
    if absa_aspect_sentiment:
        sentimen_per_aspek = absa_aspect_sentiment[:3]  # Top 3 aspects
    # Fallback: gunakan likert columns
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
    
    # Ensure the dashboard always shows the three requested aspects (aroma, kemasan, ketahanan)
    # even if they have zero counts — this makes the frontend consistent.
    desired_display_aspects = ["aroma", "kemasan", "ketahanan"]
    existing_aspek_keys = {a['aspek'].lower(): a for a in sentimen_per_aspek}
    for da in desired_display_aspects:
        if da not in existing_aspek_keys:
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

    # 9) akurasi_model & confusion matrix: kalau ada aspek dari text, buat matrix dari top aspek
    # NOTE: when we actually trained an ML model, prefer to report its validation
    # accuracy (best_acc) instead of the crude confusion-based metric. This makes
    # the dashboard number more meaningful for users who expect the ML score.
    akurasi_model = None
    confusion_matrix = {
        "tp": 0,
        "fp": 0,
        "fn": 0,
        "tn": 0
    }
    
    # If the ML pipeline produced a model, override the default accuracy
    # Prioritize F1 Score as primary metric (more robust for imbalanced data)
    if f1_nb is not None and f1_svm is not None:
        # Report the best model's F1 score as primary metric
        best_f1_score = max(f1_nb, f1_svm)
        akurasi_model = round(best_f1_score, 4)

        if f1_nb >= f1_svm:
            best_model_name = "Naive Bayes"
        else:
            best_model_name = "SVM"
    
    # build confusion matrix for backwards compatibility / charting
    if absa_aspect_sentiment and len(absa_aspect_sentiment) > 0:
        top_absa = absa_aspect_sentiment[0]
        confusion_matrix = {
            "tp": top_absa.get("positif", 0),
            "fp": top_absa.get("negatif", 0),
            "fn": top_absa.get("netral", 0),
            "tn": 0
        }
    # Fallback: gunakan total sentiment distribution
    elif dist_total:
        confusion_matrix = {
            "tp": dist_total.get("Positif", 0),
            "fp": dist_total.get("Negatif", 0),
            "fn": dist_total.get("Netral", 0),
            "tn": 0
        }
    
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

    GENERIC_ISSUE_TOKENS = {
        "parfum", "produk", "wangi", "harum", "tahan", "lama", "bagus", "baik", "oke",
        "enak", "suka", "banget", "sekali", "cukup", "lebih", "kurang", "udah", "sudah",
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

    def _build_data_grounded_plan(
        aspect: str,
        tokens: List[str],
        total_comments: int,
        negative_comments: int,
        context_label: str,
        confidence_hint: str = "medium",
    ) -> Dict[str, object]:
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

    def _aspect_unique_metrics(frame: pd.DataFrame, aspect: str) -> Dict[str, int]:
        if frame is None or len(frame) == 0:
            return {"total": 0, "negatif": 0}

        aspect_cols = _aspect_likert_columns(frame, aspect)
        fallback_cols = [c for c in likert_cols if c in frame.columns]

        target_cols = aspect_cols if aspect_cols else fallback_cols
        if not target_cols:
            return {"total": int(len(frame)), "negatif": 0}

        num = frame[target_cols].apply(pd.to_numeric, errors="coerce")
        has_data = num.notna().any(axis=1)
        vals = num.mean(axis=1, skipna=True)

        total = int(has_data.sum())
        negatif = int(((vals <= 3) & has_data).sum())

        if total <= 0:
            total = int(len(frame))
        negatif = max(0, min(negatif, total))
        return {"total": total, "negatif": negatif}

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

        neg_mask_aroma = _negative_mask_for_aspect("aroma")
        neg_mask_ketahanan = _negative_mask_for_aspect("ketahanan")
        neg_mask_kemasan = _negative_mask_for_aspect("kemasan")
        if likert_cols:
            neg_mask_total = df[likert_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1, skipna=True) <= 3
        else:
            neg_mask_total = pd.Series([False] * len(df), index=df.index)

        for var in variant_list:
            var_mask = variants_series.str.lower() == var.lower()
            var_frame = df.loc[var_mask].copy()

            aroma_col = aspect_comment_cols.get("aroma") or text_col
            ketahanan_col = aspect_comment_cols.get("ketahanan") or text_col

            aroma_texts = []
            ketahanan_texts = []

            if aroma_col and aroma_col in df.columns:
                aroma_texts = df.loc[var_mask & neg_mask_aroma, aroma_col].dropna().astype(str).tolist()
                if not aroma_texts:
                    aroma_texts = df.loc[var_mask, aroma_col].dropna().astype(str).tolist()

            if ketahanan_col and ketahanan_col in df.columns:
                ketahanan_texts = df.loc[var_mask & neg_mask_ketahanan, ketahanan_col].dropna().astype(str).tolist()
                if not ketahanan_texts:
                    ketahanan_texts = df.loc[var_mask, ketahanan_col].dropna().astype(str).tolist()

            total_var = int(var_mask.sum())
            neg_var = int((var_mask & neg_mask_total).sum())
            aroma_metrics_var = _aspect_unique_metrics(var_frame, "aroma")
            ketahanan_metrics_var = _aspect_unique_metrics(var_frame, "ketahanan")
            total_var_aroma = int(aroma_metrics_var.get("total", total_var) or total_var)
            total_var_ketahanan = int(ketahanan_metrics_var.get("total", total_var) or total_var)
            neg_var_aroma = int(aroma_metrics_var.get("negatif", 0))
            neg_var_ketahanan = int(ketahanan_metrics_var.get("negatif", 0))
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

            if sample_note:
                aroma_plan["text"] = _normalize_reco_text(f"{aroma_plan.get('text', '-')}{sample_note}")
                ketahanan_plan["text"] = _normalize_reco_text(f"{ketahanan_plan.get('text', '-')}{sample_note}")
                aroma_plan["catatan_sampel"] = sample_note.strip()
                ketahanan_plan["catatan_sampel"] = sample_note.strip()

            variant_recommendations[var] = {
                "aroma": str(aroma_plan.get("text", "-")),
                "ketahanan": str(ketahanan_plan.get("text", "-")),
                "aroma_plan": aroma_plan,
                "ketahanan_plan": ketahanan_plan,
                "_meta": {
                    "total_komentar": total_var,
                    "minimum_sample": MIN_VARIANT_SAMPLE,
                    "sample_sufficient": sample_sufficient,
                    "confidence_level": confidence_level,
                },
            }

            issue_text_sources = []
            for colname in [aspect_comment_cols.get("aroma"), aspect_comment_cols.get("ketahanan"), text_col]:
                if colname and colname in df.columns:
                    issue_text_sources.extend(df.loc[var_mask & neg_mask_total, colname].dropna().astype(str).tolist())

            issue_tokens = []
            for txt in issue_text_sources:
                issue_tokens.extend(tokenize_id(str(txt)))

            issue_candidates = ISSUE_BY_ASPEK.get("aroma", set()).union(ISSUE_BY_ASPEK.get("ketahanan", set()))
            issue_filtered = [
                tok for tok in issue_tokens
                if tok in issue_candidates and tok not in GENERIC_ISSUE_TOKENS
            ]
            issue_non_generic = [tok for tok in issue_tokens if tok not in GENERIC_ISSUE_TOKENS]
            if issue_filtered:
                top_issue, top_issue_freq = Counter(issue_filtered).most_common(1)[0]
            elif issue_non_generic:
                top_issue, top_issue_freq = Counter(issue_non_generic).most_common(1)[0]
            elif issue_tokens:
                top_issue, top_issue_freq = Counter(issue_tokens).most_common(1)[0]
            else:
                top_issue, top_issue_freq = "-", 0

            quality_score = round(max(0.0, 100.0 - float(neg_pct)), 1)

            variant_rankings.append({
                "varian": var,
                "total_komentar": total_var,
                "negatif": neg_var,
                "persen_negatif": float(neg_pct),
                "skor_kualitas": float(quality_score),
                "isu_dominan": top_issue,
                "frekuensi_isu": int(top_issue_freq),
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

    def _row_sentiment(row_data) -> str:
        if not likert_cols:
            return "Unknown"
        try:
            vals = pd.to_numeric(pd.Series([row_data.get(c) for c in likert_cols]), errors="coerce").dropna()
            if len(vals) == 0:
                return "Unknown"
            return likert_to_sentiment(vals.mean())
        except Exception:
            return "Unknown"

    def _build_segment_view(frame: pd.DataFrame) -> Dict[str, object]:
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

        def _row_sentiment_for_aspect(row_data, asp: str) -> str:
            asp_cols = _aspect_likert_columns(frame, asp)
            if asp_cols:
                try:
                    vals = pd.to_numeric(pd.Series([row_data.get(c) for c in asp_cols]), errors="coerce").dropna()
                    if len(vals) > 0:
                        return likert_to_sentiment(vals.mean())
                except Exception:
                    pass
            return _row_sentiment(row_data)

        def _resolve_aspect_sentiment(row_data, asp: str, text_value: str) -> str:
            base_sent = _row_sentiment_for_aspect(row_data, asp)
            text_hint = _infer_text_sentiment_for_aspect(text_value, asp)

            # If text clearly indicates negative sentiment for this aspect,
            # prioritize it for drilldown display to avoid misleading examples.
            if text_hint == "Negatif" and base_sent in ("Positif", "Netral", "Unknown"):
                return "Negatif"

            if base_sent == "Unknown":
                return text_hint

            return base_sent

        if total > 0:
            for _, row_data in frame.iterrows():
                row_sentiment = _row_sentiment(row_data)
                if row_sentiment != "Unknown":
                    labels.append(row_sentiment)

                if not text_col or text_col not in frame.columns:
                    continue

                text_val = row_data.get(text_col)
                if pd.isna(text_val) or str(text_val).strip().lower() == "nan" or str(text_val).strip() == "":
                    continue

                text = str(text_val).strip()
                aspects = extract_aspects_from_text(text)
                local_text_tokens.extend(tokenize_id(text))

                for asp in aspects:
                    asp_sentiment = _resolve_aspect_sentiment(row_data, asp, text)
                    if asp_sentiment == "Unknown":
                        continue

                    if asp not in local_aspect_counts:
                        local_aspect_counts[asp] = Counter()
                    local_aspect_counts[asp][asp_sentiment] += 1

                    if asp_sentiment == "Negatif":
                        toks = tokenize_id(text)
                        if toks:
                            local_aspect_tokens.setdefault(asp, []).extend(toks)

                for asp in desired:
                    if asp in aspects:
                        asp_sentiment = _resolve_aspect_sentiment(row_data, asp, text)
                    else:
                        asp_sentiment = "Unknown"

                    if asp_sentiment in ("Positif", "Negatif"):
                        key = "positif" if asp_sentiment == "Positif" else "negatif"
                        count_key = "jumlah_positif" if key == "positif" else "jumlah_negatif"
                        drilldown[asp][count_key] += 1
                        current = drilldown[asp][key]
                        if text not in current and len(current) < DRILLDOWN_MAX_EXAMPLES:
                            current.append(text)

        dist = Counter(labels)
        total_labeled = sum(dist.values()) if dist else 0
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
            freq = Counter(toks).most_common(1)
            if freq:
                kata, jumlah = freq[0]
                top_isu_local.append({
                    "aspek": asp.capitalize(),
                    "isu": kata,
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
            "jumlah_komentar": total,
            "persen_negatif": float(round(persen_neg, 4)),
            "trend_periode": trend_periode,
            "early_warning": early_warning,
            "sentiment_dist": {
                "Positif": int(dist.get("Positif", 0)),
                "Netral": int(dist.get("Netral", 0)),
                "Negatif": int(dist.get("Negatif", 0)),
            },
            "top_isu": [
                {"aspek": x["aspek"], "isu": x["isu"], "frekuensi": x["frekuensi"]}
                for x in top_isu_local[:3]
            ],
            "top_kata": top_kata_local,
            "sentimen_per_aspek": sentimen_aspek[:3],
            "prioritas": prioritas_local,
            "rekomendasi": rekomendasi_local,
            "drilldown_aspek": drilldown,
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

    segment_views = {
        "all": _build_segment_view(df_raw.loc[all_mask].copy()),
        "used": _build_segment_view(df_raw.loc[used_mask_raw].copy()),
        "non_user": _build_segment_view(df_raw.loc[non_user_mask_raw].copy()),
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

    # Untuk segmen non-user, rekomendasi segmen aktif harus berbasis akuisisi,
    # bukan fallback aspek produk aroma/kemasan/ketahanan.
    if usage_col and total_belum_pakai > 0:
        non_user_rekom = _build_non_user_segment_rekomendasi(
            insights=non_user_insights,
            total_non_user=total_belum_pakai,
        )
        if non_user_rekom:
            segment_views["non_user"]["rekomendasi"] = non_user_rekom

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
            "csv_url_dipakai": csv_url,
            "suggestion_col": suggestion_col,
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