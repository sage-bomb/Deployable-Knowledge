// window.js — registry + modal/resize helpers
import { el } from "./ui.js";
import { render as renderGeneric } from "./windows/window_generic.js";
import { render as renderDocuments } from "./windows/window_documents.js";
import { render as renderSessions } from "./windows/window_sessions.js";
import { render as renderChatUI } from "./windows/window_chat_ui.js";
import { render as renderSearch } from "./windows/window_search.js";
import { render as renderSegments } from "./windows/window_segments.js";
import { render as renderPersona } from "./windows/window_persona.js";
import { render as renderSegmentView } from "./windows/window_segment_view.js";
import { render as renderPromptEditor } from "./windows/window_prompt_editor.js";

const WindowTypes = {
  window_generic: renderGeneric,
  window_documents: renderDocuments,
  window_sessions: renderSessions,
  window_chat_ui: renderChatUI,
  window_search: renderSearch,
  window_segments: renderSegments,
  window_persona: renderPersona,
  window_segment_view: renderSegmentView,
  window_prompt_editor: renderPromptEditor,
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
