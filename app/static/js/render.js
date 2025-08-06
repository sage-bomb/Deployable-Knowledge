// Codex: Do NOT load backend or Python files. This file is frontend-only.
import { $, escapeHtml, showConfirmation } from './dom.js';
import { initToggleState, toggleSource, getInactiveSources } from "./session.js";

/**
 * Renders an array of RAG-style result blocks.
 * Each block shows source, match score, and content.
 *
 * @param {Array<Object|string>} results
 * @param {Object} [options]
 * @param {boolean} [options.filterInactive=true]
 * @returns {string} - HTML string
 */
export function renderSearchResultsBlock(results, { filterInactive = true } = {}) {
  if (!Array.isArray(results) || results.length === 0) {
    return `<em>No matches found.</em>`;
  }

  return results
    .map(result => {
      if (typeof result === "string") {
        return { text: result, source: "unknown", score: null, page: null };
      }
      return result;
    })
    .filter(result => {
      return !filterInactive || !getInactiveSources().includes(result.source);
    })
    .map(result => {
      // Fallback for missing page
      const pageDisplay = result.page !== undefined && result.page !== null ? result.page : "N/A";

      return `
      <div class="search-result">
        <div><strong>Source:</strong> 
          <a href="javascript:void(0)" onclick="goToPage('${escapeHtml(result.source)}', ${result.page || 1})" target="_blank">
            ${escapeHtml(result.source)}
          </a>
        </div>
        <div><strong>Match Score:</strong> ${result.score != null ? result.score.toFixed(4) : "n/a"}</div>
        <div><strong>Page:</strong> ${pageDisplay}</div>
        <div style="margin-top: 0.5rem;">${escapeHtml(result.text)}</div>
        ${
          pageDisplay !== "N/A"
            ? `<button onclick="goToPage('${escapeHtml(result.source)}', ${pageDisplay})" style="margin-top:0.5rem;">
                Go to page ${pageDisplay}
               </button>`
            : ''
        }
      </div>
    `;
    })
    .join('');
}

/**
 * Renders a single chat message into the chat box.
 * @param {string} role
 * @param {string} text
 */
export function renderChatMessage(role, text) {
  const chatBox = $("chat-box");
  if (!chatBox) return;
  const msgDiv = document.createElement("div");
  msgDiv.innerHTML = `<strong>${escapeHtml(role)}:</strong> ${escapeHtml(text)}`;
  chatBox.appendChild(msgDiv);
  chatBox.scrollTop = chatBox.scrollHeight;
}

/**
 * Renders a pair of user/assistant messages.
 * @param {string} userText
 * @param {string} assistantText
 */
export function renderMessagePair(userText, assistantText) {
  renderChatMessage("You", userText);
  renderChatMessage("Assistant", assistantText);
}

/**
 * Clears the chat box and search results.
 */
export function clearChatUI() {
  const chatBox = $("chat-box");
  if (chatBox) chatBox.innerHTML = '';
  const searchResults = $("search-results");
  if (searchResults) searchResults.innerHTML = '';
}

/**
 * Renders the document list with optional filtering.
 * @param {Array} docs
 * @param {string} [filter=""]
 */
export function renderDocumentList(docs, filter = "", { refresh } = {}) {
  const list = $("document-list");
  if (!list) return;

  list.innerHTML = "";

  const filtered = docs.filter(doc =>
    doc.title.toLowerCase().includes(filter.toLowerCase())
  );

  if (filtered.length === 0) {
    list.innerHTML = "<li><em>No results found.</em></li>";
    return;
  }

  filtered.forEach(doc => {
    const li = document.createElement("li");
    li.setAttribute("data-doc-id", doc.id);
    li.setAttribute("data-active", "true");

    const statusSpan = document.createElement("span");
    statusSpan.className = "status-label";
    statusSpan.textContent = "Active";

    const toggleBtn = document.createElement("button");
    toggleBtn.className = "toggle-btn btn-active";
    toggleBtn.textContent = "Deactivate";

    initToggleState(doc.id, true);
    const current = !getInactiveSources().includes(doc.id);
    statusSpan.textContent = current ? "Active" : "Inactive";
    toggleBtn.textContent = current ? "Deactivate" : "Activate";
    toggleBtn.classList.toggle("btn-active", current);
    toggleBtn.classList.toggle("btn-inactive", !current);
    toggleBtn.addEventListener("click", () => {
      const current = !getInactiveSources().includes(doc.id);
      const next = !current;
      toggleSource(doc.id, !current);
      statusSpan.textContent = current ? "Inactive" : "Active";
      toggleBtn.textContent = current ? "Activate" : "Deactivate";
      toggleBtn.classList.toggle("btn-active", next);
      toggleBtn.classList.toggle("btn-inactive", !next);
    });

    const removeBtn = document.createElement("button");
    removeBtn.textContent = "Remove";
    removeBtn.style.marginLeft = "0.5rem";
    removeBtn.addEventListener("click", () => {
      showConfirmation(`Remove document "${doc.title}"?`).then(confirmed => {
        if (!confirmed) return;
        fetch("/remove", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ source: doc.id })
        })
          .then(res => res.json())
          .then(data => {
            if (data.status === "success") {
              refresh?.();
            } else {
              alert(`Error: ${data.message}`);
            }
          })
          .catch(err => alert(`Failed to remove: ${err.message || err}`));
      });
    });

    li.innerHTML = `
      <strong title="${escapeHtml(doc.title)}">${escapeHtml(doc.title)}</strong><br />
      <small>Segments: ${doc.segments}</small><br />
      <small>Status: </small>
    `;
    li.appendChild(statusSpan);
    li.appendChild(document.createElement("br"));
    li.appendChild(toggleBtn);
    li.appendChild(removeBtn);
    list.appendChild(li);
  });
}

/**
 * Loads active documents into the document panel.
 * @param {Array} docs
 */
export function loadActiveDocuments(docs) {
  const docPanel = $("document-panel");
  if (!docPanel) return;
  docPanel.innerHTML = "";
  docs.forEach(doc => {
    const div = document.createElement("div");
    div.className = "document-entry";
    div.innerHTML = `<strong>${escapeHtml(doc.name || "Untitled")}</strong><br/><small>${escapeHtml(doc.source || "Unknown")}</small>`;
    docPanel.appendChild(div);
  });
}
