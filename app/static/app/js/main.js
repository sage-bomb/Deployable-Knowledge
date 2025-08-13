// /app/main.js
import { initFramework } from "./framework.js";
import { bus } from "/static/ui/js/components.js";
import { Store } from "./store.js";
import { createChatWindow } from "./windows/chat.js";
import { createDocsWindow, refreshDocs, handleDocAction } from "./windows/docs.js";
import { createSegmentsWindow, refreshSegments, handleSegmentAction, setSegmentsSource, openSegmentViewer } from "./windows/segments.js";
import { createSearchWindow } from "./windows/search.js";
import { openSessionsWindow, loadChatHistory } from "./windows/sessions.js";
import { openPersonaEditor } from "./windows/persona.js";

initFramework();

async function ensureChatSession() {
  try {
    const res = await fetch("/session", { credentials: "same-origin" });
    const data = await res.json();
    Store.sessionId = data.session_id;
  } catch (e) {
    console.error("session", e);
  }
}

function setupMenus() {
  document.querySelector('#user-menu-dropdown [data-action="logout"]')?.addEventListener('click', () => {
    window.location.href = '/logout';
  });
  document.querySelectorAll('#tools-menu-dropdown .menu-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const act = btn.dataset.action;
      if (act === 'tool-chat') document.getElementById('win_chat')?.scrollIntoView();
      if (act === 'tool-docs') document.getElementById('win_docs')?.scrollIntoView();
      if (act === 'tool-segments') document.getElementById('win_segments')?.scrollIntoView();
      if (act === 'tool-sessions') openSessionsWindow();
      if (act === 'tool-persona') openPersonaEditor();
    });
  });
}

function registerBusHandlers() {
  bus.addEventListener("ui:list-action", async (ev) => {
    const { winId, elementId, action, item } = ev.detail || {};
    if (winId === "win_docs" && elementId === "doc_list") {
      await handleDocAction(action, item);
    }
    if (winId === "win_segments" && elementId === "segment_list") {
      await handleSegmentAction(action, item);
    }
    if (winId === "win_search" && elementId === "search_results" && action === "open" && item?.id) {
      await openSegmentViewer(item.id);
    }
    if (winId === "win_sessions" && elementId === "session_list" && action === "open" && item?.session_id) {
      Store.sessionId = item.session_id;
      await loadChatHistory(chatUI, Store.sessionId);
    }
  });
  bus.addEventListener("ui:list-select", async (ev) => {
    const { winId, elementId, item } = ev.detail || {};
    if (winId === "win_docs" && elementId === "doc_list") {
      setSegmentsSource(item?.id);
      await refreshSegments();
    }
  });
}

await ensureChatSession();
const chatUI = createChatWindow();
createSearchWindow();
createDocsWindow();
createSegmentsWindow();
setupMenus();
registerBusHandlers();
await refreshDocs();
await refreshSegments();
await loadChatHistory(chatUI, Store.sessionId);
