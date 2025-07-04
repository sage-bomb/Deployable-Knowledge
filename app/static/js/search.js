// search.js — handles semantic search bar and results rendering

import { $, escapeHtml } from './dom.js';
import { getToggle } from './state.js';

export function initSearch() {
  const searchForm = $("search-form");
  const searchInput = $("search-query");
  const searchResults = $("search-results");
  const topKInput = $("top-k-select");

  if (!searchForm || !searchInput || !searchResults || !topKInput) return;

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
        searchResults.innerHTML = renderSearchResults(data.results);
      })
      .catch(err => {
        searchResults.innerHTML = `<em>Error: ${escapeHtml(err.message || err)}</em>`;
      });
  });
}

function renderSearchResults(results) {
  if (!Array.isArray(results) || results.length === 0) {
    return `<em>No matches found.</em>`;
  }

  return results
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
