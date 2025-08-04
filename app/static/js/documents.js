// documents.js — handles document list, toggles, filters, removal

import { $, escapeHtml, showConfirmation } from './dom.js';
import { toggleSource , getInactiveSources, initToggleState } from './session.js';


let allDocs = [];

/**
 * Initialize the document management functionality.
 * Fetches documents, sets up filter form, and handles toggle states.
 */
export function initDocuments() {
  fetchDocuments();
  setupFilterForm();

  const btn = $("toggle-docs-btn");
  const wrapper = $("doc-panel-wrapper");
  if (btn && wrapper) {
    btn.addEventListener("click", () => {
      wrapper.classList.toggle("collapsed");
      btn.textContent = wrapper.classList.contains("collapsed") ? "»" : "«";
    });
  }
}

/**
 * Fetches the list of documents from the server.
 * Updates the global `allDocs` variable and renders the document list.
 */
function fetchDocuments() {
  fetch("/documents")
    .then(res => res.json())
    .then(docs => {
      allDocs = docs;
      renderDocumentList(allDocs);
    })
    .catch(err => {
      const list = $("document-list");
      if (list) {
        list.innerHTML = `<li><em>Error: ${escapeHtml(err.message || err)}</em></li>`;
      }
    });
}

/**
 * Sets up the filter form for document search.
 * @returns {Promise} Resolves when the document list is rendered.
 */
function setupFilterForm() {
  const form = $("filter-form");
  const input = $("filter-input");
  if (!form || !input) return;

  form.addEventListener("submit", e => {
    e.preventDefault();
    renderDocumentList(allDocs, input.value.trim());
  });
}

/**
 * Renders the document list with optional filtering.
 * @param {*} docs 
 * @param {*} filter 
 * @returns 
 */
function renderDocumentList(docs, filter = "") {
  const list = $("document-list");
  if (!list) return;

  list.innerHTML = ""; // Clear list

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
    const current = !getInactiveSources().includes(source);
    statusSpan.textContent = current ? "Active" : "Inactive";
    toggleBtn.textContent = current ? "Deactivate" : "Activate";

    toggleBtn.classList.toggle("btn-active", current);
    toggleBtn.classList.toggle("btn-inactive", !current);
    toggleBtn.addEventListener("click", () => {
      const current = !getInactiveSources().includes(source);
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
            if (data.status === "success") fetchDocuments();
            else alert(`Error: ${data.message}`);
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

export function loadActiveDocuments(docs) {
  const docPanel = document.getElementById("document-panel");
  if (!docPanel) return;

  // Clear and reload content
  docPanel.innerHTML = "";
  docs.forEach(doc => {
    const div = document.createElement("div");
    div.className = "document-entry";
    div.innerHTML = `<strong>${doc.name || "Untitled"}</strong><br/><small>${doc.source || "Unknown"}</small>`;
    docPanel.appendChild(div);
  });
}
