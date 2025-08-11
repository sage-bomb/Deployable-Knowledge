import { el } from "../ui.js";
import { createItemList } from "../components.js";

export function render(config, winId) {
  const layout = el("div", { class: "form" });
  const listEl = createItemList(config.id || winId, {
    id: "segment_list",
    item_template: {
      elements: [
        { type: "text", bind: "source", class: "li-title" },
        { type: "text", bind: "priority", class: "li-meta" },
        { type: "text", bind: "preview", class: "li-subtle" },
        { type: "button", label: "Open", action: "open" },
        { type: "button", label: "Remove", action: "remove", variant: "danger" }
      ]
    }
  });
  layout.appendChild(listEl);
  return layout;
}
