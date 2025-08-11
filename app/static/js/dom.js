const cache = new Map();

export function qs(selector) {
  if (cache.has(selector)) {
    return cache.get(selector);
  }
  const el = document.querySelector(selector);
  if (el) {
    cache.set(selector, el);
  }
  return el;
}
