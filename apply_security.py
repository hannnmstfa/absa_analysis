import os
import re

def apply_security_fixes():
    with open('engine.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # 1. Modify _download_csv_text for stream size limit
    old_download = '''    try:
        r = requests.get(csv_url, headers=headers, timeout=timeout_sec, allow_redirects=True)
        r.raise_for_status()'''
    
    new_download = '''    try:
        r = requests.get(csv_url, headers=headers, timeout=timeout_sec, allow_redirects=True, stream=True)
        r.raise_for_status()
        MAX_SIZE = 5 * 1024 * 1024 # 5 MB limit
        content = b""
        for chunk in r.iter_content(chunk_size=8192):
            if chunk:
                content += chunk
                if len(content) > MAX_SIZE:
                    raise ValueError(f"Ukuran file CSV melebihi batas maksimal ({MAX_SIZE // 1024 // 1024} MB).")
        r_text = content.decode('utf-8', errors='replace')'''

    text = text.replace(old_download, new_download)

    # Replace r.text with r_text in the rest of _download_csv_text
    old_tail = '''    head = r.text[:200].lower()
    if "<html" in head or "accounts.google.com" in head:
        raise ValueError(
            "Link tidak menghasilkan CSV. Pastikan Sheet publik (Anyone with the link) "
            "dan URL export format=csv. Cek juga gid tab yang benar."
        )
    return r.text'''
    new_tail = '''    head = r_text[:200].lower()
    if "<html" in head or "accounts.google.com" in head:
        raise ValueError(
            "Link tidak menghasilkan CSV. Pastikan Sheet publik (Anyone with the link) "
            "dan URL export format=csv. Cek juga gid tab yang benar."
        )
    return r_text'''
    
    text = text.replace(old_tail, new_tail)

    # 2. Add Caching wrapper
    if '_ANALYSIS_CACHE' not in text:
        # Import time if not there
        if 'import time' not in text:
            text = 'import time\n' + text
            
        text = text.replace('def run_analysis_from_csv_url(csv_url: str) -> dict:',
                            '_ANALYSIS_CACHE = {}\nCACHE_TTL = 300\n\ndef run_analysis_from_csv_url(csv_url: str) -> dict:\n    import time\n    cache_key = build_csv_export_url(csv_url)\n    current_time = time.time()\n    if cache_key in _ANALYSIS_CACHE:\n        cached_result, timestamp = _ANALYSIS_CACHE[cache_key]\n        if current_time - timestamp < CACHE_TTL:\n            return cached_result\n    \n    result = _internal_run_analysis_from_csv_url(csv_url)\n    _ANALYSIS_CACHE[cache_key] = (result, current_time)\n    return result\n\ndef _internal_run_analysis_from_csv_url(csv_url: str) -> dict:')

    with open('engine.py', 'w', encoding='utf-8') as f:
        f.write(text)

apply_security_fixes()
print("Security and Caching applied.")
