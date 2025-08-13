// /app/store.js
const stored = localStorage.getItem("inactiveDocs");
const state = {
  inactiveDocs: new Set(stored ? JSON.parse(stored) : []),
  sessionId: null,
  persona: localStorage.getItem("persona") || "",
};

export const Store = {
  get sessionId() { return state.sessionId; },
  set sessionId(id) { state.sessionId = id; },
  get persona() { return state.persona; },
  set persona(p) { state.persona = p; localStorage.setItem("persona", p); },
  inactiveList() { return [...state.inactiveDocs]; },
  isDocActive(id) { return !state.inactiveDocs.has(id); },
  toggleDoc(id) {
    state.inactiveDocs.has(id) ? state.inactiveDocs.delete(id) : state.inactiveDocs.add(id);
    localStorage.setItem("inactiveDocs", JSON.stringify([...state.inactiveDocs]));
  },
};
