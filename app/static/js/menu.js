// menu.js — simple dropdown menu
export function initMenu(onAction, triggerId="menu-trigger", dropdownId="menu-dropdown") {
  const trigger = document.getElementById(triggerId);
  const dropdown = document.getElementById(dropdownId);
  if (!trigger || !dropdown) return;

  function open() {
    dropdown.classList.add("open");
    trigger.setAttribute("aria-expanded", "true");
    dropdown.setAttribute("aria-hidden", "false");
  }
  function close() {
    dropdown.classList.remove("open");
    trigger.setAttribute("aria-expanded", "false");
    dropdown.setAttribute("aria-hidden", "true");
  }

  trigger.addEventListener("click", (e) => {
    e.stopPropagation();
    if (dropdown.classList.contains("open")) close(); else open();
  });

  document.addEventListener("click", (e) => {
    if (!dropdown.contains(e.target) && e.target !== trigger) close();
  });

  dropdown.addEventListener("click", (e) => {
    const item = e.target.closest(".menu-item");
    if (!item) return;
    const action = item.getAttribute("data-action");
    close();
    if (action && onAction) onAction(action);
  });
}
