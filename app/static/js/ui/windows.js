// ui/windows.js — initial window configs
export const windows = [
  { id: "win_docs",     window_type: "window_documents", title: "Document Library", col: "left",  unique: true },
  { id: "win_sessions", window_type: "window_sessions",  title: "Chat History",     col: "left",  unique: true },
  { id: "win_chat",     window_type: "window_chat_ui",   title: "Assistant Chat",   col: "right", unique: true },
  { id: "win_segments", window_type: "window_segments",  title: "DB Segments",      col: "right", unique: true }
];

export const windowTypes = {
  segmentView: "window_segment_view",
  promptEditor: "window_prompt_editor",
};
