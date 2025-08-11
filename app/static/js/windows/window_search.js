import { el, Field } from "../ui.js";

export function render(config, winId) {
  const wrap = el("div", { class: "form" });
  const q = Field.create({ type: "text_field", id: "search_q", placeholder: "Enter search text..." });
  const k = Field.create({ type: "number_field", id: "search_k", value: 5, min: 1, max: 50 });
  const go = el("button", { class: "btn", type: "button" }, ["Search"]);
  const bar = el("div", { class: "search-bar" }, [q, k, go]);
  const results = el("div", { class: "results", id: "search_results" });
  wrap.append(bar, results);
  wrap.dataset.winId = config.id || winId;
  return wrap;
}
