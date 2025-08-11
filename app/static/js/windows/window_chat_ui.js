import { el, Field } from "../ui.js";

export function render(config, winId) {
  const wrap = el("div", { class: "chat-window" });
  const log = el("div", { class: "chat-log", id: "chat_log" });
  const input = Field.create({ type: "text_field", id: "chat_input", placeholder: "Type a message..." });
  const send = el("button", { class: "btn", type: "button" }, ["Send"]);
  const bar = el("div", { class: "chat-input" }, [input, send]);
  wrap.append(log, bar);
  wrap.dataset.winId = config.id || winId;
  return wrap;
}
