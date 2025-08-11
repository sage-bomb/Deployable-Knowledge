// ui/controllers/sessions.js — sessions list + load history
import * as api from "../api.js";
import { renderChatLog } from "../render.js";
import { getComponent, bus } from "../../components.js";
import { Store } from "../store.js";

export async function initSessionsController(winId="win_sessions") {
  const comp = getComponent(winId, "session_list");
  if (comp) comp.render(await api.listSessions());

  bus.addEventListener("ui:list-select", async (ev) => {
    const { elementId, item } = ev.detail || {};
    if (elementId !== "session_list" || !item?.session_id) return;
    Store.sessionId = item.session_id;
    const data = await api.getSession(Store.sessionId);
    const log = document.querySelector("#win_chat #chat_log");
    if (log) renderChatLog(data.history || [], log);
  });
}
