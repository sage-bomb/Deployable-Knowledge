import { escapeHtml } from './dom.js';
import { getToggle } from './state.js';

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
        return { text: result, source: "unknown", score: null };
      }
      return result;
    })
    .filter(result => {
      return !filterInactive || getToggle(result.source);
    })
    .map(result => `
      <div class="search-result">
        <div><strong>Source:</strong> <a href="/documents/${encodeURIComponent(result.source)}" target="_blank">${escapeHtml(result.source)}</a></div>
        <div><strong>Match Score:</strong> ${result.score != null ? result.score.toFixed(4) : "n/a"}</div>
        <div style="margin-top: 0.5rem;">${escapeHtml(result.text)}</div>
      </div>
    `)
    .join('');
}