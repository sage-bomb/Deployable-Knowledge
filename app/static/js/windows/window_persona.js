import { el, Field } from "../ui.js";

export function render(config, winId) {
  const wrap = el("div", { class: "form" });

  const textarea = Field.create({
    type: "text_area",
    id: "persona_text",
    value: config.value || "",
    rows: 10
  });
  const row = el("div", { class: "row" }, [
    el("label", { for: "persona_text" }, ["Persona"]),
    textarea
  ]);

  const actions = el("div", { class: "row" }, [
    el("button", { type: "button", class: "btn js-persona-save" }, ["Save"])
  ]);

  wrap.append(row, actions);
  return wrap;
}
