from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
import html
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, unquote, urljoin, urlparse, urlsplit, urlunsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener, urlopen


CAPTIONS_ROUTER_URL = "http://10.10.10.2:20128/v1/chat/completions"
CAPTIONS_PRIMARY_MODEL = "gc/gemini-3-flash-preview"
CAPTIONS_FALLBACK_MODEL = "cc/claude-haiku-4-5-20251001"
CAPTIONS_TIMEOUT_SEC = 45

VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTENSIONS = {".aac", ".m4a", ".mp3", ".opus", ".ogg", ".wav", ".webm"}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS
RENDER_MODES = frozenset({"auto", "light", "vertical-blur", "passthrough"})
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ShopeeVideoWorkflow/1.0"
SHOPEE_PAGE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
)
TIKTOK_PAGE_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)
REQUIRED_COLUMNS = [
    "Record ID",
    "Date",
    "Product Link",
    "Product Name",
    "Shop Name",
    "Source Type",
    "Status",
    "Done",
    "Analysis Done",
    "Notes",
    "Last Processed At",
    "Output Folder",
    "Output File",
    "Hook",
]


@dataclass
class MasterRow:
    row_number: int
    record_id: str
    product_link: str
    product_name: str
    shop_name: str
    source_type: str
    status: str
    data: dict[str, str]


@dataclass
class WorkflowConfig:
    project_root: Path
    masterlist_path: Path
    force: bool = False
    dry_run: bool = False
    render_mode: str = "auto"
    skip_captions: bool = False
    captions_model: str = CAPTIONS_PRIMARY_MODEL
    skip_hooks: bool = False
    skip_cover: bool = False


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value.strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"-+", "-", cleaned)
    return cleaned.strip(" .-") or "untitled"


def build_product_folder_name(product_name: str, shop_name: str) -> str:
    return safe_filename(f"{product_name}-{shop_name}")


def build_caption(product_name: str, shop_name: str) -> str:
    return f"{shop_name.strip()} - {product_name.strip()}".strip(" -")


def derive_output_name(raw_path: Path) -> str:
    return f"{safe_filename(raw_path.stem)}_new{raw_path.suffix.lower()}"


def is_direct_media_url(url: str) -> bool:
    parsed = urlparse(url)
    suffix = Path(unquote(parsed.path)).suffix.lower()
    return parsed.scheme in {"http", "https"} and suffix in MEDIA_EXTENSIONS


def is_shopee_url(url: str) -> bool:
    host = urlparse(url).netloc.lower()
    return host.endswith("shopee.com.my") or host.endswith("s.shopee.com.my")


def is_shopee_product_url(url: str) -> bool:
    parsed = urlparse(url)
    if not is_shopee_url(url):
        return False
    path = parsed.path
    return bool(re.search(r"-i\.\d+\.\d+/?$", path) or re.search(r"/product/\d+/\d+/?$", path))


def strip_query_for_shopee_product_url(url: str) -> str:
    if not is_shopee_product_url(url):
        return url
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def is_shopee_cdn_media_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = unquote(parsed.path).lower()
    return (
        host.endswith(".vod.susercontent.com")
        or host == "mms.vod.susercontent.com"
        or (host == "down-my.img.susercontent.com" and path.startswith("/file/"))
    )


def is_tiktok_video_url(url: str) -> bool:
    """Return True for public single TikTok post URLs.

    Handles:
    - Standard long URLs: https://www.tiktok.com/@user/video/123456
    - Standard photo URLs: https://www.tiktok.com/@user/photo/123456
    - Short redirect links: https://vt.tiktok.com/ZS9hjGD43/
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not host.endswith("tiktok.com"):
        return False
    # Short links (vt.tiktok.com) are always single-video redirects — trust yt-dlp
    if host in {"vt.tiktok.com", "vm.tiktok.com"}:
        return True
    # Standard long URLs must contain /video/ or /photo/ in the path
    return "/video/" in parsed.path or "/photo/" in parsed.path


def detect_platform(url: str) -> str:
    """Return 'Shopee', 'TikTok', or 'Direct' based on the URL."""
    if is_shopee_url(url):
        return "Shopee"
    if is_tiktok_video_url(url):
        return "TikTok"
    return "Direct"


def record_prefix_for_url(url: str) -> str:
    platform = detect_platform(url)
    if platform == "TikTok":
        return "ATV"
    return "ASV"


def next_record_id(rows: list[dict[str, str]], prefix: str) -> str:
    """Generate the next sequential Record ID for a given prefix (ASV or ATV)."""
    max_num = 0
    pattern = re.compile(rf"^{re.escape(prefix)}-(\d+)$")
    for row in rows:
        match = pattern.match(row.get("Record ID", ""))
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"{prefix}-{max_num + 1:07d}"


def backfill_record_identity(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    """Ensure every row has a Record ID; assign missing ones in order."""
    for row in rows:
        if not row.get("Record ID"):
            prefix = record_prefix_for_url(row.get("Product Link", ""))
            row["Record ID"] = next_record_id(rows, prefix)
        if row.get("Analysis Done") is None or row.get("Analysis Done") == "":
            row["Analysis Done"] = "FALSE"
    return rows


def resolve_shop_folder(platform_root: Path, shop_name: str) -> Path:
    """Find an existing shop folder (case-insensitive) or return a new one."""
    if platform_root.exists():
        for existing in platform_root.iterdir():
            if existing.is_dir() and existing.name.lower() == shop_name.lower():
                return existing
    return platform_root / safe_filename(shop_name)


def resolve_product_folder(output_root: Path, platform: str, shop_name: str, product_name: str) -> Path:
    """Resolve output/<Platform>/<Shop>/<Product> path with case-insensitive shop matching."""
    platform_root = output_root / platform
    shop_folder = resolve_shop_folder(platform_root, shop_name)
    return shop_folder / safe_filename(product_name)


def write_product_info(product_dir: Path, row: dict[str, str], platform: str) -> None:
    """Write or refresh product-info.md in the product folder."""
    product_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = product_dir / "raw"
    video_count = 0
    image_count = 0
    if raw_dir.exists():
        for f in raw_dir.iterdir():
            if f.suffix.lower() in VIDEO_EXTENSIONS:
                video_count += 1
            elif f.suffix.lower() in IMAGE_EXTENSIONS:
                image_count += 1
    output_file_summary = row.get("Output File", "") or "None"
    content = f"""# Product Info

| Field | Value |
|---|---|
| Record ID | {row.get("Record ID", "")} |
| Date | {row.get("Date", "")} |
| Product Link | {row.get("Product Link", "")} |
| Product Name | {row.get("Product Name", "")} |
| Shop Name | {row.get("Shop Name", "")} |
| Platform | {platform} |
| Source Type | {row.get("Source Type", "")} |
| Status | {row.get("Status", "")} |
| Done | {row.get("Done", "FALSE")} |
| Analysis Done | {row.get("Analysis Done", "FALSE")} |
| Notes | {row.get("Notes", "")} |

## Media Summary

| Type | Count |
|---|---|
| Videos downloaded | {video_count} |
| Images downloaded | {image_count} |
| Latest output file | {output_file_summary} |
"""
    (product_dir / "product-info.md").write_text(content, encoding="utf-8")


def no_media_message(url: str) -> str:
    if is_shopee_url(url):
        return "Shopee page did not expose downloadable product media; use an approved seller media/direct file link"
    if is_tiktok_video_url(url):
        return (
            "TikTok video could not be downloaded; ensure the URL is a public single-video post link. "
            "Photo-mode (carousel) posts normally fall back to the cover thumbnail with background audio."
        )
    return "No downloadable media found"


def is_pending_status(status: str, force: bool = False) -> bool:
    return force or status.strip().lower() in {"", "pending"}


def find_executable(name: str, extra_candidates: Iterable[Path] | None = None) -> str | None:
    found = shutil.which(name)
    if found:
        return found
    for candidate in extra_candidates or []:
        if candidate.exists() and candidate.is_file():
            return str(candidate)
    return None


def python_user_scripts_candidates(executable_name: str) -> list[Path]:
    appdata = os.environ.get("APPDATA")
    if not appdata:
        return []
    version = f"Python{sys.version_info.major}{sys.version_info.minor}"
    return [Path(appdata) / "Python" / version / "Scripts" / executable_name]


def ffprobe_path() -> str | None:
    direct = find_executable("ffprobe", [])
    if direct:
        return direct
    ffmpeg = find_executable("ffmpeg", ffmpeg_candidates())
    if ffmpeg:
        candidate = Path(ffmpeg).with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if candidate.exists():
            return str(candidate)
    return None


def probe_video_dimensions(path: Path) -> tuple[int, int] | None:
    probe = ffprobe_path()
    if not probe:
        return None
    try:
        result = subprocess.run(
            [
                probe, "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height",
                "-of", "csv=p=0:s=,",
                str(path),
            ],
            capture_output=True, text=True, check=False, timeout=15,
        )
    except Exception:
        return None
    if result.returncode != 0:
        return None
    parts = (result.stdout or "").strip().split(",")
    if len(parts) < 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def probe_video_duration(path: Path) -> float | None:
    probe = ffprobe_path()
    if not probe:
        return None
    try:
        result = subprocess.run(
            [
                probe, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=nw=1:nk=1",
                str(path),
            ],
            capture_output=True, text=True, check=False, timeout=15,
        )
    except Exception:
        return None
    raw = (result.stdout or "").strip()
    try:
        return float(raw) if raw else None
    except ValueError:
        return None


def is_vertical_9_16(width: int, height: int, *, min_height: int = 720) -> bool:
    """True for vertical sources whose aspect is close to 9:16 (TikTok/Reels native)."""
    if width <= 0 or height < min_height or height <= width:
        return False
    ratio = width / height
    return 0.50 <= ratio <= 0.62


def ffmpeg_candidates() -> list[Path]:
    candidates: list[Path] = []
    local_appdata = os.environ.get("LOCALAPPDATA")
    if local_appdata:
        package_root = Path(local_appdata) / "Microsoft" / "WinGet" / "Packages"
        if package_root.exists():
            candidates.extend(package_root.glob("*FFmpeg*/**/bin/ffmpeg.exe"))
    return candidates


def build_ytdlp_command(
    url: str,
    raw_dir: Path,
    ytdlp_path: str | None = None,
    python_executable: str | None = None,
    allow_path_lookup: bool = True,
) -> list[str]:
    prefix = build_ytdlp_prefix(
        ytdlp_path=ytdlp_path,
        python_executable=python_executable,
        allow_path_lookup=allow_path_lookup,
    )
    command = [
        *prefix,
        "--no-playlist",
        "--paths",
        str(raw_dir),
        "--output",
        "%(title).80s.%(ext)s",
    ]
    if is_tiktok_video_url(url):
        command.extend([
            "--format",
            "bv*+ba/b",
            "--merge-output-format",
            "mp4",
        ])
    command.append(url)
    return command


def build_ytdlp_prefix(
    ytdlp_path: str | None = None,
    python_executable: str | None = None,
    allow_path_lookup: bool = True,
) -> list[str]:
    executable = ytdlp_path
    if allow_path_lookup:
        executable = executable or find_executable("yt-dlp", python_user_scripts_candidates("yt-dlp.exe"))
    return [executable] if executable else [python_executable or sys.executable, "-m", "yt_dlp"]


def default_value_for_column(column: str) -> str:
    defaults = {
        "Record ID": "",
        "Source Type": "Auto",
        "Status": "Pending",
        "Done": "FALSE",
        "Analysis Done": "FALSE",
    }
    return defaults.get(column, "")


def normalize_record(record: dict[str, str]) -> dict[str, str]:
    normalized = {}
    for column in REQUIRED_COLUMNS:
        value = record.get(column)
        normalized[column] = (value if value not in (None, "") else default_value_for_column(column)).strip()
    return normalized


def ensure_masterlist_columns(masterlist_path: Path) -> None:
    if not masterlist_path.exists():
        write_masterlist(masterlist_path, [])
        return
    else:
        with masterlist_path.open("r", newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            original_rows = list(reader)
            rows = [normalize_record(row) for row in original_rows]

    current_rows = []
    for row in original_rows:
        current_rows.append({column: (row.get(column) or "").strip() for column in REQUIRED_COLUMNS})
    rows = backfill_record_identity(rows)
    if fieldnames == REQUIRED_COLUMNS and current_rows == rows:
        return
    write_masterlist(masterlist_path, rows)


def read_masterlist(masterlist_path: Path) -> list[dict[str, str]]:
    ensure_masterlist_columns(masterlist_path)
    with masterlist_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Masterlist is missing required columns: {', '.join(missing)}")
        return [normalize_record(row) for row in reader]


def write_masterlist(masterlist_path: Path, rows: list[dict[str, str]], sync_excel: bool = True) -> None:
    rows = backfill_record_identity(rows)
    with masterlist_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
    if sync_excel:
        sync_excel_masterlist(masterlist_path, rows)


def find_workbook_path(masterlist_path: Path) -> Path | None:
    for suffix in (".xlsm", ".xlsx"):
        candidate = masterlist_path.with_suffix(suffix)
        if candidate.exists():
            return candidate
    return None


def sync_excel_masterlist(masterlist_path: Path, rows: list[dict[str, str]]) -> None:
    workbook_path = find_workbook_path(masterlist_path)
    if workbook_path is None:
        return
    try:
        from openpyxl import Workbook, load_workbook
    except ImportError:
        return

    keep_vba = workbook_path.suffix.lower() == ".xlsm"
    if workbook_path.exists():
        workbook = load_workbook(workbook_path, keep_vba=keep_vba)
    else:
        workbook = Workbook()
    sheet = workbook["List of Link Shopee VIdeo"] if "List of Link Shopee VIdeo" in workbook.sheetnames else workbook.active
    sheet.title = "List of Link Shopee VIdeo"
    if sheet.max_row:
        sheet.delete_rows(1, sheet.max_row)
    if sheet.max_column:
        sheet.delete_cols(1, sheet.max_column)
    for column_index, header in enumerate(REQUIRED_COLUMNS, start=1):
        sheet.cell(1, column_index).value = header
    for row_index, row in enumerate(rows, start=2):
        normalized = normalize_record(row)
        for column_index, header in enumerate(REQUIRED_COLUMNS, start=1):
            sheet.cell(row_index, column_index).value = normalized[header]
    widths = {
        "A": 14,  # Record ID
        "B": 14,  # Date
        "C": 44,  # Product Link
        "D": 28,  # Product Name
        "E": 22,  # Shop Name
        "F": 18,  # Source Type
        "G": 16,  # Status
        "H": 12,  # Done
        "I": 14,  # Analysis Done
        "J": 34,  # Notes
        "K": 22,  # Last Processed At
        "L": 36,  # Output Folder
        "M": 36,  # Output File
        "N": 28,  # Hook
    }
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    workbook.save(workbook_path)


def master_row_from_record(record: dict[str, str], row_number: int) -> MasterRow:
    return MasterRow(
        row_number=row_number,
        record_id=record.get("Record ID", ""),
        product_link=record["Product Link"],
        product_name=record["Product Name"],
        shop_name=record["Shop Name"],
        source_type=record["Source Type"] or "Auto",
        status=record["Status"],
        data=record,
    )


def load_rows(masterlist_path: Path, force: bool = False) -> list[MasterRow]:
    rows = []
    for index, record in enumerate(read_masterlist(masterlist_path), start=2):
        row = master_row_from_record(record, index)
        if row.product_link and is_pending_status(row.status, force=force):
            rows.append(row)
    return rows


def request_headers(url: str) -> dict[str, str]:
    if urlparse(url).netloc.lower().endswith("tiktok.com"):
        return {
            "User-Agent": TIKTOK_PAGE_USER_AGENT,
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.tiktok.com/",
        }
    return {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "*/*",
    }


def page_request_headers(url: str) -> dict[str, str]:
    if is_shopee_url(url):
        return {
            "User-Agent": SHOPEE_PAGE_USER_AGENT,
            "Accept": "text/html,*/*",
            "Accept-Language": "en-MY,en;q=0.9",
        }
    if is_tiktok_video_url(url) or urlparse(url).netloc.lower().endswith("tiktok.com"):
        return {
            "User-Agent": TIKTOK_PAGE_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.tiktok.com/",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
    return request_headers(url)


def request_url(url: str, headers: dict[str, str] | None = None):
    request = Request(
        url,
        headers=headers or request_headers(url),
    )
    return urlopen(request, timeout=45)


def request_url_with_cookies(url: str, cookie_jar: CookieJar, headers: dict[str, str] | None = None):
    opener = build_opener(HTTPCookieProcessor(cookie_jar))
    request = Request(
        url,
        headers=headers or request_headers(url),
    )
    return opener.open(request, timeout=45)


def canonicalize_tiktok_url(
    url: str,
    request_fn=request_url,
) -> str:
    if not is_tiktok_video_url(url):
        return url
    parsed = urlparse(url)
    if ("/video/" in parsed.path or "/photo/" in parsed.path) and parsed.netloc.lower() not in {"vt.tiktok.com", "vm.tiktok.com"}:
        return url

    oembed_url = f"https://www.tiktok.com/oembed?url={quote(url, safe='')}"
    try:
        with request_fn(oembed_url, request_headers(oembed_url)) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception:
        return url

    for candidate in (payload.get("html", ""), payload.get("author_url", "")):
        match = re.search(r"https://www\.tiktok\.com/@[^\"'?\s]+/(?:video|photo)/\d+", candidate)
        if match:
            return match.group(0)
    return url


def tiktok_video_id_from_url(url: str) -> str | None:
    match = re.search(r"/(?:video|photo)/(\d+)", urlparse(url).path)
    return match.group(1) if match else None


def tiktok_username_from_url(url: str) -> str | None:
    match = re.search(r"/@([^/?#]+)/?(?:video|photo)/\d+", urlparse(url).path)
    return f"@{match.group(1)}" if match else None


def first_nonempty(*values: str) -> str | None:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def unique_urls(urls: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for url in urls:
        if not isinstance(url, str):
            continue
        candidate = url.strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        ordered.append(candidate)
    return ordered


def collect_tiktok_image_candidates(value) -> list[str]:
    urls: list[str] = []
    if isinstance(value, dict):
        direct = first_nonempty(value.get("url"), value.get("src"))
        if direct:
            urls.append(direct)
        url_list = value.get("urlList") or value.get("url_list") or []
        if isinstance(url_list, list):
            urls.extend(url for url in url_list if isinstance(url, str))
        for item in value.values():
            urls.extend(collect_tiktok_image_candidates(item))
    elif isinstance(value, list):
        for item in value:
            urls.extend(collect_tiktok_image_candidates(item))
    return unique_urls(urls)


def build_tiktok_photo_image_urls(item_struct: dict) -> list[str]:
    image_post = item_struct.get("imagePost") or item_struct.get("image_post")
    if image_post:
        image_urls = collect_tiktok_image_candidates(image_post)
        if image_urls:
            return image_urls

    video = item_struct.get("video") or {}
    zoom_cover = video.get("zoomCover") or {}
    best_zoom_cover = None
    if isinstance(zoom_cover, dict) and zoom_cover:
        numeric_sizes = []
        for key, value in zoom_cover.items():
            if isinstance(value, str) and value.strip():
                try:
                    numeric_sizes.append((int(key), value.strip()))
                except (TypeError, ValueError):
                    continue
        if numeric_sizes:
            best_zoom_cover = max(numeric_sizes)[1]

    fallback_image = first_nonempty(
        (video.get("imagePostCover") or {}).get("imageURL", {}).get("url"),
        video.get("originCover", ""),
        best_zoom_cover or "",
        video.get("cover", ""),
        video.get("dynamicCover", ""),
    )
    return [fallback_image] if fallback_image else []


def extract_tiktok_item_struct(payload: dict[str, object], page_url: str) -> dict[str, object] | None:
    video_id = tiktok_video_id_from_url(page_url) or ""
    candidates = [
        payload.get("__DEFAULT_SCOPE__", {}).get("webapp.video-detail", {}).get("itemInfo", {}).get("itemStruct", {}),
        payload.get("props", {}).get("pageProps", {}).get("itemInfo", {}).get("itemStruct", {}),
        payload.get("itemInfo", {}).get("itemStruct", {}),
        payload.get("ItemModule", {}).get(video_id, {}),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and candidate:
            return candidate
    return None


def build_tiktok_media_bundle(payload: dict[str, object], page_url: str) -> dict[str, object] | None:
    if not is_tiktok_video_url(page_url):
        return None
    item_struct = extract_tiktok_item_struct(payload, page_url)
    if not isinstance(item_struct, dict):
        return None
    video = item_struct.get("video") or {}
    music = item_struct.get("music") or {}
    video_id = str(item_struct.get("id") or tiktok_video_id_from_url(page_url) or "").strip()
    video_urls = unique_urls([
        first_nonempty(video.get("downloadAddr", ""), video.get("playAddr", "")) or "",
        first_nonempty(video.get("playAddr", "")) or "",
    ])
    image_urls = build_tiktok_photo_image_urls(item_struct)
    audio_url = first_nonempty(music.get("playUrl", ""))
    if video_urls:
        kind = "video"
    elif image_urls:
        kind = "photo_mode"
    else:
        kind = "unknown"

    return {
        "kind": kind,
        "post_type": kind,
        "video_id": video_id,
        "video_urls": video_urls,
        "image_urls": image_urls,
        "audio_url": audio_url,
    }


def extract_tiktok_media_bundle_from_html(page_url: str, body: str) -> dict[str, object] | None:
    if not is_tiktok_video_url(page_url):
        return None

    script_patterns = [
        r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>',
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        r'<script id="SIGI_STATE" type="application/json">(.*?)</script>',
    ]
    for pattern in script_patterns:
        match = re.search(pattern, body, flags=re.DOTALL)
        if not match:
            continue
        try:
            payload = json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
        bundle = build_tiktok_media_bundle(payload, page_url)
        if bundle:
            return bundle
    return None


def build_tiktok_node_share_url(url: str) -> str | None:
    username = tiktok_username_from_url(url)
    video_id = tiktok_video_id_from_url(url)
    if not username or not video_id:
        return None
    return f"https://www.tiktok.com/node/share/video/{username.lstrip('@')}/{video_id}"


def build_tiktok_id_lookup_url(url: str) -> str | None:
    video_id = tiktok_video_id_from_url(url)
    if not video_id:
        return None
    return f"https://www.tiktok.com/@tiktok/video/{video_id}"


def fetch_tiktok_json(url: str, cookie_jar: CookieJar) -> dict[str, object] | None:
    try:
        with request_url_with_cookies(url, cookie_jar, page_request_headers(url)) as response:
            return json.loads(response.read().decode("utf-8", errors="replace"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None


def fetch_tiktok_html(url: str, cookie_jar: CookieJar) -> str | None:
    try:
        with request_url_with_cookies(url, cookie_jar, page_request_headers(url)) as response:
            return response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError):
        return None


def build_tiktok_media_bundle_from_ytdlp_metadata(
    metadata: dict[str, object],
    page_url: str,
) -> dict[str, object] | None:
    if not is_tiktok_video_url(page_url):
        return None

    video_id = str(metadata.get("id") or tiktok_video_id_from_url(page_url) or "").strip()
    formats = metadata.get("formats") or []
    video_urls: list[str] = []
    audio_url = ""
    if isinstance(formats, list):
        ranked_video_formats: list[tuple[tuple[int, int, int], str]] = []
        for fmt in formats:
            if not isinstance(fmt, dict):
                continue
            media_url = str(fmt.get("url") or "").strip()
            if not media_url:
                continue
            vcodec = str(fmt.get("vcodec") or "").strip().lower()
            ext = str(fmt.get("ext") or "").strip().lower()
            if vcodec and vcodec != "none":
                rank = (
                    int(fmt.get("height") or 0),
                    int(fmt.get("tbr") or 0),
                    1 if ext in {"mp4", "mov", "m4v", "webm"} else 0,
                )
                ranked_video_formats.append((rank, media_url))
            elif not audio_url and str(fmt.get("acodec") or "").strip().lower() not in {"", "none"}:
                audio_url = media_url
        ranked_video_formats.sort(reverse=True)
        video_urls = unique_urls(url for _, url in ranked_video_formats)

    thumbnails = metadata.get("thumbnails") or []
    ranked_images: list[tuple[int, str]] = []
    if isinstance(thumbnails, list):
        for thumb in thumbnails:
            if not isinstance(thumb, dict):
                continue
            image_url = str(thumb.get("url") or "").strip()
            if image_url:
                ranked_images.append((int(thumb.get("preference") or 0), image_url))
    ranked_images.sort(reverse=True)
    image_urls = unique_urls(url for _, url in ranked_images)
    thumbnail = str(metadata.get("thumbnail") or "").strip()
    if thumbnail:
        image_urls = unique_urls([thumbnail, *image_urls])

    if video_urls:
        kind = "video"
    elif image_urls:
        kind = "photo_mode"
    else:
        kind = "unknown"

    return {
        "kind": kind,
        "post_type": kind,
        "video_id": video_id,
        "video_urls": video_urls,
        "image_urls": image_urls,
        "audio_url": audio_url or None,
    }


def discover_tiktok_media_bundle_from_ytdlp(url: str) -> dict[str, object] | None:
    command = [
        *build_ytdlp_prefix(allow_path_lookup=True),
        "--dump-single-json",
        "--skip-download",
        "--no-warnings",
        url,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        metadata = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(metadata, dict):
        return None
    return build_tiktok_media_bundle_from_ytdlp_metadata(metadata, url)


def unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / safe_filename(filename)
    if not candidate.exists():
        return candidate
    for number in range(2, 1000):
        numbered = directory / f"{candidate.stem}-{number}{candidate.suffix}"
        if not numbered.exists():
            return numbered
    raise FileExistsError(f"Could not create unique filename for {candidate}")


def replace_path(directory: Path, filename: str) -> Path:
    target = directory / safe_filename(filename)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    return target


def filename_from_url(url: str, fallback: str = "media") -> str:
    parsed = urlparse(url)
    name = Path(unquote(parsed.path)).name
    if Path(name).suffix.lower() in MEDIA_EXTENSIONS:
        return name
    return fallback


def discover_tiktok_media_bundle(url: str) -> dict[str, object] | None:
    canonical_url = canonicalize_tiktok_url(url)
    cookie_jar = CookieJar()

    body = fetch_tiktok_html(canonical_url, cookie_jar)
    if body:
        bundle = extract_tiktok_media_bundle_from_html(canonical_url, body)
        if bundle and bundle.get("kind") != "unknown":
            return bundle

    node_share_url = build_tiktok_node_share_url(canonical_url)
    if node_share_url:
        payload = fetch_tiktok_json(node_share_url, cookie_jar)
        bundle = build_tiktok_media_bundle(payload or {}, canonical_url) if payload else None
        if bundle and bundle.get("kind") != "unknown":
            return bundle

    id_lookup_url = build_tiktok_id_lookup_url(canonical_url)
    if id_lookup_url and id_lookup_url != canonical_url:
        fallback_body = fetch_tiktok_html(id_lookup_url, cookie_jar)
        if fallback_body:
            bundle = extract_tiktok_media_bundle_from_html(canonical_url, fallback_body)
            if bundle:
                return bundle

    ytdlp_bundle = discover_tiktok_media_bundle_from_ytdlp(canonical_url)
    if ytdlp_bundle:
        return ytdlp_bundle

    if body:
        return extract_tiktok_media_bundle_from_html(canonical_url, body)
    return None


def download_url(url: str, target_dir: Path, fallback_name: str = "media") -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = filename_from_url(url, fallback=fallback_name)
    try:
        with request_url(url) as response:
            content_type = response.headers.get("content-type", "").lower()
            suffix = Path(filename).suffix.lower()
            if suffix not in MEDIA_EXTENSIONS:
                suffix = extension_from_content_type(content_type)
                filename = f"{fallback_name}{suffix}"
            target_path = unique_path(target_dir, filename)
            with target_path.open("wb") as output:
                shutil.copyfileobj(response, output)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Download failed: {exc}") from exc
    return target_path


def extension_from_content_type(content_type: str) -> str:
    if "audio/mp4" in content_type or "mp4a" in content_type:
        return ".m4a"
    if "audio/mpeg" in content_type or "audio/mp3" in content_type:
        return ".mp3"
    if "audio/aac" in content_type:
        return ".aac"
    if "audio/ogg" in content_type:
        return ".ogg"
    if "audio/webm" in content_type:
        return ".webm"
    if "audio/wav" in content_type or "audio/x-wav" in content_type:
        return ".wav"
    if "mp4" in content_type:
        return ".mp4"
    if "webm" in content_type:
        return ".webm"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    if "png" in content_type:
        return ".png"
    if "webp" in content_type:
        return ".webp"
    return ".bin"


def extract_media_urls_from_html(page_url: str, body: str) -> list[str]:
    body = html.unescape(body)
    found = set()
    patterns = [
        r'https?://[^"\'<>\\\s),]+\.(?:mp4|mov|m4v|webm|jpg|jpeg|png|webp)(?:\?[^"\'<>\\\s),]*)?',
        r'(?:src|href|content)=["\']([^"\']+\.(?:mp4|mov|m4v|webm|jpg|jpeg|png|webp)(?:\?[^"\']*)?)["\']',
    ]
    if is_shopee_url(page_url):
        patterns.extend(
            [
                r'https?://down-my\.img\.susercontent\.com/file/[^"\'<>\\\s),]+',
                r'https?://(?:down-[a-z-]+|mms)\.vod\.susercontent\.com/[^"\'<>\\\s),]+\.mp4(?:\?[^"\'<>\\\s),]*)?',
            ]
        )
    for pattern in patterns:
        for match in re.finditer(pattern, body, flags=re.IGNORECASE):
            url = match.group(1) if match.lastindex else match.group(0)
            found.add(urljoin(page_url, url))

    if is_shopee_url(page_url):
        found = {url for url in found if is_shopee_cdn_media_url(url)}

    return filter_media_urls(found)


def discover_media_urls(page_url: str) -> list[str]:
    page_url = strip_query_for_shopee_product_url(page_url)
    try:
        with request_url(page_url, page_request_headers(page_url)) as response:
            body = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Page fetch failed: {exc}") from exc

    return extract_media_urls_from_html(page_url, body)


def media_priority(url: str) -> tuple[int, str]:
    suffix = Path(unquote(urlparse(url).path)).suffix.lower()
    return (0 if suffix in VIDEO_EXTENSIONS else 1, url)


def video_quality_score(url: str) -> int:
    scores = [int(value) for value in re.findall(r"\.(\d{6,})\.mp4(?:\?|$)", url, flags=re.IGNORECASE)]
    return max(scores) if scores else 0


def select_media_urls_for_download(media_urls: list[str]) -> list[str]:
    video_urls = [
        url for url in media_urls
        if Path(unquote(urlparse(url).path)).suffix.lower() in VIDEO_EXTENSIONS
    ]
    if video_urls:
        return [max(video_urls, key=video_quality_score)]
    return media_urls[:5]


def is_site_chrome_media_url(url: str) -> bool:
    parsed = urlparse(url)
    name = Path(unquote(urlparse(url).path)).name.lower()
    path = unquote(parsed.path).lower()
    return (
        "favicon" in name
        or "splash" in name
        or name.startswith("icon_")
        or name.startswith("ios_icon")
        or name.startswith("apple-touch-icon")
        or name.startswith("android-chrome")
        or name.startswith("logo")
        or "sprite" in name
        or "placeholder" in name
        or "shopee-mobilemall-live-sg/productdetailspage/" in path
        or "shopee-pcmall-live-sg/productdetailspage/" in path
    )


def filter_media_urls(urls: Iterable[str]) -> list[str]:
    filtered = [url for url in urls if not is_site_chrome_media_url(url)]
    return sorted(filtered, key=media_priority)


def download_with_ytdlp(url: str, raw_dir: Path) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    before = {path.resolve() for path in raw_dir.iterdir()} if raw_dir.exists() else set()
    canonical_url = canonicalize_tiktok_url(url)
    command = build_ytdlp_command(canonical_url, raw_dir)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        media = []
    else:
        after = {path.resolve() for path in raw_dir.iterdir()}
        media = sorted(path for path in after - before if path.suffix.lower() in MEDIA_EXTENSIONS)
    if media:
        if is_tiktok_video_url(canonical_url) and all(path.suffix.lower() in IMAGE_EXTENSIONS for path in media):
            bundle = discover_tiktok_media_bundle(canonical_url)
            if bundle:
                bundle_media = download_tiktok_bundle(bundle, raw_dir)
                if bundle_media:
                    for existing in media:
                        if existing not in bundle_media:
                            existing.unlink(missing_ok=True)
                    cleanup_non_media_outputs(raw_dir)
                    return bundle_media
            download_tiktok_photo_audio(canonical_url, raw_dir)
        cleanup_non_media_outputs(raw_dir)
        return media
    if is_tiktok_video_url(canonical_url):
        bundle = discover_tiktok_media_bundle(canonical_url)
        if bundle:
            bundle_media = download_tiktok_bundle(bundle, raw_dir)
            if bundle_media:
                cleanup_non_media_outputs(raw_dir)
                return bundle_media
        thumbnails = download_tiktok_thumbnail_with_ytdlp(canonical_url, raw_dir)
        if thumbnails:
            # Photo-mode post detected: attempt to grab background audio for the render.
            download_tiktok_photo_audio(canonical_url, raw_dir)
        cleanup_non_media_outputs(raw_dir)
        return thumbnails
    cleanup_non_media_outputs(raw_dir)
    return []


def cleanup_non_media_outputs(directory: Path) -> list[Path]:
    """Remove yt-dlp scratch files from directory, preserving media and background audio."""
    removed: list[Path] = []
    if not directory.exists():
        return removed
    for path in directory.iterdir():
        if path.is_dir():
            continue
        if path.suffix.lower() in MEDIA_EXTENSIONS:
            continue
        if path.stem == "background" and path.suffix.lower() in AUDIO_EXTENSIONS:
            continue
        path.unlink(missing_ok=True)
        removed.append(path)
    return removed


def infer_image_extension(path: Path) -> str | None:
    with path.open("rb") as handle:
        header = handle.read(16)
    if header.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if header.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if header.startswith(b"GIF87a") or header.startswith(b"GIF89a"):
        return ".gif"
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return ".webp"
    return None


def normalize_downloaded_image_artifact(path: Path) -> Path:
    if path.suffix.lower() != ".image":
        return path
    extension = infer_image_extension(path) or ".jpg"
    target = replace_path(path.parent, f"{path.stem}{extension}")
    path.rename(target)
    return target


def download_tiktok_thumbnail_with_ytdlp(url: str, raw_dir: Path) -> list[Path]:
    before = {path.resolve() for path in raw_dir.iterdir()} if raw_dir.exists() else set()
    command = [
        *build_ytdlp_prefix(),
        "--skip-download",
        "--write-thumbnail",
        "--force-overwrites",
        "--paths",
        str(raw_dir),
        "--output",
        "%(id)s.%(ext)s",
        url,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    after = {path.resolve() for path in raw_dir.iterdir()}
    created = [Path(path) for path in sorted(after - before)]
    images: list[Path] = []
    for artifact in created:
        if artifact.suffix.lower() in IMAGE_EXTENSIONS:
            images.append(artifact)
        elif artifact.suffix.lower() == ".image":
            images.append(normalize_downloaded_image_artifact(artifact))
    if images:
        return images

    video_id = tiktok_video_id_from_url(url)
    if video_id:
        existing_images = sorted(
            path for path in raw_dir.iterdir()
            if path.is_file()
            and path.stem == video_id
            and path.suffix.lower() in IMAGE_EXTENSIONS
        )
        if existing_images:
            return existing_images
    return []


def download_tiktok_photo_audio(url: str, raw_dir: Path) -> Path | None:
    """Download the background audio track from a TikTok photo-mode (carousel) post.

    Saves the audio as ``background.<ext>`` inside *raw_dir*.
    Returns the path on success, or ``None`` if unavailable or if yt-dlp fails.
    Photo-mode posts have no downloadable video stream but always carry a music track;
    the audio file is later picked up by ``render_video`` and merged into the rendered output.
    """
    for existing in raw_dir.glob("background.*"):
        existing.unlink(missing_ok=True)
    command = [
        *build_ytdlp_prefix(),
        "--no-playlist",
        "--format", "bestaudio",
        "--force-overwrites",
        "--paths", str(raw_dir),
        "--output", "background.%(ext)s",
        url,
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode == 0:
        for target in sorted(raw_dir.glob("background.*")):
            if target.suffix.lower() in AUDIO_EXTENSIONS and target.stat().st_size > 0:
                return target
    for target in raw_dir.glob("background.*"):
        target.unlink(missing_ok=True)
    return None


def download_tiktok_bundle(bundle: dict[str, object], raw_dir: Path) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    kind = str(bundle.get("post_type") or bundle.get("kind") or "").strip().lower()
    video_id = str(bundle.get("video_id", "")).strip() or "tiktok"

    if kind == "video":
        for media_url in bundle.get("video_urls", []) or []:
            try:
                target = download_url(str(media_url), raw_dir, fallback_name=video_id)
            except RuntimeError:
                continue
            if target.suffix.lower() in VIDEO_EXTENSIONS:
                desired = raw_dir / safe_filename(f"{video_id}{target.suffix.lower()}")
                if target != desired:
                    desired.unlink(missing_ok=True)
                    target.rename(desired)
                    target = desired
                return [target]
        return []

    if kind == "photo_mode":
        for existing in raw_dir.iterdir():
            if existing.is_file() and existing.suffix.lower() in IMAGE_EXTENSIONS:
                existing.unlink(missing_ok=True)
        media_files: list[Path] = []
        for index, media_url in enumerate(bundle.get("image_urls", []) or [], start=1):
            fallback_name = video_id if index == 1 else f"{video_id}-{index}"
            try:
                target = download_url(str(media_url), raw_dir, fallback_name=fallback_name)
            except RuntimeError:
                continue
            if target.suffix.lower() == ".image":
                target = normalize_downloaded_image_artifact(target)
            desired = raw_dir / safe_filename(f"{fallback_name}{target.suffix.lower()}")
            if target != desired:
                desired.unlink(missing_ok=True)
                target.rename(desired)
                target = desired
            if target.suffix.lower() in IMAGE_EXTENSIONS:
                media_files.append(target)

        for existing in raw_dir.glob("background.*"):
            existing.unlink(missing_ok=True)
        audio_url = str(bundle.get("audio_url", "") or "").strip()
        if audio_url:
            try:
                audio_target = download_url(audio_url, raw_dir, fallback_name="background")
                if audio_target.suffix.lower() not in AUDIO_EXTENSIONS:
                    audio_target.unlink(missing_ok=True)
            except RuntimeError:
                pass
        return media_files

    return []


def find_background_audio(raw_dir: Path) -> Path | None:
    for candidate in sorted(raw_dir.glob("background.*")):
        if candidate.suffix.lower() in AUDIO_EXTENSIONS and candidate.is_file():
            return candidate
    return None


def is_tiktok_photo_mode_result(url: str, raw_files: Iterable[Path]) -> bool:
    files = list(raw_files)
    return bool(files) and is_tiktok_video_url(url) and all(path.suffix.lower() in IMAGE_EXTENSIONS for path in files)


def group_photo_mode_images(seed_image: Path, raw_dir: Path) -> list[Path]:
    stem = seed_image.stem.split("-")[0]
    ordered: list[Path] = []
    matches: list[Path] = []
    for candidate in raw_dir.iterdir():
        if not candidate.is_file() or candidate.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        if candidate.stem == stem or candidate.stem.startswith(f"{stem}-"):
            matches.append(candidate)
    for candidate in sorted(
        matches,
        key=lambda path: (
            0 if path.stem == stem else 1,
            int(path.stem.split("-")[-1]) if "-" in path.stem and path.stem.split("-")[-1].isdigit() else 0,
            path.name.lower(),
        ),
    ):
        ordered.append(candidate)
    return ordered or [seed_image]


def build_photo_mode_status_message(image_count: int, edited_count: int, has_audio: bool) -> str:
    raw_count = image_count + (1 if has_audio else 0)
    note = " (photo-mode post with background audio)" if has_audio else " (photo-mode post)"
    return f"Downloaded {raw_count} media file(s); edited {edited_count} slideshow video file(s){note}"


def clear_rendered_outputs(edited_dir: Path) -> None:
    if not edited_dir.exists():
        return
    for candidate in edited_dir.iterdir():
        if candidate.is_file() and candidate.suffix.lower() in VIDEO_EXTENSIONS:
            candidate.unlink(missing_ok=True)


def copy_local_media(source: Path, target_dir: Path) -> Path:
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = unique_path(target_dir, source.name)
    shutil.copy2(source, target_path)
    return target_path


def collect_media(row: MasterRow, raw_dir: Path) -> list[Path]:
    link = row.product_link.strip()
    local_path = Path(link)
    if local_path.exists() and local_path.is_file():
        return [copy_local_media(local_path, raw_dir)]

    if is_direct_media_url(link):
        return [download_url(link, raw_dir, fallback_name=f"row-{row.row_number}")]

    ytdlp_files = download_with_ytdlp(link, raw_dir)
    if ytdlp_files:
        return ytdlp_files

    media_urls = discover_media_urls(link)
    if not media_urls:
        return []

    downloaded = []
    for index, media_url in enumerate(select_media_urls_for_download(media_urls), start=1):
        try:
            downloaded.append(download_url(media_url, raw_dir, fallback_name=f"row-{row.row_number}-{index}"))
        except RuntimeError:
            continue
    return downloaded


def escape_drawtext(value: str) -> str:
    """Escape special characters for FFmpeg drawtext filter values.

    Characters that must be escaped:
    - backslash, colon, single-quote (filter syntax)
    - semicolon (filter_complex chain separator)
    - percent (drawtext text expansion function trigger)
    - square brackets (stream label delimiters in filter_complex)
    """
    return (
        value
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(":", "\\:")
        .replace("'", "\\'")
        .replace("[", "\\[")
        .replace("]", "\\]")
        .replace("%", "%%")
    )


def build_hook_drawtext(font: str, hook_text: str) -> str:
    """Top-of-frame drawtext clause for a hook that shows for 1.5s and fades over the last 0.3s."""
    text = escape_drawtext(hook_text)
    return (
        f"drawtext=fontfile='{font}':text='{text}':"
        "x=(w-text_w)/2:y=120:fontsize=64:"
        "fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=24:"
        "enable='between(t,0,1.5)':"
        "alpha='if(lt(t,1.2),1,if(lt(t,1.5),(1.5-t)/0.3,0))'"
    )


def _resolve_font() -> str:
    """Return an FFmpeg-escaped font path, with fallback if arial.ttf is missing."""
    candidates = [
        Path("C:/Windows/Fonts/arial.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/tahoma.ttf"),
        Path("C:/Windows/Fonts/verdana.ttf"),
    ]
    for candidate in candidates:
        if candidate.exists():
            # FFmpeg drawtext requires colon-escaped Windows paths with forward slashes
            return str(candidate).replace("\\", "/").replace(":", "\\:")
    # Last resort: return arial and let FFmpeg error if truly missing
    return "C\\:/Windows/Fonts/arial.ttf"


def build_ffmpeg_command(
    ffmpeg: str,
    raw_path: Path,
    output_path: Path,
    caption: str,
    render_mode: str = "auto",
    background_audio: Path | None = None,
    hook_text: str | None = None,
) -> list[str]:
    """Build an FFmpeg command for rendering a product video.

    Render modes:
    - ``auto``         — ``light`` for video sources, ``vertical-blur`` for image sources
    - ``light``        — scale-to-fit with black padding, small caption, preserves audio
    - ``vertical-blur``— blurred background canvas composition, larger caption, preserves audio
    Image sources always use the ``vertical-blur`` composition regardless of render_mode.
    """
    suffix = raw_path.suffix.lower()
    is_image = suffix in IMAGE_EXTENSIONS

    font = _resolve_font()
    text = escape_drawtext(caption)
    has_caption = bool(caption.strip())

    def _drawtext(x: str, y: str, fontsize: int, boxborderw: int, boxcolor_alpha: str = "0.58") -> str:
        """Return a drawtext clause, or empty string if caption is blank."""
        if not has_caption:
            return ""
        return (
            f",drawtext=fontfile='{font}':text='{text}':"
            f"x={x}:y={y}:fontsize={fontsize}:"
            f"fontcolor=white:box=1:boxcolor=black@{boxcolor_alpha}:boxborderw={boxborderw}"
        )

    if is_image:
        # Image source: loop for 8 s, vertical-blur canvas.
        # Photo-mode TikTok posts: include background audio when available.
        if background_audio and background_audio.exists():
            input_args = ["-loop", "1", "-t", "8", "-i", str(raw_path), "-i", str(background_audio)]
            has_audio = True
        else:
            input_args = ["-loop", "1", "-t", "8", "-i", str(raw_path)]
            has_audio = False
        duration_args: list[str] = ["-shortest"]
        caption_clause = _drawtext("(w-text_w)/2", "h-120", 42, 20)
        filter_graph = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=20:1[bg];"
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            f"[bg][fg]overlay=(W-w)/2:(H-h)/2{caption_clause}[v]"
        )
    else:
        # Video source: 'auto' is resolved by render_video before getting here
        effective_mode = "light" if render_mode == "auto" else render_mode
        input_args = ["-i", str(raw_path)]
        duration_args = []
        has_audio = True

        if effective_mode == "passthrough":
            # Source is already vertical 9:16 — skip blur/padding, just normalize size and caption.
            caption_clause = _drawtext("(w-text_w)/2", "h-180", 48, 22, "0.55")
            filter_graph = (
                f"[0:v]scale=1080:1920:flags=lanczos,setsar=1{caption_clause}[v]"
            )
        elif effective_mode == "light":
            # Scale to fit inside 1080x1920 with black padding; minimal caption
            caption_clause = _drawtext("(w-text_w)/2", "h-100", 40, 18, "0.55")
            filter_graph = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
                f"pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black{caption_clause}[v]"
            )
        else:
            # vertical-blur: blurred background + centred overlay + larger caption
            caption_clause = _drawtext("(w-text_w)/2", "h-220", 54, 28)
            filter_graph = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,boxblur=20:1[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                f"[bg][fg]overlay=(W-w)/2:(H-h)/2{caption_clause}[v]"
            )

    if hook_text and filter_graph.endswith("[v]"):
        # Splice the hook drawtext into the existing graph just before the [v] sink.
        filter_graph = filter_graph[:-3] + "," + build_hook_drawtext(font, hook_text) + "[v]"

    if is_image and background_audio and background_audio.exists():
        # Photo-mode: audio comes from the second input (background.aac)
        # Use '?' suffix so a corrupted/empty audio file won't crash the render.
        audio_map = ["-map", "1:a?", "-c:a", "aac"]
    elif has_audio:
        # Video source: map optional audio from the single input
        audio_map = ["-map", "0:a?", "-c:a", "aac"]
    else:
        audio_map = []

    return [
        ffmpeg,
        "-y",
        *input_args,
        "-filter_complex",
        filter_graph,
        "-map", "[v]",
        *audio_map,
        "-r", "30",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        *duration_args,
        str(output_path),
    ]


def render_video(
    raw_path: Path,
    edited_dir: Path,
    caption: str,
    render_mode: str = "auto",
    *,
    hook_text: str | None = None,
) -> Path | None:
    ffmpeg = find_executable("ffmpeg", ffmpeg_candidates())
    if not ffmpeg:
        return None

    edited_dir.mkdir(parents=True, exist_ok=True)
    effective_mode = render_mode
    if raw_path.suffix.lower() in VIDEO_EXTENSIONS:
        output_name = derive_output_name(raw_path)
        background_audio = None
        # Auto: pick passthrough for already-vertical 9:16 sources, else light
        if render_mode == "auto":
            dims = probe_video_dimensions(raw_path)
            effective_mode = "passthrough" if dims and is_vertical_9_16(*dims) else "light"
    elif raw_path.suffix.lower() in IMAGE_EXTENSIONS:
        output_name = f"{safe_filename(raw_path.stem)}_new.mp4"
        # Photo-mode TikTok: look for background audio saved alongside the thumbnail
        background_audio = find_background_audio(raw_path.parent)
    else:
        return None

    output_path = replace_path(edited_dir, output_name)
    command = build_ffmpeg_command(
        ffmpeg, raw_path, output_path, caption,
        render_mode=effective_mode, background_audio=background_audio,
        hook_text=hook_text,
    )
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=300)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"FFmpeg timed out after 5 minutes for {raw_path.name}")
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed for {raw_path.name}: {result.stderr.strip()[-500:]}")
    return output_path


def render_photo_mode_slideshow(
    image_paths: list[Path],
    edited_dir: Path,
    caption: str,
    render_mode: str = "auto",
    *,
    hook_text: str | None = None,
) -> Path | None:
    if not image_paths:
        return None

    ffmpeg = find_executable("ffmpeg", ffmpeg_candidates())
    if not ffmpeg:
        return None

    edited_dir.mkdir(parents=True, exist_ok=True)
    base_stem = image_paths[0].stem.split("-")[0]
    output_path = replace_path(edited_dir, f"{safe_filename(base_stem)}_new.mp4")
    background_audio = find_background_audio(image_paths[0].parent)
    image_duration = 8 if len(image_paths) == 1 else 3
    font = _resolve_font()
    text = escape_drawtext(caption)

    input_args: list[str] = []
    filter_parts: list[str] = []
    concat_inputs: list[str] = []
    for index, image_path in enumerate(image_paths):
        input_args.extend(["-loop", "1", "-t", str(image_duration), "-i", str(image_path)])
        filter_parts.append(
            f"[{index}:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            f"crop=1080:1920,setsar=1,format=yuv420p[v{index}]"
        )
        concat_inputs.append(f"[v{index}]")

    if len(image_paths) == 1:
        filter_parts.append(
            f"[v0]drawtext=fontfile='{font}':text='{text}':"
            "x=(w-text_w)/2:y=h-120:fontsize=42:"
            "fontcolor=white:box=1:boxcolor=black@0.58:boxborderw=20[v]"
        )
    else:
        filter_parts.append(f"{''.join(concat_inputs)}concat=n={len(image_paths)}:v=1:a=0[base]")
        filter_parts.append(
            f"[base]drawtext=fontfile='{font}':text='{text}':"
            "x=(w-text_w)/2:y=h-120:fontsize=42:"
            "fontcolor=white:box=1:boxcolor=black@0.58:boxborderw=20[v]"
        )

    if hook_text and filter_parts and filter_parts[-1].endswith("[v]"):
        filter_parts[-1] = filter_parts[-1][:-3] + "," + build_hook_drawtext(font, hook_text) + "[v]"

    audio_index = len(image_paths)
    if background_audio and background_audio.exists():
        input_args.extend(["-i", str(background_audio)])
        # Use '?' suffix so a corrupted/empty audio file won't crash the render.
        audio_args = ["-map", f"{audio_index}:a?", "-c:a", "aac", "-shortest"]
    else:
        audio_args = []

    command = [
        ffmpeg,
        "-y",
        *input_args,
        "-filter_complex",
        ";".join(filter_parts),
        "-map",
        "[v]",
        *audio_args,
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(output_path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=300)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"FFmpeg timed out after 5 minutes for slideshow {image_paths[0].name}")
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed for {image_paths[0].name}: {result.stderr.strip()[-500:]}")
    return output_path


def append_log(log_path: Path, row: MasterRow, status: str, message: str, output_file: str = "") -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    exists = log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        if not exists:
            writer.writerow(["timestamp", "row_number", "product_link", "product_name", "shop_name", "status", "message", "output_file"])
        writer.writerow([
            datetime.now().isoformat(timespec="seconds"),
            row.row_number,
            row.product_link,
            row.product_name,
            row.shop_name,
            status,
            message,
            output_file,
        ])


def update_record(record: dict[str, str], status: str, notes: str, output_folder: Path | None, output_files: Iterable[Path]) -> None:
    record["Status"] = status
    record["Done"] = "TRUE" if status in {"Downloaded", "Edited"} else "FALSE"
    record["Notes"] = notes
    record["Last Processed At"] = datetime.now().isoformat(timespec="minutes")
    if output_folder:
        record["Output Folder"] = str(output_folder)
    files = [str(path) for path in output_files]
    record["Output File"] = ""
    if files:
        record["Output File"] = "; ".join(files)


def find_record_by_id(records: list[dict[str, str]], record_id: str) -> dict[str, str] | None:
    """Return the first record whose Record ID matches (case-sensitive)."""
    for record in records:
        if record.get("Record ID", "") == record_id:
            return record
    return None


def media_summary_for_analysis(media_path: Path) -> dict[str, str]:
    """Extract technical metadata from a media file using FFprobe.

    Falls back to 'unknown' for any value that cannot be determined.
    """
    summary = {
        "duration": "unknown",
        "resolution": "unknown",
        "fps": "unknown",
        "audio": "unknown",
    }
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        return summary

    cmd = [
        ffprobe, "-v", "quiet", "-print_format", "json",
        "-show_streams", "-show_format", str(media_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=30)
        if result.returncode != 0:
            return summary
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        fmt = data.get("format", {})
        # Duration from format
        dur = fmt.get("duration")
        if dur:
            try:
                seconds = float(dur)
                summary["duration"] = f"{seconds:.1f}s"
            except ValueError:
                pass
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
        if video_stream:
            w = video_stream.get("width")
            h = video_stream.get("height")
            if w and h:
                summary["resolution"] = f"{w}x{h}"
            # FPS from avg_frame_rate or r_frame_rate
            for key in ("avg_frame_rate", "r_frame_rate"):
                rate = video_stream.get(key, "")
                if rate and "/" in rate:
                    try:
                        num, den = rate.split("/")
                        fps = float(num) / float(den)
                        if fps > 0:
                            summary["fps"] = f"{fps:.2f}"
                            break
                    except (ValueError, ZeroDivisionError):
                        pass
        summary["audio"] = "yes" if audio_stream else "no"
    except Exception:
        pass
    return summary


def choose_analysis_media(product_dir: Path, output_file: str = "") -> Path | None:
    """Choose the best available media file for analysis.

    Priority: edited video > raw video > raw image.
    Falls back to the recorded output_file path if provided.
    """
    # 1. Try output_file from masterlist
    if output_file:
        for path_str in output_file.split(";"):
            candidate = Path(path_str.strip())
            if candidate.exists() and candidate.suffix.lower() in MEDIA_EXTENSIONS:
                return candidate

    # 2. Scan edited/ for videos
    edited_dir = product_dir / "edited"
    if edited_dir.exists():
        edited_videos = sorted(
            (f for f in edited_dir.iterdir() if f.suffix.lower() in VIDEO_EXTENSIONS),
            key=lambda f: f.stat().st_size,
            reverse=True,
        )
        if edited_videos:
            return edited_videos[0]

    # 3. Scan raw/ for videos then images
    raw_dir = product_dir / "raw"
    if raw_dir.exists():
        raw_videos = sorted(
            (f for f in raw_dir.iterdir() if f.suffix.lower() in VIDEO_EXTENSIONS),
            key=lambda f: f.stat().st_size,
            reverse=True,
        )
        if raw_videos:
            return raw_videos[0]
        raw_images = sorted(
            (f for f in raw_dir.iterdir() if f.suffix.lower() in IMAGE_EXTENSIONS),
        )
        if raw_images:
            return raw_images[0]

    return None


def write_analysis_result(product_dir: Path, row: dict[str, str], platform: str, media_path: Path) -> None:
    """Write analysis/analysis-result.md into the product folder."""
    analysis_dir = product_dir / "analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    tech = media_summary_for_analysis(media_path)
    content = f"""# Analysis Result

| Field | Value |
|---|---|
| Record ID | {row.get("Record ID", "")} |
| Platform | {platform} |
| Product Name | {row.get("Product Name", "")} |
| Shop Name | {row.get("Shop Name", "")} |
| Product Link | {row.get("Product Link", "")} |
| Source Type | {row.get("Source Type", "")} |
| Analyzed File | {media_path.name} |

## Technical Summary

| Property | Value |
|---|---|
| Duration | {tech["duration"]} |
| Resolution | {tech["resolution"]} |
| FPS | {tech["fps"]} |
| Audio | {tech["audio"]} |

## Suggested Hooks

- Opening frame: capture the most visually striking moment in the first 3 seconds
- Lead with the product in action, not the packaging
- Consider a before/after or problem/solution opener if the product solves a visible issue

## Suggested Angles

- Lifestyle context: show the product being used in a realistic setting
- Feature callout: zoom in on the key differentiating feature
- Social proof angle: results-focused framing (e.g. "this cleared my room in 5 minutes")

## Suggested Clip Sequence

1. Hook clip — product highlight or dramatic result
2. Context clip — product shown in environment/use
3. Feature clip — close-up on key details
4. CTA clip — price, offer, or call to action

## CTA Suggestions

- "Tap the link in bio to order"
- "Limited stocks — check Shopee now"
- "Free shipping this week only"

## CapCut / Manual Handoff Note

Import the analyzed file into CapCut. Trim to hook within first 1–3 s.
Apply captions from the Product Name and Shop Name. Export at 1080×1920 (9:16) for TikTok/Reels.
"""
    (analysis_dir / "analysis-result.md").write_text(content, encoding="utf-8")


def analyze_row_record(project_root: Path, record: dict[str, str]) -> None:
    """Run analysis on a single row identified by its Record ID.

    Raises RuntimeError if no media is available.
    Updates Analysis Done and refreshes product-info.md on success.
    """
    record_id = record.get("Record ID", "")
    platform = detect_platform(record.get("Product Link", ""))
    product_folder = resolve_product_folder(
        project_root / "output",
        platform,
        record.get("Shop Name", ""),
        record.get("Product Name", ""),
    )
    media_path = choose_analysis_media(product_folder, record.get("Output File", ""))
    if not media_path:
        raise RuntimeError(
            f"No downloaded media found for Record ID {record_id}. Run Download first."
        )
    write_analysis_result(product_folder, record, platform, media_path)
    record["Analysis Done"] = "TRUE"
    write_product_info(product_folder, record, platform)


def is_shopee_shortlink(url: str) -> bool:
    return urlparse(url).netloc.lower().endswith("s.shopee.com.my")


def shopee_slug_to_product_name(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.lstrip("/")
    match = re.match(r"^(.*?)-i\.\d+\.\d+", path)
    if not match:
        return ""
    slug = match.group(1)
    name = unquote(slug).replace("-", " ").strip()
    return re.sub(r"\s+", " ", name)[:200]


def fetch_shopee_page_title(url: str) -> str | None:
    try:
        with request_url(url, page_request_headers(url)) as response:
            body = response.read().decode("utf-8", errors="replace")
    except Exception:
        return None
    og = re.search(r'<meta\s+property="og:title"\s+content="([^"]+)"', body, re.IGNORECASE)
    if og:
        return html.unescape(og.group(1)).strip()
    title = re.search(r"<title>([^<]+)</title>", body, re.IGNORECASE)
    if title:
        return html.unescape(title.group(1)).strip()
    return None


def make_pending_record(url: str, date: str, product_name: str, shop_name: str) -> dict[str, str]:
    record = {column: default_value_for_column(column) for column in REQUIRED_COLUMNS}
    record["Date"] = date
    record["Product Link"] = url
    record["Product Name"] = product_name or ""
    record["Shop Name"] = shop_name or ""
    return normalize_record(record)


def derive_metadata_from_url(url: str, fetch_remote: bool = False) -> dict[str, str]:
    """Best-effort extraction of {platform, product_name, shop_name, error}."""
    result = {"url": url, "platform": "", "product_name": "", "shop_name": "", "error": ""}
    if not url:
        result["error"] = "Empty URL"
        return result
    if is_shopee_shortlink(url):
        result["error"] = "Shopee short links (s.shopee.com.my) are not supported — paste the full product URL."
        return result
    platform = detect_platform(url)
    result["platform"] = platform
    if platform == "Shopee":
        result["product_name"] = shopee_slug_to_product_name(url)
        if fetch_remote:
            title = fetch_shopee_page_title(url)
            if title:
                clean = re.sub(r"\s*\|\s*Shopee.*$", "", title, flags=re.IGNORECASE).strip()
                if clean and len(clean) > len(result["product_name"]):
                    result["product_name"] = clean[:200]
    elif platform == "TikTok":
        username = tiktok_username_from_url(url) or ""
        result["shop_name"] = username
        vid = tiktok_video_id_from_url(url) or ""
        result["product_name"] = f"TikTok {vid}" if vid else "TikTok Video"
        if fetch_remote:
            try:
                bundle = discover_tiktok_media_bundle(url)
                if bundle:
                    desc = bundle.get("desc") or bundle.get("description") or ""
                    if isinstance(desc, str) and desc.strip():
                        result["product_name"] = desc.strip()[:120]
                    author = bundle.get("author_unique_id") or bundle.get("author") or ""
                    if isinstance(author, str) and author.strip():
                        result["shop_name"] = author.strip() if author.startswith("@") else f"@{author.strip()}"
            except Exception:
                pass
    elif platform == "Direct":
        stem = Path(unquote(urlparse(url).path)).stem
        result["product_name"] = stem or "Direct Media"
    return result


def parse_url_lines(text: str) -> list[str]:
    """Extract URLs (one per line, trimmed). Strips empties, comments, and duplicates while preserving order."""
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in (text or "").splitlines():
        candidate = raw.strip()
        if not candidate or candidate.startswith("#"):
            continue
        # Allow lines like "1. https://..." or "- https://..."
        match = re.search(r"https?://\S+", candidate)
        if match:
            candidate = match.group(0)
        if candidate not in seen:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


def bulk_intake_rows(
    urls: Iterable[str],
    masterlist_path: Path,
    *,
    fetch_remote: bool = False,
    today: str | None = None,
) -> list[dict[str, str]]:
    """For each URL, append a Pending row to the masterlist if not already present.

    Returns one dict per URL with keys: url, status (added|skipped|error), message,
    and on success: record_id, platform, product_name, shop_name.
    """
    rows = read_masterlist(masterlist_path)
    existing_links = {r.get("Product Link", "").strip() for r in rows}
    today = today or datetime.now().strftime("%Y-%m-%d")
    results: list[dict[str, str]] = []
    new_records: list[dict[str, str]] = []
    for raw_url in urls:
        url = (raw_url or "").strip()
        if not url:
            continue
        meta = derive_metadata_from_url(url, fetch_remote=fetch_remote)
        if meta["error"]:
            results.append({"url": url, "status": "error", "message": meta["error"]})
            continue
        if url in existing_links:
            results.append({"url": url, "status": "skipped", "message": "Already in masterlist."})
            continue
        record = make_pending_record(url, today, meta["product_name"], meta["shop_name"])
        new_records.append(record)
        existing_links.add(url)
        results.append({
            "url": url,
            "status": "added",
            "platform": meta["platform"],
            "product_name": meta["product_name"],
            "shop_name": meta["shop_name"],
        })
    if new_records:
        rows.extend(new_records)
        write_masterlist(masterlist_path, rows)
        refreshed = read_masterlist(masterlist_path)
        link_to_rid = {r["Product Link"]: r["Record ID"] for r in refreshed}
        for entry in results:
            if entry.get("status") == "added":
                entry["record_id"] = link_to_rid.get(entry["url"], "")
    return results


def call_llm(
    prompt: str,
    *,
    model: str = CAPTIONS_PRIMARY_MODEL,
    fallback_model: str | None = CAPTIONS_FALLBACK_MODEL,
    timeout: int = CAPTIONS_TIMEOUT_SEC,
    router_url: str = CAPTIONS_ROUTER_URL,
    transport=None,
) -> str:
    """Call the local 9Router (OpenAI-compatible) and return the assistant message.

    On HTTP 401 (auth expired) or 5xx, retries once with `fallback_model` if set.
    `transport` is an injection point for tests — a callable taking (url, payload, timeout)
    and returning a (status_code, json_dict) tuple. Defaults to a real HTTP call.
    """

    def _default_transport(url: str, payload: dict, timeout_s: int) -> tuple[int, dict]:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=timeout_s) as response:
                body = response.read().decode("utf-8", errors="replace")
                return response.status, json.loads(body) if body else {}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            try:
                payload_err = json.loads(body) if body else {"error": {"message": body}}
            except Exception:
                payload_err = {"error": {"message": body}}
            return exc.code, payload_err

    transport = transport or _default_transport

    def _attempt(model_id: str) -> tuple[int, dict]:
        return transport(
            router_url,
            {
                "model": model_id,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
            },
            timeout,
        )

    status, payload = _attempt(model)
    if status >= 400 and fallback_model and fallback_model != model:
        status, payload = _attempt(fallback_model)

    if status >= 400:
        message = ""
        if isinstance(payload, dict):
            err = payload.get("error", {})
            if isinstance(err, dict):
                message = err.get("message", "") or ""
        raise RuntimeError(f"LLM call failed ({status}): {message[:300]}")

    try:
        return str(payload["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"LLM response missing content: {exc}; body={str(payload)[:300]}")


def build_caption_pack_prompt(record: dict[str, str], platform: str) -> str:
    product_name = record.get("Product Name", "") or "(unknown product)"
    shop_name = record.get("Shop Name", "") or ""
    product_link = record.get("Product Link", "") or ""
    notes = record.get("Notes", "") or ""
    return f"""You write upload-ready short-form video copy for affiliate creators in Malaysia.

Write captions for this product, returning ONLY a single JSON object — no prose, no markdown fences.

Product: {product_name}
Shop: {shop_name}
Source platform: {platform}
Product link: {product_link}
Pipeline notes: {notes}

JSON keys (ALL required, plain ASCII apart from emojis allowed in caption bodies):
- "tiktok"          : TikTok caption, ≤150 chars, energetic hook + CTA, end with 3-5 hashtags
- "reels"           : Instagram Reels caption, no Shopee link in text, hashtag-heavy
- "shorts_caption"  : YouTube Shorts description, can mention "link in description"
- "shorts_title"    : YouTube Shorts title, ≤60 chars, hook-style
- "shopee"          : Shopee Affiliate caption, longer, persuasive, include CTA to buy
- "hashtags"        : array of 6-10 platform-agnostic hashtags as strings, with the # included

Constraints: native-feeling copy, no clickbait lies, English (mix in BM only if natural). Return raw JSON only."""


def extract_json_object(text: str) -> dict | None:
    """Pull the first {...} JSON object from a string. Tolerates markdown fences and trailing prose."""
    if not text:
        return None
    candidate = text.strip()
    if candidate.startswith("```"):
        # strip ```json ... ``` fences
        candidate = re.sub(r"^```[a-zA-Z]*\s*", "", candidate)
        candidate = re.sub(r"\s*```\s*$", "", candidate)
    # try whole string first
    try:
        result = json.loads(candidate)
        return result if isinstance(result, dict) else None
    except json.JSONDecodeError:
        pass
    # fall back to the first balanced {...} block
    depth = 0
    start = -1
    for index, char in enumerate(candidate):
        if char == "{":
            if depth == 0:
                start = index
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0 and start != -1:
                snippet = candidate[start : index + 1]
                try:
                    result = json.loads(snippet)
                    return result if isinstance(result, dict) else None
                except json.JSONDecodeError:
                    start = -1
    return None


def format_captions_pack(pack: dict, record: dict[str, str]) -> str:
    def section(title: str, body: str) -> str:
        return f"=== {title} ===\n{(body or '').strip()}\n"

    hashtags = pack.get("hashtags") or []
    if isinstance(hashtags, list):
        hashtags_line = " ".join(str(tag).strip() for tag in hashtags if str(tag).strip())
    else:
        hashtags_line = str(hashtags).strip()

    header = (
        f"# Caption Pack — {record.get('Record ID', '')}\n"
        f"# Product: {record.get('Product Name', '')}\n"
        f"# Shop:    {record.get('Shop Name', '')}\n"
        f"# Link:    {record.get('Product Link', '')}\n\n"
    )

    body = "\n".join([
        section("TikTok", str(pack.get("tiktok", ""))),
        section("Reels (Instagram)", str(pack.get("reels", ""))),
        section("Shorts (YouTube)", str(pack.get("shorts_caption", ""))),
        section("Shorts Title", str(pack.get("shorts_title", ""))),
        section("Shopee Affiliate", str(pack.get("shopee", ""))),
        section("Hashtags", hashtags_line),
    ])
    return header + body


def build_hook_prompt(record: dict[str, str], platform: str) -> str:
    product = record.get("Product Name", "") or "(unknown product)"
    shop = record.get("Shop Name", "") or ""
    return f"""Pick the BEST 3-6 word video hook for an affiliate Short/Reel/TikTok about this product.

Product: {product}
Shop: {shop}
Platform: {platform}

Choose the hook style that fits this product:
- Curiosity ("You won't believe step 3", "I didn't expect this")
- Problem-solution ("Tired of X?", "Stop doing this")
- Price-deal ("Only RM 49", "Wait for the discount")

Return ONLY the hook text. No quotes, no punctuation at the end, no explanation, no model commentary. Just the hook."""


def sanitize_hook(text: str) -> str:
    """Strip quotes, surrounding whitespace, trailing punctuation, and collapse whitespace."""
    if not text:
        return ""
    # Remove surrounding quotes / backticks / asterisks repeatedly
    cleaned = text.strip()
    for _ in range(3):
        if cleaned and cleaned[0] in {'"', "'", "`", "*", "“", "”", "‘", "’"}:
            cleaned = cleaned[1:].strip()
        if cleaned and cleaned[-1] in {'"', "'", "`", "*", "“", "”", "‘", "’"}:
            cleaned = cleaned[:-1].strip()
    # Take only the first line if the model returned several
    cleaned = cleaned.splitlines()[0].strip() if cleaned else ""
    # Strip a trailing period or quotation mark
    while cleaned and cleaned[-1] in {".", "!", "?", ":", ";", ",", '"', "'"}:
        # Keep '?' or '!' since hooks often use them — only strip if preceded by other terminator-like chars
        if cleaned[-1] in {"?", "!"}:
            break
        cleaned = cleaned[:-1].strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    # Cap to a reasonable length
    return cleaned[:80]


def generate_hook(
    record: dict[str, str],
    platform: str,
    *,
    model: str = CAPTIONS_PRIMARY_MODEL,
    transport=None,
) -> str | None:
    """Return a sanitized hook string, or None if the model call fails."""
    try:
        response = call_llm(build_hook_prompt(record, platform), model=model, transport=transport)
    except Exception:
        return None
    hook = sanitize_hook(response)
    return hook or None


def write_captions_pack(
    product_dir: Path,
    record: dict[str, str],
    platform: str,
    *,
    model: str = CAPTIONS_PRIMARY_MODEL,
    transport=None,
) -> tuple[Path | None, str | None]:
    """Generate and write a caption pack next to the rendered video.

    Returns (path, error). On success: (path, None). On failure: (None, error_message).
    Never raises — captions are best-effort and must not break the batch.
    """
    edited_dir = product_dir / "edited"
    edited_dir.mkdir(parents=True, exist_ok=True)
    output_path = edited_dir / "captions.txt"

    try:
        prompt = build_caption_pack_prompt(record, platform)
        response = call_llm(prompt, model=model, transport=transport)
    except Exception as exc:
        return None, f"LLM call failed: {exc}"

    pack = extract_json_object(response)
    if not pack:
        # Save raw response so the user still has SOMETHING to copy.
        output_path.write_text(
            f"# Caption Pack — {record.get('Record ID', '')}\n"
            f"# WARNING: model output was not valid JSON; raw text below.\n\n{response}\n",
            encoding="utf-8",
        )
        return output_path, "LLM did not return valid JSON; raw text saved."

    output_path.write_text(format_captions_pack(pack, record), encoding="utf-8")
    return output_path, None


def cover_extract_time(duration: float | None) -> float:
    if duration is None or duration <= 0:
        return 0.5
    if duration < 2.0:
        return max(0.1, duration / 2)
    return 2.0


def build_cover_ffmpeg_command(
    ffmpeg: str,
    mp4_path: Path,
    output_path: Path,
    hook_text: str | None,
    extract_time: float,
) -> list[str]:
    font = "C\\:/Windows/Fonts/arial.ttf"
    # Single frame extracted at -ss (input seek) + -frames:v 1, scaled to 1080x1920.
    base_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"
    if hook_text:
        text = escape_drawtext(hook_text)
        # Larger font for cover — keep one line; FFmpeg auto-truncates if too wide,
        # but for 3-6 word hooks at 80pt this fits inside 1080 in nearly all cases.
        cover_drawtext = (
            f"drawtext=fontfile='{font}':text='{text}':"
            "x=(w-text_w)/2:y=h/2-text_h:fontsize=80:"
            "fontcolor=white:box=1:boxcolor=black@0.65:boxborderw=28"
        )
        filter_chain = f"{base_filter},{cover_drawtext}"
    else:
        filter_chain = base_filter
    return [
        ffmpeg,
        "-y",
        "-ss", f"{extract_time:.2f}",
        "-i", str(mp4_path),
        "-frames:v", "1",
        "-vf", filter_chain,
        "-q:v", "3",
        str(output_path),
    ]


def render_cover_image(mp4_path: Path, hook_text: str | None, output_path: Path) -> Path | None:
    """Extract a frame from the rendered MP4 and overlay the hook for use as a thumbnail."""
    ffmpeg = find_executable("ffmpeg", ffmpeg_candidates())
    if not ffmpeg or not mp4_path.exists():
        return None
    duration = probe_video_duration(mp4_path)
    extract_time = cover_extract_time(duration)
    command = build_cover_ffmpeg_command(ffmpeg, mp4_path, output_path, hook_text, extract_time)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=30)
    except Exception:
        return None
    if result.returncode != 0 or not output_path.exists():
        return None
    return output_path


def process_pending_rows(config: WorkflowConfig) -> int:
    records = read_masterlist(config.masterlist_path)
    log_path = config.project_root / "logs" / "run-log.csv"
    processed = 0

    for index, record in enumerate(records, start=2):
        row = master_row_from_record(record, index)
        if not row.product_link or not is_pending_status(row.status, force=config.force):
            continue

        processed += 1
        if not row.product_name or not row.shop_name:
            message = "Missing Product Name or Shop Name"
            if not config.dry_run:
                update_record(record, "Failed", message, None, [])
                append_log(log_path, row, "Failed", message)
            print(f"Row {row.row_number}: {message}")
            continue

        platform = detect_platform(row.product_link)
        product_folder = resolve_product_folder(config.project_root / "output", platform, row.shop_name, row.product_name)
        raw_dir = product_folder / "raw"
        edited_dir = product_folder / "edited"

        if config.dry_run:
            print(f"Row {row.row_number}: would process {row.product_link} -> {product_folder}")
            continue

        try:
            raw_files = collect_media(row, raw_dir)
            if not raw_files:
                raise RuntimeError(no_media_message(row.product_link))

            # Detect TikTok photo-mode: yt-dlp returned images rather than video
            photo_mode = is_tiktok_photo_mode_result(row.product_link, raw_files)

            caption = build_caption(row.product_name, row.shop_name)

            # Hook generation (cached on the row): reuse Hook column on rerun, otherwise call LLM.
            hook_text: str | None = (record.get("Hook") or "").strip() or None
            if not hook_text and not config.skip_hooks:
                hook_text = generate_hook(record, platform, model=config.captions_model)
                if hook_text:
                    record["Hook"] = hook_text

            edited_files = []
            if photo_mode:
                clear_rendered_outputs(edited_dir)
                photo_images = group_photo_mode_images(raw_files[0], raw_dir)
                rendered = render_photo_mode_slideshow(photo_images, edited_dir, caption, render_mode=config.render_mode, hook_text=hook_text)
                if rendered:
                    edited_files.append(rendered)
            else:
                for raw_file in raw_files:
                    rendered = render_video(raw_file, edited_dir, caption, render_mode=config.render_mode, hook_text=hook_text)
                    if rendered:
                        edited_files.append(rendered)
            if edited_files:
                if photo_mode:
                    message = build_photo_mode_status_message(
                        image_count=len(photo_images),
                        edited_count=len(edited_files),
                        has_audio=find_background_audio(raw_dir) is not None,
                    )
                else:
                    message = f"Downloaded {len(raw_files)} media file(s); edited {len(edited_files)} video file(s)"
                update_record(record, "Edited", message, product_folder, edited_files)
                append_log(log_path, row, "Edited", message, "; ".join(str(path) for path in edited_files))
                # Best-effort caption pack — never fail the row on caption errors.
                if not config.skip_captions:
                    captions_path, captions_error = write_captions_pack(
                        product_folder, record, platform, model=config.captions_model
                    )
                    if captions_error:
                        print(f"Row {row.row_number}: captions skipped — {captions_error}")
                    elif captions_path:
                        print(f"Row {row.row_number}: captions written to {captions_path.name}")
                # Best-effort cover image — only for video outputs (skip image-derived photo-mode for now).
                if not config.skip_cover and edited_files and not photo_mode:
                    cover_path = edited_dir / "cover.jpg"
                    cover = render_cover_image(edited_files[0], hook_text, cover_path)
                    if cover:
                        print(f"Row {row.row_number}: cover image written to {cover.name}")
            else:
                message = "Downloaded raw media; FFmpeg is not installed or no renderable media was found"
                update_record(record, "Downloaded", message, product_folder, raw_files)
                append_log(log_path, row, "Downloaded", message, "; ".join(str(path) for path in raw_files))
            write_product_info(product_folder, record, platform)
            print(f"Row {row.row_number}: {message}")
        except Exception as exc:
            message = str(exc)
            update_record(record, "Failed", message, product_folder, [])
            append_log(log_path, row, "Failed", message)
            print(f"Row {row.row_number}: Failed - {message}")

        # Incremental write so the frontend sees live progress mid-batch (CSV only; xlsm synced at end)
        if not config.dry_run:
            write_masterlist(config.masterlist_path, records, sync_excel=False)

    if not config.dry_run:
        write_masterlist(config.masterlist_path, records)

    if processed == 0:
        print("No pending rows found.")
    return processed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Process AI - Shoppee Video v1.0 masterlist rows.")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--masterlist", type=Path, default=None)
    parser.add_argument("--force", action="store_true", help="Reprocess rows even when Status is not Pending.")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without downloading or updating files.")
    parser.add_argument(
        "--render-mode",
        choices=list(RENDER_MODES),
        default="auto",
        help=(
            "Video render mode: 'auto' (default) uses light for videos and vertical-blur for images; "
            "'light' scales to fit with black padding and preserves audio; "
            "'vertical-blur' uses a blurred background canvas."
        ),
    )
    parser.add_argument(
        "--analyze-record-id",
        type=str,
        default=None,
        metavar="RECORD_ID",
        help="Run analysis only for the given Record ID (e.g. ASV-0000001). No download is performed.",
    )
    parser.add_argument(
        "--download-and-analyze-record-id",
        type=str,
        default=None,
        metavar="RECORD_ID",
        help="Download then analyze the given Record ID in one step.",
    )
    parser.add_argument(
        "--bulk-intake",
        type=Path,
        default=None,
        metavar="PATH",
        help="Path to a text file with one product URL per line (or '-' for stdin); appends Pending rows.",
    )
    parser.add_argument(
        "--bulk-fetch-remote",
        action="store_true",
        help="With --bulk-intake, fetch each page to enrich product/shop names (slower).",
    )
    parser.add_argument(
        "--skip-captions",
        action="store_true",
        help="Disable Gemini caption-pack generation (offline / quick render only).",
    )
    parser.add_argument(
        "--skip-hooks",
        action="store_true",
        help="Disable Gemini hook overlay generation; videos render without the top hook text.",
    )
    parser.add_argument(
        "--skip-cover",
        action="store_true",
        help="Skip the cover.jpg thumbnail render after the video.",
    )
    parser.add_argument(
        "--captions-model",
        type=str,
        default=CAPTIONS_PRIMARY_MODEL,
        help=f"Override the caption-generation model (default: {CAPTIONS_PRIMARY_MODEL}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project_root = args.project_root.resolve()
    masterlist = args.masterlist or project_root / "masterlist" / "List of Link Shopee VIdeo.csv"
    config = WorkflowConfig(
        project_root=project_root,
        masterlist_path=masterlist.resolve(),
        force=args.force,
        dry_run=args.dry_run,
        render_mode=args.render_mode,
        skip_captions=getattr(args, "skip_captions", False),
        captions_model=getattr(args, "captions_model", CAPTIONS_PRIMARY_MODEL),
        skip_hooks=getattr(args, "skip_hooks", False),
        skip_cover=getattr(args, "skip_cover", False),
    )

    # Bulk-intake mode: read URLs from file/stdin, append rows, exit
    bulk_path = getattr(args, "bulk_intake", None)
    if bulk_path is not None:
        try:
            if str(bulk_path) == "-":
                text = sys.stdin.read()
            else:
                text = bulk_path.read_text(encoding="utf-8")
            urls = parse_url_lines(text)
            results = bulk_intake_rows(
                urls,
                config.masterlist_path,
                fetch_remote=getattr(args, "bulk_fetch_remote", False),
            )
        except Exception as exc:
            print(f"Bulk intake failed: {exc}", file=sys.stderr)
            return 1
        added = sum(1 for r in results if r.get("status") == "added")
        skipped = sum(1 for r in results if r.get("status") == "skipped")
        errors = sum(1 for r in results if r.get("status") == "error")
        for entry in results:
            status = entry.get("status", "")
            if status == "added":
                print(f"  + {entry.get('record_id', '?')}  {entry['url']}  ({entry.get('product_name', '')})")
            elif status == "skipped":
                print(f"  = (skip) {entry['url']}")
            else:
                print(f"  ! (error) {entry['url']}: {entry.get('message', '')}")
        print(f"Bulk intake: {added} added, {skipped} skipped, {errors} error(s).")
        return 0

    # Analyze-only mode
    analyze_id = getattr(args, "analyze_record_id", None)
    if analyze_id:
        try:
            records = read_masterlist(config.masterlist_path)
            record = find_record_by_id(records, analyze_id)
            if not record:
                print(f"Record ID {analyze_id} not found in masterlist.", file=sys.stderr)
                return 1
            analyze_row_record(project_root, record)
            write_masterlist(config.masterlist_path, records)
            print(f"Analysis complete for {analyze_id}.")
        except Exception as exc:
            print(f"Analysis failed: {exc}", file=sys.stderr)
            return 1
        return 0

    # Download + Analyze mode
    dl_analyze_id = getattr(args, "download_and_analyze_record_id", None)
    if dl_analyze_id:
        try:
            records = read_masterlist(config.masterlist_path)
            record = find_record_by_id(records, dl_analyze_id)
            if not record:
                print(f"Record ID {dl_analyze_id} not found in masterlist.", file=sys.stderr)
                return 1
            row = master_row_from_record(record, 0)
            platform = detect_platform(row.product_link)
            product_folder = resolve_product_folder(
                project_root / "output", platform, row.shop_name, row.product_name
            )
            raw_dir = product_folder / "raw"
            raw_files = collect_media(row, raw_dir)
            if not raw_files:
                raise RuntimeError(no_media_message(row.product_link))
            caption = build_caption(row.product_name, row.shop_name)
            edited_files = []
            photo_mode = is_tiktok_photo_mode_result(row.product_link, raw_files)
            if photo_mode:
                clear_rendered_outputs(product_folder / "edited")
                photo_images = group_photo_mode_images(raw_files[0], raw_dir)
                rendered = render_photo_mode_slideshow(photo_images, product_folder / "edited", caption, render_mode=config.render_mode)
                if rendered:
                    edited_files.append(rendered)
            else:
                for raw_file in raw_files:
                    rendered = render_video(raw_file, product_folder / "edited", caption, render_mode=config.render_mode)
                    if rendered:
                        edited_files.append(rendered)
            if edited_files:
                if photo_mode:
                    message = build_photo_mode_status_message(
                        image_count=len(photo_images),
                        edited_count=len(edited_files),
                        has_audio=find_background_audio(raw_dir) is not None,
                    )
                else:
                    message = f"Downloaded {len(raw_files)} media file(s); edited {len(edited_files)} video file(s)"
                update_record(record, "Edited", message, product_folder, edited_files)
            else:
                message = "Downloaded raw media; FFmpeg not available or no renderable media"
                update_record(record, "Downloaded", message, product_folder, raw_files)
            write_product_info(product_folder, record, platform)
            analyze_row_record(project_root, record)
            write_masterlist(config.masterlist_path, records)
            print(f"Download + Analyze complete for {dl_analyze_id}.")
        except Exception as exc:
            print(f"Download + Analyze failed: {exc}", file=sys.stderr)
            return 1
        return 0

    try:
        process_pending_rows(config)
    except Exception as exc:
        print(f"Workflow failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
