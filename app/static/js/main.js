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

// mount initial windows
for (const w of windows) {
  const node = createMiniWindowFromConfig(w);
  document.getElementById(w.col === "left" ? "col-left" : "col-right").appendChild(node);
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
      const cfg = { id: "win_search", window_type: "window_search", title: "Search Documents", col: "right" };
      const node = createMiniWindowFromConfig(cfg);
      document.getElementById("col-right").appendChild(node);
      initSearchController("win_search");
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
