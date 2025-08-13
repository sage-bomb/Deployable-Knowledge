import { spawnWindow } from "../framework.js";
import { listDocuments, uploadDocuments, removeDocument } from "../sdk.js";
import { getComponent } from "/static/ui/js/components.js";
import { Store } from "../store.js";
import { moveLabelTop } from "../util.js";

export async function refreshDocs() {
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

export function createDocsWindow() {
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
        label: "Upload",
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
            { type: "text", bind: "title", class: "li-title" },
            { type: "text", bind: "segments", class: "li-meta" },
            { type: "button", toggle: { prop: "active", on: "Deactivate", off: "Activate", action: "toggle_active" } },
            { type: "button", label: "Remove", action: "remove", variant: "danger" }
          ]
        }
      }
    ]
  });
  const win = document.getElementById("win_docs");
  moveLabelTop(win?.querySelector("#docs_upload")?.closest(".row"));
  moveLabelTop(win?.querySelector("#doc_list")?.closest(".row"));
}

export async function handleDocAction(action, item) {
  if (action === "toggle_active") { Store.toggleDoc(item.id); await refreshDocs(); }
  if (action === "remove")        { try { await removeDocument(item.id); } finally { await refreshDocs(); } }
}
