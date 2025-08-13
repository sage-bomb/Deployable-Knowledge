// main.js — tiny glue after refactor
import { initWindowDnD } from "./dnd.js";
import { initSplitter } from "./splitter.js";
import { createMiniWindowFromConfig, initWindowResize } from "./window.js";
import { windows } from "./ui/windows.js";
import { initMenu } from "./menu.js";

// controllers
import { initDocsController }     from "./ui/controllers/docs.js";
import { initSessionsController } from "./ui/controllers/sessions.js";
import { initChatController }     from "./ui/controllers/chat.js";
import { initSearchController, runSearch }   from "./ui/controllers/search.js";
import { initSegmentsController } from "./ui/controllers/segments.js";
import { openPersonaModal }       from "./ui/controllers/persona.js";
import { openSettingsModal }      from "./ui/controllers/settings.js";
import { openPromptEditor }       from "./ui/controllers/prompt_editor.js";

import { dkClient as api } from "./ui/sdk/sdk.js";
import { Store } from "./ui/store.js";

initSplitter();
initWindowDnD();
initWindowResize();

function spawnWindow(cfg, init) {
  const existing = cfg.id && document.getElementById(cfg.id);
  if (cfg.unique && existing) {
    existing.scrollIntoView({ behavior: "smooth", block: "start" });
    return existing;
  }
  const node = createMiniWindowFromConfig(cfg);
  const colEl = document.getElementById(cfg.col === "left" ? "col-left" : "col-right");
  colEl.appendChild(node);
  const bottom = colEl.scrollTop + colEl.clientHeight;
  if (node.offsetTop > bottom) {
    let indicator = colEl.querySelector(".down-indicator");
    if (!indicator) {
      indicator = document.createElement("div");
      indicator.className = "down-indicator";
      indicator.textContent = "⌄";
      colEl.appendChild(indicator);
if (!indicator) {
  indicator = document.createElement("div");
  indicator.className = "down-indicator";
  indicator.textContent = "⌄";
  colEl.appendChild(indicator);
} else {
  indicator.className = "down-indicator";  // Ensure consistent class handling
}
    }

    const onScroll = () => {
      if (colEl.scrollTop + colEl.clientHeight >= node.offsetTop) {
        indicator.classList.add("hide");
        setTimeout(() => indicator.remove(), 300);
        colEl.removeEventListener("scroll", onScroll);
      }
    };
    colEl.addEventListener("scroll", onScroll);

  }
  if (init) init(cfg.id);
  return node;
}

// mount initial windows
for (const w of windows) {
  spawnWindow(w);
}

// init controllers
initDocsController("win_docs");
initSessionsController("win_sessions");
initChatController();
initSegmentsController("win_segments");

// ensure we have a session at boot
api.getOrCreateChatSession().then(id => Store.sessionId = id);
api.getUser().then(u => {
  const btn = document.getElementById("user-menu-trigger");
  if (btn && u?.user) btn.textContent = `${u.user} ▾`;
});

// header menu
initMenu(async (action) => {
  if (action === "new-chat") {
    Store.sessionId = await api.startNewSession();
    // refresh sessions list
    initSessionsController("win_sessions");
  }
  if (action === "toggle-search") {
    const existing = document.getElementById("win_search");
    if (existing) {
      existing.remove();
    } else {
      const cfg = { id: "win_search", window_type: "window_search", title: "Search Documents", col: "right", unique: true };
      spawnWindow(cfg, initSearchController);
      if (Store.lastQuery) runSearch(Store.lastQuery);
    }
  }
  if (action === "edit-persona") {
    openPersonaModal();
  }
  if (action === "settings") {
    openSettingsModal();
  }
  if (action === "prompt-templates") {
    openPromptEditor();
  }
});

// user menu
initMenu((action) => {
  if (action === "logout") window.location.href = "/logout";
}, "user-menu-trigger", "user-menu-dropdown");

// tools menu
initMenu((action) => {
  if (action === "tool-chat") {
    spawnWindow({ id: "win_chat", window_type: "window_chat_ui", title: "Assistant Chat", col: "right", unique: true }, initChatController);
  }
  if (action === "tool-docs") {
    spawnWindow({ id: "win_docs", window_type: "window_documents", title: "Document Library", col: "left", unique: true }, initDocsController);
  }
  if (action === "tool-sessions") {
    spawnWindow({ id: "win_sessions", window_type: "window_sessions", title: "Chat History", col: "left", unique: true }, initSessionsController);
  }
  if (action === "tool-segments") {
    spawnWindow({ id: "win_segments", window_type: "window_segments", title: "DB Segments", col: "right", unique: true }, initSegmentsController);
  }
}, "tools-menu-trigger", "tools-menu-dropdown");
