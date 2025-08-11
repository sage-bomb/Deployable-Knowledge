// ui/render.js — shared rendering helpers
export function escapeHtml(s="") {
  return s.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
}
export function md(str="") {
  return (window.marked?.parse) ? window.marked.parse(str) : escapeHtml(str).replaceAll("\n","<br>");
}
export function renderChatLog(history, logEl) {
  logEl.innerHTML = "";
  for (const [user, assistant] of (history || [])) {
    if (user) {
      const div = document.createElement("div");
      div.className = "msg you";
      div.innerHTML = "You: " + escapeHtml(user);
      logEl.appendChild(div);
    }
    if (assistant) {
      const div = document.createElement("div");
      div.className = "msg assistant";
      div.innerHTML = md(assistant);
      logEl.appendChild(div);
    }
  }
  logEl.scrollTop = logEl.scrollHeight;
}
