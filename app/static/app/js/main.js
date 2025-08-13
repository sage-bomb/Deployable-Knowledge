// /app/main.js
import { initFramework, spawnWindow } from "./framework.js";
import { bus, getComponent } from "/static/ui/js/components.js";
import {
  listDocuments, uploadDocuments, removeDocument,
  listSegments, getSegment, removeSegment, chat, chatStream, searchSegments
} from "./sdk.js";
import { Store } from "./store.js";

initFramework(); // splitter + dnd + resizer



// === ADD helpers ===
const htmlEscape = (s="") => s.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
const renderMd = (s="") => (window.marked?.parse ? window.marked.parse(s) : htmlEscape(s).replaceAll("\n","<br>"));

// spawn a Segment Viewer window and render payload
async function openSegmentViewer(id) {
  const seg = await getSegment(id);
  const winId = `seg_view_${id}`;
  // create the window shell
  spawnWindow({
    id: winId,
    window_type: "window_generic",
    title: seg?.source ? `Segment • ${seg.source}` : "Segment",
    col: "right",
    unique: false,
    resizable: true,
    Elements: [
      { type: "text", id: "seg_meta", value: "" },
      { type: "note", id: "seg_text", text: "" } // we'll overwrite as HTML
    ]
  });

  // render metadata + body
  const win = document.getElementById(winId);
  const meta = win?.querySelector("#seg_meta")?.closest(".row")?.querySelector(".value") || win?.querySelector("#seg_meta");
  const bodyRow = win?.querySelector("#seg_text")?.closest(".row");
  if (meta) {
    meta.innerHTML = `
      <div class="kv">
        <div><strong>ID:</strong> ${htmlEscape(seg.id||"")}</div>
        <div><strong>Source:</strong> ${htmlEscape(seg.source||"")}</div>
        <div><strong>Index:</strong> ${htmlEscape(String(seg.segment_index ?? ""))}</div>
        <div><strong>Priority:</strong> ${htmlEscape(seg.priority||"")}</div>
        <div><strong>Chars:</strong> ${htmlEscape(String(seg.start_char ?? ""))}–${htmlEscape(String(seg.end_char ?? ""))}</div>
      </div>
    `;
  }
  if (bodyRow) {
    const viewer = document.createElement("div");
    viewer.className = "segment-view prose";
    viewer.innerHTML = renderMd(seg.text || seg.preview || "(empty)");
    bodyRow.replaceWith(viewer);
  }
}
// === REPLACE your current Search window spawn block ===
spawnWindow({
  id: "win_search",
  window_type: "window_generic",
  title: "Semantic Search",
  col: "right",
  unique: true,
  resizable: true,
  Elements: [
    { type: "text_field",  id: "search_q", placeholder: "Search text…" },
    { type: "number_field", id: "search_k", label: "Top K", value: 10, min: 1, max: 100 },
    {
      type: "item_list",
      id: "search_results",
      label: "Results",
      item_template: {
        elements: [
          { type: "text", bind: "source",  class: "li-title"  },
          { type: "text", bind: "preview", class: "li-subtle" },
          { type: "button", label: "Open", action: "open" } // buttons are allowed here
        ]
      }
    }
  ]
});
// === ADD right after the spawnWindow(...) above ===
{
  const win = document.getElementById("win_search");
  const qInput = win?.querySelector("#search_q");
  const kInput = win?.querySelector("#search_k") || { value: 10 };

  if (qInput) {
    // build a tiny action bar under the query field
    const qRow = qInput.closest(".row");
    const bar  = document.createElement("div");
    bar.className = "actions";
    const btn  = document.createElement("button");
    btn.type = "button";
    btn.className = "btn";
    btn.id = "search_btn";
    btn.textContent = "Search";
    bar.appendChild(btn);
    qRow?.after(bar);

    async function runSearch() {
      const q = qInput.value.trim();
      const k = parseInt(kInput.value || "10", 10);
      if (!q) return;
      const inactive = Store?.inactiveList?.() || [];
      const res = await searchSegments({ q, top_k: k, inactive });
      const results = Array.isArray(res?.results) ? res.results : (Array.isArray(res) ? res : []);
      const comp = getComponent("win_search", "search_results");
      comp?.render(results);
    }

    btn.addEventListener("click", runSearch);
    qInput.addEventListener("keydown", (e) => { if (e.key === "Enter") runSearch(); });
  }
}


// --- chat helpers ---
const escapeHtml = (s="") => s.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
const md = (s="") => (window.marked?.parse ? window.marked.parse(s) : escapeHtml(s).replaceAll("\n","<br>"));

// --- spawn Chat window ---
spawnWindow({
  id: "win_chat",
  window_type: "window_generic",   // no window_chat_ui in this framework
  title: "Assistant Chat",
  col: "right",
  unique: true,
  resizable: true,
  Elements: [
    { type: "text_area",  id: "chat_log",   rows: 14, value: "" },
    { type: "text_field", id: "chat_input", placeholder: "Type a message…" }
  ]
});


// ── Document Library helpers ──────────────────────────────────────────────
async function refreshDocs() {
  const data = await listDocuments();
  const docs = (data || []).map(d => ({ ...d, active: Store.isDocActive(d.id) }));
  const comp = getComponent("win_docs", "doc_list");
  comp?.render(docs);
}

async function handleUpload(files) {
  if (!files || !files.length) return;
  await uploadDocuments(files);
  document.getElementById("docs_upload")?.clear?.();
  await refreshDocs();
}

// ── Segments helpers ──────────────────────────────────────────────────────
let currentSource = null; // when you click a doc, we filter segments by its id/source

async function refreshSegments() {
  const segs = await listSegments(currentSource);
  const comp = getComponent("win_segments", "segment_list");
  comp?.render(segs || []);
}

async function openSegment(id) {
  const data = await getSegment(id);
  if (!data) return;
  spawnWindow({
    id: `seg_${id}`,
    window_type: "window_segment_view",
    title: data.source || "Segment",
    col: "right",
    unique: false,
    segment: data
  });
}

// ── Spawn windows ─────────────────────────────────────────────────────────
spawnWindow({
  id: "win_docs",
  window_type: "window_generic",
  title: "Document Library",
  col: "left",
  unique: true,
  resizable: true,
  Elements: [
    {
      type: "file_upload",
      id: "docs_upload",
      multiple: true,
      selectLabel: "Choose Files",
      buttonLabel: "Upload",
      onUpload: handleUpload,
    },
    {
      type: "item_list",
      id: "doc_list",
      label: "Documents",
      item_template: {
        elements: [
          { type: "text", bind: "title",   class: "li-title" },
          { type: "text", bind: "segments", class: "li-meta" },
          { type: "button", toggle: { prop: "active", on: "Deactivate", off: "Activate", action: "toggle_active" } },
          { type: "button", label: "Remove", action: "remove", variant: "danger" }
        ]
      }
    }
  ]
});

// replace the segments spawn block
spawnWindow({
  id: "win_segments",
  window_type: "window_generic",   // <- was "window_segments"
  title: "DB Segments",
  col: "right",
  unique: true,
  resizable: true,
  Elements: [
    {
      type: "item_list",
      id: "segment_list",
      label: "Segments",
      item_template: {
        elements: [
          { type: "text", bind: "source",  class: "li-title"  },
          { type: "text", bind: "priority", class: "li-meta"  },
          { type: "text", bind: "preview",  class: "li-subtle" },
          { type: "button", label: "Open",   action: "open"    },
          { type: "button", label: "Remove", action: "remove", variant: "danger" }
        ]
      }
    }
  ]
});

// ── Bus wiring ────────────────────────────────────────────────────────────
// Docs list row actions
bus.addEventListener("ui:list-action", async (ev) => {
  const { winId, elementId, action, item } = ev.detail || {};
  if (winId === "win_docs" && elementId === "doc_list") {
    if (action === "toggle_active") { Store.toggleDoc(item.id); await refreshDocs(); }
    if (action === "remove")        { try { await removeDocument(item.id); } finally { await refreshDocs(); } }
  }
});

// Docs list row selection -> filter Segments
bus.addEventListener("ui:list-select", async (ev) => {
  const { winId, elementId, item } = ev.detail || {};
  if (winId === "win_docs" && elementId === "doc_list") {
    currentSource = item?.id || null;   // you might prefer item.source depending on your backend
    await refreshSegments();
  }
});

// Segment list actions
bus.addEventListener("ui:list-action", async (ev) => {
  const { winId, elementId, action, item } = ev.detail || {};
  if (winId === "win_segments" && elementId === "segment_list") {
    if (action === "open")   await openSegment(item.id);
    if (action === "remove") { try { await removeSegment(item.id); } finally { await refreshSegments(); } }
  }
});

// --- chat wiring (generic window -> proper chat) ---
{
  const win   = document.getElementById("win_chat");
  const taRow = win?.querySelector("#chat_log")?.closest(".row");
  if (!win || !taRow) { /* window not mounted */ }
  else {
    // upgrade textarea to a div.log
    const log = document.createElement("div");
    log.id = "chat_log";
    log.className = "chat-log";
    taRow.replaceWith(log);

    // move input into a bar + add Send button
    const input    = win.querySelector("#chat_input");
    const inputRow = input?.closest(".row");
    const bar      = document.createElement("div");
    bar.className  = "chat-input";
    const btn      = document.createElement("button");
    btn.type = "button"; btn.className = "btn"; btn.textContent = "Send";
    if (inputRow) inputRow.replaceWith(bar);
    bar.append(input, btn);

    // helpers
    const escapeHtml = (s="") => s.replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;");
    const md = (s="") => (window.marked?.parse ? window.marked.parse(s) : escapeHtml(s).replaceAll("\n","<br>"));
    const pushUser = (text) => {
      const d = document.createElement("div");
      d.className = "msg you";
      d.innerHTML = "You: " + escapeHtml(text);
      log.appendChild(d); log.scrollTop = log.scrollHeight;
    };
    const pushAssistant = () => {
      const d = document.createElement("div");
      d.className = "msg assistant";
      d.innerHTML = "…";
      log.appendChild(d); log.scrollTop = log.scrollHeight;
      return d;
    };

    async function send() {
      const text = input.value.trim();
      if (!text) return;
      input.value = "";
      pushUser(text);
      const bubble = pushAssistant();

      // try streaming first; fallback to non-stream
      try {
        const { reader, decoder } = await chatStream({
          message: text,
          session_id: (Store?.sessionId ?? "") + "",
          persona: Store?.persona || "",
          inactive: Store?.inactiveList?.() || [],
        });
        let buf = "";
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          const chunks = buf.split("\n\n");  // naive SSE framing
          buf = chunks.pop();
          for (const chunk of chunks) {
            let event = "delta", data = "";
            for (const line of chunk.split("\n")) {
              if (line.startsWith("event:")) event = line.slice(6).trim();
              else if (line.startsWith("data:")) data += line.slice(5).trim();
            }
            if (event === "delta") bubble.innerHTML = md((bubble._acc ||= "") + data);
          }
          log.scrollTop = log.scrollHeight;
        }
      } catch {
        try {
          const res = await chat({
            message: text,
            session_id: (Store?.sessionId ?? "") + "",
            persona: Store?.persona || "",
            inactive: Store?.inactiveList?.() || [],
          });
          bubble.innerHTML = md(res.response ?? "(no response)");
        } catch (e2) {
          bubble.innerHTML = `<em>Error:</em> ${escapeHtml(e2.message)}`;
        }
      }
    }

    btn.addEventListener("click", send);
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") send(); });
  }
}


bus.addEventListener("ui:list-action", async (ev) => {
  const { winId, elementId, action, item } = ev.detail || {};
  // open from Search results
  if (winId === "win_search" && elementId === "search_results" && action === "open" && item?.id) {
    await openSegmentViewer(item.id);
  }
  // open from Segments list (reuse your existing handler if present)
  if (winId === "win_segments" && elementId === "segment_list" && action === "open" && item?.id) {
    await openSegmentViewer(item.id);
  }
});

// === ADD: when a doc is selected, refresh segments (assumes you have refreshSegments) ===
bus.addEventListener("ui:list-select", async (ev) => {
  const { winId, elementId, item } = ev.detail || {};
  if (winId === "win_docs" && elementId === "doc_list") {
    currentSource = item?.id || null;
    await refreshSegments();
  }
});


// ── Initial loads ─────────────────────────────────────────────────────────
await refreshDocs();
await refreshSegments();
