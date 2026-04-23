from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import subprocess
import sys
import webbrowser

from process_shopee_video import (
    REQUIRED_COLUMNS,
    build_product_folder_name,
    ensure_masterlist_columns,
    read_masterlist,
    write_masterlist,
)


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>AI - Shoppee Video v1.0</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #1d2433;
      --muted: #667085;
      --line: #d6dae3;
      --panel: #ffffff;
      --wash: #f5f7fb;
      --brand: #0f766e;
      --brand-2: #b42318;
      --focus: #d97706;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Arial, sans-serif;
      color: var(--ink);
      background: var(--wash);
    }
    header {
      background: var(--brand);
      color: white;
      padding: 18px 24px;
    }
    h1 {
      font-size: 22px;
      margin: 0;
      font-weight: 700;
      letter-spacing: 0;
    }
    main {
      width: min(1040px, calc(100vw - 32px));
      margin: 22px auto 36px;
      display: grid;
      gap: 18px;
    }
    section {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }
    label {
      display: grid;
      gap: 6px;
      font-size: 13px;
      font-weight: 650;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 11px;
      font: inherit;
      background: white;
      color: var(--ink);
    }
    textarea { min-height: 76px; resize: vertical; }
    .wide { grid-column: 1 / -1; }
    .checkline {
      display: flex;
      align-items: center;
      gap: 10px;
      min-height: 42px;
      font-weight: 650;
    }
    .checkline input { width: 18px; height: 18px; }
    .actions {
      display: flex;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }
    button {
      border: 0;
      border-radius: 6px;
      padding: 10px 14px;
      min-height: 42px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
    }
    .primary { background: var(--brand); color: white; }
    .danger { background: var(--brand-2); color: white; }
    .plain { background: #e8edf4; color: var(--ink); }
    .status {
      border-left: 5px solid var(--focus);
      background: #fff8eb;
      color: #533600;
      white-space: pre-wrap;
      min-height: 56px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }
    th, td {
      border-bottom: 1px solid var(--line);
      padding: 8px;
      text-align: left;
      vertical-align: top;
      word-break: break-word;
    }
    th { color: var(--muted); font-weight: 700; }
    @media (max-width: 720px) {
      .grid { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header><h1>AI - Shoppee Video v1.0</h1></header>
  <main>
    <section>
      <form id="entryForm" class="grid">
        <label>Date
          <input name="Date" type="date" required>
        </label>
        <label>Source Type
          <select name="Source Type">
            <option>Auto</option>
            <option>Approved Media</option>
            <option>Shopee Page</option>
          </select>
        </label>
        <label class="wide">Product Link
          <input name="Product Link" type="url" required value="https://shopee.com.my/product/32632559/41452031782">
        </label>
        <label>Product Name
          <input name="Product Name" required value="Shopee Product 41452031782">
        </label>
        <label>Shop Name
          <input name="Shop Name" required value="Shop 32632559">
        </label>
        <label>Status
          <select name="Status">
            <option>Pending</option>
            <option>Downloaded</option>
            <option>Edited</option>
            <option>Failed</option>
            <option>Skipped</option>
          </select>
        </label>
        <label class="checkline">
          <input name="Done" type="checkbox">
          Done
        </label>
        <label class="wide">Notes
          <textarea name="Notes"></textarea>
        </label>
      </form>
      <div class="actions">
        <button class="primary" id="saveBtn" type="button">Save</button>
        <button class="danger" id="downloadBtn" type="button">Download</button>
        <button class="plain" id="refreshBtn" type="button">Refresh</button>
        <button class="plain" id="openBtn" type="button">Open Output Folder</button>
      </div>
    </section>
    <section class="status" id="statusBox">Ready.</section>
    <section>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Product</th>
            <th>Shop</th>
            <th>Status</th>
            <th>Done</th>
            <th>Notes</th>
          </tr>
        </thead>
        <tbody id="rows"></tbody>
      </table>
    </section>
  </main>
  <script>
    const form = document.getElementById("entryForm");
    const statusBox = document.getElementById("statusBox");
    const rowsBody = document.getElementById("rows");
    form.elements["Date"].valueAsDate = new Date();

    function payload() {
      const data = Object.fromEntries(new FormData(form).entries());
      data.Done = form.elements["Done"].checked ? "TRUE" : "FALSE";
      return data;
    }

    async function postJSON(url, body = {}) {
      const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.message || "Request failed");
      return data;
    }

    async function refresh() {
      const res = await fetch("/api/rows");
      const data = await res.json();
      rowsBody.innerHTML = "";
      for (const row of data.rows.slice(-20).reverse()) {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${row.Date || ""}</td><td>${row["Product Name"] || ""}</td><td>${row["Shop Name"] || ""}</td><td>${row.Status || ""}</td><td>${row.Done || ""}</td><td>${row.Notes || ""}</td>`;
        rowsBody.appendChild(tr);
      }
    }

    document.getElementById("saveBtn").onclick = async () => {
      statusBox.textContent = "Saving...";
      const result = await postJSON("/api/save", payload());
      statusBox.textContent = result.message;
      await refresh();
    };

    document.getElementById("downloadBtn").onclick = async () => {
      statusBox.textContent = "Saving and running workflow...";
      const result = await postJSON("/api/download", payload());
      statusBox.textContent = result.message + "\\n\\n" + (result.output || "");
      await refresh();
    };

    document.getElementById("refreshBtn").onclick = refresh;
    document.getElementById("openBtn").onclick = async () => {
      const result = await postJSON("/api/open-output");
      statusBox.textContent = result.message;
    };
    refresh();
  </script>
</body>
</html>
"""


def default_row() -> dict[str, str]:
    return {
        "Date": "",
        "Product Link": "",
        "Product Name": "",
        "Shop Name": "",
        "Source Type": "Auto",
        "Status": "Pending",
        "Done": "FALSE",
        "Notes": "",
        "Last Processed At": "",
        "Output Folder": "",
        "Output File": "",
    }


def normalize_frontend_row(payload: dict[str, str]) -> dict[str, str]:
    row = default_row()
    for key in row:
        row[key] = str(payload.get(key, row[key])).strip()
    row["Source Type"] = row["Source Type"] or "Auto"
    row["Status"] = row["Status"] or "Pending"
    row["Done"] = "TRUE" if row["Done"].upper() in {"TRUE", "YES", "ON", "1"} else "FALSE"
    return row


def upsert_masterlist_row(masterlist_path: Path, payload: dict[str, str]) -> int:
    ensure_masterlist_columns(masterlist_path)
    rows = read_masterlist(masterlist_path)
    row = normalize_frontend_row(payload)
    if not row["Product Link"] or not row["Product Name"] or not row["Shop Name"]:
        raise ValueError("Product Link, Product Name, and Shop Name are required.")

    for index, existing in enumerate(rows):
        if existing["Product Link"] == row["Product Link"]:
            merged = existing.copy()
            merged.update(row)
            rows[index] = merged
            write_masterlist(masterlist_path, rows)
            return index + 2

    rows.append(row)
    write_masterlist(masterlist_path, rows)
    return len(rows) + 1


def run_workflow(project_root: Path) -> subprocess.CompletedProcess[str]:
    runner = project_root / "scripts" / "run_shopee_video_workflow.ps1"
    return subprocess.run(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(runner),
            "-OpenOutput",
        ],
        cwd=project_root.parent,
        capture_output=True,
        text=True,
        check=False,
    )


def open_output_folder(project_root: Path) -> None:
    subprocess.Popen(["explorer.exe", str(project_root / "output")])


class FrontendHandler(BaseHTTPRequestHandler):
    project_root: Path
    masterlist_path: Path

    def log_message(self, format: str, *args) -> None:
        return

    def send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        if self.path == "/":
            body = HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if self.path == "/api/rows":
            ensure_masterlist_columns(self.masterlist_path)
            self.send_json({"rows": read_masterlist(self.masterlist_path)})
            return
        self.send_json({"message": "Not found"}, status=404)

    def do_POST(self) -> None:
        try:
            if self.path == "/api/save":
                row_number = upsert_masterlist_row(self.masterlist_path, self.read_json())
                self.send_json({"message": f"Saved row {row_number} to masterlist."})
                return
            if self.path == "/api/download":
                row_number = upsert_masterlist_row(self.masterlist_path, self.read_json())
                result = run_workflow(self.project_root)
                status = "completed" if result.returncode == 0 else "failed"
                self.send_json({
                    "message": f"Saved row {row_number}; workflow {status}. Output folder opened.",
                    "output": (result.stdout + result.stderr).strip(),
                }, status=200 if result.returncode == 0 else 500)
                return
            if self.path == "/api/open-output":
                open_output_folder(self.project_root)
                self.send_json({"message": "Output folder opened."})
                return
            self.send_json({"message": "Not found"}, status=404)
        except Exception as exc:
            self.send_json({"message": str(exc)}, status=500)


def run_server(project_root: Path, host: str, port: int, open_browser: bool) -> None:
    FrontendHandler.project_root = project_root
    FrontendHandler.masterlist_path = project_root / "masterlist" / "List of Link Shopee VIdeo.csv"
    ensure_masterlist_columns(FrontendHandler.masterlist_path)
    server = ThreadingHTTPServer((host, port), FrontendHandler)
    url = f"http://{host}:{port}/"
    print(f"AI - Shoppee Video v1.0 frontend: {url}")
    if open_browser:
        webbrowser.open(url)
    server.serve_forever()


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the AI - Shoppee Video v1.0 local frontend.")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    run_server(args.project_root.resolve(), args.host, args.port, not args.no_browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
