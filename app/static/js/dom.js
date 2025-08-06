// Codex: Do NOT load backend or Python files. This file is frontend-only.
// dom.js — shared DOM helpers and modal logic

/**
 * Get an element by its ID.
 * @param {string} id 
 * @returns {HTMLElement|null}
 */
export function $(id) {
  return document.getElementById(id);
}

/**
 * Escapes HTML special characters in a string.
 * @param {string} str 
 * @returns {string}
 */
export function escapeHtml(str) {
  return str.replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
}

/**
 * Shows a confirmation modal with the given message.
 * @param {string} message 
 * @returns {Promise<boolean>}
 */
export function showConfirmation(message) {
  return new Promise((resolve) => {
    const modal = $("confirm-modal");
    const msg = $("confirm-message");
    const yes = $("confirm-yes");
    const no = $("confirm-no");

    if (!modal || !msg || !yes || !no) return resolve(false);

    msg.textContent = message;
    modal.classList.remove("hidden");

    function cleanup(result) {
      modal.classList.add("hidden");
      yes.removeEventListener("click", yesHandler);
      no.removeEventListener("click", noHandler);
      resolve(result);
    }

    function yesHandler() { cleanup(true); }
    function noHandler() { cleanup(false); }

    yes.addEventListener("click", yesHandler);
    no.addEventListener("click", noHandler);
  });
}
