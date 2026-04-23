from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import datetime
import html
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urljoin, urlparse
from urllib.request import Request, urlopen


VIDEO_EXTENSIONS = {".mp4", ".mov", ".m4v", ".webm"}
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MEDIA_EXTENSIONS = VIDEO_EXTENSIONS | IMAGE_EXTENSIONS
REQUIRED_COLUMNS = [
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
]


@dataclass
class MasterRow:
    row_number: int
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
    executable = ytdlp_path
    if allow_path_lookup:
        executable = executable or find_executable("yt-dlp", python_user_scripts_candidates("yt-dlp.exe"))
    prefix = [executable] if executable else [python_executable or sys.executable, "-m", "yt_dlp"]
    return [
        *prefix,
        "--no-playlist",
        "--paths",
        str(raw_dir),
        "--output",
        "%(title).80s.%(ext)s",
        url,
    ]


def read_masterlist(masterlist_path: Path) -> list[dict[str, str]]:
    with masterlist_path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        missing = [column for column in REQUIRED_COLUMNS if column not in (reader.fieldnames or [])]
        if missing:
            raise ValueError(f"Masterlist is missing required columns: {', '.join(missing)}")
        return [{column: (row.get(column) or "").strip() for column in REQUIRED_COLUMNS} for row in reader]


def write_masterlist(masterlist_path: Path, rows: list[dict[str, str]]) -> None:
    with masterlist_path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def master_row_from_record(record: dict[str, str], row_number: int) -> MasterRow:
    return MasterRow(
        row_number=row_number,
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


def request_url(url: str):
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ShopeeVideoWorkflow/1.0",
            "Accept": "*/*",
        },
    )
    return urlopen(request, timeout=45)


def unique_path(directory: Path, filename: str) -> Path:
    candidate = directory / safe_filename(filename)
    if not candidate.exists():
        return candidate
    for number in range(2, 1000):
        numbered = directory / f"{candidate.stem}-{number}{candidate.suffix}"
        if not numbered.exists():
            return numbered
    raise FileExistsError(f"Could not create unique filename for {candidate}")


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


def discover_media_urls(page_url: str) -> list[str]:
    try:
        with request_url(page_url) as response:
            body = response.read().decode("utf-8", errors="replace")
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"Page fetch failed: {exc}") from exc

    body = html.unescape(body)
    found = set()
    patterns = [
        r'https?://[^"\'<>\\ ]+\.(?:mp4|mov|m4v|webm|jpg|jpeg|png|webp)(?:\?[^"\'<>\\ ]*)?',
        r'(?:src|href|content)=["\']([^"\']+\.(?:mp4|mov|m4v|webm|jpg|jpeg|png|webp)(?:\?[^"\']*)?)["\']',
    ]
    for pattern in patterns:
        for match in re.finditer(pattern, body, flags=re.IGNORECASE):
            url = match.group(1) if match.lastindex else match.group(0)
            found.add(urljoin(page_url, url))

    return filter_media_urls(found)


def media_priority(url: str) -> tuple[int, str]:
    suffix = Path(unquote(urlparse(url).path)).suffix.lower()
    return (0 if suffix in VIDEO_EXTENSIONS else 1, url)


def is_site_chrome_media_url(url: str) -> bool:
    name = Path(unquote(urlparse(url).path)).name.lower()
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
    )


def filter_media_urls(urls: Iterable[str]) -> list[str]:
    filtered = [url for url in urls if not is_site_chrome_media_url(url)]
    return sorted(filtered, key=media_priority)


def download_with_ytdlp(url: str, raw_dir: Path) -> list[Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    before = {path.resolve() for path in raw_dir.iterdir()} if raw_dir.exists() else set()
    command = build_ytdlp_command(url, raw_dir)
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    after = {path.resolve() for path in raw_dir.iterdir()}
    return sorted(path for path in after - before if path.suffix.lower() in MEDIA_EXTENSIONS)


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
    for index, media_url in enumerate(media_urls[:5], start=1):
        try:
            downloaded.append(download_url(media_url, raw_dir, fallback_name=f"row-{row.row_number}-{index}"))
        except RuntimeError:
            continue
    return downloaded


def escape_drawtext(value: str) -> str:
    return value.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")


def build_ffmpeg_command(ffmpeg: str, raw_path: Path, output_path: Path, caption: str) -> list[str]:
    if raw_path.suffix.lower() in VIDEO_EXTENSIONS:
        input_args = ["-i", str(raw_path)]
        duration_args: list[str] = []
    else:
        input_args = ["-loop", "1", "-t", "8", "-i", str(raw_path)]
        duration_args = ["-shortest"]

    font = "C\\:/Windows/Fonts/arial.ttf"
    text = escape_drawtext(caption)
    filter_graph = (
        "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=20:1[bg];"
        "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease[fg];"
        "[bg][fg]overlay=(W-w)/2:(H-h)/2,"
        f"drawtext=fontfile='{font}':text='{text}':"
        "x=(w-text_w)/2:y=h-220:fontsize=54:"
        "fontcolor=white:box=1:boxcolor=black@0.58:boxborderw=28[v]"
    )
    return [
        ffmpeg,
        "-y",
        *input_args,
        "-filter_complex",
        filter_graph,
        "-map",
        "[v]",
        "-r",
        "30",
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        *duration_args,
        str(output_path),
    ]


def render_video(raw_path: Path, edited_dir: Path, caption: str) -> Path | None:
    ffmpeg = find_executable("ffmpeg", ffmpeg_candidates())
    if not ffmpeg:
        return None

    edited_dir.mkdir(parents=True, exist_ok=True)
    if raw_path.suffix.lower() in VIDEO_EXTENSIONS:
        output_name = derive_output_name(raw_path)
    elif raw_path.suffix.lower() in IMAGE_EXTENSIONS:
        output_name = f"{safe_filename(raw_path.stem)}_new.mp4"
    else:
        return None

    output_path = unique_path(edited_dir, output_name)
    command = build_ffmpeg_command(ffmpeg, raw_path, output_path, caption)
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
    record["Notes"] = notes
    record["Last Processed At"] = datetime.now().isoformat(timespec="minutes")
    if output_folder:
        record["Output Folder"] = str(output_folder)
    files = [str(path) for path in output_files]
    record["Output File"] = ""
    if files:
        record["Output File"] = "; ".join(files)


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

        product_folder = config.project_root / "output" / build_product_folder_name(row.product_name, row.shop_name)
        raw_dir = product_folder / "raw"
        edited_dir = product_folder / "edited"

        if config.dry_run:
            print(f"Row {row.row_number}: would process {row.product_link} -> {product_folder}")
            continue

        try:
            raw_files = collect_media(row, raw_dir)
            if not raw_files:
                raise RuntimeError("No downloadable media found")
            caption = build_caption(row.product_name, row.shop_name)
            edited_files = []
            for raw_file in raw_files:
                rendered = render_video(raw_file, edited_dir, caption)
                if rendered:
                    edited_files.append(rendered)
            if edited_files:
                message = f"Downloaded {len(raw_files)} media file(s); edited {len(edited_files)} video file(s)"
                update_record(record, "Edited", message, product_folder, edited_files)
                append_log(log_path, row, "Edited", message, "; ".join(str(path) for path in edited_files))
            else:
                message = "Downloaded raw media; FFmpeg is not installed or no renderable media was found"
                update_record(record, "Downloaded", message, product_folder, raw_files)
                append_log(log_path, row, "Downloaded", message, "; ".join(str(path) for path in raw_files))
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
    )
    try:
        process_pending_rows(config)
    except Exception as exc:
        print(f"Workflow failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
