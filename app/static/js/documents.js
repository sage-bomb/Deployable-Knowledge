// Codex: Do NOT load backend or Python files. This file is frontend-only.
// documents.js — handles document list, toggles, filters, removal

import { $, escapeHtml, initPanelToggle } from './dom.js';
import { renderDocumentList } from './render.js';


let allDocs = [];

/**
 * Initialize the document management functionality.
 * Fetches documents, sets up filter form, and handles toggle states.
 */
export function initDocuments() {
  fetchDocuments();
  setupFilterForm();
  initPanelToggle('doc-panel-wrapper', 'toggle-docs-btn');
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
      renderDocumentList(allDocs, '', { refresh: fetchDocuments });
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
    renderDocumentList(allDocs, input.value.trim(), { refresh: fetchDocuments });
  });
}

/**
 * Renders the document list with optional filtering.
 * @param {*} docs 
 * @param {*} filter 
 * @returns 
 */
