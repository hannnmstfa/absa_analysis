import pandas as pd
import sys
from io import StringIO
from engine import (
    build_csv_export_url, 
    _download_csv_text, 
    run_analysis_from_csv_url
)

def export_audit_data(csv_url):
    print("--- Memulai Proses Ekspor Data Audit ---")
    print(f"URL: {csv_url}")
    
    try:
        # Jalankan analisis penuh menggunakan engine yang sama dengan dashboard
        print("Sedang menganalisis data (menjalankan engine)...")
        result = run_analysis_from_csv_url(csv_url)
        
        # 1. Download ulang data
        export_url = build_csv_export_url(csv_url)
        csv_text = _download_csv_text(export_url)
        df_raw = pd.read_csv(StringIO(csv_text), on_bad_lines="skip")
        df_raw.columns = [c.strip() for c in df_raw.columns]
        
        # 2. Ambil informasi kolom yang dideteksi oleh engine
        meta = result.get("analysis_meta", {}).get("selected_columns", {})
        text_col = meta.get("text_col")
        likert_cols = result.get("kpi", {}).get("kolom_likert_terdeteksi", [])
        
        if not text_col or not likert_cols:
            print("Kesalahan: Kolom teks atau likert tidak terdeteksi.")
            return

        print(f"Kolom Teks: {text_col}")
        print(f"Kolom Label: {likert_cols[0]} (digunakan sebagai acuan)")

        # 3. Buat DataFrame Audit
        audit_df = pd.DataFrame()
        audit_df['Teks_Komentar_Asli'] = df_raw[text_col]
        
        # Fungsi likert_to_sentiment (Sama dengan engine.py)
        def likert_to_sentiment(score):
            try:
                s = float(score)
                if s <= 2: return "Negatif"
                if s == 3: return "Netral"
                return "Positif"
            except: return "Unknown"

        audit_df['Sentimen_Asli_Likert'] = df_raw[likert_cols[0]].apply(likert_to_sentiment)
        
        # Note: Prediksi model per baris biasanya tidak dikembalikan secara masal via API 
        # untuk efisiensi, tapi di file ini Anda sudah punya 'Sentimen_Asli'.
        # Anda bisa menambahkan kolom prediksi manual atau jika ingin simulasi otomatis.
        
        output_file = "audit_sentimen_untuk_excel.csv"
        audit_df.to_csv(output_file, index=False)
        
        print(f"\nBERHASIL! File telah dibuat: {output_file}")
        print("Silakan buka file ini di Excel untuk melakukan perhitungan manual.")
        print("-" * 40)
        print(f"Total Baris Analisis: {result.get('kpi', {}).get('modeling_rows', 0)}")
        print("-" * 40)
        
        # Tampilkan Perbandingan Model
        kpi = result.get('kpi', {})
        print(f"{'METRIK':<15} | {'NAIVE BAYES':<15} | {'SVM':<15}")
        print("-" * 49)
        print(f"{'Accuracy':<15} | {kpi.get('accuracy_nb', 0):<15.4f} | {kpi.get('accuracy_svm', 0):<15.4f}")
        print(f"{'F1-Score':<15} | {kpi.get('f1_nb', 0):<15.4f} | {kpi.get('f1_svm', 0):<15.4f}")
        print(f"{'Precision':<15} | {kpi.get('precision_nb', 0):<15.4f} | {kpi.get('precision_svm', 0):<15.4f}")
        print(f"{'Recall':<15} | {kpi.get('recall_nb', 0):<15.4f} | {kpi.get('recall_svm', 0):<15.4f}")
        print("-" * 49)
        print(f"Model Terbaik: {kpi.get('model_used', '-')}")
        print(f"Metode Evaluasi: {kpi.get('evaluation_source_label', '-')}")
        print("-" * 49)
        
    except Exception as e:
        print(f"Terjadi kesalahan: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = input("Masukkan URL Google Sheets: ")
    
    export_audit_data(url)
