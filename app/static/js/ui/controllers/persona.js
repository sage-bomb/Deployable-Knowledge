// ui/controllers/persona.js — persona modal
import { createMiniWindowFromConfig } from "../../window.js";
import { Store } from "../store.js";

export function openPersonaModal() {
  const cfg = {
    id: `win_persona_${crypto.randomUUID().slice(0,6)}`,
    window_type: "window_persona",
    title: "Persona",
    modal: true,
    value: Store.persona || ""
  };
  const win = createMiniWindowFromConfig(cfg);

  const wrap = document.createElement("div");
  wrap.className = "modal-wrap";
  const back = document.createElement("div");
  back.className = "modal-backdrop";
  wrap.append(back, win);
  document.body.appendChild(wrap);

  const textarea = win.querySelector("#persona_text");
  const saveBtn = win.querySelector(".js-persona-save");
  saveBtn?.addEventListener("click", () => {
    Store.persona = textarea?.value || "";
    wrap.remove();
  });
}
