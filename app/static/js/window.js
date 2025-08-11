// window.js — window types + modal helper
import { el, Field, fieldRow } from "./ui.js";
import { createItemList } from "./components.js";
import { md } from "./ui/render.js";

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
          { type: "text", bind: "segments", class: "li-meta" },
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

  "window_segments": (config, winId) => {
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

  "window_segment_view": (config, winId) => {
    const seg = config.segment || {};
    const wrap = el("div", { class: "form segment-view" });
    const metaTop = el("div", { class: "row" }, [
      el("label", {}, ["Source"]),
      el("span", { class: "li-subtle" }, [
        `${seg.source || ""}${seg.page != null ? `, p.${seg.page}` : ""}`
      ])
    ]);
    const metaDates = el("div", { class: "row" }, [
      el("label", {}, ["Dates"]),
      el("span", { class: "li-subtle" }, [
        `${seg.created_at || ""}${seg.updated_at ? ` • ${seg.updated_at}` : ""}`
      ])
    ]);
    const tags = el("div", { class: "row" }, [
      el("label", {}, ["Tags"]),
      el("span", { class: "li-subtle" }, [(seg.tags || []).join(", ")])
    ]);
    const body = el("div", { class: "segment-text" });
    body.innerHTML = md(seg.text || "");
    wrap.append(metaTop, metaDates, tags, body);
    return wrap;
  },

  "window_prompt_editor": (config, winId) => {
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
  },


};

export function createMiniWindowFromConfig(config) {
  const winId = (() => {
    let id = config.id || `mw-${crypto.randomUUID()}`;
    while (document.getElementById(id)) {
      id = `mw-${crypto.randomUUID()}`;
    }
    return id;
  })();
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

  const RESIZABLE = new Set([
    "window_chat_ui",
    "window_documents",
    "window_segments",
    "window_search",
    "window_segment_view",
    "window_prompt_editor",
  ]);
  if (RESIZABLE.has(config.window_type)) {
    const handle = el("div", { class: "win-resizer-y", "aria-label": "Resize window height" });
    win.appendChild(handle);
    const saved = localStorage.getItem(`win:${winId}:h`);
    if (saved) win.style.height = saved;
  }

  return win;
}

export function mountModal(win) {
  const wrap = el("div", { class: "modal-wrap" });
  const backdrop = el("div", { class: "modal-backdrop" });
  wrap.append(backdrop, win);
  document.body.appendChild(wrap);
  return wrap;
}

export function initWindowResize() {
  let resizing = null;
  let startY = 0;
  let startH = 0;

  const onMove = (e) => {
    if (!resizing) return;
    let h = startH + (e.clientY - startY);
    const min = 240;
    const max = window.innerHeight * 0.9;
    h = Math.max(min, Math.min(max, h));
    resizing.style.height = `${h}px`;
  };

  const onUp = () => {
    if (!resizing) return;
    localStorage.setItem(`win:${resizing.id}:h`, resizing.style.height);
    document.removeEventListener("pointermove", onMove);
    resizing = null;
  };

  document.addEventListener("pointerdown", (e) => {
    const handle = e.target.closest(".win-resizer-y");
    if (!handle) return;
    e.preventDefault();
    resizing = handle.closest(".miniwin");
    const rect = resizing.getBoundingClientRect();
    startY = e.clientY;
    startH = rect.height;
    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp, { once: true });
  });
}
