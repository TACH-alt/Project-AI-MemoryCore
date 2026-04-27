from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
import html
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
from urllib.request import Request, urlopen


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
AUDIO_EXTENSIONS = {".aac", ".m4a", ".mp3", ".opus", ".ogg", ".wav", ".webm"}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS
RENDER_MODES = frozenset({"auto", "light", "vertical-blur"})
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ShopeeVideoWorkflow/1.0"
SHOPEE_PAGE_USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Mobile/15E148 Safari/604.1"
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
    """Return True for public single TikTok video URLs.

    Handles:
    - Standard long URLs: https://www.tiktok.com/@user/video/123456
    - Short redirect links: https://vt.tiktok.com/ZS9hjGD43/
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if not host.endswith("tiktok.com"):
        return False
    # Short links (vt.tiktok.com) are always single-video redirects — trust yt-dlp
    if host == "vt.tiktok.com":
        return True
    # Standard long URLs must contain /video/ in the path
    return "/video/" in parsed.path


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


def write_masterlist(masterlist_path: Path, rows: list[dict[str, str]]) -> None:
    rows = backfill_record_identity(rows)
    with masterlist_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)
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
    return request_headers(url)


def request_url(url: str, headers: dict[str, str] | None = None):
    request = Request(
        url,
        headers=headers or request_headers(url),
    )
    return urlopen(request, timeout=45)


def canonicalize_tiktok_url(
    url: str,
    request_fn=request_url,
) -> str:
    if not is_tiktok_video_url(url):
        return url
    parsed = urlparse(url)
    if "/video/" in parsed.path and parsed.netloc.lower() != "vt.tiktok.com":
        return url

    oembed_url = f"https://www.tiktok.com/oembed?url={quote(url, safe='')}"
    try:
        with request_fn(oembed_url, request_headers(oembed_url)) as response:
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
    except Exception:
        return url

    for candidate in (payload.get("html", ""), payload.get("author_url", "")):
        match = re.search(r"https://www\.tiktok\.com/@[^\"'?\s]+/video/\d+", candidate)
        if match:
            return match.group(0)
    return url


def tiktok_video_id_from_url(url: str) -> str | None:
    match = re.search(r"/video/(\d+)", urlparse(url).path)
    return match.group(1) if match else None


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
        return []
    after = {path.resolve() for path in raw_dir.iterdir()}
    media = sorted(path for path in after - before if path.suffix.lower() in MEDIA_EXTENSIONS)
    if media:
        cleanup_non_media_outputs(raw_dir)
        return media
    if is_tiktok_video_url(canonical_url):
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


def find_background_audio(raw_dir: Path) -> Path | None:
    for candidate in sorted(raw_dir.glob("background.*")):
        if candidate.suffix.lower() in AUDIO_EXTENSIONS and candidate.is_file():
            return candidate
    return None


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
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def build_ffmpeg_command(
    ffmpeg: str,
    raw_path: Path,
    output_path: Path,
    caption: str,
    render_mode: str = "auto",
    background_audio: Path | None = None,
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

    font = "C\\:/Windows/Fonts/arial.ttf"
    text = escape_drawtext(caption)

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
        filter_graph = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,boxblur=20:1[bg];"
            "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
            "[bg][fg]overlay=(W-w)/2:(H-h)/2,"
            f"drawtext=fontfile='{font}':text='{text}':"
            "x=(w-text_w)/2:y=h-120:fontsize=42:"
            "fontcolor=white:box=1:boxcolor=black@0.58:boxborderw=20[v]"
        )
    else:
        # Video source: resolve auto mode
        effective_mode = "light" if render_mode == "auto" else render_mode
        input_args = ["-i", str(raw_path)]
        duration_args = []
        has_audio = True

        if effective_mode == "light":
            # Scale to fit inside 1080x1920 with black padding; minimal caption
            filter_graph = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,"
                f"drawtext=fontfile='{font}':text='{text}':"
                "x=(w-text_w)/2:y=h-100:fontsize=40:"
                "fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=18[v]"
            )
        else:
            # vertical-blur: blurred background + centred overlay + larger caption
            filter_graph = (
                "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
                "crop=1080:1920,boxblur=20:1[bg];"
                "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
                "[bg][fg]overlay=(W-w)/2:(H-h)/2,"
                f"drawtext=fontfile='{font}':text='{text}':"
                "x=(w-text_w)/2:y=h-220:fontsize=54:"
                "fontcolor=white:box=1:boxcolor=black@0.58:boxborderw=28[v]"
            )

    if is_image and background_audio and background_audio.exists():
        # Photo-mode: audio comes from the second input (background.aac)
        audio_map = ["-map", "1:a", "-c:a", "aac"]
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


def render_video(raw_path: Path, edited_dir: Path, caption: str, render_mode: str = "auto") -> Path | None:
    ffmpeg = find_executable("ffmpeg", ffmpeg_candidates())
    if not ffmpeg:
        return None

    edited_dir.mkdir(parents=True, exist_ok=True)
    if raw_path.suffix.lower() in VIDEO_EXTENSIONS:
        output_name = derive_output_name(raw_path)
        background_audio = None
    elif raw_path.suffix.lower() in IMAGE_EXTENSIONS:
        output_name = f"{safe_filename(raw_path.stem)}_new.mp4"
        # Photo-mode TikTok: look for background audio saved alongside the thumbnail
        background_audio = find_background_audio(raw_path.parent)
    else:
        return None

    output_path = replace_path(edited_dir, output_name)
    command = build_ffmpeg_command(
        ffmpeg, raw_path, output_path, caption,
        render_mode=render_mode, background_audio=background_audio,
    )
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg failed for {raw_path.name}: {result.stderr.strip()[-500:]}")
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
            photo_mode = (
                is_tiktok_video_url(row.product_link)
                and all(f.suffix.lower() in IMAGE_EXTENSIONS for f in raw_files)
            )

            caption = build_caption(row.product_name, row.shop_name)
            edited_files = []
            for raw_file in raw_files:
                rendered = render_video(raw_file, edited_dir, caption, render_mode=config.render_mode)
                if rendered:
                    edited_files.append(rendered)
            if edited_files:
                photo_note = " (photo-mode post — cover thumbnail rendered with background audio)" if photo_mode else ""
                message = f"Downloaded {len(raw_files)} media file(s); edited {len(edited_files)} video file(s){photo_note}"
                update_record(record, "Edited", message, product_folder, edited_files)
                append_log(log_path, row, "Edited", message, "; ".join(str(path) for path in edited_files))
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
    )

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
            raw_files = collect_media(row, product_folder / "raw")
            if not raw_files:
                raise RuntimeError(no_media_message(row.product_link))
            caption = build_caption(row.product_name, row.shop_name)
            edited_files = []
            for raw_file in raw_files:
                rendered = render_video(raw_file, product_folder / "edited", caption, render_mode=config.render_mode)
                if rendered:
                    edited_files.append(rendered)
            if edited_files:
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
