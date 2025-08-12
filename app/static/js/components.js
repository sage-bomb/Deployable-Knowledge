// components.js — registry for interactive components (lists, etc.) + event bus
import { el, Field } from "./ui.js";

const registry = new Map(); // key: `${winId}:${elementId}` -> api

export function registerComponent(winId, elementId, api) {
  registry.set(`${winId}:${elementId}`, api);
}

export function getComponent(winId, elementId) {
  return registry.get(`${winId}:${elementId}`);
}

export const bus = new EventTarget();

export function createItemList(winId, cfg) {
  const container = el("div", { class: "list", id: cfg.id });

  function makeButton(p, item) {
    let label = p.label ?? "Action";
    if (p.toggle) {
      const isOn = !!item[p.toggle.prop];
      label = isOn ? (p.toggle.on || "On") : (p.toggle.off || "Off");
    }
    const btn = el("button", { class: p.variant === "danger" ? "btn btn-danger" : "btn" }, [label]);
    btn.addEventListener("click", (ev) => {
      ev.stopPropagation();
      bus.dispatchEvent(new CustomEvent("ui:list-action", {
        detail: { winId, elementId: cfg.id, action: p.action || p.toggle?.action, item }
      }));
    });
    return btn;
  }

  function renderItem(item, idx) {
    const row = el("div", { class: "list-item", "data-index": String(idx) });
    const parts = (cfg.item_template?.elements || []);

    const left = el("div", {});
    const right = el("div", { class: "li-actions" });
    row.append(left, right);

    parts.forEach((p) => {
      if (p.type === "text") {
        const content = p.bind ? item[p.bind] : p.text ?? "";
        const span = Field.create({ type: "text", text: content, className: p.class });
        (p.align === "right" ? right : left).appendChild(span);
      } else if (p.type === "button") {
        right.appendChild(makeButton(p, item));
      }
    });

    row.addEventListener("click", () => {
      container.querySelectorAll(".list-item.selected").forEach(el => el.classList.remove("selected"));
      row.classList.add("selected");
      bus.dispatchEvent(new CustomEvent("ui:list-select", {
        detail: { winId, elementId: cfg.id, item, index: idx }
      }));
    });

    return row;
  }

  function render(items = []) {
    container.innerHTML = "";
    items.forEach((it, i) => container.appendChild(renderItem(it, i)));
  }

  registerComponent(winId, cfg.id, { render });
  return container;
}
