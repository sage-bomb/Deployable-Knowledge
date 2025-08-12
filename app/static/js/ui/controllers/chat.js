// ui/controllers/chat.js — chat send + stream
import { dkClient as api } from "../sdk/sdk.js";
import { Store } from "../store.js";
import { md, escapeHtml } from "../render.js";
import { qs } from "../../dom.js";
import { showContext } from "./search.js";

export function initChatController() {
  const chatWin = qs("#win_chat");
  if (!chatWin) return;
  const log = qs("#win_chat #chat_log");
  const input = qs("#win_chat #chat_input");
  const sendBtn = qs("#win_chat .chat-input .btn");

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

  let aborter = null;
  const send = async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    Store.lastQuery = text;
    pushUser(text);
    const bubble = pushAssistantBubble();

    aborter?.abort();
    aborter = new AbortController();
    let buf = "";
    try {
      await api.streamChat(
        {
          message: text,
          session_id: Store.sessionId,
          inactive: Store.inactiveList(),
          persona: Store.persona,
        },
        {
          signal: aborter.signal,
          onDelta(delta) {
            buf += delta;
            bubble.innerHTML = md(buf);
            log.scrollTop = log.scrollHeight;
          },
          onDone(data) {
            if (data?.sources) showContext(data.sources, text);
          },
        }
      );
    } catch (e) {
      if (e.name === "AbortError") return;
      try {
        const res = await api.chat({
          message: text,
          session_id: Store.sessionId,
          inactive: Store.inactiveList(),
          persona: Store.persona,
        });
        bubble.innerHTML = md(res.response ?? "(no response)");
        if (res.context) showContext(res.context, text);
      } catch (e2) {
        bubble.innerHTML = `<em>Error:</em> ${escapeHtml(e2.message)}`;
      }
    }
  };

  sendBtn.addEventListener("click", send);
  input.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });
}
