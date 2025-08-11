// app/api.js — ALL fetch calls live here (app layer only)
const JSON_HEADERS = { "Accept": "application/json" };

async function asJsonSafe(res) {
  const ct = res.headers.get("content-type") || "";
  const txt = await res.text();
  if (ct.includes("application/json")) {
    try { return JSON.parse(txt); } catch (e) { /* fall-through */ }
  }
  const lines = txt.split(/\r?\n/).filter(Boolean);
  for (let i = lines.length - 1; i >= 0; i--) {
    try { return JSON.parse(lines[i]); } catch {}
  }
  return { response: txt };
}

async function ok(res) {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res;
}

export async function getOrCreateChatSession() {
  try {
    const res = await fetch("/session", { method: "POST", headers: JSON_HEADERS, credentials: "same-origin" });
    const data = await asJsonSafe(await ok(res));
    return data.session_id;
  } catch (e) {
    const res = await fetch("/session", { headers: JSON_HEADERS, credentials: "same-origin" });
    const data = await asJsonSafe(await ok(res));
    return data.session_id;
  }
}

export async function listSessions() {
  const res = await ok(await fetch("/sessions", { headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function listDocuments() {
  const res = await ok(await fetch("/documents", { headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function listSegments() {
  const res = await ok(await fetch("/segments", { headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function getSegment(id) {
  const res = await ok(await fetch(`/segments/${encodeURIComponent(id)}`, { headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function removeDocument(source) {
  const fd = new FormData();
  fd.append("source", source);
  const res = await ok(await fetch("/remove", { method: "POST", body: fd, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function removeSegment(id) {
  const res = await ok(await fetch(`/segments/${encodeURIComponent(id)}`, { method: "DELETE", headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function uploadDocuments(files) {
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  const res = await ok(await fetch("/upload", { method: "POST", body: fd, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function getUser() {
  const res = await ok(await fetch("/user", { headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function searchDocuments(q, top_k=5) {
  const res = await ok(await fetch(`/search?q=${encodeURIComponent(q)}&top_k=${encodeURIComponent(top_k)}`, { headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function getSettings(userId) {
  const res = await ok(await fetch(`/api/settings/${encodeURIComponent(userId)}`, { headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function patchSettings(userId, payload) {
  const res = await ok(await fetch(`/api/settings/${encodeURIComponent(userId)}`, {
    method: "PATCH",
    headers: { ...JSON_HEADERS, "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload)
  }));
  return asJsonSafe(res);
}

export async function listPromptTemplates() {
  const res = await ok(await fetch(`/api/prompt-templates`, { headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function getPromptTemplate(id) {
  const res = await ok(await fetch(`/api/prompt-templates/${encodeURIComponent(id)}`, { headers: JSON_HEADERS, credentials: "same-origin" }));
  return asJsonSafe(res);
}

export async function savePromptTemplate(id, payload) {
  const res = await ok(await fetch(`/api/prompt-templates/${encodeURIComponent(id)}`, {
    method: "PUT",
    headers: { ...JSON_HEADERS, "Content-Type": "application/json" },
    credentials: "same-origin",
    body: JSON.stringify(payload)
  }));
  return asJsonSafe(res);
}

// Non-streaming fallback (if you have a non-streaming route)
export async function chat({ message, session_id, persona="", inactive=[] }) {
  const fd = new FormData();
  fd.append("message", message);
  fd.append("inactive", JSON.stringify(inactive));
  fd.append("persona", persona);
  fd.append("session_id", session_id);
  const res = await fetch(`/chat?stream=false`, { method: "POST", body: fd, headers: { "Accept": "application/json" }, credentials: "same-origin" });
  return asJsonSafe(await ok(res));
}

// Streaming chat using x-www-form-urlencoded to match legacy UI
export async function chatStream({ message, session_id, persona="", inactive=[] }) {
  const params = new URLSearchParams();
  params.set("message", message);
  params.set("persona", persona);
  params.set("session_id", session_id);
  // Legacy UI omitted inactive — keep optional
  if (inactive && inactive.length) params.set("inactive", JSON.stringify(inactive));

  const res = await fetch(`/chat-stream`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8", "Accept": "*/*" },
    body: params.toString(),
    credentials: "same-origin"
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  if (!res.body) throw new Error("No response body");
  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  return { reader, decoder };
}

// Start a brand-new chat session
export async function startNewSession() {
  const res = await fetch("/session", {
    method: "POST",
    headers: { "Accept": "application/json" },
    credentials: "same-origin"
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  const data = await res.json();
  return data.session_id;
}

// Fetch one session's message history: returns { history: [[user, assistant], ...] }
export async function getSession(session_id) {
  const res = await fetch(`/sessions/${encodeURIComponent(session_id)}`, {
    headers: { "Accept": "application/json" },
    credentials: "same-origin"
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json();
}
