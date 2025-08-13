import { spawnWindow } from "../framework.js";
import { listSegments, getSegment, removeSegment } from "../sdk.js";
import { getComponent } from "/static/ui/js/components.js";
import { md, htmlEscape } from "../util.js";

let currentSource = null;

export function setSegmentsSource(id) {
  currentSource = id || null;
}

export async function refreshSegments() {
  const segs = await listSegments(currentSource);
  const comp = getComponent("win_segments", "segment_list");
  comp?.render(segs || []);
}

export function createSegmentsWindow() {
  spawnWindow({
    id: "win_segments",
    window_type: "window_generic",
    title: "DB Segments",
    col: "right",
    unique: true,
    resizable: true,
    Elements: [
      {
        type: "item_list",
        id: "segment_list",
        item_template: {
          elements: [
            { type: "text", bind: "source",  class: "li-title" },
            { type: "text", bind: "priority", class: "li-meta"  },
            { type: "text", bind: "preview",  class: "li-subtle" },
            { type: "button", label: "Open",   action: "open" },
            { type: "button", label: "Remove", action: "remove", variant: "danger" }
          ]
        }
      }
    ]
  });
}

export async function handleSegmentAction(action, item) {
  if (action === "open")   await openSegmentViewer(item.id);
  if (action === "remove") { try { await removeSegment(item.id); } finally { await refreshSegments(); } }
}

export async function openSegmentViewer(id) {
  const seg = await getSegment(id);
  const winId = `seg_view_${id}`;
  spawnWindow({
    id: winId,
    window_type: "window_generic",
    title: seg?.source ? `Segment • ${seg.source}` : "Segment",
    col: "right",
    unique: false,
    resizable: true,
    Elements: [
      { type: "text", id: "seg_meta", value: "" },
      { type: "text", id: "seg_text", value: "" }
    ]
  });
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
      </div>`;
  }
  if (bodyRow) {
    const viewer = document.createElement("div");
    viewer.className = "segment-view prose";
    viewer.innerHTML = md(seg.text || seg.preview || "(empty)");
    bodyRow.replaceWith(viewer);
  }
}
