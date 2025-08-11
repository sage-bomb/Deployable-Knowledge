// splitter.js — resizable columns
export function initSplitter() {
  const columns = document.getElementById("columns");
  const splitter = document.getElementById("splitter");
  const left = document.getElementById("col-left");
  const right = document.getElementById("col-right");

  let dragging = false, startX = 0, leftStartWidth = 0;

  const onDown = (e) => {
    dragging = true;
    splitter.classList.add("dragging");
    startX = e.clientX;
    leftStartWidth = left.getBoundingClientRect().width;
    document.addEventListener("pointermove", onMove);
    document.addEventListener("pointerup", onUp, { once: true });
  };

  const onMove = (e) => {
    if (!dragging) return;
    const dx = e.clientX - startX;
    const newLeft = Math.max(200, leftStartWidth + dx);
    const total = columns.clientWidth - splitter.clientWidth;
    const maxLeft = total - 200;
    const clamped = Math.min(maxLeft, newLeft);
    left.style.flex = `0 0 ${clamped}px`;
    right.style.flex = `1 1 auto`;
  };

  const onUp = () => {
    dragging = false;
    splitter.classList.remove("dragging");
    document.removeEventListener("pointermove", onMove);
  };

  splitter.addEventListener("pointerdown", onDown);
}
