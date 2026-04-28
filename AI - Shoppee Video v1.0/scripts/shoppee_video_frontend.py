from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import subprocess
import sys
import webbrowser

from process_shopee_video import (
    REQUIRED_COLUMNS,
    analyze_row_record,
    detect_platform,
    discover_tiktok_media_bundle,
    ensure_masterlist_columns,
    find_record_by_id,
    is_tiktok_video_url,
    read_masterlist,
    resolve_product_folder,
    write_masterlist,
    write_product_info,
)


HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>AI - Shoppee Video v1.0</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #1d2433; --muted: #667085; --line: #d6dae3;
      --panel: #fff; --wash: #f5f7fb;
      --brand: #0f766e; --brand-dk: #0c5f58; --brand-2: #b42318; --focus: #d97706;
    }
    * { box-sizing: border-box; }
    body { margin: 0; font-family: "Segoe UI", Arial, sans-serif; color: var(--ink); background: var(--wash);
           padding-bottom: env(safe-area-inset-bottom); }
    header { background: var(--brand); color: white; padding: 13px 22px; display: flex; align-items: center; gap: 10px;
             padding-left: max(22px, env(safe-area-inset-left)); padding-right: max(22px, env(safe-area-inset-right)); }
    h1 { font-size: 19px; margin: 0; font-weight: 700; }
    #headerSub { font-size: 12px; opacity: .8; margin-left: auto; }
    main { width: min(1120px, calc(100vw - 28px)); margin: 18px auto 40px; display: grid; gap: 14px; }
    section { background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 16px 18px; }
    .sec-title { font-size: 11px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; margin: 0 0 12px; }
    .grid3 { display: grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap: 11px; }
    .grid2 { display: grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: 11px; }
    .wide  { grid-column: 1 / -1; }
    label  { display: grid; gap: 4px; font-size: 13px; font-weight: 600; }
    label span.hint { font-weight: 400; color: var(--muted); font-size: 11px; }
    input, select, textarea {
      width: 100%; border: 1px solid var(--line); border-radius: 6px;
      padding: 8px 10px; font: inherit; background: white; color: var(--ink); transition: border-color .15s;
    }
    input:focus, select:focus, textarea:focus { outline: none; border-color: var(--brand); }
    textarea { min-height: 56px; resize: vertical; }
    .checkline { display: flex; align-items: center; gap: 9px; min-height: 38px; font-size: 13px; font-weight: 600; }
    .checkline input[type=checkbox] { width: 16px; height: 16px; cursor: pointer; }
    .actions { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 13px; padding-top: 13px; border-top: 1px solid var(--line); }
    button { border: 0; border-radius: 6px; padding: 8px 15px; min-height: 44px; font: inherit; font-size: 13px; font-weight: 700; cursor: pointer; transition: opacity .15s; touch-action: manipulation; -webkit-tap-highlight-color: transparent; }
    button:hover { opacity: .87; } button:disabled { opacity: .42; cursor: not-allowed; }
    .btn-primary { background: var(--brand); color: white; }
    .btn-danger  { background: var(--brand-2); color: white; }
    .btn-plain   { background: #e6ecf4; color: var(--ink); }
    .btn-sm      { padding: 3px 9px; min-height: 26px; font-size: 12px; border-radius: 5px; }

    /* Status bar */
    #statusBox {
      border-left: 4px solid var(--focus); background: #fff8eb; color: #533600;
      white-space: pre-wrap; min-height: 44px; font-size: 13px; line-height: 1.5;
      border-radius: 0 8px 8px 0; transition: border-color .25s, background .25s;
    }
    #statusBox.ok  { border-color: #16a34a; background: #f0fdf4; color: #14532d; }
    #statusBox.err { border-color: #dc2626; background: #fef2f2; color: #7f1d1d; }

    /* Badges */
    .badge { display: inline-block; padding: 2px 8px; border-radius: 11px; font-size: 11px; font-weight: 700; white-space: nowrap; }
    .badge-edited     { background: #d1fae5; color: #065f46; }
    .badge-downloaded { background: #dbeafe; color: #1e40af; }
    .badge-failed     { background: #fee2e2; color: #991b1b; }
    .badge-pending    { background: #fef3c7; color: #92400e; }
    .badge-skipped    { background: #f3f4f6; color: #374151; }

    /* Table */
    .tbl-wrap { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; min-width: 700px; }
    th, td { border-bottom: 1px solid var(--line); padding: 8px 10px; text-align: left; vertical-align: middle; }
    th { color: var(--muted); font-size: 12px; font-weight: 700; white-space: nowrap; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: #f8faff; }
    .col-date { width: 88px; } .col-status { width: 96px; } .col-done { width: 52px; text-align: center; } .col-act { width: 120px; white-space: nowrap; }
    .out-link { font-size: 11px; color: var(--brand); text-decoration: underline; cursor: pointer; display: block; margin-top: 3px; }
    .done-ic  { font-size: 15px; }

    @keyframes spin { to { transform: rotate(360deg); } }
    .spinner { display: inline-block; width: 13px; height: 13px; border: 2px solid #f3a800; border-top-color: transparent; border-radius: 50%; animation: spin .7s linear infinite; vertical-align: middle; margin-right: 5px; }

    @media (max-width: 740px) { .grid3, .grid2 { grid-template-columns: 1fr; } }

    /* ── Mobile (phone) ───────────────────────────────────────────────────── */
    @media (max-width: 600px) {
      header { padding: 10px 14px; padding-left: max(14px, env(safe-area-inset-left)); padding-right: max(14px, env(safe-area-inset-right)); gap: 6px; }
      h1 { font-size: 15px; }
      #headerSub { font-size: 10px; max-width: 130px; text-align: right; line-height: 1.3; }
      main { width: calc(100vw - 16px); margin: 10px auto 28px; gap: 10px; }
      section { padding: 12px 12px; border-radius: 6px; }
      .sec-title { font-size: 10px; margin-bottom: 10px; }

      /* Inputs — 16px stops iOS from auto-zooming on focus */
      input, select, textarea { font-size: 16px; padding: 12px; }
      textarea { min-height: 64px; }

      /* Action buttons — full width stack on phone */
      .actions { flex-direction: column; gap: 8px; }
      .actions button { width: 100%; font-size: 15px; min-height: 48px; border-radius: 8px; }
      #refreshBtn { margin-left: 0 !important; order: 99; }
      .btn-sm { min-height: 38px; padding: 6px 14px; font-size: 13px; }

      /* Status box */
      #statusBox { font-size: 13px; }

      /* ── Card table layout ── */
      .tbl-wrap { overflow-x: visible; }
      table { min-width: 0; }
      table, thead, tbody, tr, th, td { display: block; width: 100%; }
      thead { display: none; }
      tr {
        background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
        margin-bottom: 12px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,.06);
      }
      tr:last-child td { border-bottom: none; }
      tr:hover td { background: transparent; }
      td {
        border: none; padding: 5px 0;
        display: flex; gap: 8px; align-items: flex-start; font-size: 13px;
        border-bottom: 1px solid var(--wash);
      }
      td:last-child { border-bottom: none; }
      td::before {
        content: attr(data-label);
        font-size: 10px; font-weight: 700; color: var(--muted);
        text-transform: uppercase; letter-spacing: .04em;
        min-width: 62px; padding-top: 2px; flex-shrink: 0;
      }
      td.col-act { margin-top: 6px; justify-content: flex-start; gap: 8px; flex-wrap: wrap; }
      td.col-act::before { display: none; }
      td.col-act button { flex: 1; min-width: 100px; }
      .col-date, .col-status, .col-done, .col-act { width: auto; white-space: normal; }
      .out-link { font-size: 12px; display: inline; }
    }
  </style>
</head>
<body>
  <header>
    <h1>🎬 Shoppee Video v1.0</h1>
    <span id="headerSub">Loading…</span>
  </header>
  <main>

    <!-- Form -->
    <section>
      <p class="sec-title">Add / Update Product Row</p>
      <div class="grid3">
        <label>Date <input id="fDate" name="Date" type="date" required></label>
        <label>Source Type
          <select id="fSrc">
            <option>Auto</option><option>Approved Media</option><option>Shopee Page</option>
          </select>
        </label>
        <label>Render Mode
          <select id="fMode">
            <option value="auto">Auto (light for video / blur for image)</option>
            <option value="light">Light — scale + preserve audio</option>
            <option value="vertical-blur">Vertical Blur — blur canvas</option>
          </select>
        </label>
        <label style="opacity:.7">Record ID <span class="hint">Auto-assigned</span>
          <input id="fRecordId" readonly placeholder="e.g. ASV-0000001" style="background:#f5f7fb;cursor:default">
        </label>
      </div>
      <div class="grid2" style="margin-top:11px">
        <label class="wide">Product Link <span class="hint">Full Shopee/TikTok URL or direct media link — avoid short s.shopee.com.my links</span>
          <input id="fLink" type="url" required placeholder="https://shopee.com.my/Product-Name-i.xxx.xxxxxxx or https://vt.tiktok.com/…">
          <span id="linkTypeHint" style="display:none;font-size:11px;color:#0f766e;font-weight:700;margin-top:3px;line-height:1.4"></span>
          <span id="tiktokHint" style="display:none;font-size:11px;color:#7c3aed;font-weight:600;margin-top:3px;line-height:1.4">
            📸 TikTok photo-mode (carousel) posts have no downloadable video — the workflow will render the cover thumbnail with background audio instead. For best affiliate results, use a standard TikTok video post URL.
          </span>
        </label>
        <label>Product Name <input id="fName" required placeholder="e.g. Electrova Cordless UV Mite"></label>
        <label>Shop Name    <input id="fShop" required placeholder="e.g. Electrova"></label>
        <label>Status
          <select id="fStatus">
            <option>Pending</option><option>Downloaded</option><option>Edited</option>
            <option>Failed</option><option>Skipped</option>
          </select>
        </label>
        <label class="checkline wide"><input id="fDone" type="checkbox"> Mark as Done</label>
        <label class="wide">Notes <textarea id="fNotes" placeholder="Optional — e.g. retry reason, approved source…"></textarea></label>
      </div>
      <div class="actions">
        <button class="btn-primary" id="saveBtn">💾 Save Row</button>
        <button class="btn-primary" id="saveNextBtn" style="background:#0369a1">💾 Save &amp; Add Next</button>
        <button class="btn-danger"  id="dlBtn">⬇️ Save &amp; Download</button>
        <button class="btn-danger"  id="dlAnalyzeBtn" style="background:#7c3aed">⬇️🔍 Save + Download + Analyze</button>
        <button class="btn-plain"   id="analyzeBtn" style="background:#d1fae5;color:#065f46">🔍 Analyze</button>
        <button class="btn-plain"   id="runAllBtn">▶ Run All Pending <span id="pendingBadge" class="badge badge-pending" style="display:none;margin-left:2px"></span></button>
        <button class="btn-plain"   id="clearBtn">✕ Clear</button>
        <button class="btn-plain"   id="openBtn">📂 Output Folder</button>
        <button class="btn-plain"   id="refreshBtn" style="margin-left:auto">↺ Refresh</button>
      </div>
    </section>

    <!-- Status -->
    <section id="statusBox">Ready — fill in a row and click Save or Download.</section>

    <!-- Table -->
    <section>
      <p class="sec-title">Masterlist <span id="rowCount" style="font-weight:400;font-size:11px"></span></p>
      <div class="tbl-wrap">
        <table>
          <thead>
            <tr>
              <th class="col-date">Date</th>
              <th>Product</th>
              <th>Shop</th>
              <th class="col-status">Status</th>
              <th class="col-done">Done</th>
              <th class="col-done" title="Analysis Done">🔍</th>
              <th>Notes / Output</th>
              <th class="col-act">Actions</th>
            </tr>
          </thead>
          <tbody id="rows"></tbody>
        </table>
      </div>
    </section>
  </main>

  <script>
    const statusBox = document.getElementById("statusBox");
    const rowsBody  = document.getElementById("rows");

    // ─── Helpers ────────────────────────────────────────────────────────────
    function esc(s) { return String(s || "").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;"); }

    function setStatus(msg, type) {
      statusBox.className = type || "";
      statusBox.innerHTML = (!type || type === "busy")
        ? `<span class="spinner"></span>${esc(msg)}`
        : esc(msg);
    }

    function badge(status) {
      const cls = { Edited:"badge-edited", Downloaded:"badge-downloaded",
                    Failed:"badge-failed", Pending:"badge-pending", Skipped:"badge-skipped" };
      return `<span class="badge ${cls[status]||"badge-pending"}">${esc(status||"Pending")}</span>`;
    }

    async function api(url, body) {
      const opts = body !== undefined
        ? { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body) }
        : {};
      const res  = await fetch(url, opts);
      const data = await res.json();
      if (!res.ok) { const e = new Error(data.message || "Request failed"); e.output = data.output; throw e; }
      return data;
    }

    // ─── Form ────────────────────────────────────────────────────────────────
    function getPayload() {
      return {
        "Record ID":    document.getElementById("fRecordId").value.trim(),
        "Date":         document.getElementById("fDate").value,
        "Product Link": document.getElementById("fLink").value,
        "Product Name": document.getElementById("fName").value,
        "Shop Name":    document.getElementById("fShop").value,
        "Source Type":  document.getElementById("fSrc").value,
        "Status":       document.getElementById("fStatus").value,
        "Done":         document.getElementById("fDone").checked ? "TRUE" : "FALSE",
        "Notes":        document.getElementById("fNotes").value,
        "Render Mode":  document.getElementById("fMode").value,
      };
    }

    function clearForm() {
      document.getElementById("fLink").value      = "";
      document.getElementById("fName").value      = "";
      document.getElementById("fShop").value      = "";
      document.getElementById("fNotes").value     = "";
      document.getElementById("fStatus").value    = "Pending";
      document.getElementById("fSrc").value       = "Auto";
      document.getElementById("fMode").value      = "auto";
      document.getElementById("fDone").checked    = false;
      document.getElementById("fRecordId").value  = "";
      document.getElementById("fDate").valueAsDate = new Date();
    }

    function loadRow(row) {
      document.getElementById("fDate").value      = row.Date || "";
      document.getElementById("fLink").value      = row["Product Link"] || "";
      document.getElementById("fName").value      = row["Product Name"] || "";
      document.getElementById("fShop").value      = row["Shop Name"] || "";
      document.getElementById("fNotes").value     = row.Notes || "";
      document.getElementById("fStatus").value    = row.Status || "Pending";
      document.getElementById("fSrc").value       = row["Source Type"] || "Auto";
      document.getElementById("fDone").checked    = row.Done === "TRUE";
      document.getElementById("fRecordId").value  = row["Record ID"] || "";
      window.scrollTo({ top: 0, behavior: "smooth" });
      document.getElementById("fLink").focus();
    }

    // ─── Table ───────────────────────────────────────────────────────────────
    async function refresh() {
      try {
        const { rows } = await api("/api/rows");
        const total   = rows.length;
        const edited  = rows.filter(r => r.Status === "Edited").length;
        const failed  = rows.filter(r => r.Status === "Failed").length;
        const pending = rows.filter(r => !r.Status || r.Status === "Pending").length;
        document.getElementById("rowCount").textContent =
          `(${total} row${total!==1?"s":""} · ✅ ${edited} · ❌ ${failed} · ⏳ ${pending})`;
        document.getElementById("headerSub").textContent =
          `${edited} edited · ${failed} failed · ${pending} pending`;
        const pb = document.getElementById("pendingBadge");
        if (pending > 0) { pb.textContent = pending; pb.style.display = "inline-block"; }
        else { pb.style.display = "none"; }

        rowsBody.innerHTML = "";
        [...rows].reverse().slice(0, 40).forEach(row => {
          const tr  = document.createElement("tr");
          const summary = row._summary || {};
          const out = (row["Output File"] || "").split(";")[0].trim();
          const postType = summary.post_type ? `<div style="font-size:11px;font-weight:700;color:#7c3aed;margin-bottom:4px">${esc(summary.post_type)}</div>` : "";
          const notesCell = postType + esc(row.Notes || "") +
            (out ? `<span class="out-link" data-path="${esc(out)}" title="${esc(out)}">📂 Open output file</span>` : "");

          const recordId = row["Record ID"] || "";
          tr.innerHTML = `
            <td class="col-date" data-label="Date">${esc(row.Date)}</td>
            <td data-label="Product">
              <strong>${esc(row["Product Name"])}</strong>
              ${recordId ? `<br><span style="color:var(--muted);font-size:10px;font-weight:600">${esc(recordId)}</span>` : ""}
              <br><span style="color:var(--muted);font-size:11px">${esc(row["Product Link"])}</span>
            </td>
            <td data-label="Shop">${esc(row["Shop Name"])}</td>
            <td class="col-status" data-label="Status">${badge(row.Status)}</td>
            <td class="col-done" data-label="Done"><span class="done-ic">${row.Done==="TRUE"?"✅":"⬜"}</span></td>
            <td class="col-done" data-label="Analyzed"><span class="done-ic">${row["Analysis Done"]==="TRUE"?"🔍":"⬜"}</span></td>
            <td data-label="Notes" style="font-size:12px">${notesCell}</td>
            <td class="col-act">
              <button class="btn-plain btn-sm load-btn">↑ Load</button>
              ${recordId ? `<button class="btn-plain btn-sm analyze-row-btn" style="background:#d1fae5;color:#065f46" data-rid="${esc(recordId)}">🔍</button>` : ""}
              ${row.Status==="Failed"?`<button class="btn-danger btn-sm retry-btn" style="margin-left:4px">↺ Retry</button>`:""}
            </td>`;

          tr.querySelector(".load-btn").onclick = () => loadRow(row);
          const retryBtn = tr.querySelector(".retry-btn");
          if (retryBtn) retryBtn.onclick = () => { loadRow({...row, Status:"Pending"}); setStatus("Row loaded — click Save & Download to retry.", "ok"); };
          const analyzeRowBtn = tr.querySelector(".analyze-row-btn");
          if (analyzeRowBtn) analyzeRowBtn.onclick = async () => {
            const rid = analyzeRowBtn.dataset.rid;
            analyzeRowBtn.disabled = true;
            setStatus(`Analyzing ${rid}…`);
            try {
              const r = await api("/api/analyze", { record_id: rid });
              setStatus("✅ " + r.message, "ok"); await refresh();
            } catch(e) { setStatus("❌ " + e.message, "err"); }
            finally { analyzeRowBtn.disabled = false; }
          };
          if (out) tr.querySelector(".out-link").onclick = async () => {
            try { await api("/api/open-file", { path: out }); }
            catch(e) { setStatus("Could not open file: " + e.message, "err"); }
          };
          rowsBody.appendChild(tr);
        });
      } catch(e) { setStatus("Could not load rows: " + e.message, "err"); }
    }

    // ─── Button handlers ─────────────────────────────────────────────────────
    document.getElementById("saveBtn").onclick = async () => {
      const btn = document.getElementById("saveBtn");
      btn.disabled = true; setStatus("Saving row to masterlist…");
      try {
        const r = await api("/api/save", getPayload());
        setStatus("✅ " + r.message, "ok"); clearForm(); await refresh();
      } catch(e) { setStatus("❌ " + e.message, "err"); }
      finally { btn.disabled = false; }
    };

    document.getElementById("dlBtn").onclick = async () => {
      const btn = document.getElementById("dlBtn");
      btn.disabled = true; setStatus("Saving row and running workflow — this may take 30–90 s…");
      try {
        const r = await api("/api/download", getPayload());
        setStatus("✅ " + r.message + (r.output ? "\\n\\n" + r.output : ""), "ok");
        clearForm(); await refresh();
      } catch(e) { setStatus("❌ " + e.message + (e.output ? "\\n\\n" + e.output : ""), "err"); await refresh(); }
      finally { btn.disabled = false; }
    };

    document.getElementById("dlAnalyzeBtn").onclick = async () => {
      const btn = document.getElementById("dlAnalyzeBtn");
      btn.disabled = true; setStatus("Saving row, downloading, and analyzing — this may take 60–120 s…");
      try {
        const r = await api("/api/download-analyze", getPayload());
        setStatus("✅ " + r.message + (r.output ? "\\n\\n" + r.output : ""), "ok");
        clearForm(); await refresh();
      } catch(e) { setStatus("❌ " + e.message + (e.output ? "\\n\\n" + e.output : ""), "err"); await refresh(); }
      finally { btn.disabled = false; }
    };

    document.getElementById("analyzeBtn").onclick = async () => {
      const rid = document.getElementById("fRecordId").value.trim();
      if (!rid) { setStatus("❌ Load a row first — Record ID is required for Analyze.", "err"); return; }
      const btn = document.getElementById("analyzeBtn");
      btn.disabled = true; setStatus(`Analyzing ${rid}…`);
      try {
        const r = await api("/api/analyze", { record_id: rid });
        setStatus("✅ " + r.message, "ok"); await refresh();
      } catch(e) { setStatus("❌ " + e.message, "err"); }
      finally { btn.disabled = false; }
    };

    document.getElementById("saveNextBtn").onclick = async () => {
      const btn = document.getElementById("saveNextBtn");
      btn.disabled = true; setStatus("Saving row…");
      try {
        const r = await api("/api/save", getPayload());
        setStatus("✅ Saved — add your next link.", "ok");
        clearForm(); await refresh();
        document.getElementById("fLink").focus();
      } catch(e) { setStatus("❌ " + e.message, "err"); }
      finally { btn.disabled = false; }
    };

    document.getElementById("runAllBtn").onclick = async () => {
      const btn = document.getElementById("runAllBtn");
      btn.disabled = true; setStatus("Running workflow on all pending rows — this may take a while…");
      try {
        const r = await api("/api/run-workflow", {});
        setStatus("✅ " + r.message + (r.output ? "\\n\\n" + r.output : ""), "ok");
        await refresh();
      } catch(e) { setStatus("❌ " + e.message + (e.output ? "\\n\\n" + e.output : ""), "err"); await refresh(); }
      finally { btn.disabled = false; }
    };

    document.getElementById("clearBtn").onclick   = () => { clearForm(); setStatus("Form cleared.", "ok"); };
    document.getElementById("refreshBtn").onclick = refresh;
    document.getElementById("openBtn").onclick    = async () => {
      try { const r = await api("/api/open-output", {}); setStatus("📂 " + r.message, "ok"); }
      catch(e) { setStatus("❌ " + e.message, "err"); }
    };

    // Init
    document.getElementById("fDate").valueAsDate = new Date();
    refresh();
    setInterval(refresh, 20000);

    // TikTok hint + preflight detection
    (function() {
      const linkInput = document.getElementById("fLink");
      const linkTypeHint = document.getElementById("linkTypeHint");
      const hint = document.getElementById("tiktokHint");
      let detectTimer = null;
      let detectSeq = 0;

      function clearLinkTypeHint() {
        linkTypeHint.style.display = "none";
        linkTypeHint.textContent = "";
      }

      function updateTikTokHint() {
        const val = linkInput.value.trim().toLowerCase();
        const isTikTok = val.includes("tiktok.com");
        hint.style.display = isTikTok ? "block" : "none";
        if (!isTikTok) {
          clearLinkTypeHint();
          return;
        }

        clearTimeout(detectTimer);
        detectTimer = setTimeout(async () => {
          const url = linkInput.value.trim();
          if (!url.toLowerCase().includes("tiktok.com")) {
            clearLinkTypeHint();
            return;
          }
          const seq = ++detectSeq;
          try {
            const result = await api("/api/detect-link", { url });
            if (seq !== detectSeq) return;
            if (result.post_type) {
              linkTypeHint.textContent = "🔎 " + result.post_type + " — " + result.message;
              linkTypeHint.style.display = "block";
              linkTypeHint.style.color = result.post_type === "Direct Video Post" ? "#065f46" : "#7c3aed";
            } else {
              clearLinkTypeHint();
            }
          } catch (_) {
            if (seq === detectSeq) clearLinkTypeHint();
          }
        }, 350);
      }
      linkInput.addEventListener("input", updateTikTokHint);
      linkInput.addEventListener("change", updateTikTokHint);
    })();
  </script>
</body>
</html>
"""


def default_row() -> dict[str, str]:
    return {
        "Record ID": "",
        "Date": "",
        "Product Link": "",
        "Product Name": "",
        "Shop Name": "",
        "Source Type": "Auto",
        "Status": "Pending",
        "Done": "FALSE",
        "Analysis Done": "FALSE",
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
    row["Analysis Done"] = "TRUE" if row["Analysis Done"].upper() in {"TRUE", "YES", "ON", "1"} else "FALSE"
    return row


def build_frontend_media_summary(row: dict[str, str]) -> dict[str, str]:
    notes = (row.get("Notes", "") or "").lower()
    product_link = (row.get("Product Link", "") or "").lower()
    if "photo-mode post" in notes:
        post_type = "Photo-mode Post"
    elif "video post" in notes:
        post_type = "Video Post"
    elif "tiktok.com" in product_link or "vt.tiktok.com" in product_link or "vm.tiktok.com" in product_link:
        post_type = "Unknown TikTok Media"
    else:
        post_type = ""
    return {
        "post_type": post_type,
        "analysis_done": row.get("Analysis Done", "FALSE"),
        "output_file": row.get("Output File", ""),
    }


def build_tiktok_preflight_summary(url: str, bundle: dict[str, object] | None) -> dict[str, str]:
    if not is_tiktok_video_url(url):
        return {"post_type": "", "message": ""}

    bundle = bundle or {}
    post_type = str(bundle.get("post_type") or bundle.get("kind") or "").strip().lower()
    if post_type == "video":
        return {
            "post_type": "Direct Video Post",
            "message": "TikTok exposed a native video stream for direct download.",
        }
    if post_type == "photo_mode":
        image_count = len(bundle.get("image_urls") or [])
        has_audio = bool(bundle.get("audio_url"))
        audio_note = " plus background audio" if has_audio else ""
        return {
            "post_type": "Photo-mode Post",
            "message": f"TikTok exposed {image_count} image asset(s){audio_note}; the workflow will render a slideshow MP4.",
        }
    return {
        "post_type": "Unknown TikTok Media",
        "message": "TikTok media type is not clear yet; download is still the best verification step.",
    }


def upsert_masterlist_row(masterlist_path: Path, payload: dict[str, str]) -> tuple[int, dict[str, str]]:
    """Save or update a row. Returns (row_number, final_record)."""
    ensure_masterlist_columns(masterlist_path)
    rows = read_masterlist(masterlist_path)
    row = normalize_frontend_row(payload)
    if not row["Product Link"] or not row["Product Name"] or not row["Shop Name"]:
        raise ValueError("Product Link, Product Name, and Shop Name are required.")

    # Match by Record ID first (stable identity), fall back to Product Link
    incoming_id = row.get("Record ID", "").strip()
    for index, existing in enumerate(rows):
        match_id = incoming_id and existing.get("Record ID", "") == incoming_id
        match_link = not incoming_id and existing["Product Link"] == row["Product Link"]
        if match_id or match_link:
            merged = existing.copy()
            # Preserve fields the frontend does not edit
            merged.update({k: v for k, v in row.items() if v or k not in {"Analysis Done", "Last Processed At", "Output Folder", "Output File"}})
            rows[index] = merged
            write_masterlist(masterlist_path, rows)
            # Write product-info.md on save
            platform = detect_platform(merged.get("Product Link", ""))
            product_folder = resolve_product_folder(
                masterlist_path.parent.parent / "output",
                platform,
                merged.get("Shop Name", ""),
                merged.get("Product Name", ""),
            )
            try:
                write_product_info(product_folder, merged, platform)
            except Exception:
                pass
            return index + 2, merged

    rows.append(row)
    write_masterlist(masterlist_path, rows)
    # The backfill in write_masterlist will have assigned a Record ID — get the refreshed list
    refreshed = read_masterlist(masterlist_path)
    final = refreshed[-1]
    platform = detect_platform(final.get("Product Link", ""))
    product_folder = resolve_product_folder(
        masterlist_path.parent.parent / "output",
        platform,
        final.get("Shop Name", ""),
        final.get("Product Name", ""),
    )
    try:
        write_product_info(product_folder, final, platform)
    except Exception:
        pass
    return len(refreshed) + 1, final


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


def detect_lan_ip() -> str | None:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            ip = sock.getsockname()[0]
            if ip and not ip.startswith("127."):
                return ip
    except OSError:
        pass

    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and not ip.startswith("127."):
            return ip
    except OSError:
        return None
    return None


def build_access_urls(host: str, port: int, local_ip: str | None = None) -> list[str]:
    if host == "0.0.0.0":
        urls = [f"http://127.0.0.1:{port}/"]
        if local_ip and local_ip != "127.0.0.1":
            urls.append(f"http://{local_ip}:{port}/")
        return urls
    return [f"http://{host}:{port}/"]


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
            rows = []
            for row in read_masterlist(self.masterlist_path):
                enriched = row.copy()
                enriched["_summary"] = build_frontend_media_summary(enriched)
                rows.append(enriched)
            self.send_json({"rows": rows})
            return
        self.send_json({"message": "Not found"}, status=404)

    def do_POST(self) -> None:
        try:
            if self.path == "/api/save":
                row_number, _ = upsert_masterlist_row(self.masterlist_path, self.read_json())
                self.send_json({"message": f"Saved row {row_number} to masterlist."})
                return
            if self.path == "/api/download":
                row_number, _ = upsert_masterlist_row(self.masterlist_path, self.read_json())
                result = run_workflow(self.project_root)
                status = "completed" if result.returncode == 0 else "failed"
                self.send_json({
                    "message": f"Saved row {row_number}; workflow {status}.",
                    "output": (result.stdout + result.stderr).strip(),
                }, status=200 if result.returncode == 0 else 500)
                return
            if self.path == "/api/download-analyze":
                row_number, record = upsert_masterlist_row(self.masterlist_path, self.read_json())
                record_id = record.get("Record ID", "")
                # Run download + analyze via CLI so render mode and full pipeline are used
                script = self.project_root / "scripts" / "process_shopee_video.py"
                result = subprocess.run(
                    [sys.executable, str(script),
                     "--project-root", str(self.project_root),
                     "--download-and-analyze-record-id", record_id],
                    capture_output=True, text=True, check=False,
                )
                if result.returncode != 0:
                    raise RuntimeError((result.stdout + result.stderr).strip())
                self.send_json({
                    "message": f"Saved row {row_number} ({record_id}); download + analyze complete.",
                    "output": (result.stdout + result.stderr).strip(),
                })
                return
            if self.path == "/api/analyze":
                data = self.read_json()
                record_id = data.get("record_id", "").strip()
                if not record_id:
                    self.send_json({"message": "record_id is required."}, status=400)
                    return
                records = read_masterlist(self.masterlist_path)
                record = find_record_by_id(records, record_id)
                if not record:
                    self.send_json({"message": f"Record ID {record_id} not found."}, status=404)
                    return
                analyze_row_record(self.project_root, record)
                write_masterlist(self.masterlist_path, records)
                self.send_json({"message": f"Analysis complete for {record_id}. analysis-result.md written."})
                return
            if self.path == "/api/detect-link":
                data = self.read_json()
                url = data.get("url", "").strip()
                summary = build_tiktok_preflight_summary(url, discover_tiktok_media_bundle(url) if url else None)
                self.send_json(summary)
                return
            if self.path == "/api/open-output":
                open_output_folder(self.project_root)
                self.send_json({"message": "Output folder opened."})
                return
            if self.path == "/api/open-file":
                data = self.read_json()
                file_path = data.get("path", "")
                if file_path and Path(file_path).exists():
                    subprocess.Popen(["explorer.exe", "/select,", file_path])
                    self.send_json({"message": "File highlighted in Explorer."})
                else:
                    self.send_json({"message": "File not found."}, status=404)
                return
            if self.path == "/api/run-workflow":
                result = run_workflow(self.project_root)
                status = "completed" if result.returncode == 0 else "failed"
                self.send_json({
                    "message": f"Workflow {status}.",
                    "output": (result.stdout + result.stderr).strip(),
                }, status=200 if result.returncode == 0 else 500)
                return
            self.send_json({"message": "Not found"}, status=404)
        except Exception as exc:
            self.send_json({"message": str(exc)}, status=500)


def run_server(project_root: Path, host: str, port: int, open_browser: bool) -> None:
    FrontendHandler.project_root = project_root
    FrontendHandler.masterlist_path = project_root / "masterlist" / "List of Link Shopee VIdeo.csv"
    ensure_masterlist_columns(FrontendHandler.masterlist_path)
    server = ThreadingHTTPServer((host, port), FrontendHandler)
    urls = build_access_urls(host, port, detect_lan_ip() if host == "0.0.0.0" else None)
    print("AI - Shoppee Video v1.0 frontend:")
    for url in urls:
        print(f"  {url}")
    if open_browser:
        webbrowser.open(urls[0])
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
