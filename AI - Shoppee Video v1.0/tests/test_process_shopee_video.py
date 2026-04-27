from pathlib import Path
import csv
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from process_shopee_video import (
    build_ffmpeg_command,
    build_ytdlp_prefix,
    build_ytdlp_command,
    build_caption,
    build_product_folder_name,
    canonicalize_tiktok_url,
    cleanup_non_media_outputs,
    derive_output_name,
    download_tiktok_photo_audio,
    download_tiktok_thumbnail_with_ytdlp,
    ensure_masterlist_columns,
    extract_media_urls_from_html,
    find_background_audio,
    filter_media_urls,
    find_executable,
    infer_image_extension,
    is_direct_media_url,
    load_rows,
    normalize_downloaded_image_artifact,
    page_request_headers,
    REQUIRED_COLUMNS,
    replace_path,
    safe_filename,
    select_media_urls_for_download,
    strip_query_for_shopee_product_url,
    tiktok_video_id_from_url,
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

    def test_ytdlp_command_forces_video_download_for_tiktok(self):
        command = build_ytdlp_command(
            "https://vt.tiktok.com/ZS9hjGD43/",
            Path("raw"),
            ytdlp_path="yt-dlp",
            allow_path_lookup=False,
        )
        self.assertIn("--format", command)
        self.assertIn("bv*+ba/b", command)
        self.assertIn("--merge-output-format", command)
        self.assertIn("mp4", command)

    def test_ytdlp_prefix_falls_back_to_python_module(self):
        self.assertEqual(
            build_ytdlp_prefix(ytdlp_path=None, python_executable="python", allow_path_lookup=False),
            ["python", "-m", "yt_dlp"],
        )

    def test_canonicalize_tiktok_url_extracts_long_video_url_from_oembed(self):
        class FakeResponse:
            def __init__(self, body: bytes):
                self._body = body

            def read(self) -> bytes:
                return self._body

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_request(url: str, headers=None):
            self.assertIn("oembed", url)
            return FakeResponse(
                b'{"author_url":"https://www.tiktok.com/@shopdemo","html":"<blockquote cite=\\"https://www.tiktok.com/@shopdemo/video/7490123456789012345\\"></blockquote>"}'
            )

        result = canonicalize_tiktok_url(
            "https://vt.tiktok.com/ZS9hjGD43/",
            request_fn=fake_request,
        )

        self.assertEqual(
            result,
            "https://www.tiktok.com/@shopdemo/video/7490123456789012345",
        )

    def test_tiktok_video_id_from_url_extracts_numeric_id(self):
        self.assertEqual(
            tiktok_video_id_from_url("https://www.tiktok.com/@shopdemo/video/7490123456789012345"),
            "7490123456789012345",
        )

    def test_cleanup_non_media_outputs_removes_audio_only_tiktok_artifacts(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            raw_dir = Path(tmp) / "raw"
            raw_dir.mkdir()
            keep = raw_dir / "video.mp4"
            remove = raw_dir / "audio-only.m4a"
            keep.write_bytes(b"video")
            remove.write_bytes(b"audio")

            removed = cleanup_non_media_outputs(raw_dir)

            self.assertEqual(removed, [remove])
            self.assertTrue(keep.exists())
            self.assertFalse(remove.exists())

    def test_cleanup_non_media_outputs_keeps_background_audio(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            raw_dir = Path(tmp) / "raw"
            raw_dir.mkdir()
            keep = raw_dir / "background.m4a"
            keep.write_bytes(b"audio")

            removed = cleanup_non_media_outputs(raw_dir)

            self.assertEqual(removed, [])
            self.assertTrue(keep.exists())

    def test_infer_image_extension_detects_jpeg_bytes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            artifact = Path(tmp) / "thumb.image"
            artifact.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 8)
            self.assertEqual(infer_image_extension(artifact), ".jpg")

    def test_normalize_downloaded_image_artifact_renames_image_suffix(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            artifact = Path(tmp) / "thumb.image"
            artifact.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 8)
            normalized = normalize_downloaded_image_artifact(artifact)
            self.assertEqual(normalized.suffix.lower(), ".jpg")
            self.assertTrue(normalized.exists())
            self.assertFalse(artifact.exists())

    def test_normalize_downloaded_image_artifact_replaces_existing_target(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            artifact = Path(tmp) / "thumb.image"
            existing = Path(tmp) / "thumb.jpg"
            existing.write_bytes(b"old")
            artifact.write_bytes(b"\xff\xd8\xff\xe0" + b"new-bytes")

            normalized = normalize_downloaded_image_artifact(artifact)

            self.assertEqual(normalized, existing)
            self.assertEqual(existing.read_bytes(), b"\xff\xd8\xff\xe0new-bytes")
            self.assertFalse(artifact.exists())

    def test_download_tiktok_thumbnail_with_ytdlp_returns_normalized_image(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            raw_dir = Path(tmp) / "raw"
            raw_dir.mkdir()

            def fake_run(command, capture_output, text, check):
                self.assertIn("--write-thumbnail", command)
                self.assertIn("--force-overwrites", command)
                self.assertIn(str(raw_dir), command)
                (raw_dir / "7129084799339351323.image").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 8)

                class Result:
                    returncode = 0
                return Result()

            from unittest.mock import patch

            with patch("process_shopee_video.subprocess.run", side_effect=fake_run):
                images = download_tiktok_thumbnail_with_ytdlp(
                    "https://www.tiktok.com/@shopdemo/video/7490123456789012345",
                    raw_dir,
                )

            self.assertEqual(len(images), 1)
            self.assertEqual(images[0].suffix.lower(), ".jpg")
            self.assertTrue(images[0].exists())

    def test_download_tiktok_thumbnail_with_ytdlp_reuses_overwritten_existing_image(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            raw_dir = Path(tmp) / "raw"
            raw_dir.mkdir()
            existing = raw_dir / "7490123456789012345.jpg"
            existing.write_bytes(b"old")

            def fake_run(command, capture_output, text, check):
                existing.write_bytes(b"\xff\xd8\xff\xe0" + b"updated")

                class Result:
                    returncode = 0
                return Result()

            from unittest.mock import patch

            with patch("process_shopee_video.subprocess.run", side_effect=fake_run):
                images = download_tiktok_thumbnail_with_ytdlp(
                    "https://www.tiktok.com/@shopdemo/video/7490123456789012345",
                    raw_dir,
                )

            self.assertEqual(images, [existing])
            self.assertEqual(existing.read_bytes(), b"\xff\xd8\xff\xe0updated")

    def test_download_tiktok_photo_audio_returns_downloaded_native_audio(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            raw_dir = Path(tmp) / "raw"
            raw_dir.mkdir()

            def fake_run(command, capture_output, text, check):
                self.assertIn("--format", command)
                self.assertIn("bestaudio", command)
                self.assertIn("--force-overwrites", command)
                self.assertNotIn("-x", command)
                (raw_dir / "background.m4a").write_bytes(b"audio")

                class Result:
                    returncode = 0
                return Result()

            from unittest.mock import patch

            with patch("process_shopee_video.subprocess.run", side_effect=fake_run):
                audio = download_tiktok_photo_audio(
                    "https://www.tiktok.com/@shopdemo/video/7490123456789012345",
                    raw_dir,
                )

            self.assertIsNotNone(audio)
            self.assertEqual(audio.name, "background.m4a")
            self.assertTrue(audio.exists())

    def test_find_background_audio_prefers_existing_supported_file(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            raw_dir = Path(tmp) / "raw"
            raw_dir.mkdir()
            audio = raw_dir / "background.m4a"
            audio.write_bytes(b"audio")

            self.assertEqual(find_background_audio(raw_dir), audio)

    def test_replace_path_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as tmp:
            base = Path(tmp)
            target = base / "clip.mp4"
            target.write_bytes(b"old")

            resolved = replace_path(base, "clip.mp4")
            resolved.write_bytes(b"new")

            self.assertEqual(resolved, target)
            self.assertEqual(target.read_bytes(), b"new")

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
            headers = [sheet.cell(1, column).value for column in range(1, sheet.max_column + 1)]
            self.assertEqual(headers, REQUIRED_COLUMNS)
            self.assertEqual(sheet.cell(2, 1).value, "ASV-0000001")
            self.assertEqual(sheet.cell(2, 8).value, "TRUE")

    def test_no_media_message_is_actionable_for_shopee_pages(self):
        from process_shopee_video import no_media_message

        self.assertEqual(
            no_media_message("https://shopee.com.my/product/32632559/41452031782"),
            "Shopee page did not expose downloadable product media; use an approved seller media/direct file link",
        )


if __name__ == "__main__":
    unittest.main()
