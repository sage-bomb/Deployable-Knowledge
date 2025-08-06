const SESSION_COOKIE_NAME = "chat_session_id";

// --- Cookies ---
export function getCookie(name) {
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

export function setCookie(name, value, days = 30) {
  const expires = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; SameSite=Lax`;
}

export function clearCookie(name) {
  document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
}

// --- App State ---
let appState = {
  sessionId: null,
  inactiveSources: [],
};

function updateSessionStorage() {
  sessionStorage.setItem("appState", JSON.stringify(appState));
}

function loadSessionStorage() {
  const saved = sessionStorage.getItem("appState");
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      appState.inactiveSources = Array.isArray(parsed.inactiveSources) ? parsed.inactiveSources : [];
    } catch (err) {
      console.warn("⚠️ Failed to parse appState from sessionStorage:", err);
    }
  }
}

// --- Session Management ---

export function setSessionId(sessionId) {
  if (sessionId) {
    setCookie(SESSION_COOKIE_NAME, sessionId);
  } else {
    clearCookie(SESSION_COOKIE_NAME);
  }
  appState.sessionId = sessionId;
  updateSessionStorage();
  return sessionId;
}

export async function startNewSession() {
  const res = await fetch("/session", { method: "POST" });
  const data = await res.json();
  const sessionId = data.session_id;
  setSessionId(sessionId);
  appState.inactiveSources = [];
  return sessionId;
}

export function getSessionId() {
  return appState.sessionId;
}

export function getSessionState() {
  return { ...appState };
}

export async function initAppState() {
  loadSessionStorage();
  clearCookie(SESSION_COOKIE_NAME);
  appState.sessionId = null;
  updateSessionStorage();
}

// --- Source Toggle Logic ---
export function getInactiveSources() {
  return [...appState.inactiveSources];
}

export function setInactiveSources(newSources) {
  appState.inactiveSources = [...newSources];
  updateSessionStorage();
}

export function toggleSource(source, enabled) {
  const idx = appState.inactiveSources.indexOf(source);
  if (enabled && idx !== -1) {
    appState.inactiveSources.splice(idx, 1);
  } else if (!enabled && idx === -1) {
    appState.inactiveSources.push(source);
  }
  updateSessionStorage();
}

export function initToggleState(source, defaultValue = true) {
  const isInactive = appState.inactiveSources.includes(source);
  if (!isInactive && !defaultValue) {
    appState.inactiveSources.push(source);
  } else if (isInactive && defaultValue) {
    appState.inactiveSources = appState.inactiveSources.filter(s => s !== source);
  }
  updateSessionStorage();
}

export function getToggle(source) {
  return !appState.inactiveSources.includes(source);
}
