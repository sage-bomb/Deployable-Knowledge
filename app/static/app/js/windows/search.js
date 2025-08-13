import { spawnWindow } from "../framework.js";
import { searchSegments } from "../sdk.js";
import { getComponent } from "/static/ui/js/components.js";
import { Store } from "../store.js";

export function createSearchWindow() {
  spawnWindow({
    id: "win_search",
    window_type: "window_generic",
    title: "Semantic Search",
    col: "right",
    unique: true,
    resizable: true,
    Elements: [
      { type: "text_field", id: "search_q", placeholder: "Search text…" },
      { type: "number_field", id: "search_k", label: "Top K", value: 10, min: 1, max: 100 },
      {
        type: "item_list",
        id: "search_results",
        label: "Results",
        item_template: {
          elements: [
            { type: "text", bind: "source", class: "li-title" },
            { type: "text", bind: "preview", class: "li-subtle" },
            { type: "button", label: "Open", action: "open" }
          ]
        }
      }
    ]
  });
  const win = document.getElementById("win_search");
  const qInput = win?.querySelector("#search_q");
  const kInput = win?.querySelector("#search_k") || { value: 10 };
  if (qInput) {
    const qRow = qInput.closest(".row");
    const bar = document.createElement("div");
    bar.className = "actions";
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn";
    btn.id = "search_btn";
    btn.textContent = "Search";
    bar.appendChild(btn);
    qRow?.after(bar);
    async function runSearch() {
      const q = qInput.value.trim();
      const k = parseInt(kInput.value || "10", 10);
      if (!q) return;
      const inactive = Store?.inactiveList?.() || [];
      const res = await searchSegments({ q, top_k: k, inactive });
      const results = Array.isArray(res?.results) ? res.results : (Array.isArray(res) ? res : []);
      const comp = getComponent("win_search", "search_results");
      comp?.render(results);
    }
    btn.addEventListener("click", runSearch);
    qInput.addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(); });
  }
}
