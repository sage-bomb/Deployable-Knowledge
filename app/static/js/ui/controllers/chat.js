// ui/controllers/chat.js — chat send + stream
import * as api from "../api.js";
import { Store } from "../store.js";
import { md, escapeHtml } from "../render.js";

export function initChatController() {
  const chatWin = document.getElementById("win_chat");
  if (!chatWin) return;
  const controller = new AbortController();
  chatWin.addEventListener("DOMNodeRemoved", (e) => {
    if (e.target === chatWin) controller.abort();
  }, { once: true });
  const log = chatWin.querySelector("#chat_log");
  const input = chatWin.querySelector("#chat_input");
  const sendBtn = chatWin.querySelector(".chat-input .btn");

  const pushUser = (text) => {
    const div = document.createElement("div");
    div.className = "msg you";
    div.innerHTML = "You: " + escapeHtml(text);
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  };
  const pushAssistantBubble = () => {
    const div = document.createElement("div");
    div.className = "msg assistant";
    div.innerHTML = "…";
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
    return div;
  };

  const send = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    pushUser(text);
    const bubble = pushAssistantBubble();

    try {
      const { reader, decoder } = await api.chatStream({
        message: text,
        session_id: Store.sessionId,
        inactive: Store.inactiveList(),
        persona: Store.persona
      });
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        bubble.innerHTML = md(buf);
        log.scrollTop = log.scrollHeight;
      }
    } catch (e) {
      try {
        const res = await api.chat({
          message: text,
          session_id: Store.sessionId,
          inactive: Store.inactiveList(),
          persona: Store.persona
        });
        bubble.innerHTML = md(res.response ?? "(no response)");
      } catch (e2) {
        bubble.innerHTML = `<em>Error:</em> ${e2.message}`;
      }
    }
  };

  sendBtn.addEventListener("click", send, { signal: controller.signal });
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); }, { signal: controller.signal });
}
