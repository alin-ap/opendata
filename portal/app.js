/* global window, document */

const $ = (id) => document.getElementById(id);

function deriveBaseUrl(url) {
  try {
    const u = new URL(url);
    u.pathname = u.pathname.replace(/\/[^/]*$/, "/");
    return u.toString();
  } catch (_) {
    return url.replace(/\/[^/]*$/, "/");
  }
}

const fmt = {
  bytes: (n) => {
    if (!Number.isFinite(n) || n <= 0) return "-";
    const u = ["B", "KB", "MB", "GB"];
    let v = n, i = 0;
    while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
    return `${v.toFixed(i ? 1 : 0)} ${u[i]}`;
  },
  rows: (n) => Number.isFinite(n) && n >= 0 ? n.toLocaleString() : "-",
  date: (s) => s ? s.slice(0, 10) : "-",
};

const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function pad(s, len, right) {
  s = String(s);
  if (s.length >= len) return s.slice(0, len);
  const sp = " ".repeat(len - s.length);
  return right ? sp + s : s + sp;
}

function renderTable(datasets) {
  if (!datasets.length) return "No datasets.";

  const cols = [
    { k: "id", l: "Dataset ID", w: 35 },
    { k: "row_count", l: "Rows", w: 10, r: 1, f: fmt.rows },
    { k: "data_size_bytes", l: "Size", w: 10, r: 1, f: fmt.bytes },
    { k: "updated_at", l: "Updated", w: 12, f: fmt.date },
  ];

  const W = cols.reduce((s, c) => s + c.w, 0) + cols.length + 1;
  const L = [];

  L.push("." + "-".repeat(W - 2) + ".");
  const t = "Dataset Registry";
  const p = Math.floor((W - 2 - t.length) / 2);
  L.push("|" + " ".repeat(p) + t + " ".repeat(W - 2 - p - t.length) + "|");
  L.push("|" + "-".repeat(W - 2) + "|");
  L.push("| " + cols.map(c => pad(c.l, c.w, c.r)).join(" | ") + " |");
  L.push("|-" + cols.map(c => "-".repeat(c.w)).join("-|-") + "-|");

  for (const ds of datasets) {
    const cells = cols.map(c => pad(c.f ? c.f(ds[c.k]) : (ds[c.k] ?? "-"), c.w, c.r));
    const link = `<a href="#/d/${encodeURIComponent(ds.id)}">${esc(cells[0].trim())}</a>`;
    L.push("| " + link + " ".repeat(cols[0].w - cells[0].trim().length) + " | " + cells.slice(1).join(" | ") + " |");
  }

  L.push("'" + "-".repeat(W - 2) + "'");
  return L.join("\n");
}

function renderPreview(p) {
  if (!p.columns?.length) return "<span class='muted'>No preview.</span>";
  const h = p.columns.map(c => `<th>${esc(c)}</th>`).join("");
  const b = (p.rows || []).map(r => "<tr>" + p.columns.map(c => `<td>${esc(r[c] ?? "")}</td>`).join("") + "</tr>").join("");
  return `<table><thead><tr>${h}</tr></thead><tbody>${b}</tbody></table>`;
}

async function fetchJson(url) {
  const r = await fetch(url, { cache: "no-store" });
  if (!r.ok) throw new Error(r.status);
  return r.json();
}

async function fetchText(url) {
  const r = await fetch(url, { cache: "no-store" });
  return r.ok ? r.text() : null;
}

const state = { url: null, base: null, datasets: [] };

async function load() {
  const cfg = window.OPENDATA_CONFIG || {};
  const candidates = [
    new URL(window.location.href).searchParams.get("index"),
    cfg.defaultIndexUrl,
    new URL("../index.json", window.location.href).toString(),
  ].filter(Boolean);

  for (const url of candidates) {
    try {
      const idx = await fetchJson(url);
      state.url = url;
      state.base = deriveBaseUrl(url);
      state.datasets = idx.datasets || [];
      render();
      return;
    } catch (_) {}
  }
  $("dataset-list").textContent = "Failed to load index.json";
}

function render() {
  const q = ($("search").value || "").toLowerCase();
  const filtered = state.datasets.filter(d => {
    if (!q) return true;
    return `${d.id} ${d.title || ""} ${d.description || ""}`.toLowerCase().includes(q);
  });
  $("dataset-list").innerHTML = renderTable(filtered);
}

async function showDetail(id) {
  const ds = state.datasets.find(d => d.id === id);
  if (!ds) return;

  $("detail-title").textContent = ds.id;
  $("detail-data").href = ds.data_key ? state.base + ds.data_key : "#";
  $("detail-snippet").textContent = `import opendata as od\ndf = od.load("${ds.id}")`;

  const stats = [
    ["updated", fmt.date(ds.updated_at)],
    ["rows", fmt.rows(ds.row_count)],
    ["size", fmt.bytes(ds.data_size_bytes)],
    ["license", ds.license],
    ["frequency", ds.frequency],
  ].filter(([,v]) => v && v !== "-");
  $("detail-stats").innerHTML = stats.map(([k,v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("");

  $("preview").innerHTML = "<span class='muted'>Loading...</span>";
  $("schema").textContent = "Loading...";

  if (ds.preview_key) {
    try {
      $("preview").innerHTML = renderPreview(await fetchJson(state.base + ds.preview_key));
    } catch (_) {
      $("preview").innerHTML = "<span class='muted'>Failed.</span>";
    }
  } else {
    $("preview").innerHTML = "<span class='muted'>No preview.</span>";
  }

  if (ds.metadata_key) {
    try {
      const meta = await fetchJson(state.base + ds.metadata_key);
      const schema = { format: meta.format, columns: meta.columns };
      $("schema").textContent = JSON.stringify(schema, null, 2);
    } catch (_) {
      $("schema").textContent = "(failed)";
    }
  } else {
    $("schema").textContent = "(none)";
  }

  $("list-view").classList.add("hidden");
  $("detail-view").classList.remove("hidden");
}

function route() {
  const h = window.location.hash;
  if (h.startsWith("#/d/")) {
    showDetail(decodeURIComponent(h.slice(4)));
  } else {
    $("list-view").classList.remove("hidden");
    $("detail-view").classList.add("hidden");
  }
}

$("search").addEventListener("input", render);
window.addEventListener("hashchange", route);
load().then(route);
