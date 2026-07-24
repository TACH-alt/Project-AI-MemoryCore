"""hermes_make_video.py — single-link worker for the hermes-agent integration.

Processes ONE Shopee/TikTok product link end-to-end (intake → download →
render + enrich → analyze) and emits a single JSON line on stdout describing
the result, so the hermes agent can decide what to send back over Telegram.

Design notes
------------
- ONE link per invocation. Sequencing a queue of links is the agent's job
  (process one fully before starting the next) — the masterlist write path is
  not concurrency-safe, so never run two of these in parallel.
- stdout is JSON ONLY. The underlying pipeline prints progress with `print()`;
  we redirect that to stderr so the agent gets a clean, parseable result line.
- Returns BOTH the original (raw downloaded) and edited (rendered) file paths,
  so the agent can ask the user "original or edited?" and send the right one.

Usage
-----
    py hermes_make_video.py "<product_url>" [--render-mode auto] [--no-desktop-copy]

JSON result shape
-----------------
    {"url", "record_id", "status", "product_name", "shop_name", "platform",
     "original": [paths], "edited": [paths], "captions": path|null,
     "cover": path|null, "desktop": folder|null, "error": str|null}
"""
from __future__ import annotations

import argparse
import contextlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import process_shopee_video as psv

DEFAULT_MASTERLIST_REL = Path("masterlist") / "List of Link Shopee VIdeo.csv"


def _list_media(folder: Path, exts) -> list[str]:
    if not folder.exists():
        return []
    return sorted(str(p) for p in folder.iterdir() if p.is_file() and p.suffix.lower() in exts)


def _find_record_by_link(records: list[dict[str, str]], url: str) -> dict[str, str] | None:
    target = (url or "").strip()
    for record in records:
        if record.get("Product Link", "").strip() == target:
            return record
    return None


def make_one_video(
    url: str,
    project_root: Path,
    masterlist_path: Path,
    render_mode: str = "auto",
    copy_to_desktop: bool = True,
    shop: str | None = None,
    product: str | None = None,
    hook: str | None = None,
    download_only: bool = False,
) -> dict:
    project_root = Path(project_root)
    masterlist_path = Path(masterlist_path)
    result = {
        "url": url,
        "record_id": "",
        "status": "",
        "product_name": "",
        "shop_name": "",
        "platform": "",
        "original": [],
        "edited": [],
        "captions": None,
        "cover": None,
        "desktop": None,
        "error": None,
    }

    config = psv.WorkflowConfig(
        project_root=project_root,
        masterlist_path=masterlist_path,
        render_mode=render_mode,
        copy_to_desktop=copy_to_desktop,
    )

    # 1. Intake this single URL (appends a Pending row if it is new; dedupes otherwise).
    intake = psv.bulk_intake_rows([url], masterlist_path)
    intake0 = intake[0] if intake else {"status": "error", "message": "No intake result."}
    if intake0.get("status") == "error":
        result["status"] = "Failed"
        result["error"] = intake0.get("message", "Intake error.")
        return result

    # 2. Locate the row (Record IDs are backfilled by read_masterlist).
    records = psv.read_masterlist(masterlist_path)
    record = _find_record_by_link(records, url)
    if record is None:
        result["status"] = "Failed"
        result["error"] = "Row not found in masterlist after intake."
        return result

    # Apply user-supplied editing/DB info (Telegram-collected) before processing,
    # so the output folder, caption, and masterlist row are correct from the start.
    if shop and shop.strip():
        record["Shop Name"] = shop.strip()
    if product and product.strip():
        record["Product Name"] = product.strip()
    if hook is not None and hook.strip():
        record["Hook"] = hook.strip()

    row = psv.master_row_from_record(record, 0)
    platform = psv.detect_platform(row.product_link)
    result["record_id"] = record.get("Record ID", "")
    result["product_name"] = row.product_name
    result["shop_name"] = row.shop_name
    result["platform"] = platform

    # An edited video must have a Shop Name (for the DB row + output folder).
    # The original (download-only) path does not require it.
    if not download_only and not record.get("Shop Name", "").strip():
        result["status"] = "Failed"
        result["error"] = "Shop Name is required to produce an edited video — provide a shop name, or request the original instead."
        return result

    product_folder = psv.resolve_product_folder(
        project_root / "output", platform, row.shop_name, row.product_name
    )
    raw_dir = product_folder / "raw"
    edited_dir = product_folder / "edited"
    log_path = project_root / "logs" / "run-log.csv"
    error_log_path = project_root / "logs" / "error-log.csv"

    try:
        raw_files = psv.collect_media(row, raw_dir)
        if not raw_files:
            raise RuntimeError(psv.no_media_message(row.product_link))

        if download_only:
            # Original only: download the raw media, no rendering/enrichment.
            message = f"Downloaded {len(raw_files)} media file(s) (original, no edit)"
            psv.update_record(record, "Downloaded", message, product_folder, raw_files)
            psv.write_product_info(product_folder, record, platform)
            if copy_to_desktop:
                psv.copy_outputs_to_desktop(row.shop_name, row.product_name, [], raw_files)
            psv.write_masterlist(masterlist_path, records)
            result["status"] = record.get("Status", "")
            result["original"] = _list_media(raw_dir, psv.MEDIA_EXTENSIONS)
            result["edited"] = []
            if copy_to_desktop:
                dest = psv.desktop_output_root() / psv.safe_filename(row.shop_name) / psv.safe_filename(row.product_name)
                result["desktop"] = str(dest) if dest.exists() else None
            return result

        # Shared render+enrich path (hook + captions + cover + Desktop mirror).
        psv.render_and_enrich_row(
            config, record, row, platform, product_folder, raw_files,
            log_path=log_path, error_log_path=error_log_path,
        )
        # Analysis is best-effort — never fail the row over it.
        try:
            psv.analyze_row_record(project_root, record)
        except Exception:
            pass
        psv.write_masterlist(masterlist_path, records)

        result["status"] = record.get("Status", "")
        result["original"] = _list_media(raw_dir, psv.MEDIA_EXTENSIONS)
        result["edited"] = _list_media(edited_dir, psv.VIDEO_EXTENSIONS)
        captions = edited_dir / "captions.txt"
        cover = edited_dir / "cover.jpg"
        result["captions"] = str(captions) if captions.exists() else None
        result["cover"] = str(cover) if cover.exists() else None
        if copy_to_desktop:
            dest = psv.desktop_output_root() / psv.safe_filename(row.shop_name) / psv.safe_filename(row.product_name)
            result["desktop"] = str(dest) if dest.exists() else None
    except Exception as exc:
        message = str(exc)
        psv.update_record(record, "Failed", message, product_folder, [])
        psv.append_log(log_path, row, "Failed", message)
        psv.append_error_log(error_log_path, row, platform, psv.classify_error(message), message)
        psv.write_masterlist(masterlist_path, records)
        result["status"] = "Failed"
        result["error"] = message

    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Process ONE Shopee/TikTok link end-to-end and emit a JSON result line (for hermes)."
    )
    parser.add_argument("url")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--masterlist", type=Path, default=None)
    parser.add_argument("--render-mode", default="auto", choices=sorted(psv.RENDER_MODES))
    parser.add_argument("--no-desktop-copy", action="store_true")
    parser.add_argument("--shop", default=None, help="Shop Name for the masterlist row + output folder (required unless --download-only).")
    parser.add_argument("--product", default=None, help="Override the auto-derived Product Name.")
    parser.add_argument("--hook", default=None, help="Custom on-screen hook overlay text (skips LLM hook).")
    parser.add_argument("--download-only", action="store_true", help="Original only: download raw media, skip rendering. Shop Name not required.")
    args = parser.parse_args(argv)

    project_root = args.project_root.resolve()
    masterlist = (args.masterlist or project_root / DEFAULT_MASTERLIST_REL).resolve()

    # Keep stdout clean: the pipeline's progress prints go to stderr; stdout = JSON only.
    with contextlib.redirect_stdout(sys.stderr):
        result = make_one_video(
            args.url, project_root, masterlist,
            render_mode=args.render_mode, copy_to_desktop=not args.no_desktop_copy,
            shop=args.shop, product=args.product, hook=args.hook,
            download_only=args.download_only,
        )

    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("error") is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
