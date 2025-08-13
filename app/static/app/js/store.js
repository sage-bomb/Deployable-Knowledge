// /app/store.js
const stored = localStorage.getItem("inactiveDocs");
const state = { inactiveDocs: new Set(stored ? JSON.parse(stored) : []) };

export const Store = {
  isDocActive(id) { return !state.inactiveDocs.has(id); },
  toggleDoc(id) {
    state.inactiveDocs.has(id) ? state.inactiveDocs.delete(id) : state.inactiveDocs.add(id);
    localStorage.setItem("inactiveDocs", JSON.stringify([...state.inactiveDocs]));
  }
};
