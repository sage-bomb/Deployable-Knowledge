import { initChat } from './chat.js';
import { initSearch } from './search.js';
import { initUpload } from './upload.js';
import { initDocuments } from './documents.js';
import { initPersonaModal } from './persona_editor.js';

function runInit() {
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
