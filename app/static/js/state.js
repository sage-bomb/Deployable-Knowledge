// state.js — manages toggle state for document sources

const toggleStates = {};

/**
 * Sets the toggle state for a document source.
 * @param {string} id 
 * @param {boolean} value 
 */
export function setToggle(id, value) {
  toggleStates[id] = value;
}

/**
 * Gets the toggle state for a document source.
 * @param {string} id 
 * @returns {boolean}
 */
export function getToggle(id) {
  return toggleStates[id] ?? true; // default to active
}

/**
 * Gets the IDs of all inactive document sources.
 * @returns {Array<string>} - Array of inactive document IDs
 */
export function getInactiveIds() {
  return Object.entries(toggleStates)
    .filter(([_, isActive]) => isActive === false)
    .map(([id]) => id);
}

/**
 * Initializes the toggle state for a document source.
 * @param {string} id 
 * @param {boolean} initialValue 
 */
export function initToggleState(id, initialValue = true) {
  toggleStates[id] = initialValue;
}
