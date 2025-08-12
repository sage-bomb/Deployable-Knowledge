import { el } from "../ui.js";
import { createItemList } from "../components.js";

export function render(config, winId) {
  const layout = el("div", { class: "form" });

  const id = config.id || winId;
  const upWrap = el("div", { class: "row" });
  const upInput = el("input", { type: "file", multiple: true, id: `${id}-upload`, style: { display: "none" } });
  const chooseBtn = el("button", { class: "btn", type: "button", id: `${id}-choose-btn` }, ["Choose Files"]);
  const upBtn = el("button", { class: "btn", type: "button", id: `${id}-upload-btn` }, ["Upload"]);
  upWrap.append(el("label", {}, ["Upload Documents"]), chooseBtn, upBtn, upInput);
  const fileList = el("ul", { class: "upload-list", id: `${id}-upload-list` });
  layout.append(upWrap, fileList);

  const listEl = createItemList(id, {
    id: "doc_list",
    item_template: {
      elements: [
        { type: "text", bind: "title", class: "li-title" },
        { type: "text", bind: "segments", class: "li-meta" },
        { type: "button", toggle: { prop: "active", on: "Deactivate", off: "Activate", action: "toggle_active" } },
        { type: "button", label: "Remove", action: "remove", variant: "danger" }
      ]
    }
  });
  layout.appendChild(listEl);
  return layout;
}
