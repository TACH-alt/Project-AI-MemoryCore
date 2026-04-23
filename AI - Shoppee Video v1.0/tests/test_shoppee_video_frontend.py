from pathlib import Path
import csv
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from shoppee_video_frontend import normalize_frontend_row, upsert_masterlist_row


class FrontendTests(unittest.TestCase):
    def test_normalize_frontend_row_defaults_done_false(self):
        row = normalize_frontend_row({
            "Date": "2026-04-23",
            "Product Link": "https://example.com/video.mp4",
            "Product Name": "Mini Fan",
            "Shop Name": "Cool Shop",
        })
        self.assertEqual(row["Source Type"], "Auto")
        self.assertEqual(row["Status"], "Pending")
        self.assertEqual(row["Done"], "FALSE")

    def test_upsert_masterlist_row_appends_then_updates_by_product_link(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            path = Path(tmp) / "master.csv"
            first_row = upsert_masterlist_row(path, {
                "Date": "2026-04-23",
                "Product Link": "https://example.com/video.mp4",
                "Product Name": "Mini Fan",
                "Shop Name": "Cool Shop",
                "Source Type": "Approved Media",
            })
            second_row = upsert_masterlist_row(path, {
                "Date": "2026-04-24",
                "Product Link": "https://example.com/video.mp4",
                "Product Name": "Mini Fan Updated",
                "Shop Name": "Cool Shop",
                "Done": "TRUE",
            })

            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.DictReader(handle))

            self.assertEqual(first_row, 2)
            self.assertEqual(second_row, 2)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["Product Name"], "Mini Fan Updated")
            self.assertEqual(rows[0]["Done"], "TRUE")


if __name__ == "__main__":
    unittest.main()
