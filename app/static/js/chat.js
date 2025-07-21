// chat.js

import { $, escapeHtml } from './dom.js';
import { getInactiveIds } from './state.js';
import { renderSearchResultsBlock } from './render.js';

function getUserId() {
  let userId = localStorage.getItem("user_id");
  if (!userId) {
    userId = "guest-" + Math.random().toString(36).substring(2, 10);
    localStorage.setItem("user_id", userId);
  }
  return userId;
}

export function initChat() {
  //console.log("✅ initChat called");

  const chatForm = $("chat-form");
  const chatInput = $("user-input");
  const chatBox = $("chat-box");
  const docLimitInput = $("doc-limit");
  const submitButton = $("submit-button");
  const clearButton = $("clear-history");

  // console.log("chatForm:", chatForm);
  // console.log("chatInput:", chatInput);
  // console.log("submitButton:", submitButton)

  chatForm.addEventListener("submit", async function (e) {
    //console.log("Chat form submitted and fired");
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    //Disabling inputs
    chatInput.disabled = true;
    submitButton.disabled = true;
    submitButton.textContent = "Loading...";

    //Clearing input
    chatInput.value = '';

    chatBox.innerHTML += `<br><div><strong>You:</strong> ${escapeHtml(msg)}</div>`;
    const botMsg = document.createElement("div");
    botMsg.innerHTML = ``;
    chatBox.appendChild(botMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    // === Run context search BEFORE clearing the input ===
    try {
      const searchLimit = $("search-doc-limit")?.value || 5;
      const contextResponse = await fetch(`/search?q=${encodeURIComponent(msg)}&top_k=${searchLimit}`);
      const contextData = await contextResponse.json();

      if (contextData?.results?.length) {
        const searchResults = $("search-results");
        searchResults.innerHTML = `
          <h3>RAG Context Used:</h3>
          ${renderSearchResultsBlock(contextData.results)}
        `;
      }
    } catch (err) {
      console.error("Context search failed", err);
    }

  clearButton.addEventListener("click", function() {
    clearButton.disabled = true;

    chatBox.innerHTML = "";

    clearButton.disabled = false;
    chatInput.focus();
  })

  const persona = $("persona-text")?.value || "";
  
  const userId = getUserId();
  console.log(userId);

  const response = await fetch("/chat-stream", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      message: msg,
      persona,
      user_id: userId
    })
  });

    if (!response.body) {
      botMsg.innerHTML += "<em>No response body</em>";
      return;
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      botMsg.innerHTML = `<br>${window.marked.parse(buffer)}`;
      chatBox.scrollTop = chatBox.scrollHeight;
    }

    chatInput.disabled = false;
    submitButton.disabled = false;
    submitButton.textContent = "Send";
    chatInput.focus();
  });
}


// export function initChat() {
//   const chatForm = $("chat-form");
//   const chatInput = $("user-input");
//   const chatBox = $("chat-box");
//   const searchResults = $("search-results");

//   chatForm.addEventListener("submit", async function (e) {
//     e.preventDefault();
//     const msg = chatInput.value.trim();
//     if (!msg) return;

//     const inactive = getInactiveIds();
//     chatBox.innerHTML += `<div><strong>You:</strong> ${escapeHtml(msg)}</div>`;

//     const botMsg = document.createElement("div");
//     botMsg.innerHTML = `<strong>Assistant:</strong><em> Thinking...</em>`;
//     chatBox.appendChild(botMsg);
//     chatBox.scrollTop = chatBox.scrollHeight;

//     // === Step 1: Fetch search context ===
//     try {
//       const searchRes = await fetch(`/search?q=${encodeURIComponent(msg)}`);
//       const data = await searchRes.json();
//       if (Array.isArray(data.results)) {
//         searchResults.innerHTML = `
//           <h3>RAG Context Used:</h3>
//           ${renderSearchResultsBlock(data.results)}
//         `;
//       }
//     } catch (err) {
//       console.error("Search error:", err);
//     }

//     // === Step 2: Stream response from /chat-stream ===
//     try {
//       const response = await fetch("/chat-stream", {
//         method: "POST",
//         headers: { "Content-Type": "application/x-www-form-urlencoded" },
//         body: new URLSearchParams({
//           message: msg,
//           inactive: JSON.stringify(inactive),
//         }),
//       });

//       if (!response.ok || !response.body) {
//         botMsg.innerHTML = `<strong>Assistant:</strong> <em>Failed to connect to server.</em>`;
//         return;
//       }

//       const reader = response.body.getReader();
//       const decoder = new TextDecoder("utf-8");
//       let full = "";

//       while (true) {
//         const { done, value } = await reader.read();
//         if (done) break;

//         const chunk = decoder.decode(value, { stream: true });
//         full += chunk;
//         botMsg.innerHTML = full;
//         chatBox.scrollTop = chatBox.scrollHeight;
//       }
//     } catch (err) {
//       botMsg.innerHTML = `<strong>Assistant:</strong> <em>Error: ${escapeHtml(err.message || err)}</em>`;
//     }

//     chatInput.value = '';
//   });
// }