import sys
import os
import pandas as pd

# Menambahkan direktori saat ini ke path agar bisa import engine
sys.path.append(os.getcwd())

from engine import _infer_text_sentiment_for_aspect

def test_sentiment():
    test_cases = [
        # Teks, Aspek, Ekspektasi
        ("Tidak terlalu tahan Lama", "ketahanan", "Negatif"),
        ("Kurang wangi", "aroma", "Negatif"),
        ("Tahan lama banget", "ketahanan", "Positif"),
        ("Aroma tidak tercium", "aroma", "Negatif"),
        ("Tidak bocor", "kemasan", "Positif"),
        ("Cepat hilang wanginya", "ketahanan", "Negatif"),
        ("Botol rusak", "kemasan", "Negatif"),
        ("Wangi enak tapi tidak tahan lama", "ketahanan", "Negatif"),
        ("Lumayan tahan lama", "ketahanan", "Positif"),
        ("Agak rembes", "kemasan", "Negatif"),
        ("Suka banget", "umum", "Positif"),
        ("Kecewa", "umum", "Negatif"),
        ("Bau alkohol banget", "aroma", "Negatif"),
        ("Tidak pernah mengalami masalah", "kemasan", "Positif"),
        ("Sejauh ini tidak ada masalah di kemasan.", "kemasan", "Positif"),
    ]

    print(f"{'Teks':<40} | {'Aspek':<12} | {'Hasil':<10} | {'Status'}")
    print("-" * 80)

    all_passed = True
    for text, aspect, expected in test_cases:
        actual = _infer_text_sentiment_for_aspect(text, aspect)
        status = "PASS" if actual == expected else "FAIL"
        if status == "FAIL":
            all_passed = False
        print(f"{text:<40} | {aspect:<12} | {actual:<10} | {status}")

    if all_passed:
        print("\nSemua tes BERHASIL!")
    else:
        print("\nBeberapa tes GAGAL. Perbaikan diperlukan.")

if __name__ == "__main__":
    test_sentiment()
