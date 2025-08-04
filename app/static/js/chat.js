// chat.js

import { $, escapeHtml } from './dom.js';
import { renderSearchResultsBlock } from './render.js';

/**
 * Appends a chat message to the chat box.
 * @param {string} role - 'You' or 'Assistant'
 * @param {string} text - Text to display
 */
function appendMessage(role, text) {
  const chatBox = $("chat-box");
  if (!chatBox) return;

  const msgDiv = document.createElement("div");
  msgDiv.innerHTML = `<strong>${role}:</strong> ${escapeHtml(text)}`;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * Clears the chat box entirely.
 */
function resetChatUI() {
  const chatBox = $("chat-box");
  if (chatBox) chatBox.innerHTML = '';
  const searchResults = $("search-results");
  if (searchResults) searchResults.innerHTML = '';
}

/**
 * Initializes the chat functionality.
 * @param {Object} session - Session object with sessionId
 */
export function initChat(session) {
  const chatForm = $("chat-form");
  const chatInput = $("user-input");
  const chatBox = $("chat-box");
  const docLimitInput = $("top-k-select");
  const submitButton = $("submit-button");
  const clearButton = $("clear-history");
  const resetLLMButton = $("reset-llm");
  const downloadButton = $("download-chat");
  const personaButton = $("open-persona-btn");

  if (!chatForm || !chatInput || !submitButton) return;

  // 🔁 CHAT SUBMISSION
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    // Disable UI
    chatInput.disabled = true;
    submitButton.disabled = true;
    resetLLMButton.disabled = true;
    clearButton.disabled = true;
    submitButton.textContent = "Loading...";

    appendMessage("You", msg);
    chatInput.value = "";

    const botMsg = document.createElement("div");
    chatBox.appendChild(botMsg);

    // 📄 CONTEXT SEARCH (RAG)
    try {
      const topK = docLimitInput?.value || 5;
      const contextRes = await fetch(`/search?q=${encodeURIComponent(msg)}&top_k=${topK}`);
      const contextData = await contextRes.json();

      if (contextData?.results?.length) {
        const resultsHTML = renderSearchResultsBlock(contextData.results);
        $("search-results").innerHTML = `<h3>RAG Context Used:</h3>${resultsHTML}`;
      }
    } catch (err) {
      console.error("Context search failed", err);
    }

    // 🤖 LLM RESPONSE
    try {
      const persona = $("persona-text")?.value || "";
      const response = await fetch("/chat-stream", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          message: msg,
          persona,
          user_id: session.sessionId
        })
      });

      if (!response.body) {
        botMsg.innerHTML = `<em>No response body</em>`;
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        botMsg.innerHTML = `<br>${window.marked.parse(buffer)}`;
        chatBox.scrollTop = chatBox.scrollHeight;
      }

    } catch (err) {
      botMsg.innerHTML = `<em>Error: ${escapeHtml(err.message || String(err))}</em>`;
    }

    // Restore UI
    chatInput.disabled = false;
    submitButton.disabled = false;
    resetLLMButton.disabled = false;
    clearButton.disabled = false;
    submitButton.textContent = "Send";
    chatInput.focus();
  });

  // 🧼 CLEAR CHAT
  clearButton?.addEventListener("click", () => {
    resetChatUI();
    chatInput.focus();
  });

  // 🧠 RESET MEMORY
  resetLLMButton?.addEventListener("click", async () => {
    resetChatUI();
    chatInput.disabled = true;
    submitButton.disabled = true;
    resetLLMButton.disabled = true;

    try {
      await fetch(`/debug/memory?user_id=${encodeURIComponent(session.sessionId)}`, {
        method: "DELETE"
      });
      appendMessage("Assistant", "Memory has been cleared.");
    } catch (err) {
      appendMessage("Assistant", `Error resetting memory: ${escapeHtml(err.message || err)}`);
    }

    chatInput.disabled = false;
    submitButton.disabled = false;
    resetLLMButton.disabled = false;
    chatInput.focus();
  });
}
