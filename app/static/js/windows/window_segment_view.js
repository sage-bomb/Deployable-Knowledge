import { el } from "../ui.js";
import { md } from "../ui/render.js";

export function render(config, winId) {
  const seg = config.segment || {};
  const wrap = el("div", { class: "form segment-view" });
  const metaTop = el("div", { class: "row" }, [
    el("label", {}, ["Source"]),
    el("span", { class: "li-subtle" }, [
      `${seg.source || ""}${seg.page != null ? `, p.${seg.page}` : ""}`
    ])
  ]);
  const metaDates = el("div", { class: "row" }, [
    el("label", {}, ["Dates"]),
    el("span", { class: "li-subtle" }, [
      `${seg.created_at || ""}${seg.updated_at ? ` • ${seg.updated_at}` : ""}`
    ])
  ]);
  const tags = el("div", { class: "row" }, [
    el("label", {}, ["Tags"]),
    el("span", { class: "li-subtle" }, [(seg.tags || []).join(", ")])
  ]);
  const body = el("div", { class: "segment-text" });
  body.innerHTML = md(seg.text || "");
  wrap.append(metaTop, metaDates, tags, body);
  return wrap;
}
