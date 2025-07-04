// state.js — manages toggle state for document sources

const toggleStates = {};

export function setToggle(id, value) {
  toggleStates[id] = value;
}

export function getToggle(id) {
  return toggleStates[id] ?? true; // default to active
}

export function getInactiveIds() {
  return Object.entries(toggleStates)
    .filter(([_, isActive]) => isActive === false)
    .map(([id]) => id);
}

export function initToggleState(id, initialValue = true) {
  toggleStates[id] = initialValue;
}
