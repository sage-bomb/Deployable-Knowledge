// chat.js — handles chat form submission and RAG context rendering

import { $, escapeHtml } from './dom.js';
import { getInactiveIds, getToggle } from './state.js';
import { renderSearchResultsBlock } from './render.js';

export function initChat() {
  const chatForm = $("chat-form");
  const chatInput = $("user-input");
  const chatBox = $("chat-box");
  const searchResults = $("search-results");

  chatForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    const inactive = getInactiveIds();
    chatBox.innerHTML += `<div><strong>You:</strong> ${escapeHtml(msg)}</div>`;

    const botMsg = document.createElement("div");
    botMsg.innerHTML = `<strong>Assistant:</strong><em> Thinking...</em>`;
    chatBox.appendChild(botMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    // === Step 1: Fetch search context ===
    try {
      const searchRes = await fetch(`/search?q=${encodeURIComponent(msg)}`);
      const data = await searchRes.json();
      if (Array.isArray(data.results)) {
        searchResults.innerHTML = `
          <h3>RAG Context Used:</h3>
          ${renderSearchResultsBlock(data.results)}
        `;
      }
    } catch (err) {
      console.error("Search error:", err);
    }

    // === Step 2: Stream response from /chat-stream ===
    try {
      const response = await fetch("/chat-stream", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({
          message: msg,
          inactive: JSON.stringify(inactive),
        }),
      });

      if (!response.ok || !response.body) {
        botMsg.innerHTML = `<strong>Assistant:</strong> <em>Failed to connect to server.</em>`;
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let full = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        full += chunk;
        botMsg.innerHTML = full;
        chatBox.scrollTop = chatBox.scrollHeight;
      }
    } catch (err) {
      botMsg.innerHTML = `<strong>Assistant:</strong> <em>Error: ${escapeHtml(err.message || err)}</em>`;
    }

    chatInput.value = '';
  });
}
