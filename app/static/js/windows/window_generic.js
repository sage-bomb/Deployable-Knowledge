import { el, Field, fieldRow } from "../ui.js";
import { createItemList } from "../components.js";

export function render(config, winId) {
  const form = el("form", { class: "form", autocomplete: "off" });
  (config.Elements || []).forEach((e, idx) => {
    const baseId = e.id || (e.name ? e.name.toLowerCase().replace(/\s+/g, "_") : `field_${idx+1}`);
    const id = `${baseId}`;
    const label = e.label || e.name || baseId;

    if (e.type === "item_list") {
      const listEl = createItemList(config.id || winId, { ...e, id });
      const row = el("div", { class: "row" }, [
        el("label", {}, [label]),
        listEl
      ]);
      form.appendChild(row);
      return;
    }

    const input = Field.create({ ...e, id });
    form.appendChild(fieldRow(id, label, input));
  });
  return form;
}
