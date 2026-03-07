import csv
import io
import unittest
from unittest.mock import patch

import engine


def _csv_from_rows(rows):
    fieldnames = ["Komentar", "Ulasan Keseluruhan", "Pernah Pakai", "Varian"]
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue()


class GuardrailTests(unittest.TestCase):
    def _run_analysis(self, rows):
        csv_text = _csv_from_rows(rows)
        fake_url = "https://docs.google.com/spreadsheets/d/FAKE_ID/edit?gid=0"
        with patch("engine._download_csv_text", return_value=csv_text):
            return engine.run_analysis_from_csv_url(fake_url)

    def test_operational_readiness_not_ready_when_sample_small(self):
        rows = [
            {"Komentar": "aroma cepat hilang", "Ulasan Keseluruhan": 2, "Pernah Pakai": "ya", "Varian": "Alpha"},
            {"Komentar": "wangi enak tapi cepat pudar", "Ulasan Keseluruhan": 2, "Pernah Pakai": "ya", "Varian": "Alpha"},
            {"Komentar": "kemasan bagus dan rapi", "Ulasan Keseluruhan": 4, "Pernah Pakai": "ya", "Varian": "Beta"},
            {"Komentar": "ketahanan lumayan", "Ulasan Keseluruhan": 3, "Pernah Pakai": "ya", "Varian": "Beta"},
            {"Komentar": "aroma menyengat", "Ulasan Keseluruhan": 2, "Pernah Pakai": "ya", "Varian": "Alpha"},
            {"Komentar": "botol kokoh", "Ulasan Keseluruhan": 4, "Pernah Pakai": "ya", "Varian": "Beta"},
            {"Komentar": "wangi tahan lama", "Ulasan Keseluruhan": 5, "Pernah Pakai": "ya", "Varian": "Alpha"},
            {"Komentar": "spray kurang stabil", "Ulasan Keseluruhan": 2, "Pernah Pakai": "ya", "Varian": "Beta"},
        ]

        result = self._run_analysis(rows)
        readiness = result.get("operational_readiness", {})

        self.assertEqual(readiness.get("level"), "not_ready")
        self.assertFalse(readiness.get("ready_for_business_use"))
        self.assertFalse(readiness.get("ready_for_auto_actions"))

        sample_check = next(
            (c for c in readiness.get("checks", []) if c.get("key") == "sample_size"),
            {},
        )
        self.assertFalse(sample_check.get("passed"))
        self.assertEqual(sample_check.get("minimum"), engine.MIN_TOTAL_RESPONDENTS)

    def test_variant_rankings_mark_low_sample_variants(self):
        rows = []
        for _ in range(12):
            rows.append(
                {"Komentar": "aroma cepat hilang", "Ulasan Keseluruhan": 2, "Pernah Pakai": "ya", "Varian": "Alpha"}
            )
        for _ in range(4):
            rows.append(
                {"Komentar": "wangi cukup enak", "Ulasan Keseluruhan": 4, "Pernah Pakai": "ya", "Varian": "Beta"}
            )

        result = self._run_analysis(rows)
        variant_analysis = result.get("variant_analysis", {})
        rankings = variant_analysis.get("rankings", [])

        alpha = next((x for x in rankings if x.get("varian") == "Alpha"), {})
        beta = next((x for x in rankings if x.get("varian") == "Beta"), {})

        self.assertTrue(alpha.get("sample_sufficient"))
        self.assertFalse(beta.get("sample_sufficient"))
        self.assertEqual(beta.get("minimum_sample"), engine.MIN_VARIANT_SAMPLE)

        beta_reco = variant_analysis.get("recommendations_by_variant", {}).get("Beta", {})
        beta_meta = beta_reco.get("_meta", {})
        self.assertFalse(beta_meta.get("sample_sufficient"))
        self.assertIn("Catatan: sampel varian", beta_reco.get("aroma", ""))


if __name__ == "__main__":
    unittest.main()
