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

function setupMenus(chatUI) {
  document.querySelectorAll('.menu').forEach(menu => {
    const trigger = menu.querySelector('.menu-trigger');
    const drop = menu.querySelector('.menu-dropdown');
    if (!trigger || !drop) return;
    const close = () => {
      trigger.setAttribute('aria-expanded', 'false');
      drop.setAttribute('aria-hidden', 'true');
    };
    trigger.addEventListener('click', e => {
      e.stopPropagation();
      const open = trigger.getAttribute('aria-expanded') === 'true';
      document.querySelectorAll('.menu .menu-dropdown[aria-hidden="false"]').forEach(d => {
        d.setAttribute('aria-hidden', 'true');
        d.previousElementSibling?.setAttribute('aria-expanded', 'false');
      });
      if (!open) {
        trigger.setAttribute('aria-expanded', 'true');
        drop.setAttribute('aria-hidden', 'false');
      } else {
        close();
      }
    });
    document.addEventListener('click', e => { if (!menu.contains(e.target)) close(); });
  });

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

  document.querySelectorAll('#menu-dropdown .menu-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const act = btn.dataset.action;
      if (act === 'new-chat') {
        chatUI.log.innerHTML = '';
        Store.sessionId = '';
        ensureChatSession();
      }
      if (act === 'toggle-search') {
        const w = document.getElementById('win_search');
        if (w) w.style.display = w.style.display === 'none' ? '' : 'none';
      }
      if (act === 'prompt-templates') alert('Prompt templates not implemented');
      if (act === 'settings') alert('Settings not implemented');
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
setupMenus(chatUI);
registerBusHandlers();
await refreshDocs();
await refreshSegments();
await loadChatHistory(chatUI, Store.sessionId);
