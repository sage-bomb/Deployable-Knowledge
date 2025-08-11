// ui/controllers/settings.js — settings modal
import { createMiniWindowFromConfig, mountModal } from "../../window.js";
import { Store } from "../store.js";

export function openSettingsModal() {
  const cfg = {
    id: `win_settings_${crypto.randomUUID().slice(0,6)}`,
    window_type: "window_generic",
    title: "Settings",
    modal: true,
    Elements: [
      { type: "text_field", label: "LLM Target Address", id: "llm_target_address", value: Store.llmTargetAddress || "" },
      { type: "text_field", label: "llm_api_token", id: "llm_api_token", placeholder: "Optional", value: Store.llmToken || "" }
    ]
  };
  const win = createMiniWindowFromConfig(cfg);
  const wrap = mountModal(win);
  const save = document.createElement("button");
  save.className = "btn js-settings-save";
  save.type = "button";
  save.textContent = "Save";
  win.querySelector(".form")?.appendChild(save);
  save.addEventListener("click", () => {
    const addr = win.querySelector("#llm_target_address")?.value || "";
    const tok = win.querySelector("#llm_api_token")?.value || "";
    Store.llmTargetAddress = addr;
    Store.llmToken = tok;
    wrap.remove();
  });
  return win;
}
