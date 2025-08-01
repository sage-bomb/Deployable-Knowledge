import { initChat } from '/static/js/chat.js';
import { initSearch } from '/static/js/search.js';
import { initUpload } from '/static/js/upload.js';
import { initDocuments } from '/static/js/documents.js';
import { initPersonaModal } from '/static/js/persona_editor.js';
import { initDownloadButton } from './download.js';

/**
 * Run all initializations for the application.
 * This function is called when the DOM is fully loaded.
 */
function runInit() {
  //console.log("✅ runInit executing");
  initDocuments();
  initChat();
  initSearch();
  initUpload();
  initPersonaModal();
  initDownloadButton();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", runInit);
} else {
  runInit();
}

window.goToPage = function (source, page) {
  if (!page) {
    alert("No page information available");
    return;
  }

  // Open the PDF file directly at a specific page
  window.open(`/documents/${encodeURIComponent(source)}#page=${page}`, "_blank");
};