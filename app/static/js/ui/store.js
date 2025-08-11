// ui/store.js — central app state
const state = { sessionId: null, persona: "", inactiveDocs: new Set() };
export const Store = {
  get sessionId() { return state.sessionId; },
  set sessionId(v) { state.sessionId = v; },
  get persona() { return state.persona; },
  set persona(v) { state.persona = v; },
  isDocActive(id) { return !state.inactiveDocs.has(id); },
  toggleDoc(id) { state.inactiveDocs.has(id) ? state.inactiveDocs.delete(id) : state.inactiveDocs.add(id); },
  inactiveList() { return Array.from(state.inactiveDocs); }
};
