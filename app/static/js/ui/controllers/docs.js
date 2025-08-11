// ui/controllers/docs.js — document list: refresh + upload + actions
import * as api from "../api.js";
import { getComponent, bus } from "../../components.js";
import { Store } from "../store.js";

export async function initDocsController(winId="win_docs") {
  const controller = new AbortController();
  const win = document.getElementById(winId);
  win?.addEventListener("DOMNodeRemoved", (e) => {
    if (e.target === win) controller.abort();
  }, { once: true });

  const refresh = async () => {
    const docs = await api.listDocuments();
    const comp = getComponent(winId, "doc_list");
    if (comp) comp.render(docs.map(d => ({ ...d, active: Store.isDocActive(d.id) })));
  };
  await refresh();

  bus.addEventListener("ui:list-action", async (ev) => {
    const { winId: srcWin, elementId, action, item } = ev.detail || {};
    if (elementId !== "doc_list" || srcWin !== winId) return;
    if (action === "toggle_active") { Store.toggleDoc(item.id); await refresh(); }
    if (action === "remove")        { try { await api.removeDocument(item.id); } finally { await refresh(); } }
  }, { signal: controller.signal });

  const input = win?.querySelector(`#${winId}-upload`);
  const btn   = win?.querySelector(`#${winId}-upload-btn`);
  btn?.addEventListener("click", async () => {
    if (!input?.files?.length) return;
    btn.disabled = true; btn.textContent = "Uploading…";
    try { await api.uploadDocuments(input.files); input.value = ""; await refresh(); }
    catch (e) { alert("Upload failed: " + e.message); }
    finally { btn.disabled = false; btn.textContent = "Upload"; }
  }, { signal: controller.signal });
}
