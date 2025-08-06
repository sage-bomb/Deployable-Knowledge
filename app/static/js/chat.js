// Codex: Do NOT load backend or Python files. This file is frontend-only.
// chat.js

import { $, escapeHtml } from './dom.js';

import { renderSearchResultsBlock, renderChatMessage, clearChatUI } from './render.js';
import { startNewSession } from './session.js';
import { chatHistory } from './chatHistory.js';

// Rendering helpers moved to render.js

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
  const newChatButton = $("new-chat");

  if (!chatForm || !chatInput || !submitButton) return;


  clearChatUI();

  // 🔁 CHAT SUBMISSION
  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    if (!session.sessionId) {
      const newId = await startNewSession();
      session.sessionId = newId;
      chatHistory.init(session);
    }

    // Disable UI
    chatInput.disabled = true;
    submitButton.disabled = true;
    resetLLMButton.disabled = true;
    clearButton.disabled = true;
    submitButton.textContent = "Loading...";

    renderChatMessage("You", msg);
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
      const params = new URLSearchParams();
      params.set("message", msg);
      params.set("persona", persona);
      params.set("session_id", session.sessionId);

      const response = await fetch("/chat-stream", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params.toString()
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
    clearChatUI();
    chatInput.focus();
  });

  // 🆕 START NEW CHAT SESSION
  newChatButton?.addEventListener("click", async () => {
    const newId = await startNewSession();
    session.sessionId = newId;
    clearChatUI();
    chatHistory.init(session);
    chatInput.focus();
  });

  // 🧠 RESET MEMORY
  resetLLMButton?.addEventListener("click", async () => {
    clearChatUI();
    chatInput.disabled = true;
    submitButton.disabled = true;
    resetLLMButton.disabled = true;

    try {
      await fetch(`/debug/memory?session_id=${encodeURIComponent(session.sessionId)}`, {
        method: "DELETE"
      });
      renderChatMessage("Assistant", "Memory has been cleared.");
    } catch (err) {
      renderChatMessage("Assistant", `Error resetting memory: ${escapeHtml(err.message || err)}`);
    }

    chatInput.disabled = false;
    submitButton.disabled = false;
    resetLLMButton.disabled = false;
    chatInput.focus();
  });
}
