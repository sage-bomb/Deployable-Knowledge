import { el } from "../ui.js";

export function render(config, winId) {
  const wrap = el("div", { class: "form" });
  const selectRow = el("div", { class: "row" }, [
    el("label", { for: "tmpl_select" }, ["Template"]),
    el("select", { id: "tmpl_select", class: "input" })
  ]);
  const textRow = el("div", { class: "row" }, [
    el("label", { for: "tmpl_text" }, ["JSON"]),
    el("textarea", { id: "tmpl_text", class: "textarea", style: { fontFamily: "monospace", minHeight: "200px" } })
  ]);
  const actions = el("div", { class: "row" }, [
    el("button", { type: "button", class: "btn", id: "tmpl_save" }, ["Save"])
  ]);
  wrap.append(selectRow, textRow, actions);
  return wrap;
}
