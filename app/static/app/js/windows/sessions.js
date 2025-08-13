import { spawnWindow } from "../framework.js";
import { getComponent } from "/static/ui/js/components.js";
import { Store } from "../store.js";
import { md } from "../util.js";

export async function refreshSessions() {
  const res = await fetch("/sessions", { credentials: "same-origin" });
  const data = await res.json();
  const comp = getComponent("win_sessions", "session_list");
  comp?.render(data);
}

export async function openSessionsWindow() {
  if (!document.getElementById("win_sessions")) {
    spawnWindow({
      id: "win_sessions",
      window_type: "window_generic",
      title: "Chat History",
      col: "left",
      unique: true,
      resizable: true,
      Elements: [
        {
          type: "item_list",
          id: "session_list",
          label: "Sessions",
          item_template: {
            elements: [
              { type: "text", bind: "title", class: "li-title" },
              { type: "text", bind: "created_at", class: "li-meta" },
              { type: "button", label: "Open", action: "open" }
            ]
          }
        }
      ]
    });
  }
  await refreshSessions();
}

export async function loadChatHistory(chatUI, id) {
  if (!id) return;
  try {
    const res = await fetch(`/sessions/${encodeURIComponent(id)}`, { credentials: "same-origin" });
    if (!res.ok) return;
    const data = await res.json();
    chatUI.log.innerHTML = "";
    for (const [user, assistant] of data.history || []) {
      chatUI.pushUser(user);
      const b = chatUI.pushAssistant();
      b.innerHTML = md(assistant || "");
    }
  } catch {}
}
