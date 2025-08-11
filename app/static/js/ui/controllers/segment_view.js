// ui/controllers/segment_view.js — open single segment viewer
import { dkClient as api } from "../sdk/sdk.js";
import { createMiniWindowFromConfig } from "../../window.js";

export async function openSegmentView(id) {
  const data = await api.getSegment(id);
  if (!data) return;
  const cfg = {
    id: `seg_${id}`,
    window_type: "window_segment_view",
    title: data.source || "Segment",
    col: "right",
    segment: data,
  };
  const node = createMiniWindowFromConfig(cfg);
  document.getElementById("col-right").appendChild(node);
}
