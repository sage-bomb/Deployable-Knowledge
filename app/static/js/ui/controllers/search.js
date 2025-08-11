// ui/controllers/search.js — semantic search
import * as api from "../api.js";
import { escapeHtml } from "../render.js";

export function initSearchController(winId="win_search") {
  const win = document.getElementById(winId);
  if (!win) return;
  const q = win.querySelector("#search_q");
  const k = win.querySelector("#search_k");
  const go = win.querySelector(".search-bar .btn");
  const results = win.querySelector("#search_results");

  go.addEventListener("click", async () => {
    const data = await api.searchDocuments(q.value, Number(k.value || 5));
    results.innerHTML = "";
    (data.results || []).forEach(r => {
      const card = document.createElement("div");
      card.className = "result-card";
      const text = escapeHtml(r.text ?? "");
      const source = escapeHtml(r.source ?? "");
      const page = escapeHtml(String(r.page ?? "?"));
      card.innerHTML = `<div>${text}</div>
        <div class="result-meta"><span>Source: ${source}</span>
        <span>Score: ${Number(r.score).toFixed(3)} • Page: ${page}</span></div>`;
      results.appendChild(card);
    });
  });
}
