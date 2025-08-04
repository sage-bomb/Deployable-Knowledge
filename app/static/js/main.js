import { initAppState, getSessionState } from './session.js';
import { initChat } from './chat.js';
import { chatHistory } from './chatHistory.js';
import { initDocuments } from './documents.js';
import { initSearch } from './search.js';
import { initUpload } from './upload.js';
import { initPersonaModal } from './persona_editor.js';
import { initDownloadButton } from './download.js';

async function runInit() {
  await initAppState(); // ensures session and app state
  const session = getSessionState();

  initDocuments(session);
  initChat(session);
  chatHistory.init(session);
  initSearch(session);
  initUpload(session);
  initPersonaModal();
  initDownloadButton();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", runInit);
} else {
  runInit();
}