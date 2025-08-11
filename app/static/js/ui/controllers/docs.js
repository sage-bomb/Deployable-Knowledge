// ui/controllers/docs.js — document list: refresh + upload + actions
import * as api from "../api.js";
import { getComponent, bus } from "../../components.js";
import { Store } from "../store.js";

export async function initDocsController(winId="win_docs") {
  const refresh = async () => {
    try {
      const docs = await api.listDocuments();
      const comp = getComponent(winId, "doc_list");
      if (comp) comp.render(docs.map(d => ({ ...d, active: Store.isDocActive(d.id) })));
    } catch (e) {
      api.handleApiError(e);
    }
  };
  await refresh();

  bus.addEventListener("ui:list-action", async (ev) => {
    const { winId: srcWin, elementId, action, item } = ev.detail || {};
    if (elementId !== "doc_list" || srcWin !== winId) return;
    if (action === "toggle_active") { Store.toggleDoc(item.id); await refresh(); }
    if (action === "remove") {
      try { await api.removeDocument(item.id); }
      catch (e) { api.handleApiError(e); }
      finally { await refresh(); }
    }
  });

  const win = document.getElementById(winId);
  const input = win?.querySelector(`#${winId}-upload`);
  const btn   = win?.querySelector(`#${winId}-upload-btn`);
  btn?.addEventListener("click", async () => {
    if (!input?.files?.length) return;
    btn.disabled = true; btn.textContent = "Uploading…";
    try { await api.uploadDocuments(input.files); input.value = ""; await refresh(); }
    catch (e) { api.handleApiError(e); }
    finally { btn.disabled = false; btn.textContent = "Upload"; }
  });
}
