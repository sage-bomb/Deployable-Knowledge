// ui/controllers/settings.js — settings modal
import { createMiniWindowFromConfig, mountModal } from "../../window.js";
import { dkClient as api } from "../sdk/sdk.js";

export async function openSettingsModal() {
  const user = await api.getUser();
  const userId = user?.user || "default";
  const [settings, prompts] = await Promise.all([
    api.getSettings(userId),
    api.listPromptTemplates()
  ]);

  const promptOptions = [{ value: "", label: "(default)" }];
  for (const t of prompts) {
    promptOptions.push({ value: t.id, label: t.name || t.id });
  }

  const cfg = {
    id: `win_settings_${crypto.randomUUID().slice(0,6)}`,
    window_type: "window_generic",
    title: "Settings",
    modal: true,
    Elements: [
      {
        type: "select",
        label: "LLM Provider",
        id: "llm_provider",
        options: [
          { value: "ollama", label: "Ollama" },
          { value: "openai", label: "OpenAI" },
        ],
        value: settings.llm_provider
      },
      { type: "text_field", label: "LLM Model", id: "llm_model", value: settings.llm_model || "" },
      { type: "select", label: "Prompt Template", id: "prompt_template_id", options: promptOptions, value: settings.prompt_template_id || "" }
    ]
  };
  const win = createMiniWindowFromConfig(cfg);
  const wrap = mountModal(win);
  const save = document.createElement("button");
  save.className = "btn js-settings-save";
  save.type = "button";
  save.textContent = "Save";
  win.querySelector(".form")?.appendChild(save);
  save.addEventListener("click", async () => {
    const payload = {
      llm_provider: win.querySelector("#llm_provider")?.value,
      llm_model: win.querySelector("#llm_model")?.value,
      prompt_template_id: win.querySelector("#prompt_template_id")?.value || null,
    };
    await api.patchSettings(userId, payload);
    wrap.remove();
  });
  return win;
}
