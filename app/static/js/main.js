// main.js — tiny glue after refactor
import { initWindowDnD } from "./dnd.js";
import { initSplitter } from "./splitter.js";
import { createMiniWindowFromConfig } from "./window.js";
import { windows } from "./ui/windows.js";
import { initMenu } from "./menu.js";

// controllers
import { initDocsController }     from "./ui/controllers/docs.js";
import { initSessionsController } from "./ui/controllers/sessions.js";
import { initChatController }     from "./ui/controllers/chat.js";
import { initSearchController }   from "./ui/controllers/search.js";
import { openPersonaModal }       from "./ui/controllers/persona.js";

import * as api from "./ui/api.js";
import { Store } from "./ui/store.js";

initSplitter();
initWindowDnD();

// mount initial windows
for (const w of windows) {
  const node = createMiniWindowFromConfig(w);
  document.getElementById(w.col === "left" ? "col-left" : "col-right").appendChild(node);
}

// init controllers
initDocsController("win_docs");
initSessionsController("win_sessions");
initChatController();
initSearchController("win_search");

// ensure we have a session at boot
api.getOrCreateChatSession().then(id => Store.sessionId = id);

// header menu
initMenu(async (action) => {
  if (action === "new-chat") {
    Store.sessionId = await api.startNewSession();
    // refresh sessions list
    initSessionsController("win_sessions");
  }
  if (action === "edit-persona") {
    openPersonaModal();
  }
});
