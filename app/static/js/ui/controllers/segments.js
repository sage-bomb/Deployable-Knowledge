// ui/controllers/segments.js — list database segments
import { dkClient as api } from "../sdk/sdk.js";
import { getComponent, bus } from "../../components.js";

export async function initSegmentsController(winId="win_segments") {
  const refresh = async () => {
    const segs = await api.listSegments();
    const comp = getComponent(winId, "segment_list");
    if (comp) comp.render(segs);
  };
  await refresh();

  bus.addEventListener("ui:list-action", async (ev) => {
    const { winId: srcWin, elementId, action, item } = ev.detail || {};
    if (srcWin !== winId || elementId !== "segment_list") return;
    if (action === "remove") {
      try { await api.removeSegment(item.id); } finally { await refresh(); }
    }
  });
}
