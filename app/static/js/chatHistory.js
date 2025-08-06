// Codex: Do NOT load backend or Python files. This file is frontend-only.
// chatHistory.js

import { $ } from './dom.js';
import { setSessionId } from './session.js';
import { renderMessagePair, clearChatUI } from './render.js';

/**
 * Loads and displays messages for a specific session.
 * @param {string} sessionId 
 */
async function loadSessionMessages(sessionId) {
  try {
    const res = await fetch(`/sessions/${encodeURIComponent(sessionId)}`);
    if (!res.ok) throw new Error("Failed to fetch session");

    const data = await res.json();
    const history = data.history;

    clearChatUI();

    for (const [user, assistant] of history) {
      renderMessagePair(user, assistant);
    }
  } catch (err) {
    console.error("❌ Error loading session messages:", err);
    clearChatUI();
    renderMessagePair("System", `⚠️ Failed to load session history: ${err.message}`);
  }
}

function formatTimestamp(isoString) {
  const date = new Date(isoString);
  return date.toLocaleString();
}

/**
 * Renders chat history list and binds session click events.
 * @param {Object} session - Session state object
 */
export const chatHistory = {
  init(session) {
    const container = $("chat-history-list");
    if (!container) return;

    container.innerHTML = `<div class="loading">Loading sessions...</div>`;

    fetch("/sessions")
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch sessions");
        return res.json();
      })
      .then(sessions => {
        container.innerHTML = "";

        sessions.forEach(sessionEntry => {
          const div = document.createElement("div");
          div.className = "session-item";
          div.innerHTML = `
            <div class="session-title"><strong>Session ID:</strong> ${sessionEntry.session_id}</div>
            <div class="session-timestamp">${formatTimestamp(sessionEntry.created_at)}</div>
          `;
          div.addEventListener("click", () => {
            console.log("📦 Loading session:", sessionEntry.session_id);
            setSessionId(sessionEntry.session_id);
            session.sessionId = sessionEntry.session_id;
            loadSessionMessages(sessionEntry.session_id);
          });
          container.appendChild(div);
        });
      })
      .catch(err => {
        console.error("[chatHistory] Error loading sessions:", err);
        container.innerHTML = `<div class="error">Failed to load sessions.</div>`;
      });
  }
};
