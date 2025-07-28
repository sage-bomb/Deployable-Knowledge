import { $, escapeHtml } from './dom.js';
import { initDocuments } from './documents.js'; // to refresh doc list

/**
 * Initializes the file upload functionality.
 * @returns {void}
 */
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

    let successCount = 0;
    let errorFiles = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      uploadStatus.innerHTML = `⏳ Uploading (${i + 1}/${files.length})... <span style="color: red;">Using chat at the same time may cause performance issues.</span>`;

      const formData = new FormData();
      formData.append("files", file); // same field name the server expects

      try {
        const res = await fetch("/upload", {
          method: "POST",
          body: formData
        });

        const data = await res.json();
        console.log(`Upload response for ${file.name}:`, data);

        if (
          data.uploads &&
          Array.isArray(data.uploads) &&
          data.uploads[0]?.status === "success"
        ) {
          successCount++;
        } else {
          errorFiles.push({
            filename: file.name,
            message: data.uploads?.[0]?.message || "Unknown error"
          });
        }
      } catch (err) {
        errorFiles.push({
          filename: file.name,
          message: err.message || "Network error"
        });
      }
    }

    uploadStatus.textContent = `✅ ${successCount} file(s) uploaded successfully.`;

    if (errorFiles.length > 0) {
      const errorMessages = errorFiles.map(f => `${f.filename}: ${f.message}`).join("\n");
      alert(`Some files failed to upload:\n${errorMessages}`);
    }

    initDocuments(); // Refresh document list
  });
}