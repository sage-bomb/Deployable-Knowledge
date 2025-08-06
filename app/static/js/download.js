// Codex: Do NOT load backend or Python files. This file is frontend-only.
// download.js

import { $ } from './dom.js';

/**
 * Initializes the download button for the chat log.
 * @returns {string} userId
 */
export function initDownloadButton() {
  const downloadButton = $("download-chat");
  const chatBox = $("chat-box");

  if (!downloadButton || !chatBox) return;

  downloadButton.addEventListener("click", function () {
    const content = chatBox.innerHTML;
    const blob = new Blob([content], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "chat_log.html";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  });
}
