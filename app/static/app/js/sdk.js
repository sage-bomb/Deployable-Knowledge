// /app/sdk.js
const JSON_HEADERS = { Accept: "application/json" };

function csrfHeader() {
  const m = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]+)/);
  return m ? { 'X-CSRF-Token': decodeURIComponent(m[1]) } : {};
}

async function ok(res) {
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res;
}
async function asJsonSafe(res) {
  const ct = res.headers.get("content-type") || "";
  const txt = await res.text();
  if (ct.includes("application/json")) { try { return JSON.parse(txt); } catch {} }
  const lines = txt.split(/\r?\n/).filter(Boolean);
  for (let i = lines.length - 1; i >= 0; i--) { try { return JSON.parse(lines[i]); } catch {} }
  return { response: txt };
}

export async function listDocuments() {
  const res = await ok(await fetch("/documents", { headers: { ...JSON_HEADERS, ...csrfHeader() }, credentials: "same-origin" }));
  return asJsonSafe(res);
}
export async function uploadDocuments(files) {
  const fd = new FormData();
  for (const f of files) fd.append("files", f);
  const res = await ok(await fetch("/upload", { method: "POST", body: fd, credentials: "same-origin", headers: csrfHeader() }));
  return asJsonSafe(res);
}
export async function removeDocument(source) {
  const fd = new FormData();
  fd.append("source", source);
  const res = await ok(await fetch("/remove", { method: "POST", body: fd, credentials: "same-origin", headers: csrfHeader() }));
  return asJsonSafe(res);
}

// in /app/sdk.js
export async function listSegments(source) {
  const url = source ? `/segments?source=${encodeURIComponent(source)}` : `/segments`;
  const res = await fetch(url, { headers: { Accept: "application/json", ...csrfHeader() }, credentials: "same-origin" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json();
}
export async function getSegment(id) {
  const res = await fetch(`/segments/${encodeURIComponent(id)}`, { headers: { Accept: "application/json", ...csrfHeader() }, credentials: "same-origin" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json();
}
export async function removeSegment(id) {
  const res = await fetch(`/segments/${encodeURIComponent(id)}`, { method: "DELETE", headers: { Accept: "application/json", ...csrfHeader() }, credentials: "same-origin" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json();
}
// --- chat (non-stream) ---
export async function chat({ message, session_id, persona = "", inactive = [] }) {
  const fd = new FormData();
  fd.append("message", message);
  fd.append("session_id", session_id);
  fd.append("persona", persona);
  fd.append("inactive", JSON.stringify(inactive));
  const res = await fetch(`/chat?stream=false`, {
    method: "POST",
    body: fd,
    headers: { "Accept": "application/json", ...csrfHeader() },
    credentials: "same-origin"
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json(); // { response, sources? }
}

// --- chat (streaming SSE-ish via fetch body reader) ---
export async function chatStream({ message, session_id, persona = "", inactive = [] }) {
  const params = new URLSearchParams();
  params.set("message", message);
  params.set("session_id", session_id);
  params.set("persona", persona);
  if (inactive?.length) params.set("inactive", JSON.stringify(inactive));

  const res = await fetch(`/chat?stream=true`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8", "Accept": "*/*", ...csrfHeader() },
    body: params.toString(),
    credentials: "same-origin",
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  if (!res.body) throw new Error("No response body");
  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  return { reader, decoder };
}

// simple search (segments by text)
export async function searchSegments({ q, top_k = 10, inactive = [] }) {
  const params = new URLSearchParams();
  params.set("q", q);
  params.set("top_k", String(top_k));
  if (inactive?.length) params.set("inactive", JSON.stringify(inactive));
  const res = await fetch(`/search?${params.toString()}`, {
    headers: { Accept: "application/json", ...csrfHeader() }, credentials: "same-origin"
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json(); // array of segments or {results:[...]}
}
