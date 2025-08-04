// chatHistory.js

import { $ } from './dom.js';
import { ensureSession } from './session.js';

/**
 * Clears the chat UI.
 */
function clearChatBox() {
  const chatBox = $("chat-box");
  if (chatBox) chatBox.innerHTML = '';
  const searchResults = $("search-results");
  if (searchResults) searchResults.innerHTML = '';
}

/**
 * Renders a single message pair to the chat box.
 * @param {string} userText 
 * @param {string} assistantText 
 */
function renderMessagePair(userText, assistantText) {
  const chatBox = $("chat-box");
  if (!chatBox) return;

  const userDiv = document.createElement("div");
  userDiv.innerHTML = `<strong>You:</strong> ${userText}`;
  chatBox.appendChild(userDiv);

  const botDiv = document.createElement("div");
  botDiv.innerHTML = `<strong>Assistant:</strong> ${assistantText}`;
  chatBox.appendChild(botDiv);
}

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

    clearChatBox();
    await ensureSession();

    for (const [user, assistant] of history) {
      renderMessagePair(user, assistant);
    }
  } catch (err) {
    console.error("❌ Error loading session messages:", err);
    clearChatBox();
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
