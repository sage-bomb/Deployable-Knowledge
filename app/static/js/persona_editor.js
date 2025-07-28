// persona_editor.js
import { $ } from './dom.js';

/**
 * Initializes the persona modal functionality.
 * Sets up event listeners for opening, closing, and saving the persona.
 */
export function initPersonaModal() {
  const modal = $("persona-modal");
  const openBtn = $("open-persona-btn");
  const closeBtn = $("close-persona-btn");
  const saveBtn = $("save-persona-btn");
  const input = $("persona-text");

  openBtn?.addEventListener("click", () => {
    const saved = localStorage.getItem("chatPersona") || "";
    input.value = saved;
    modal.classList.remove("hidden");
    modal.style.display = "flex"; // this is what was missing
  });

  closeBtn?.addEventListener("click", () => {
    modal.classList.add("hidden");
    modal.style.display = "none";
  });

  saveBtn?.addEventListener("click", () => {
    localStorage.setItem("chatPersona", input.value.trim());
    modal.classList.add("hidden");
    modal.style.display = "none";
  });
}
