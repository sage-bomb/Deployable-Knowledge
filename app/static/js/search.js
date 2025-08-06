// Codex: Do NOT load backend or Python files. This file is frontend-only.
// search.js — handles semantic search bar and results rendering

import { $, escapeHtml, initPanelToggle } from './dom.js';
import { renderSearchResultsBlock } from './render.js';

/**
 * Initializes the search functionality.
 * @returns {void}
 */
export function initSearch() {
  const searchForm = $("search-form");
  const searchInput = $("search-query");
  const searchResults = $("search-results");
  const topKInput = $("top-k-select");

  if (!searchForm || !searchInput || !searchResults || !topKInput) return;

    initPanelToggle('search-panel-wrapper', 'toggle-search-btn');

  searchForm.addEventListener("submit", function (e) {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (!query) return;

    searchResults.innerHTML = `<em>Searching...</em>`;
    const topKInput = $("top-k-select");
    const topK = parseInt(topKInput.value, 10);

    fetch(`/search?q=${encodeURIComponent(query)}&top_k=${topK}`)
      .then(res => res.json())
      .then(data => {
      searchResults.innerHTML = renderSearchResultsBlock(data.results);
    })
      .catch(err => {
        searchResults.innerHTML = `<em>Error: ${escapeHtml(err.message || err)}</em>`;
      });
  });
}