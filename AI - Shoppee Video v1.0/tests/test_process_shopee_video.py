from pathlib import Path
import csv
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from process_shopee_video import (
    build_caption,
    build_product_folder_name,
    derive_output_name,
    is_direct_media_url,
    load_rows,
    safe_filename,
)


class HelperTests(unittest.TestCase):
    def test_safe_filename_removes_windows_forbidden_characters(self):
        self.assertEqual(safe_filename('A/B:C*D?E"F<G>H|I'), "A-B-C-D-E-F-G-H-I")

    def test_product_folder_uses_product_dash_shop(self):
        self.assertEqual(build_product_folder_name("Mini Fan", "Cool Shop"), "Mini Fan-Cool Shop")

    def test_caption_uses_shop_dash_product(self):
        self.assertEqual(build_caption("Mini Fan", "Cool Shop"), "Cool Shop - Mini Fan")

    def test_output_name_appends_new_before_extension(self):
        self.assertEqual(derive_output_name(Path("demo.mp4")), "demo_new.mp4")

    def test_direct_media_detection(self):
        self.assertTrue(is_direct_media_url("https://example.com/video.mp4?download=1"))
        self.assertTrue(is_direct_media_url("https://example.com/image.jpeg"))
        self.assertFalse(is_direct_media_url("https://shopee.com.my/product/123"))

    def test_load_rows_reads_pending_csv(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            path = Path(tmp) / "master.csv"
            with path.open("w", newline="", encoding="utf-8-sig") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "Date",
                        "Product Link",
                        "Product Name",
                        "Shop Name",
                        "Source Type",
                        "Status",
                        "Notes",
                        "Last Processed At",
                        "Output Folder",
                        "Output File",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "Date": "2026-04-23",
                        "Product Link": "https://example.com/video.mp4",
                        "Product Name": "Mini Fan",
                        "Shop Name": "Cool Shop",
                        "Source Type": "Approved Media",
                        "Status": "Pending",
                    }
                )
            rows = load_rows(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].row_number, 2)
            self.assertEqual(rows[0].product_name, "Mini Fan")


if __name__ == "__main__":
    unittest.main()
