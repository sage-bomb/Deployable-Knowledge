// dnd.js — drag and drop between columns, minimize + close behavior
export function initWindowDnD() {
  const columnsEl = document.getElementById("columns");
  const cols = [...document.querySelectorAll(".col")];

  let draggingWin = null;
  let isModalDrag = false;
  let winStart = { x: 0, y: 0 };
  let pointerStart = { x: 0, y: 0 };

  const getDropColumnAt = (x, y) => {
    const els = document.elementsFromPoint(x, y);
    const hit = els.find(el => el.classList && el.classList.contains("col"));
    return hit || null;
  };

  const onTitlebarDown = (e) => {
    const titlebar = e.target.closest(".titlebar");
    if (!titlebar) return;

    if (e.target.closest(".actions") || e.target.closest(".icon-btn")) return;

    const win = titlebar.closest(".miniwin");
    if (!win) return;

    draggingWin = win;
    isModalDrag = win.classList.contains("modal");
    draggingWin.classList.add("dragging");
    if (!isModalDrag) columnsEl.classList.add("dragging");

    const rect = win.getBoundingClientRect();
    draggingWin.style.setProperty("--drag-w", `${rect.width}px`);
    winStart = { x: rect.left, y: rect.top };
    pointerStart = { x: e.clientX, y: e.clientY };

    if (!isModalDrag) {
      Object.assign(draggingWin.style, { left: `${rect.left}px`, top: `${rect.top}px` });
    }

    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp, { once: true });
  };

  const onMove = (e) => {
    if (!draggingWin) return;
    const dx = e.clientX - pointerStart.x;
    const dy = e.clientY - pointerStart.y;
    draggingWin.style.left = `${winStart.x + dx}px`;
    draggingWin.style.top = `${winStart.y + dy}px`;

    if (!isModalDrag) {
      cols.forEach(c => c.classList.remove("drop-candidate"));
      const over = getDropColumnAt(e.clientX, e.clientY);
      if (over) over.classList.add("drop-candidate");
    }
  };

  const onUp = (e) => {
    if (!draggingWin) return;

    if (!isModalDrag) {
      const targetCol = getDropColumnAt(e.clientX, e.clientY);
      cols.forEach(c => c.classList.remove("drop-candidate"));
      columnsEl.classList.remove("dragging");

      draggingWin.classList.remove("dragging");
      draggingWin.style.left = "";
      draggingWin.style.top = "";
      draggingWin.style.removeProperty("--drag-w");
      draggingWin.style.position = "";
      draggingWin.style.width = "";
      draggingWin.style.pointerEvents = "";

      if (targetCol) {
        targetCol.appendChild(draggingWin);
        draggingWin.focus({ preventScroll: true });
      }
    } else {
      draggingWin.classList.remove("dragging");
      draggingWin.style.removeProperty("--drag-w");
    }

    document.removeEventListener("pointermove", onMove);
    draggingWin = null;
    isModalDrag = false;
  };

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".js-min");
    if (!btn) return;
    const win = btn.closest(".miniwin");
    if (!win) return;
    const collapsed = win.classList.toggle("collapsed");
    btn.setAttribute("aria-pressed", String(collapsed));
  });

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".js-close");
    if (!btn) return;
    const win = btn.closest(".miniwin");
    if (!win) return;
    if (win.classList.contains("modal")) {
      const wrap = win.closest(".modal-wrap");
      if (wrap) wrap.remove(); else win.remove();
    } else {
      win.remove();
    }
  });

  document.addEventListener("pointerdown", onTitlebarDown, { passive: true });
}
