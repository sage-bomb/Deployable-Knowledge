// chat.js — handles chat form submission and RAG context rendering

import { $, escapeHtml } from './dom.js';
import { getInactiveIds, getToggle } from './state.js';

export function initChat() {
  const chatForm = $("chat-form");
  const chatInput = $("user-input");
  const chatBox = $("chat-box");
  const searchResults = $("search-results");

  chatForm.addEventListener("submit", function (e) {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    const inactive = getInactiveIds();

    chatBox.innerHTML += `<div><strong>You:</strong> ${escapeHtml(msg)}</div>`;
    const botMsg = document.createElement("div");
    botMsg.innerHTML = `<strong>Assistant:</strong> <em>Thinking...</em>`;
    chatBox.appendChild(botMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        message: msg,
        inactive: JSON.stringify(inactive)
      })
    })
      .then(res => res.json())
      .then(data => {
        if (!data.response) {
          botMsg.innerHTML = `<strong>Assistant:</strong> <em>No response received from the server.</em>`;
          return;
        }

        botMsg.innerHTML = `<strong>Assistant:</strong><br>${data.response}`;
        chatBox.scrollTop = chatBox.scrollHeight;

        if (Array.isArray(data.context)) {
          searchResults.innerHTML = `
            <h3>RAG Context Used:</h3>
            ${renderSearchResults(data.context)}
          `;
        }
      })
      .catch(err => {
        botMsg.innerHTML = `<strong>Assistant:</strong> <em>Error: ${escapeHtml(err.message || err)}</em>`;
      });

    chatInput.value = '';
  });
}

function renderSearchResults(results) {
  if (!Array.isArray(results) || results.length === 0) {
    return `<em>No matches found.</em>`;
  }

  return results
    .map(result => {
      if (typeof result === "string") {
        return { text: result, source: "unknown", score: null };
      }
      return result;
    })
    .filter(r => getToggle(r.source))
    .map(result => `
      <div class="search-result">
        <div><strong>Source:</strong> <a href="/documents/${encodeURIComponent(result.source)}" target="_blank">${escapeHtml(result.source)}</a></div>
        <div><strong>Match Score:</strong> ${result.score != null ? result.score.toFixed(4) : "n/a"}</div>
        <div style="margin-top: 0.5rem;">${escapeHtml(result.text)}</div>
      </div>
    `)
    .join('');
}
