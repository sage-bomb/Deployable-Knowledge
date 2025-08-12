// ui/controllers/search.js — semantic search
import { dkClient as api } from "../sdk/sdk.js";
import { escapeHtml } from "../render.js";

export async function runSearch(query, winId = "win_search") {
  const win = document.getElementById(winId);
  if (!win) return;
  const q = win.querySelector("#search_q");
  const k = win.querySelector("#search_k");
  const results = win.querySelector("#search_results");
  if (query !== undefined) q.value = query;
  const qtext = q.value.trim();
  const topK = Number(k.value || 5);
  if (!qtext) {
    results.innerHTML = "";
    return;
  }

  results.innerHTML = `<div class="li-subtle">Searching…</div>`;

  try {
    const data = await api.search(qtext, topK);
    const arr = (data && data.results) || [];

    results.innerHTML = "";
    if (!arr.length) {
      results.innerHTML = `<div class="li-subtle">No results</div>`;
      return;
    }

    for (const r of arr) {
      const card = document.createElement("div");
      card.className = "result-card";

      const text = escapeHtml(r?.text ?? "");
      const source = escapeHtml(r?.source ?? "");
      const score =
        typeof r?.score === "number"
          ? r.score.toFixed(3)
          : escapeHtml(String(r?.score ?? ""));
      const page = r?.page ?? "?";

      card.innerHTML = `
          <div>${text}</div>
          <div class="result-meta">
            <span>Source: ${source}</span>
            <span>Score: ${score} • Page: ${page}</span>
          </div>`;
      results.appendChild(card);
    }
  } catch (e) {
    results.innerHTML = `<div class="li-subtle">Error: ${escapeHtml(
      e?.message || String(e)
    )}</div>`;
  }
}

export function showContext(sources = [], query, winId = "win_search") {
  const win = document.getElementById(winId);
  if (!win) return;
  const q = win.querySelector("#search_q");
  const results = win.querySelector("#search_results");
  if (query !== undefined && q) q.value = query;
  results.innerHTML = "";
  if (!sources || !sources.length) {
    results.innerHTML = `<div class="li-subtle">No context</div>`;
    return;
  }
  for (const r of sources) {
    const card = document.createElement("div");
    card.className = "result-card";
    const text = escapeHtml(r?.text ?? "");
    const source = escapeHtml(r?.source ?? "");
    const score =
      typeof r?.score === "number"
        ? r.score.toFixed(3)
        : escapeHtml(String(r?.score ?? ""));
    const page = r?.page ?? "?";
    card.innerHTML = `
        <div>${text}</div>
        <div class="result-meta">
          <span>Source: ${source}</span>
          <span>Score: ${score} • Page: ${page}</span>
        </div>`;
    results.appendChild(card);
  }
}

export function initSearchController(winId = "win_search") {
  const win = document.getElementById(winId);
  if (!win) return;
  const q = win.querySelector("#search_q");
  const go = win.querySelector(".search-bar .btn");
  go.addEventListener("click", () => runSearch(undefined, winId));
  q.addEventListener("keydown", (e) => {
    if (e.key === "Enter") runSearch(undefined, winId);
  });
}
