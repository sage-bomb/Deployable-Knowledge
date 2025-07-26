import { $, escapeHtml } from './dom.js';

function getUserId() {
  let userId = localStorage.getItem('user_id');
  if (!userId) {
    userId = 'guest-' + Math.random().toString(36).substring(2, 10);
    localStorage.setItem('user_id', userId);
  }
  return userId;
}

async function ensureSession(userId) {
  let sessionId = localStorage.getItem('session_id');
  if (!sessionId) {
    const res = await fetch('/logs/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ user_id: userId })
    });
    const data = await res.json();
    sessionId = data.session_id;
    localStorage.setItem('session_id', sessionId);
  }
  return sessionId;
}

export async function initLogs() {
  const listEl = $('log-list');
  const wrapper = $('log-panel-wrapper');
  const toggleBtn = $('toggle-logs-btn');
  const chatBox = $('chat-box');

  const userId = getUserId();
  await ensureSession(userId);

  toggleBtn?.addEventListener('click', () => {
    wrapper.classList.toggle('collapsed');
  });

  async function loadList() {
    const res = await fetch(`/logs?user_id=${encodeURIComponent(userId)}`);
    const data = await res.json();
    listEl.innerHTML = '';
    if (!data.sessions || data.sessions.length === 0) {
      listEl.innerHTML = '<li><em>No logs found.</em></li>';
      return;
    }
    data.sessions.forEach(s => {
      const li = document.createElement('li');
      const btn = document.createElement('button');
      const label = new Date(s.timestamp).toLocaleString();
      btn.textContent = label;
      btn.addEventListener('click', () => loadSession(s.session_id));
      li.appendChild(btn);
      listEl.appendChild(li);
    });
  }

  async function loadSession(sessionId) {
    const res = await fetch(`/logs/${sessionId}`);
    if (!res.ok) return;
    const data = await res.json();
    chatBox.innerHTML = '';
    const history = [];
    data.messages.forEach(m => {
      if (m.role === 'user') {
        chatBox.innerHTML += `<div><strong>You:</strong> ${escapeHtml(m.text)}</div>`;
        history.push([m.text]);
      } else if (m.role === 'assistant') {
        chatBox.innerHTML += `<div><strong>Assistant:</strong> ${escapeHtml(m.text)}</div>`;
        if (history.length > 0 && history[history.length -1].length === 1) {
          history[history.length -1].push(m.text);
        }
      }
    });
    chatBox.scrollTop = chatBox.scrollHeight;
    localStorage.setItem('session_id', sessionId);
    await fetch('/debug/memory', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, history })
    });
  }

  await loadList();
}

export { ensureSession };
