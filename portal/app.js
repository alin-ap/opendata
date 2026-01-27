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
  if (!datasets.length) return "<p class='muted'>No datasets.</p>";

  const cols = [
    { k: "id", l: "Dataset ID" },
    { k: "row_count", l: "Rows", r: 1, f: fmt.rows },
    { k: "data_size_bytes", l: "Size", r: 1, f: fmt.bytes },
    { k: "updated_at", l: "Updated", r: 1, f: fmt.date },
  ];

  const head = cols.map(c => `<th${c.r ? ' class="r"' : ""}>${esc(c.l)}</th>`).join("");
  const rows = datasets.map(ds => {
    const cells = cols.map((c, i) => {
      const val = c.f ? c.f(ds[c.k]) : (ds[c.k] ?? "-");
      if (i === 0) {
        return `<td><a href="#/d/${encodeURIComponent(ds.id)}">${esc(val)}</a></td>`;
      }
      return `<td${c.r ? ' class="r"' : ""}>${esc(val)}</td>`;
    });
    return `<tr>${cells.join("")}</tr>`;
  });

  return `<table class="data-table"><thead><tr>${head}</tr></thead><tbody>${rows.join("")}</tbody></table>`;
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

  $("brand-dataset-name").textContent = ds.id;
  $("detail-data").href = ds.data_key ? state.base + ds.data_key : "#";
  $("detail-snippet").textContent = `import opendata as od\ndf = od.load("${ds.id}")`;

  const meta = [
    ["updated", fmt.date(ds.updated_at)],
    ["rows", fmt.rows(ds.row_count)],
    ["size", fmt.bytes(ds.data_size_bytes)],
    ["license", ds.license],
    ["frequency", ds.frequency],
  ].filter(([,v]) => v && v !== "-");
  $("detail-meta").innerHTML = meta.map(([k,v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("");
  $("preview").innerHTML = "<span class='muted'>Loading...</span>";

  if (ds.metadata_key) {
    try {
      const m = await fetchJson(state.base + ds.metadata_key);
      if (m.format) meta.push(["format", m.format]);
      if (m.columns) meta.push(["columns", m.columns.map(c => c.name).join(", ")]);
      $("detail-meta").innerHTML = meta.map(([k,v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("");

      if (m.preview) {
        $("preview").innerHTML = renderPreview(m.preview);
      } else {
        $("preview").innerHTML = "<span class='muted'>No preview.</span>";
      }
    } catch (_) {
      $("preview").innerHTML = "<span class='muted'>Failed.</span>";
    }
  } else {
    $("preview").innerHTML = "<span class='muted'>No preview.</span>";
  }

  $("list-view").classList.add("hidden");
  $("detail-view").classList.remove("hidden");
}

function route() {
  const h = window.location.hash;
  if (h.startsWith("#/d/")) {
    $("brand-portal").classList.add("hidden");
    $("brand-dataset").classList.remove("hidden");
    showDetail(decodeURIComponent(h.slice(4)));
  } else {
    $("brand-portal").classList.remove("hidden");
    $("brand-dataset").classList.add("hidden");
    $("list-view").classList.remove("hidden");
    $("detail-view").classList.add("hidden");
  }
}

$("search").addEventListener("input", render);
window.addEventListener("hashchange", route);
load().then(route);
