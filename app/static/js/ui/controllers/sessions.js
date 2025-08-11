// ui/controllers/sessions.js — sessions list + load history
import * as api from "../api.js";
import { renderChatLog } from "../render.js";
import { getComponent, bus } from "../../components.js";
import { Store } from "../store.js";

// highlight selected row
let selectedIdx = null;

export async function initSessionsController(winId="win_sessions") {
  const controller = new AbortController();
  const win = document.getElementById(winId);
  win?.addEventListener("DOMNodeRemoved", (e) => {
    if (e.target === win) controller.abort();
  }, { once: true });

  const comp = getComponent(winId, "session_list");
  if (comp) comp.render(await api.listSessions());

  bus.addEventListener("ui:list-select", async (ev) => {
    const { winId: srcWin, elementId, item, index } = ev.detail || {};
    if (srcWin !== winId || elementId !== "session_list") return;

    // toggle selected
    const list = document.querySelector(`#${winId} #session_list`);
    if (list) {
      list.querySelectorAll(".list-item.selected").forEach(el => el.classList.remove("selected"));
      const row = list.querySelector(`.list-item[data-index="${index}"]`);
      row?.classList.add("selected");
      selectedIdx = index;
    }

    // load history
    Store.sessionId = item.session_id;
    const data = await api.getSession(Store.sessionId);
    const log = document.querySelector("#win_chat #chat_log");
    if (log) renderChatLog(data.history || [], log);
  }, { signal: controller.signal });
}
