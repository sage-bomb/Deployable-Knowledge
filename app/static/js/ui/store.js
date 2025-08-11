// ui/store.js — central app state
const storedPersona = localStorage.getItem("persona") || "";
const storedDocs = localStorage.getItem("inactiveDocs");
const storedSettings = JSON.parse(localStorage.getItem("settings") || "{}");
const state = {
  sessionId: null,
  persona: storedPersona,
  inactiveDocs: new Set(storedDocs ? JSON.parse(storedDocs) : []),
  llmTargetAddress: storedSettings.llm_target_address || "",
  llmToken: storedSettings.llm_token || "",
  lastQuery: "",
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
  inactiveList() { return Array.from(state.inactiveDocs); },
  get llmTargetAddress() { return state.llmTargetAddress; },
  set llmTargetAddress(v) {
    state.llmTargetAddress = v;
    saveSettings();
  },
  get llmToken() { return state.llmToken; },
  set llmToken(v) {
    state.llmToken = v;
    saveSettings();
  },
  get lastQuery() { return state.lastQuery; },
  set lastQuery(v) { state.lastQuery = v; },
};

function saveSettings() {
  localStorage.setItem("settings", JSON.stringify({
    llm_target_address: state.llmTargetAddress,
    llm_token: state.llmToken
  }));
}
