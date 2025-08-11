// ui/controllers/search.js — semantic search
import * as api from "../api.js";
import { qs } from "../../dom.js";

export function initSearchController(winId="win_search") {
  const win = qs(`#${winId}`);
  if (!win) return;
  const q = qs(`#${winId} #search_q`);
  const k = qs(`#${winId} #search_k`);
  const go = qs(`#${winId} .search-bar .btn`);
  const results = qs(`#${winId} #search_results`);

  go.addEventListener("click", async () => {
    const data = await api.searchDocuments(q.value, Number(k.value || 5));
    results.innerHTML = "";
    (data.results || []).forEach(r => {
      const card = document.createElement("div");
      card.className = "result-card";
      card.innerHTML = `<div>${r.text}</div>
        <div class="result-meta"><span>Source: ${r.source}</span>
        <span>Score: ${Number(r.score).toFixed(3)} • Page: ${r.page ?? "?"}</span></div>`;
      results.appendChild(card);
    });
  });
}
