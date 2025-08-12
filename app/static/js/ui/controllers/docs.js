// ui/controllers/docs.js — document list: refresh + upload + actions
import { dkClient as api } from "../sdk/sdk.js";
import { getComponent, bus } from "../../components.js";
import { Store } from "../store.js";
import { qs } from "../../dom.js";
import { el } from "../../ui.js";

export async function initDocsController(winId="win_docs") {
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
  });

  bus.addEventListener("ui:list-select", (ev) => {
    const { winId: srcWin, elementId, item } = ev.detail || {};
    if (srcWin !== winId || elementId !== "doc_list") return;
    bus.dispatchEvent(new CustomEvent("docs:select", { detail: { id: item.id } }));
  });

  const win = qs(`#${winId}`);
  const input  = win?.querySelector(`#${winId}-upload`);
  const choose = win?.querySelector(`#${winId}-choose-btn`);
  const list   = win?.querySelector(`#${winId}-upload-list`);
  const btn    = win?.querySelector(`#${winId}-upload-btn`);

  choose?.addEventListener("click", () => input?.click());

  input?.addEventListener("change", () => {
    if (!list) return;
    list.innerHTML = "";
    for (const f of input.files) {
      list.appendChild(el("li", {}, [f.name]));
    }
  });

  btn?.addEventListener("click", async () => {
    if (!input?.files?.length) return;
    btn.disabled = true; btn.textContent = "Uploading…";
    try {
      await api.uploadDocuments(input.files);
      input.value = "";
      if (list) list.innerHTML = "";
      await refresh();
    }
    catch (e) { alert("Upload failed: " + e.message); }
    finally { btn.disabled = false; btn.textContent = "Upload"; }
  });
}
