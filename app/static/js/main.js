// === main.js ===
// All client logic for Deployable Knowledge

document.addEventListener("DOMContentLoaded", () => {
  initToggleControls();
  initChatHandler();
  initSearchHandler();
  initUploadHandler();
  initDocumentManager();
});

// === Document Manager (Load + Filter) ===
let allDocs = [];

function initDocumentManager() {
  fetchDocuments();
  setupFilterForm();
}

function fetchDocuments() {
  fetch("/documents")
    .then(res => res.json())
    .then(docs => {
      allDocs = docs;
      renderDocumentList(allDocs);
    })
    .catch(err => {
      const list = document.getElementById("document-list");
      list.innerHTML = `<li><em>Error: ${escapeHtml(err.message || err)}</em></li>`;
    });
}

function setupFilterForm() {
  const form = document.getElementById("filter-form");
  const input = document.getElementById("filter-input");

  form.addEventListener("submit", e => {
    e.preventDefault();
    renderDocumentList(allDocs, input.value.trim());
  });
}

// === Globals ===
const toggleStates = {};

// === Utility Functions ===
function escapeHtml(str) {
  return str.replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");
}

function isActive(source) {
  return !(toggleStates[source] === false);
}

function renderSearchResults(results, filterFn = () => true) {
  if (!Array.isArray(results) || results.length === 0) {
    return `<em>No matches found.</em>`;
  }

  return results
    .map(result => {
      if (typeof result === "string") {
        return { text: result, source: "unknown", score: null };
      }
      return result;
    })
    .filter(filterFn)
    .map(result => `
      <div class="search-result">
        <div><strong>Source:</strong> ${escapeHtml(result.source || "unknown")}</div>
        <div><strong>Match Score:</strong> ${result.score != null ? result.score.toFixed(4) : "n/a"}</div>
        <div style="margin-top: 0.5rem;">${escapeHtml(result.text)}</div>
      </div>
    `)
    .join('');
}

function showConfirmation(message) {
  return new Promise((resolve) => {
    const modal = document.getElementById("confirm-modal");
    const msg = document.getElementById("confirm-message");
    const yes = document.getElementById("confirm-yes");
    const no = document.getElementById("confirm-no");

    msg.textContent = message;
    modal.classList.remove("hidden");

    function cleanup(result) {
      modal.classList.add("hidden");
      yes.removeEventListener("click", yesHandler);
      no.removeEventListener("click", noHandler);
      resolve(result);
    }

    function yesHandler() { cleanup(true); }
    function noHandler() { cleanup(false); }

    yes.addEventListener("click", yesHandler);
    no.addEventListener("click", noHandler);
  });
}


// === UI Modules ===
function initToggleControls() {
  document.querySelectorAll('.toggle-btn').forEach(btn => {
    const li = btn.closest('li');
    const docId = li.getAttribute('data-doc-id');
    const statusSpan = li.querySelector('.status-label');
    const initialActive = li.getAttribute('data-active') === "true";
    toggleStates[docId] = initialActive;

    btn.textContent = initialActive ? "Deactivate" : "Activate";

    btn.addEventListener('click', () => {
      const isActive = toggleStates[docId];
      toggleStates[docId] = !isActive;
      statusSpan.textContent = isActive ? "Inactive" : "Active";
      btn.textContent = isActive ? "Activate" : "Deactivate";
    });
  });
}

function initChatHandler() {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('user-input');
  const chatBox = document.getElementById('chat-box');
  const searchResults = document.getElementById('search-results');

  chatForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const msg = chatInput.value.trim();
    if (!msg) return;

    const inactive = Object.entries(toggleStates)
      .filter(([_, v]) => v === false)
      .map(([k]) => k);

    chatBox.innerHTML += `<div><strong>You:</strong> ${escapeHtml(msg)}</div>`;
    const botMsg = document.createElement('div');
    botMsg.innerHTML = `<strong>Assistant:</strong> <em>Thinking...</em>`;
    chatBox.appendChild(botMsg);
    chatBox.scrollTop = chatBox.scrollHeight;

    fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        message: msg,
        inactive: JSON.stringify(inactive)
      })
    })
      .then(res => res.json())
      .then(data => {
        if (!data.response) {
    botMsg.innerHTML = `<strong>Assistant:</strong> <em>No response received from the server.</em>`;
    return;
  }
        console.log("✅ Chat response data:", data);  // add this line

        // const formatted = data.response.replace(/```(.*?)\n([\s\S]*?)```/g, (_, lang, code) =>
        //   `<pre><code class="language-${lang}">${escapeHtml(code)}</code></pre>`
        // );
        // botMsg.innerHTML = `<strong>Assistant:</strong><br>${formatted}`;

        botMsg.innerHTML = `<strong>Assistant:</strong><br>${data.response}`;

        chatBox.scrollTop = chatBox.scrollHeight;

        if (Array.isArray(data.context)) {
          searchResults.innerHTML = `
            <h3>RAG Context Used:</h3>
            ${renderSearchResults(data.context, r => isActive(r.source))}
          `;
        }
      })
      .catch(err => {
        botMsg.innerHTML = `<strong>Assistant:</strong> <em>Error: ${escapeHtml(err.message || err)}</em>`;
      });

    chatInput.value = '';
  });
}

function initSearchHandler() {
  const searchForm = document.getElementById('search-form');
  const searchInput = document.getElementById('search-query');
  const searchResults = document.getElementById('search-results');

  searchForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const query = searchInput.value.trim();
    if (!query) return;

    searchResults.innerHTML = `<em>Searching...</em>`;

    fetch(`/search?q=${encodeURIComponent(query)}&top_k=5`)
      .then(res => res.json())
      .then(data => {
        searchResults.innerHTML = renderSearchResults(data.results, r => isActive(r.source));
      })
      .catch(err => {
        searchResults.innerHTML = `<em>Error: ${escapeHtml(err.message || err)}</em>`;
      });
  });
}

function initUploadHandler() {
  const uploadForm = document.getElementById('upload-form');
  const fileInput = document.getElementById('file-input');
  const uploadStatus = document.getElementById('upload-status');

  uploadForm.addEventListener('submit', function (e) {
    e.preventDefault();
    const file = fileInput.files[0];
    if (!file) {
      uploadStatus.textContent = "⚠️ Please select a file to upload.";
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    uploadStatus.textContent = "⏳ Uploading...";

    fetch("/upload", {
      method: "POST",
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          uploadStatus.textContent = `✅ ${data.message}`;
          fetchDocuments(); // Refresh document list after upload
        } else {
          uploadStatus.textContent = `❌ Error: ${data.message}`;
        }
      })
      .catch(err => {
        uploadStatus.textContent = `❌ Upload failed: ${escapeHtml(err.message || err)}`;
      });
  });
}
function renderDocumentList(docs, filter = "") {
  const list = document.getElementById("document-list");
  list.innerHTML = ""; // Clear current list

  const filtered = docs.filter(doc =>
    doc.title.toLowerCase().includes(filter.toLowerCase())
  );

  if (filtered.length === 0) {
    list.innerHTML = "<li><em>No results found.</em></li>";
    return;
  }

  filtered.forEach(doc => {
  const li = document.createElement("li");
  li.setAttribute("data-doc-id", doc.id);
  li.setAttribute("data-active", "true");

  const statusSpan = document.createElement("span");
  statusSpan.className = "status-label";
  statusSpan.textContent = "Active";

  const toggleBtn = document.createElement("button");
  toggleBtn.className = "toggle-btn";
  toggleBtn.textContent = "Deactivate";

  toggleStates[doc.id] = true;

  toggleBtn.addEventListener("click", () => {
    const isActive = toggleStates[doc.id];
    toggleStates[doc.id] = !isActive;
    statusSpan.textContent = isActive ? "Inactive" : "Active";
    toggleBtn.textContent = isActive ? "Activate" : "Deactivate";
  });

  const removeBtn = document.createElement("button");
  removeBtn.textContent = "Remove";
  removeBtn.style.marginLeft = "0.5rem";
  removeBtn.addEventListener("click", () => {
 showConfirmation(`Remove document "${doc.title}"?`).then(confirmed => {
  if (!confirmed) return;

  fetch("/remove", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ source: doc.id })
  })
    .then(res => res.json())
    .then(data => {
      if (data.status === "success") {
        fetchDocuments(); // refresh the list
      } else {
        alert(`Error: ${data.message}`);
      }
    })
    .catch(err => {
      alert(`Failed to remove: ${err.message || err}`);
    });
});

    fetch("/remove", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({ source: doc.id })
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          fetchDocuments(); // refresh the list
        } else {
          alert(`Error: ${data.message}`);
        }
      })
      .catch(err => {
        alert(`Failed to remove: ${err.message || err}`);
      });
  });

  li.innerHTML = `
    <strong>${escapeHtml(doc.title)}</strong><br />
    <small>Segments: ${doc.segments}</small><br />
    <small>Status: </small>
  `;
  li.appendChild(statusSpan);
  li.appendChild(document.createElement("br"));
  li.appendChild(toggleBtn);
  li.appendChild(removeBtn);
  list.appendChild(li);
});
}