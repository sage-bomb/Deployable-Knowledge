// /static/ui/js/framework.js
import { initWindowDnD } from "/static/ui/js/dnd.js";
import { initSplitter } from "/static/ui/js/splitter.js";
import { createMiniWindowFromConfig, initWindowResize, mountModal } from "/static/ui/js/window.js";

export function initFramework() {
  initSplitter();
  initWindowDnD();
  initWindowResize();
}

export function spawnWindow(cfg) {
  const node = createMiniWindowFromConfig(cfg);
  if (cfg.modal) {
    mountModal(node, { fade: cfg.modalFade !== false });
  } else {
    const col = document.getElementById(cfg.col === "right" ? "col-right" : "col-left");
    col.appendChild(node);
  }
  return node;
}
