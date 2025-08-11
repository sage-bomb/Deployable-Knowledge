// Utilities for reading and writing CSS variables and applying saved themes

export function getVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name);
}

export function setVar(name, value) {
  document.documentElement.style.setProperty(name, value);
}

// Apply theme settings from an object, JSON string or localStorage
export function applyThemeSettings(source) {
  let settings = source;

  if (!settings) {
    try {
      const stored = localStorage.getItem("theme");
      if (stored) settings = JSON.parse(stored);
    } catch (e) {
      settings = null;
    }
  } else if (typeof settings === "string") {
    try {
      settings = JSON.parse(settings);
    } catch (e) {
      settings = null;
    }
  }

  if (!settings) return;

  Object.entries(settings).forEach(([key, value]) => {
    setVar(`--${key}`, value);
  });
}

