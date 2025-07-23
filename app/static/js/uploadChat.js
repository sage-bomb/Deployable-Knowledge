// uploadChat.js
import { $ } from './dom.js';

function parseChatHTML(html) {

    const temp = document.createElement('div');
    temp.innerHTML = html;
    const divs = Array.from(temp.querySelectorAll('div'));
    const history = [];
    let lastUser = null;
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
      const html = evt.target.result;
      chatBox.innerHTML = html;

      let history = parseChatHTML(html);
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
