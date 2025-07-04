// upload.js — handles file upload logic and refresh

import { $, escapeHtml } from './dom.js';
import { initDocuments } from './documents.js'; // to refresh doc list

export function initUpload() {
  const uploadForm = $("upload-form");
  const fileInput = $("file-input");
  const uploadStatus = $("upload-status");

  if (!uploadForm || !fileInput || !uploadStatus) return;

  uploadForm.addEventListener("submit", async function (e) {
    e.preventDefault();
    const files = fileInput.files;
    if (!files || files.length === 0) {
      uploadStatus.textContent = "⚠️ Please select one or more files to upload.";
      return;
    }

    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }

    uploadStatus.textContent = "⏳ Uploading...";

    try {
      const res = await fetch("/upload", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      console.log("Upload response:", data);

      if (data.uploads && Array.isArray(data.uploads)) {
        const successCount = data.uploads.filter(f => f.status === 'success').length;
        const errorFiles = data.uploads.filter(f => f.status === 'error');

        uploadStatus.textContent = `✅ ${successCount} file(s) uploaded successfully.`;

        if (errorFiles.length > 0) {
          const errorMessages = errorFiles.map(f => `${f.filename}: ${f.message}`).join('\n');
          alert(`Some files failed to upload:\n${errorMessages}`);
        }

        initDocuments(); // Refresh document list
      } else {
        uploadStatus.textContent = `❌ Error: Unexpected response from server.`;
      }
    } catch (err) {
      uploadStatus.textContent = `❌ Upload failed: ${escapeHtml(err.message || err)}`;
    }
  });
}
