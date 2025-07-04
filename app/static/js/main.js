import { initChat } from './chat.js';
import { initSearch } from './search.js';
import { initUpload } from './upload.js';
import { initDocuments } from './documents.js';

function runInit() {
  initDocuments();
  initChat();
  initSearch();
  initUpload();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", runInit);
} else {
  runInit(); // DOM already loaded
}
