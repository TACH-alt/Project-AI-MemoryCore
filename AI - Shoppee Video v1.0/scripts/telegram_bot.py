"""Telegram bot for AI - Shoppee Video v1.0.

Lets a whitelisted user submit URLs, run the batch, and receive finished MP4s
without leaving Telegram. Reuses the same bulk_intake_rows / process_pending_rows
helpers as the local frontend.

Setup:
  1. pip install python-telegram-bot==21.*
  2. Talk to @BotFather on Telegram, /newbot, copy the token.
  3. Talk to @userinfobot to get your numeric user ID.
  4. Copy config/telegram.example.json to config/telegram.json and fill it in.
  5. python scripts/telegram_bot.py
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from process_shopee_video import (
    WorkflowConfig,
    bulk_intake_rows,
    parse_url_lines,
    process_pending_rows,
    read_masterlist,
)

try:
    from telegram import Update
    from telegram.constants import ChatAction
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )
    _TELEGRAM_IMPORT_ERROR: Exception | None = None
except ImportError as _exc:  # pragma: no cover - error path surfaced at main()
    Update = ChatAction = ApplicationBuilder = CommandHandler = None  # type: ignore[assignment]
    ContextTypes = MessageHandler = filters = None  # type: ignore[assignment]
    _TELEGRAM_IMPORT_ERROR = _exc


logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO,
)
log = logging.getLogger("shopee-bot")


# MarkdownV2 reserved characters per Telegram docs — must be backslash-escaped outside code blocks.
_MD_V2_SPECIAL = r"_*[]()~`>#+-=|{}.!"
_MD_V2_CODE_SPECIAL = r"`\\"


def escape_md_v2(text: str) -> str:
    return "".join("\\" + ch if ch in _MD_V2_SPECIAL else ch for ch in text or "")


def escape_md_v2_code(text: str) -> str:
    return "".join("\\" + ch if ch in _MD_V2_CODE_SPECIAL else ch for ch in text or "")


def parse_captions_sections(content: str) -> list[tuple[str, str]]:
    """Parse a captions.txt produced by write_captions_pack into [(label, body), ...]."""
    sections: list[tuple[str, str]] = []
    current_label: str | None = None
    buffer: list[str] = []
    for raw in (content or "").splitlines():
        line = raw.rstrip()
        if line.startswith("=== ") and line.endswith(" ==="):
            if current_label is not None:
                sections.append((current_label, "\n".join(buffer).strip()))
            current_label = line[4:-4].strip()
            buffer = []
        elif current_label is not None:
            buffer.append(line)
    if current_label is not None:
        sections.append((current_label, "\n".join(buffer).strip()))
    return sections


def load_config(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"Config not found: {path}\n"
            f"Copy {path.parent}/telegram.example.json to {path.name} and fill it in."
        )
    cfg = json.loads(path.read_text(encoding="utf-8"))
    token = cfg.get("bot_token", "").strip()
    if not token or token == "PASTE_FROM_BOTFATHER":
        raise ValueError("bot_token is missing in config.")
    if not cfg.get("allowed_user_ids"):
        raise ValueError("allowed_user_ids is empty — at least one Telegram user ID is required.")
    return cfg


def is_authorized(update: Update, allowed_ids: set[int]) -> bool:
    user = update.effective_user
    if not user:
        return False
    return user.id in allowed_ids


async def deny(update: Update) -> None:
    user = update.effective_user
    log.warning("Denied access for user %s (id=%s)", user.username if user else "?", user.id if user else "?")
    if update.effective_message:
        await update.effective_message.reply_text(
            "Not authorized. Ask the bot owner to add your Telegram user ID to allowed_user_ids."
        )


def make_handlers(masterlist_path: Path, project_root: Path, allowed_ids: set[int]):
    """Build PTB handlers bound to this project."""

    async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_authorized(update, allowed_ids):
            return await deny(update)
        await update.effective_message.reply_text(
            "🎬 Shoppee Video bot ready.\n\n"
            "• Send URLs (one per line) to add Pending rows.\n"
            "• /run — process all Pending rows and DM the finished videos.\n"
            "• /status — counts of pending / edited / failed.\n"
            "• /help — show this again."
        )

    async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        await cmd_start(update, ctx)

    async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_authorized(update, allowed_ids):
            return await deny(update)
        rows = await asyncio.to_thread(read_masterlist, masterlist_path)
        pending = sum(1 for r in rows if (r.get("Status") or "").strip().lower() in {"", "pending"})
        edited = sum(1 for r in rows if r.get("Status") == "Edited")
        failed = sum(1 for r in rows if r.get("Status") == "Failed")
        await update.effective_message.reply_text(
            f"📊 Masterlist:\n"
            f"   Pending  ⏳ {pending}\n"
            f"   Edited   ✅ {edited}\n"
            f"   Failed   ❌ {failed}\n"
            f"   Total       {len(rows)}"
        )

    async def on_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_authorized(update, allowed_ids):
            return await deny(update)
        text = update.effective_message.text or ""
        urls = parse_url_lines(text)
        if not urls:
            await update.effective_message.reply_text(
                "No URLs found. Paste full Shopee/TikTok URLs, one per line."
            )
            return

        await ctx.bot.send_chat_action(update.effective_chat.id, ChatAction.TYPING)
        results = await asyncio.to_thread(bulk_intake_rows, urls, masterlist_path)

        added = sum(1 for r in results if r["status"] == "added")
        skipped = sum(1 for r in results if r["status"] == "skipped")
        errors = sum(1 for r in results if r["status"] == "error")
        lines = [f"✅ {added} added · ↷ {skipped} skipped · ❌ {errors} error(s)"]
        for r in results:
            if r["status"] == "added":
                lines.append(f"➕ {r.get('record_id', '?')} · {r.get('platform', '?')} · {r.get('product_name', '')[:60]}")
            elif r["status"] == "error":
                lines.append(f"❌ {r['url']}\n   {r.get('message', '')}")
        # Telegram 4096-char limit per message; chunk if needed.
        body = "\n".join(lines)
        for chunk_start in range(0, len(body), 3500):
            await update.effective_message.reply_text(body[chunk_start:chunk_start + 3500])

        if added > 0:
            await update.effective_message.reply_text(
                "Send /run to process the new pending rows."
            )

    async def cmd_run(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
        if not is_authorized(update, allowed_ids):
            return await deny(update)

        chat_id = update.effective_chat.id
        await ctx.bot.send_message(chat_id, "▶️ Starting batch — I'll DM each finished video.")

        # Snapshot which Record IDs are Pending before the run.
        before = await asyncio.to_thread(read_masterlist, masterlist_path)
        pending_ids = {
            r["Record ID"]
            for r in before
            if (r.get("Status") or "").strip().lower() in {"", "pending"} and r.get("Record ID")
        }
        if not pending_ids:
            await ctx.bot.send_message(chat_id, "No pending rows to run.")
            return

        config = WorkflowConfig(
            project_root=project_root,
            masterlist_path=masterlist_path,
            force=False,
            dry_run=False,
            render_mode="auto",
        )
        try:
            await asyncio.to_thread(process_pending_rows, config)
        except Exception as exc:
            log.exception("Batch failed")
            await ctx.bot.send_message(chat_id, f"❌ Batch failed: {exc}")
            return

        # Find rows that flipped to Edited.
        after = await asyncio.to_thread(read_masterlist, masterlist_path)
        edited_now = [r for r in after if r.get("Record ID") in pending_ids and r.get("Status") == "Edited"]
        failed_now = [r for r in after if r.get("Record ID") in pending_ids and r.get("Status") == "Failed"]

        await ctx.bot.send_message(
            chat_id,
            f"✅ Batch done — {len(edited_now)} edited, {len(failed_now)} failed.",
        )

        for record in edited_now:
            output_file = (record.get("Output File") or "").split(";")[0].strip()
            if not output_file:
                continue
            mp4 = Path(output_file)
            if not mp4.exists():
                await ctx.bot.send_message(chat_id, f"⚠️ {record['Record ID']}: file missing on disk.")
                continue
            edited_dir = mp4.parent
            cover_path = edited_dir / "cover.jpg"
            captions_path = edited_dir / "captions.txt"

            # 1. Send cover.jpg first so the user sees the Shorts thumbnail option.
            if cover_path.exists():
                try:
                    with cover_path.open("rb") as handle:
                        await ctx.bot.send_photo(chat_id, photo=handle, caption=f"🎯 Cover · {record['Record ID']}")
                except Exception as exc:
                    log.warning("Cover send failed for %s: %s", record.get("Record ID"), exc)

            # 2. Send the MP4.
            try:
                size_mb = mp4.stat().st_size / (1024 * 1024)
                if size_mb > 49:
                    await ctx.bot.send_message(
                        chat_id,
                        f"⚠️ {record['Record ID']}: {mp4.name} is {size_mb:.1f} MB (> 50 MB limit). "
                        f"Open from PC: {mp4}",
                    )
                else:
                    hook = (record.get("Hook") or "").strip()
                    caption = (
                        f"{record.get('Record ID', '')} · {record.get('Shop Name', '')}\n"
                        f"{record.get('Product Name', '')}"
                        + (f"\n🪝 {hook}" if hook else "")
                    )[:1024]
                    await ctx.bot.send_chat_action(chat_id, ChatAction.UPLOAD_VIDEO)
                    with mp4.open("rb") as handle:
                        await ctx.bot.send_video(chat_id, video=handle, caption=caption, supports_streaming=True)
            except Exception as exc:
                log.exception("Send failed for %s", record.get("Record ID"))
                await ctx.bot.send_message(chat_id, f"⚠️ Send failed for {record['Record ID']}: {exc}")
                continue

            # 3. Send each platform caption section as its own code-fenced message for easy long-press copy.
            if captions_path.exists():
                try:
                    sections = parse_captions_sections(captions_path.read_text(encoding="utf-8"))
                    for label, body in sections:
                        if not body.strip():
                            continue
                        # Code-fenced via MarkdownV2 → long-press → Copy code.
                        text = f"*{escape_md_v2(label)}*\n```\n{escape_md_v2_code(body)}\n```"
                        await ctx.bot.send_message(chat_id, text=text, parse_mode="MarkdownV2")
                except Exception as exc:
                    log.warning("Captions send failed for %s: %s", record.get("Record ID"), exc)
                    await ctx.bot.send_message(chat_id, f"(captions delivery failed: {exc})")
            else:
                await ctx.bot.send_message(chat_id, "(captions pack not generated)")

        for record in failed_now:
            await ctx.bot.send_message(
                chat_id,
                f"❌ {record['Record ID']}: {record.get('Notes', '')[:400]}",
            )

    return [
        CommandHandler("start", cmd_start),
        CommandHandler("help", cmd_help),
        CommandHandler("status", cmd_status),
        CommandHandler("run", cmd_run),
        MessageHandler(filters.TEXT & ~filters.COMMAND, on_text),
    ]


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram bot for AI - Shoppee Video v1.0.")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Path to telegram.json (defaults to <project>/config/telegram.json).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if _TELEGRAM_IMPORT_ERROR is not None:
        print(
            "Missing dependency: python-telegram-bot.\n"
            "Install with:  pip install \"python-telegram-bot==21.*\"",
            file=sys.stderr,
        )
        return 1
    args = parse_args(argv or sys.argv[1:])
    project_root = args.project_root.resolve()
    config_path = (args.config or project_root / "config" / "telegram.json").resolve()
    cfg = load_config(config_path)
    masterlist_path = (project_root / "masterlist" / "List of Link Shopee VIdeo.csv").resolve()
    allowed_ids = {int(uid) for uid in cfg["allowed_user_ids"]}

    log.info("Project root: %s", project_root)
    log.info("Masterlist: %s", masterlist_path)
    log.info("Authorized user IDs: %s", sorted(allowed_ids))

    app = ApplicationBuilder().token(cfg["bot_token"]).build()
    for handler in make_handlers(masterlist_path, project_root, allowed_ids):
        app.add_handler(handler)

    log.info("Bot is running — press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
