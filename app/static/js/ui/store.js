// ui/store.js — central app state
const storedPersona = localStorage.getItem("persona") || "";
const storedDocs = localStorage.getItem("inactiveDocs");
const state = {
  sessionId: null,
  persona: storedPersona,
  inactiveDocs: new Set(storedDocs ? JSON.parse(storedDocs) : [])
};
export const Store = {
  get sessionId() { return state.sessionId; },
  set sessionId(v) { state.sessionId = v; },
  get persona() { return state.persona; },
  set persona(v) {
    state.persona = v;
    localStorage.setItem("persona", v);
  },
  isDocActive(id) { return !state.inactiveDocs.has(id); },
  toggleDoc(id) {
    state.inactiveDocs.has(id) ? state.inactiveDocs.delete(id) : state.inactiveDocs.add(id);
    localStorage.setItem("inactiveDocs", JSON.stringify(Array.from(state.inactiveDocs)));
  },
  inactiveList() { return Array.from(state.inactiveDocs); }
};
