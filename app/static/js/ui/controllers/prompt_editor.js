// ui/controllers/prompt_editor.js — manage prompt templates
import { dkClient as api } from "../sdk/sdk.js";
import { createMiniWindowFromConfig } from "../../window.js";

function showToast(msg) {
  const t = document.createElement("div");
  t.className = "toast";
  t.textContent = msg;
  document.body.appendChild(t);
  requestAnimationFrame(() => t.classList.add("show"));
  setTimeout(() => t.remove(), 2000);
}

export async function openPromptEditor() {
  const existing = document.getElementById("win_prompt_editor");
  if (existing) return;
  const cfg = { id: "win_prompt_editor", window_type: "window_prompt_editor", title: "Prompt Templates", col: "right" };
  const node = createMiniWindowFromConfig(cfg);
  node.style.minWidth = "480px";
  document.getElementById("col-right").appendChild(node);

  const sel = node.querySelector("#tmpl_select");
  const textarea = node.querySelector("#tmpl_text");
  const saveBtn = node.querySelector("#tmpl_save");

  async function loadList() {
    const arr = await api.listPromptTemplates();
    sel.innerHTML = "";
    for (const t of arr) {
      const opt = document.createElement("option");
      opt.value = t.id;
      opt.textContent = t.name || t.id;
      sel.appendChild(opt);
    }
    if (arr.length) {
      await loadTemplate(arr[0].id);
      sel.value = arr[0].id;
    }
  }

  async function loadTemplate(id) {
    const data = await api.getPromptTemplate(id);
    textarea.value = JSON.stringify(data, null, 2);
  }

  sel.addEventListener("change", () => loadTemplate(sel.value));

  saveBtn.addEventListener("click", async () => {
    try {
      const obj = JSON.parse(textarea.value);
      for (const f of ["id", "name", "user_format", "system"]) {
        if (!Object.prototype.hasOwnProperty.call(obj, f)) {
          alert(`Missing field: ${f}`);
          return;
        }
      }
      await api.savePromptTemplate(obj.id, obj);
      textarea.value = JSON.stringify(obj, null, 2);
      showToast("Saved");
      await loadList();
      sel.value = obj.id;
    } catch (e) {
      alert("Invalid JSON: " + e.message);
    }
  });

  await loadList();
}
