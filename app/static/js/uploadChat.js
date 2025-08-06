// Codex: Do NOT load backend or Python files. This file is frontend-only.
// uploadChat.js
import { $ } from './dom.js';

/**
 * Parses chat content in HTML format.
 * @param {string} content 
 * @returns {Array<Array<string>>} - Array of [userMessage, assistantMessage] pairs
 */
function parseChatHTML(content) {
    const history = [];
    let lastUser = null;
    const temp = document.createElement('div');
    temp.innerHTML = content;
    const divs = Array.from(temp.querySelectorAll('div'));
    divs.forEach(div => {
        const text = div.textContent.trim();
        if (text.startsWith('You:')) {
            lastUser = text.replace(/^You:\s*/, '');
        } else if (text.startsWith('Assistant:')) {
            if (lastUser !== null) {
                history.push([lastUser, text.replace(/^Assistant:\s*/, '')]);
                lastUser = null;
            }
        }
    });
    return history;
}

/**
 * Parses chat content in Markdown format.
 * @param {string} content 
 * @returns {Array<Array<string>>} - Array of [userMessage, assistantMessage] pairs
 */
function parseChatMarkdown(content) {
    const history = [];
    const lines = content.split(/\r?\n/);
    let lastRole = null;
    let userMsg = null;
    let assistantMsg = null;
    lines.forEach(line => {
        const text = line.trim();
        const userMatch = text.match(/^(\*\*|__)?You:(\*\*|__)?\s*/i);
        const assistantMatch = text.match(/^(\*\*|__)?Assistant:(\*\*|__)?\s*/i);
        if (userMatch) {
            if (userMsg !== null && assistantMsg !== null) {
                history.push([userMsg, assistantMsg]);
                userMsg = null;
                assistantMsg = null;
            }
            userMsg = text.replace(/^(\*\*|__)?You:(\*\*|__)?\s*/i, '');
            lastRole = 'user';
        } else if (assistantMatch) {
            assistantMsg = text.replace(/^(\*\*|__)?Assistant:(\*\*|__)?\s*/i, '');
            lastRole = 'assistant';
        } else if (text.length > 0) {
            if (lastRole === 'user' && userMsg !== null) {
                userMsg += '\n' + text;
            } else if (lastRole === 'assistant' && assistantMsg !== null) {
                assistantMsg += '\n' + text;
            }
        }
    });
    if (userMsg !== null && assistantMsg !== null) {
        history.push([userMsg, assistantMsg]);
    }
    return history;
}

/**
 * Parses chat content in plain text format.
 * @param {string} content 
 * @returns {Array<Array<string>>} - Array of [userMessage, assistantMessage] pairs
 */
function parseChatPlainText(content) {
    const history = [];
    const lines = content.split(/\r?\n/);
    let lastRole = null;
    let userMsg = null;
    let assistantMsg = null;
    lines.forEach(line => {
        const text = line.trim();
        const userMatch = text.match(/^You:\s*/i);
        const assistantMatch = text.match(/^Assistant:\s*/i);
        if (userMatch) {
            if (userMsg !== null && assistantMsg !== null) {
                history.push([userMsg, assistantMsg]);
                userMsg = null;
                assistantMsg = null;
            }
            userMsg = text.replace(/^You:\s*/i, '');
            lastRole = 'user';
        } else if (assistantMatch) {
            assistantMsg = text.replace(/^Assistant:\s*/i, '');
            lastRole = 'assistant';
        } else if (text.length > 0) {
            if (lastRole === 'user' && userMsg !== null) {
                userMsg += '\n' + text;
            } else if (lastRole === 'assistant' && assistantMsg !== null) {
                assistantMsg += '\n' + text;
            }
        }
    });
    if (userMsg !== null && assistantMsg !== null) {
        history.push([userMsg, assistantMsg]);
    }
    return history;
}

/**
 * Parses chat content in a specific format.
 * @param {string} content 
 * @param {string} fileType 
 * @returns {Array<Array<string>>} - Array of [userMessage, assistantMessage] pairs
 */
function parseChatHistory(content, fileType) {
    if (fileType === 'html' || fileType === 'htm') {
        return parseChatHTML(content);
    } else if (fileType === 'md' || fileType === 'markdown') {
        return parseChatMarkdown(content);
    } else {
        return parseChatPlainText(content);
    }
}

document.addEventListener("DOMContentLoaded", () => {
  const uploadBtn = $("upload-chat-btn");
  const fileInput = $("upload-chat-file");
  const chatBox = $("chat-box");

  if (!uploadBtn || !fileInput || !chatBox) return;

  uploadBtn.addEventListener("click", () => {
    fileInput.value = ""; // reset file input
    fileInput.click();
  });

  fileInput.addEventListener("change", (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async function(evt) {
      const content = evt.target.result;
      // Determine file type
      const ext = file.name.split('.').pop().toLowerCase();
      let isHTML = false;
      let isMarkdown = false;
      if (ext === 'html' || ext === 'htm') {
        isHTML = true;
      } else if (ext === 'md' || ext === 'markdown') {
        isMarkdown = true;
      }
      // For display: if HTML, render; if markdown, render as HTML using marked; else escape and show as <pre>
      if (isHTML) {
        chatBox.innerHTML = content;
      } else if (isMarkdown && window.marked) {
        chatBox.innerHTML = window.marked.parse(content);
      } else {
        chatBox.innerHTML = `<pre>${content.replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]))}</pre>`;
      }

      // For history, use specialized parser based on file type
      let history = parseChatHistory(content, ext);
      // Trim to last 20 turns
      if (history.length > 20) {
        history = history.slice(-20);
      }
      const userId = localStorage.getItem("user_id") || "guest";
      await fetch("/debug/memory", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId, history }),
      });
    };
    reader.readAsText(file);
  });
});
