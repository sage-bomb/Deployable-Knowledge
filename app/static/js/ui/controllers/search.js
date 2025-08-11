// ui/controllers/search.js — semantic search (conflict-resolved)
import * as api from "../api.js";
import { escapeHtml } from "../render.js";

export function initSearchController(winId = "win_search") {
  const win = document.getElementById(winId);
  if (!win) return;

  const q = win.querySelector("#search_q");
  const k = win.querySelector("#search_k");
  const go = win.querySelector(".search-bar .btn");
  const results = win.querySelector("#search_results");

  async function run() {
    const query = q.value.trim();
    const topK = Number(k.value || 5);
    if (!query) {
      results.innerHTML = "";
      return;
    }

    results.innerHTML = `<div class="li-subtle">Searching…</div>`;

    try {
      const data = await api.searchDocuments(query, topK);
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

  go.addEventListener("click", run);
  q.addEventListener("keydown", (e) => {
    if (e.key === "Enter") run();
  });
}
