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

function datasetPrefix(id) {
  return `datasets/${id}`;
}

function dataKey(id) {
  return `${datasetPrefix(id)}/data.parquet`;
}

function metadataKey(id) {
  return `${datasetPrefix(id)}/metadata.json`;
}

const fmt = {
  bytes: (n) => {
    if (!Number.isFinite(n) || n < 0) return "-";
    if (n === 0) return "0 B";
    const u = ["B", "KB", "MB", "GB"];
    let v = n, i = 0;
    while (v >= 1024 && i < u.length - 1) { v /= 1024; i++; }
    return `${v.toFixed(i ? 1 : 0)} ${u[i]}`;
  },
  rows: (n) => Number.isFinite(n) && n >= 0 ? n.toLocaleString() : "-",
  date: (s) => s ? s.slice(0, 10) : "-",
  bytesWithRaw: (n) => {
    if (!Number.isFinite(n) || n < 0) return "-";
    return `${n.toLocaleString()} (${fmt.bytes(n)})`;
  },
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

function formatList(list) {
  if (!Array.isArray(list) || list.length === 0) return null;
  return list.map((v) => String(v)).join(", ");
}

function formatColumns(columns) {
  if (!Array.isArray(columns) || columns.length === 0) return null;
  const out = columns.map((c) => {
    if (!c) return null;
    if (typeof c === "string") return c;
    if (typeof c === "object") {
      const name = typeof c.name === "string" ? c.name : "";
      const type = typeof c.type === "string" ? c.type : "";
      if (name && type) return `${name} (${type})`;
      if (name) return name;
      if (type) return type;
    }
    return null;
  }).filter(Boolean);
  return out.length ? out.join(", ") : null;
}

function formatValue(value) {
  if (value === null || value === undefined) return null;
  if (Array.isArray(value)) return formatList(value);
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function addMeta(entries, seen, key, value, formatter) {
  const formatted = formatter ? formatter(value) : formatValue(value);
  if (formatted === null || formatted === "" || formatted === "-") return;
  entries.push([key, formatted]);
  seen.add(key);
}

function buildMetaEntries(ds, m) {
  const merged = { ...ds, ...(m || {}) };
  const entries = [];
  const seen = new Set();
  const datasetId = (m && m.dataset_id) || ds.id;

  addMeta(entries, seen, "dataset_id", datasetId);
  addMeta(entries, seen, "title", merged.title);
  addMeta(entries, seen, "description", merged.description);
  addMeta(entries, seen, "updated_at", merged.updated_at);
  addMeta(entries, seen, "row_count", merged.row_count, fmt.rows);
  addMeta(entries, seen, "data_size_bytes", merged.data_size_bytes, fmt.bytesWithRaw);
  addMeta(entries, seen, "license", merged.license);
  addMeta(entries, seen, "frequency", merged.frequency);
  addMeta(entries, seen, "repo", merged.repo);
  addMeta(entries, seen, "topics", merged.topics, formatList);
  addMeta(entries, seen, "owners", merged.owners, formatList);

  const source = (m && m.source) || ds.source;
  if (source && typeof source === "object") {
    addMeta(entries, seen, "source.provider", source.provider);
    addMeta(entries, seen, "source.homepage", source.homepage);
    addMeta(entries, seen, "source.dataset", source.dataset);
  }

  const geo = (m && m.geo) || ds.geo;
  if (geo && typeof geo === "object") {
    addMeta(entries, seen, "geo.scope", geo.scope);
    addMeta(entries, seen, "geo.countries", geo.countries, formatList);
    addMeta(entries, seen, "geo.regions", geo.regions, formatList);
  }

  addMeta(entries, seen, "checksum_sha256", merged.checksum_sha256);
  addMeta(entries, seen, "columns", m && m.columns, formatColumns);

  if (m && m.preview && typeof m.preview === "object") {
    addMeta(entries, seen, "preview.generated_at", m.preview.generated_at);
  }

  if (m && typeof m === "object") {
    for (const [key, value] of Object.entries(m)) {
      if (seen.has(key)) continue;
      if (key === "preview" || key === "columns" || key === "source" || key === "geo") continue;
      addMeta(entries, seen, key, value);
    }
  }

  return entries;
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
  const dataHref = ds.data_key || dataKey(ds.id);
  $("detail-data").href = state.base + dataHref;
  $("detail-snippet").textContent = `import opendata as od\ndf = od.load("${ds.id}")`;

  const meta = buildMetaEntries(ds, null);
  $("detail-meta").innerHTML = meta.map(([k,v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("");
  $("preview").innerHTML = "<span class='muted'>Loading...</span>";

  const metaHref = ds.metadata_key || metadataKey(ds.id);
  if (metaHref) {
    try {
      const m = await fetchJson(state.base + metaHref);
      const metaFull = buildMetaEntries(ds, m);
      $("detail-meta").innerHTML = metaFull.map(([k,v]) => `<dt>${k}</dt><dd>${esc(v)}</dd>`).join("");

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
