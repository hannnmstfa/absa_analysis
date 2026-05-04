import os

def optimize_engine_sastrawi():
    with open('engine.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Add Sastrawi import
    if 'from Sastrawi.Stemmer.StemmerFactory import StemmerFactory' not in text:
        text = text.replace('from sklearn.pipeline import Pipeline',
                            'from sklearn.pipeline import Pipeline\nfrom Sastrawi.Stemmer.StemmerFactory import StemmerFactory\n\n_stemmer_factory = StemmerFactory()\n_stemmer = _stemmer_factory.create_stemmer()\n')

    # Expand normalization dict
    old_dict = '''normalization_dict = {
    "ga": "tidak", "gak": "tidak", "gk": "tidak", "nggak": "tidak",
    "enggak": "tidak", "tdk": "tidak", "bgt": "banget", "aja": "saja",
    "tpi": "tapi", "tp": "tapi", "krn": "karena", "karna": "karena",
    "dgn": "dengan", "dg": "dengan"
}'''
    new_dict = '''normalization_dict = {
    "ga": "tidak", "gak": "tidak", "gk": "tidak", "nggak": "tidak",
    "enggak": "tidak", "tdk": "tidak", "bgt": "banget", "bgtt": "banget",
    "bangett": "banget", "aja": "saja", "tpi": "tapi", "tp": "tapi",
    "krn": "karena", "karna": "karena", "dgn": "dengan", "dg": "dengan",
    "cepet": "cepat", "cpt": "cepat", "kureng": "kurang", "krg": "kurang",
    "wangiii": "wangi", "wangy": "wangi", "mantul": "mantap", "manteb": "mantap",
    "bgs": "bagus", "bagusss": "bagus", "awettt": "awet"
}'''
    text = text.replace(old_dict, new_dict)

    # Modify _process_row inside build_clean_text_column
    old_process = '''    def _process_row(s: str) -> str:
        toks = [t for t in s.split() if len(t) > 2 and t not in _STOPWORDS_ID]
        toks = _normalize_tokens_list(toks)
        toks = [t for t in toks if t not in _STOPWORDS_ID]
        return " ".join(toks)'''
    new_process = '''    def _process_row(s: str) -> str:
        toks = [t for t in s.split() if len(t) > 2 and t not in _STOPWORDS_ID]
        toks = _normalize_tokens_list(toks)
        toks = [_stemmer.stem(t) for t in toks]
        toks = [t for t in toks if t not in _STOPWORDS_ID]
        return " ".join(toks)'''
    text = text.replace(old_process, new_process)

    with open('engine.py', 'w', encoding='utf-8') as f:
        f.write(text)

def optimize_rfa_sastrawi():
    with open('run_full_analysis.py', 'r', encoding='utf-8') as f:
        text = f.read()

    if 'from Sastrawi.Stemmer.StemmerFactory import StemmerFactory' not in text:
        text = text.replace('import re\nimport json', 'import re\nimport json\nfrom Sastrawi.Stemmer.StemmerFactory import StemmerFactory\n_stemmer_factory = StemmerFactory()\n_stemmer = _stemmer_factory.create_stemmer()\n')

    # Add normalization_dict to run_full_analysis.py
    norm_dict_code = '''
normalization_dict = {
    "ga": "tidak", "gak": "tidak", "gk": "tidak", "nggak": "tidak",
    "enggak": "tidak", "tdk": "tidak", "bgt": "banget", "bgtt": "banget",
    "bangett": "banget", "aja": "saja", "tpi": "tapi", "tp": "tapi",
    "krn": "karena", "karna": "karena", "dgn": "dengan", "dg": "dengan",
    "cepet": "cepat", "cpt": "cepat", "kureng": "kurang", "krg": "kurang",
    "wangiii": "wangi", "wangy": "wangi", "mantul": "mantap", "manteb": "mantap",
    "bgs": "bagus", "bagusss": "bagus", "awettt": "awet"
}
'''
    if 'normalization_dict =' not in text:
        text = text.replace('# --- helpers ---', '# --- helpers ---' + norm_dict_code)

    old_clean = '''def clean_text_basic(s: str) -> str:
    if pd.isna(s):
        return ""
    t = str(s)
    t = re.sub(r'https?://\S+|www\.\S+', '', t)
    t = re.sub(r'@\w+', '', t)
    t = re.sub(r"[^a-zA-Z0-9\s]", ' ', t)
    t = re.sub(r"\d+", ' ', t)
    return re.sub(r"\s+", ' ', t).strip().lower()'''

    new_clean = '''def clean_text_basic(s: str) -> str:
    if pd.isna(s):
        return ""
    t = str(s)
    t = re.sub(r'https?://\S+|www\.\S+', '', t)
    t = re.sub(r'@\w+', '', t)
    t = re.sub(r"[^a-zA-Z0-9\s]", ' ', t)
    t = re.sub(r"\d+", ' ', t)
    t = re.sub(r"\s+", ' ', t).strip().lower()
    toks = t.split()
    toks = [normalization_dict.get(tok, tok) for tok in toks]
    toks = [_stemmer.stem(tok) for tok in toks]
    return " ".join(toks)'''

    text = text.replace(old_clean, new_clean)

    with open('run_full_analysis.py', 'w', encoding='utf-8') as f:
        f.write(text)

optimize_engine_sastrawi()
optimize_rfa_sastrawi()
print("Sastrawi Optimization complete.")
