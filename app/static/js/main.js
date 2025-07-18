import { initChat } from '/static/js/chat.js';
import { initSearch } from '/static/js/search.js';
import { initUpload } from '/static/js/upload.js';
import { initDocuments } from '/static/js/documents.js';
import { initPersonaModal } from '/static/js/persona_editor.js';

function runInit() {
  //console.log("✅ runInit executing");
  initDocuments();
  initChat();
  initSearch();
  initUpload();
  initPersonaModal();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", runInit);
} else {
  runInit();
}
