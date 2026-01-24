/* global window, document */

const STORAGE_KEY = "opendata:index_url";

function $(id) {
  const el = document.getElementById(id);
  if (!el) throw new Error(`missing element: ${id}`);
  return el;
}

function getIndexUrlFromQuery() {
  const url = new URL(window.location.href);
  const q = url.searchParams.get("index");
  if (!q) return null;
  try {
    return decodeURIComponent(q);
  } catch (_) {
    return q;
  }
}

function deriveBaseUrl(indexUrl) {
  try {
    const u = new URL(indexUrl);
    u.hash = "";
    // Remove the last path segment (index.json).
    u.pathname = u.pathname.replace(/\/[^/]*$/, "/");
    return u.toString();
  } catch (_) {
    // Fallback: best-effort.
    return indexUrl.replace(/\/[^/]*$/, "/");
  }
}

function fmtBytes(n) {
  const x = Number(n);
  if (!Number.isFinite(x) || x <= 0) return "-";
  const units = ["B", "KB", "MB", "GB"];
  let v = x;
  let i = 0;
  while (v >= 1024 && i < units.length - 1) {
    v /= 1024;
    i += 1;
  }
  return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
}

async function fetchJson(url) {
  const resp = await fetch(url, { cache: "no-store" });
  if (!resp.ok) {
    const txt = await resp.text().catch(() => "");
    throw new Error(`fetch failed: ${resp.status} ${resp.statusText} ${txt}`);
  }
  return await resp.json();
}

async function fetchText(url) {
  const resp = await fetch(url, { cache: "no-store" });
  if (!resp.ok) return null;
  return await resp.text();
}

function setView(name) {
  const list = $("list-view");
  const detail = $("detail-view");
  if (name === "list") {
    list.classList.remove("hidden");
    detail.classList.add("hidden");
  } else {
    list.classList.add("hidden");
    detail.classList.remove("hidden");
  }
}

function renderDatasetCard(ds) {
  const card = document.createElement("button");
  card.type = "button";
  card.className = "card";
  card.style.textAlign = "left";
  card.style.cursor = "pointer";
  card.innerHTML = `
    <h3>${escapeHtml(ds.title || ds.id)}</h3>
    <div class="id">${escapeHtml(ds.id)}</div>
    <div class="desc">${escapeHtml(ds.description || "")}</div>
    <div class="tags">${(ds.tags || []).slice(0, 6).map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("")}</div>
  `;
  card.addEventListener("click", () => {
    window.location.hash = `#/d/${encodeURIComponent(ds.id)}`;
  });
  return card;
}

function escapeHtml(s) {
  return String(s)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderPreviewTable(preview) {
  const cols = preview.columns || [];
  const rows = preview.rows || [];
  if (!cols.length) {
    return `<div class="muted">No preview available.</div>`;
  }
  const head = `<tr>${cols.map((c) => `<th>${escapeHtml(c)}</th>`).join("")}</tr>`;
  const body = rows
    .map((r) => `<tr>${cols.map((c) => `<td>${escapeHtml(r[c] ?? "")}</td>`).join("")}</tr>`)
    .join("");
  return `<table><thead>${head}</thead><tbody>${body}</tbody></table>`;
}

function renderStats(ds) {
  const kv = [
    ["version", ds.version],
    ["updated_at", ds.updated_at],
    ["row_count", ds.row_count],
    ["size", fmtBytes(ds.data_size_bytes)],
  ];
  return kv
    .filter(([, v]) => v !== undefined)
    .map(
      ([k, v]) =>
        `<dt>${escapeHtml(k)}</dt><dd>${escapeHtml(v === null ? "-" : v)}</dd>`,
    )
    .join("");
}

async function showDetail(state, datasetId) {
  const ds = (state.datasets || []).find((d) => d.id === datasetId);
  if (!ds) {
    $("detail-title").textContent = "Dataset not found";
    $("detail-id").textContent = datasetId;
    setView("detail");
    return;
  }

  $("detail-title").textContent = ds.title || ds.id;
  $("detail-id").textContent = ds.id;
  $("detail-repo").href = ds.repo || "#";
  $("detail-snippet").textContent = `import opendata as od\n\ndf = od.load(\"${ds.id}\")`;
  $("detail-stats").innerHTML = renderStats(ds);

  const base = deriveBaseUrl(state.indexUrl);
  const dataUrl = ds.data_key ? base + ds.data_key : "#";
  $("detail-data").href = dataUrl;

  const readmeUrl = ds.readme_key ? base + ds.readme_key : null;
  const previewUrl = ds.preview_key ? base + ds.preview_key : null;
  const schemaUrl = ds.schema_key ? base + ds.schema_key : null;

  $("readme").textContent = "(loading…)";
  $("preview").innerHTML = `<div class="muted">Loading preview…</div>`;
  $("schema").textContent = "(loading…)";

  if (readmeUrl) {
    const txt = await fetchText(readmeUrl);
    $("readme").textContent = txt || "(README not found)";
  } else {
    $("readme").textContent = "(README not available)";
  }

  if (previewUrl) {
    try {
      const preview = await fetchJson(previewUrl);
      $("preview").innerHTML = renderPreviewTable(preview);
    } catch (e) {
      $("preview").innerHTML = `<div class="muted">Failed to load preview.</div>`;
    }
  } else {
    $("preview").innerHTML = `<div class="muted">No preview key in index.</div>`;
  }

  if (schemaUrl) {
    const schema = await fetchJson(schemaUrl).catch(() => null);
    $("schema").textContent = schema ? JSON.stringify(schema, null, 2) : "(schema not found)";
  } else {
    $("schema").textContent = "(schema not available)";
  }

  setView("detail");
}

function parseRoute() {
  const h = window.location.hash || "";
  if (h.startsWith("#/d/")) {
    const raw = h.slice("#/d/".length);
    return { name: "detail", datasetId: decodeURIComponent(raw) };
  }
  return { name: "list" };
}

function openConfig(initialValue) {
  $("config").classList.remove("hidden");
  $("config-input").value = initialValue || "";
  $("config-input").focus();
}

function closeConfig() {
  $("config").classList.add("hidden");
}

async function boot() {
  const state = {
    indexUrl: null,
    baseUrl: null,
    index: null,
    datasets: [],
  };

  $("config-btn").addEventListener("click", () => openConfig(state.indexUrl));
  $("config-cancel").addEventListener("click", closeConfig);
  $("config").addEventListener("click", (e) => {
    if (e.target && e.target.id === "config") closeConfig();
  });
  $("back").addEventListener("click", () => {
    window.location.hash = "#/";
  });
  $("copy-snippet").addEventListener("click", async () => {
    const text = $("detail-snippet").textContent || "";
    await navigator.clipboard.writeText(text).catch(() => {});
  });

  $("config-save").addEventListener("click", async () => {
    const url = $("config-input").value.trim();
    if (!url) return;
    window.localStorage.setItem(STORAGE_KEY, url);
    state.indexUrl = url;
    closeConfig();
    await reloadIndex(state);
    await handleRoute(state);
  });

  const initial = getIndexUrlFromQuery() || window.localStorage.getItem(STORAGE_KEY);
  if (!initial) {
    // If the portal is hosted in the same bucket as index.json (e.g. R2), try
    // a relative default: /portal/index.html -> ../index.json.
    const auto = new URL("../index.json", window.location.href).toString();
    try {
      await fetchJson(auto);
      state.indexUrl = auto;
      window.localStorage.setItem(STORAGE_KEY, auto);
      await reloadIndex(state);
    } catch (_) {
      openConfig("");
      return;
    }
  } else {
    state.indexUrl = initial;
    await reloadIndex(state);
  }

  window.addEventListener("hashchange", () => {
    handleRoute(state);
  });

  $("search").addEventListener("input", () => {
    renderList(state);
  });

  await handleRoute(state);
}

async function reloadIndex(state) {
  state.baseUrl = deriveBaseUrl(state.indexUrl);
  $("index-url").textContent = state.indexUrl;

  state.index = await fetchJson(state.indexUrl);
  state.datasets = Array.isArray(state.index.datasets) ? state.index.datasets : [];
  renderList(state);
}

function renderList(state) {
  const q = ($("search").value || "").trim().toLowerCase();
  const list = $("dataset-list");
  list.innerHTML = "";

  const filtered = (state.datasets || []).filter((d) => {
    if (!q) return true;
    const blob = `${d.id} ${d.title || ""} ${d.description || ""} ${(d.tags || []).join(" ")}`.toLowerCase();
    return blob.includes(q);
  });

  if (!filtered.length) {
    const empty = document.createElement("div");
    empty.className = "muted";
    empty.textContent = "No datasets match your search.";
    list.appendChild(empty);
    return;
  }

  for (const ds of filtered) {
    list.appendChild(renderDatasetCard(ds));
  }
}

async function handleRoute(state) {
  const route = parseRoute();
  if (route.name === "detail") {
    await showDetail(state, route.datasetId);
  } else {
    setView("list");
  }
}

boot().catch((e) => {
  console.error(e);
  openConfig("");
});
