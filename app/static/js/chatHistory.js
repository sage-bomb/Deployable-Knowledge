// Codex: Do NOT load backend or Python files. This file is frontend-only.
// chatHistory.js

import { $, initPanelToggle } from './dom.js';
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

/**
 * Renders chat history list and binds session click events.
 * @param {Object} session - Session state object
 */
export const chatHistory = {
  init(session) {
    const container = $("chat-history-list");
    if (!container) return;

    initPanelToggle('chat-history-wrapper', 'toggle-history-btn');

    container.innerHTML = `<div class="loading">Loading sessions...</div>`;

    fetch("/sessions")
      .then(res => {
        if (!res.ok) throw new Error("Failed to fetch sessions");
        return res.json();
      })
      .then(sessions => {
        renderChatHistoryList(container, sessions, (sessionId) => {
          console.log("📦 Loading session:", sessionId);
          setSessionId(sessionId);
          session.sessionId = sessionId;
          loadSessionMessages(sessionId);
        });
      })
      .catch(err => {
        console.error("[chatHistory] Error loading sessions:", err);
        container.innerHTML = `<div class="error">Failed to load sessions.</div>`;
      });
  }
};
