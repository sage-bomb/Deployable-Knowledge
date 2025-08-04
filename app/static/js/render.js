import { escapeHtml } from './dom.js';
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
