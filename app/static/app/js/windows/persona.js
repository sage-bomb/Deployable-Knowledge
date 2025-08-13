import { spawnWindow } from "../framework.js";
import { Store } from "../store.js";

export function openPersonaEditor() {
  if (document.getElementById("modal_persona")) return;
  spawnWindow({
    id: "modal_persona",
    window_type: "window_generic",
    title: "Persona",
    modal: true,
    unique: true,
    resizable: false,
    Elements: [
      { type: "text_area", id: "persona_text", rows: 6, value: Store.persona || "" },
      { type: "button", id: "persona_save", label: "Save" }
    ]
  });
  const modal = document.getElementById("modal_persona");
  modal.querySelector("#persona_save")?.addEventListener("click", () => {
    const val = modal.querySelector("#persona_text")?.value || "";
    Store.persona = val;
    modal.remove();
  });
}
