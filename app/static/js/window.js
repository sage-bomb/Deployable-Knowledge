// window.js — window types + modal helper
import { el, Field, fieldRow } from "./ui.js";
import { createItemList } from "./components.js";

const WindowTypes = {
  "window_generic": (config, winId) => {
    const form = el("form", { class: "form", autocomplete: "off" });
    (config.Elements || []).forEach((e, idx) => {
      const baseId = e.id || (e.name ? e.name.toLowerCase().replace(/\s+/g, "_") : `field_${idx+1}`);
      const id = `${baseId}`;
      const label = e.label || e.name || baseId;

      if (e.type === "item_list") {
        const listEl = createItemList(config.id || winId, { ...e, id });
        const row = el("div", { class: "row" }, [
          el("label", {}, [label]),
          listEl
        ]);
        form.appendChild(row);
        return;
      }

      const input = Field.create({ ...e, id });
      form.appendChild(fieldRow(id, label, input));
    });
    return form;
  },

  "window_documents": (config, winId) => {
    const layout = el("div", { class: "form" });

    // Upload bar
    const id = config.id || winId;
    const upWrap = el("div", { class: "row" });
    const upInput = el("input", { type: "file", multiple: true, id: `${id}-upload`, style: { maxWidth: "100%" } });
    const upBtn = el("button", { class: "btn", type: "button", id: `${id}-upload-btn` }, ["Upload"]);
    upWrap.append(el("label", {}, ["Upload Documents"]), upInput, upBtn);
    layout.appendChild(upWrap);

    // Documents list
    const listEl = createItemList(id, {
      id: "doc_list",
      item_template: {
        elements: [
          { type: "text", bind: "title", class: "li-title" },
          { type: "text", bind: "segments", class: "li-subtle", align: "right" },
          { type: "button", toggle: { prop: "active", on: "Deactivate", off: "Activate", action: "toggle_active" } },
          { type: "button", label: "Remove", action: "remove", variant: "danger" }
        ]
      }
    });
    layout.appendChild(listEl);
    return layout;
  },

  "window_sessions": (config, winId) => {
    const layout = el("div", { class: "form" });
    const listEl = createItemList(config.id || winId, {
      id: "session_list",
      item_template: {
        elements: [
          { type: "text", bind: "title", class: "li-title" },
          { type: "text", bind: "created_at", class: "li-right" }
        ]
      }
    });
    layout.appendChild(listEl);
    return layout;
  },

  "window_chat_ui": (config, winId) => {
    const wrap = el("div", { class: "form" });
    const log = el("div", { class: "chat-log", id: "chat_log" });
    const input = Field.create({ type: "text_field", id: "chat_input", placeholder: "Type a message..." });
    const send = el("button", { class: "btn", type: "button" }, ["Send"]);
    const bar = el("div", { class: "chat-input" }, [input, send]);
    wrap.append(log, bar);
    wrap.dataset.winId = config.id || winId;
    return wrap;
  },

  "window_search": (config, winId) => {
    const wrap = el("div", { class: "form" });
    const q = Field.create({ type: "text_field", id: "search_q", placeholder: "Enter search text..." });
    const k = Field.create({ type: "number_field", id: "search_k", value: 5, min: 1, max: 50 });
    const go = el("button", { class: "btn", type: "button" }, ["Search"]);
    const bar = el("div", { class: "search-bar" }, [q, k, go]);
    const results = el("div", { class: "results", id: "search_results" });
    wrap.append(bar, results);
    wrap.dataset.winId = config.id || winId;
    return wrap;
  },

  "window_persona": (config, winId) => {
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

  // simple action row; Save handled by app layer
  const actions = el("div", { class: "row" }, [
    el("button", { type: "button", class: "btn js-persona-save" }, ["Save"])
  ]);

  wrap.append(row, actions);
  return wrap;
},


};

export function createMiniWindowFromConfig(config) {
  const winId = config.id || `mw-${crypto.randomUUID()}`;
  const win = el("div", { class: "miniwin", tabindex: "0", "data-id": winId, id: winId });

  const titlebar = el("div", { class: "titlebar" }, [
    el("div", { class: "title" }, [config.title || "Untitled"]),
    el("div", { class: "actions" }, [
      el("button", { class: "icon-btn js-min", title: "Minimize", "aria-label": "Minimize", "data-win": winId }, ["—"]),
      el("button", { class: "icon-btn js-close", title: "Close", "aria-label": "Close", "data-win": winId }, ["✕"])
    ])
  ]);

  const contentInner = el("div", { class: "content-inner" });
  const content = el("div", { class: "content" }, [contentInner]);

  const renderer = WindowTypes[config.window_type || "window_generic"];
  if (!renderer) throw new Error(`Unknown window_type: ${config.window_type}`);
  const body = renderer(config, winId);
  contentInner.appendChild(body);

  if (config.modal) {
    win.classList.add("modal");
    win.setAttribute("data-modal", "true");
  }

  win.append(titlebar, content);
  return win;
}

export function mountModal(win) {
  const wrap = el("div", { class: "modal-wrap" });
  const backdrop = el("div", { class: "modal-backdrop" });
  wrap.append(backdrop, win);
  document.body.appendChild(wrap);
  return wrap;
}
