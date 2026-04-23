from pathlib import Path
import csv
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from process_shopee_video import (
    build_ffmpeg_command,
    build_ytdlp_command,
    build_caption,
    build_product_folder_name,
    derive_output_name,
    ensure_masterlist_columns,
    extract_media_urls_from_html,
    filter_media_urls,
    find_executable,
    is_direct_media_url,
    load_rows,
    page_request_headers,
    safe_filename,
    select_media_urls_for_download,
    strip_query_for_shopee_product_url,
    update_record,
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
                        "Done",
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
                        "Done": "FALSE",
                    }
                )
            rows = load_rows(path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].row_number, 2)
            self.assertEqual(rows[0].product_name, "Mini Fan")

    def test_find_executable_checks_extra_directories(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            tool = Path(tmp) / "tool.exe"
            tool.write_text("", encoding="utf-8")
            self.assertEqual(find_executable("missing-tool", [Path(tmp) / "tool.exe"]), str(tool))

    def test_ytdlp_command_falls_back_to_python_module(self):
        command = build_ytdlp_command(
            "https://example.com/product",
            Path("raw"),
            ytdlp_path=None,
            python_executable="python",
            allow_path_lookup=False,
        )
        self.assertEqual(command[:3], ["python", "-m", "yt_dlp"])

    def test_filter_media_urls_skips_site_chrome_assets(self):
        urls = filter_media_urls(
            [
                "https://example.com/icon_favicon_1_32.png",
                "https://example.com/ios_icon_180x180.png",
                "https://example.com/ios_splash_screen_1080x2340.png",
                "https://deo.shopeemobile.com/shopee/shopee-mobilemall-live-sg/productdetailspage/share.png",
                "https://example.com/logo.png",
                "https://example.com/product-demo.mp4",
            ]
        )
        self.assertEqual(urls, ["https://example.com/product-demo.mp4"])

    def test_shopee_product_url_query_is_removed_before_scraping(self):
        cleaned = strip_query_for_shopee_product_url(
            "https://shopee.com.my/Electrova-Cordless-UV-Mite-Remover-i.297985880.25153849822"
            "?extraParams=%7B%22display_model_id%22%3A250102961680%7D"
        )
        self.assertEqual(
            cleaned,
            "https://shopee.com.my/Electrova-Cordless-UV-Mite-Remover-i.297985880.25153849822",
        )

    def test_page_request_headers_use_mobile_browser_for_shopee_pages(self):
        headers = page_request_headers("https://shopee.com.my/product/297985880/25153849822")
        self.assertIn("iPhone", headers["User-Agent"])
        self.assertIn("en-MY", headers["Accept-Language"])

    def test_extract_media_urls_from_shopee_seo_html_prefers_product_media(self):
        html = """
        <meta property="og:image" content="https://down-my.img.susercontent.com/file/my-11134207-demo@resize_w1200_nl.webp">
        <script>{"video_info_list":[{"formats":[{"url":"https://down-ws-sg.vod.susercontent.com/api/v4/11110105/mms/demo.1600325.mp4"}]}]}</script>
        <img src="https://deo.shopeemobile.com/shopee/shopee-mobilemall-live-sg/assets/icon_favicon_1_32.png">
        <style>.share{background-image:url(https://deo.shopeemobile.com/shopee/shopee-mobilemall-live-sg/productdetailspage/share.png)}</style>
        """
        urls = extract_media_urls_from_html("https://shopee.com.my/product/297985880/25153849822", html)
        self.assertEqual(
            urls,
            [
                "https://down-ws-sg.vod.susercontent.com/api/v4/11110105/mms/demo.1600325.mp4",
                "https://down-my.img.susercontent.com/file/my-11134207-demo@resize_w1200_nl.webp",
            ],
        )

    def test_select_media_urls_downloads_single_best_video_when_available(self):
        urls = select_media_urls_for_download(
            [
                "https://down-ws-sg.vod.susercontent.com/api/v4/11110105/mms/demo.1600318.mp4",
                "https://down-ws-sg.vod.susercontent.com/api/v4/11110105/mms/demo.1600325.mp4",
                "https://down-my.img.susercontent.com/file/my-11134207-demo@resize_w1200_nl.webp",
            ]
        )
        self.assertEqual(
            urls,
            ["https://down-ws-sg.vod.susercontent.com/api/v4/11110105/mms/demo.1600325.mp4"],
        )

    def test_ffmpeg_command_uses_complex_filter_for_composited_canvas(self):
        command = build_ffmpeg_command(
            "ffmpeg",
            Path("raw.png"),
            Path("edited_new.mp4"),
            "Shop - Product",
        )
        self.assertIn("-filter_complex", command)
        self.assertNotIn("-vf", command)

    def test_update_record_clears_stale_output_file_when_no_outputs(self):
        record = {
            "Status": "Edited",
            "Done": "TRUE",
            "Notes": "old",
            "Last Processed At": "",
            "Output Folder": "old-folder",
            "Output File": "old-file.mp4",
        }
        update_record(record, "Failed", "No downloadable media found", Path("folder"), [])
        self.assertEqual(record["Status"], "Failed")
        self.assertEqual(record["Done"], "FALSE")
        self.assertEqual(record["Output File"], "")

    def test_update_record_marks_done_when_downloaded_or_edited(self):
        for status in ("Downloaded", "Edited"):
            record = {
                "Status": "Pending",
                "Done": "FALSE",
                "Notes": "",
                "Last Processed At": "",
                "Output Folder": "",
                "Output File": "",
            }
            update_record(record, status, "ok", Path("folder"), [Path("video_new.mp4")])
            self.assertEqual(record["Done"], "TRUE")

    def test_ensure_masterlist_columns_adds_done_to_existing_csv(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            path = Path(tmp) / "master.csv"
            path.write_text(
                "Date,Product Link,Product Name,Shop Name,Source Type,Status,Notes,Last Processed At,Output Folder,Output File\n"
                "2026-04-23,https://example.com/video.mp4,Mini Fan,Cool Shop,Approved Media,Pending,,,,\n",
                encoding="utf-8-sig",
            )
            ensure_masterlist_columns(path)
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                rows = list(csv.DictReader(handle))
            self.assertIn("Done", rows[0])
            self.assertEqual(rows[0]["Done"], "FALSE")

    def test_write_masterlist_syncs_existing_workbook(self):
        from openpyxl import Workbook, load_workbook
        from process_shopee_video import write_masterlist

        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            csv_path = Path(tmp) / "master.csv"
            workbook_path = Path(tmp) / "master.xlsx"
            workbook = Workbook()
            workbook.active.title = "List of Link Shopee VIdeo"
            workbook.save(workbook_path)

            write_masterlist(csv_path, [{
                "Date": "2026-04-23",
                "Product Link": "https://example.com/video.mp4",
                "Product Name": "Mini Fan",
                "Shop Name": "Cool Shop",
                "Source Type": "Approved Media",
                "Status": "Downloaded",
                "Done": "TRUE",
                "Notes": "ok",
                "Last Processed At": "",
                "Output Folder": "",
                "Output File": "",
            }])

            updated = load_workbook(workbook_path)
            sheet = updated["List of Link Shopee VIdeo"]
            self.assertEqual(sheet.cell(1, 7).value, "Done")
            self.assertEqual(sheet.cell(2, 7).value, "TRUE")

    def test_no_media_message_is_actionable_for_shopee_pages(self):
        from process_shopee_video import no_media_message

        self.assertEqual(
            no_media_message("https://shopee.com.my/product/32632559/41452031782"),
            "Shopee page did not expose downloadable product media; use an approved seller media/direct file link",
        )


if __name__ == "__main__":
    unittest.main()
