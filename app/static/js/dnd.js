// dnd.js — drag and drop between columns, minimize + close behavior

export function findDraggableWin(e) {
  const titlebar = e.target.closest(".titlebar");
  if (!titlebar) return null;
  if (e.target.closest(".actions") || e.target.closest(".icon-btn")) return null;
  return titlebar.closest(".miniwin");
}

export function calcDragPosition(winStart, pointerStart, e) {
  return {
    left: winStart.x + (e.clientX - pointerStart.x),
    top: winStart.y + (e.clientY - pointerStart.y),
  };
}

export function handleDrop(draggingWin, isModalDrag, columnsEl, cols, e, getDropColumnAt, dropMarker) {
  if (!isModalDrag) {
    const targetCol = dropMarker.parentNode || getDropColumnAt(e.clientX, e.clientY);
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
      if (dropMarker.parentNode === targetCol) {
        targetCol.insertBefore(draggingWin, dropMarker);
      } else {
        targetCol.appendChild(draggingWin);
      }
      if (dropMarker.parentNode) dropMarker.parentNode.removeChild(dropMarker);
      draggingWin.focus({ preventScroll: true });
    }
  } else {
    draggingWin.classList.remove("dragging");
    draggingWin.style.removeProperty("--drag-w");
  }
}

export function initWindowDnD() {
  const columnsEl = document.getElementById("columns");
  const cols = [...document.querySelectorAll(".col")];

  const dropMarker = document.createElement("div");
  dropMarker.className = "drop-marker";

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
    const win = findDraggableWin(e);
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
    const pos = calcDragPosition(winStart, pointerStart, e);
    draggingWin.style.left = `${pos.left}px`;
    draggingWin.style.top = `${pos.top}px`;

    if (!isModalDrag) {
      cols.forEach(c => c.classList.remove("drop-candidate"));
      const over = getDropColumnAt(e.clientX, e.clientY);
      if (over) {
        over.classList.add("drop-candidate");
        const siblings = [...over.querySelectorAll('.miniwin')].filter(w => w !== draggingWin);
        let inserted = false;
        for (const sib of siblings) {
          const rect = sib.getBoundingClientRect();
          if (e.clientY < rect.top + rect.height / 2) {
            over.insertBefore(dropMarker, sib);
            inserted = true;
            break;
          }
        }
        if (!inserted) over.appendChild(dropMarker);
      } else if (dropMarker.parentNode) {
        dropMarker.parentNode.removeChild(dropMarker);
      }
    }
  };

  const onUp = (e) => {
    if (!draggingWin) return;

    handleDrop(draggingWin, isModalDrag, columnsEl, cols, e, getDropColumnAt, dropMarker);

    document.removeEventListener("pointermove", onMove);
    draggingWin = null;
    isModalDrag = false;
  };

  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".js-min");
    if (!btn) return;
    const win = btn.closest(".miniwin");
    if (!win) return;
    if (!win.classList.contains("collapsed")) {
      win.dataset.prevHeight = win.style.height;
      win.style.height = '';
      win.classList.add("collapsed");
      btn.setAttribute("aria-pressed", "true");
    } else {
      win.classList.remove("collapsed");
      btn.setAttribute("aria-pressed", "false");
      if (win.dataset.prevHeight) {
        win.style.height = win.dataset.prevHeight;
        delete win.dataset.prevHeight;
      }
    }
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
