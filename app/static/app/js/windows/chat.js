import { spawnWindow } from "../framework.js";
import { chat, chatStream } from "../sdk.js";
import { Store } from "../store.js";
import { md, htmlEscape } from "../util.js";

export function createChatWindow() {
  spawnWindow({
    id: "win_chat",
    window_type: "window_generic",
    title: "Assistant Chat",
    col: "right",
    unique: true,
    resizable: true,
    Elements: [
      { type: "text_area", id: "chat_log", rows: 14, value: "" },
      { type: "text_field", id: "chat_input", placeholder: "Type a message…" }
    ]
  });
  const win = document.getElementById("win_chat");
  const taRow = win?.querySelector("#chat_log")?.closest(".row");
  if (!win || !taRow) return {};
  const log = document.createElement("div");
  log.id = "chat_log";
  log.className = "chat-log";
  taRow.replaceWith(log);
  const input = win.querySelector("#chat_input");
  const inputRow = input?.closest(".row");
  const bar = document.createElement("div");
  bar.className = "chat-input";
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn";
  btn.textContent = "Send";
  inputRow?.replaceWith(bar);
  bar.append(input, btn);
  const pushUser = (text) => {
    const d = document.createElement("div");
    d.className = "msg you";
    d.innerHTML = "You: " + htmlEscape(text);
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
  };
  const pushAssistant = () => {
    const d = document.createElement("div");
    d.className = "msg assistant";
    d.innerHTML = "…";
    log.appendChild(d);
    log.scrollTop = log.scrollHeight;
    return d;
  };
  async function send() {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    pushUser(text);
    const bubble = pushAssistant();
    try {
      const { reader, decoder } = await chatStream({
        message: text,
        session_id: (Store.sessionId || "") + "",
        persona: Store.persona || "",
        inactive: Store.inactiveList?.() || [],
      });
      let buf = "";
      let acc = "";
      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const chunks = buf.split("\n\n");
        buf = chunks.pop();
        for (const chunk of chunks) {
          let event = "delta", data = "";
          for (const line of chunk.split("\n")) {
            if (line.startsWith("event:")) event = line.slice(6).trim();
            else if (line.startsWith("data:")) data += line.slice(5).trim();
          }
          if (event === "delta") {
            let parsed;
            try { parsed = JSON.parse(data); } catch {}
            if (parsed !== undefined) {
              if (typeof parsed === "object" && parsed) {
                data = parsed.delta ?? parsed.response ?? Object.values(parsed)[0] ?? "";
              } else {
                data = parsed + "";
              }
            }
            if (data === "." || data === "[DONE]") continue;
            acc += data;
            bubble.innerHTML = md(acc);
          }
        }
        log.scrollTop = log.scrollHeight;
      }
    } catch {
      try {
        const res = await chat({
          message: text,
          session_id: (Store.sessionId || "") + "",
          persona: Store.persona || "",
          inactive: Store.inactiveList?.() || [],
        });
        bubble.innerHTML = md(res.response ?? "(no response)");
      } catch (e2) {
        bubble.innerHTML = `<em>Error:</em> ${htmlEscape(e2.message)}`;
      }
    }
  }
  btn.addEventListener("click", send);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });
  return { log, pushUser, pushAssistant };
}
