import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import axios from "axios";

const API = "https://web-production-3d94.up.railway.app";

export default function Sidebar({ documents, setDocuments }) {
  const [uploading, setUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState(null);

  const onDrop = useCallback(
    async (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (!file) return;

      setUploading(true);
      setUploadStatus(null);

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await axios.post(`${API}/upload`, formData, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        setUploadStatus({
          type: "success",
          message: `✓ ${res.data.document_name} — ${res.data.chunks_stored} chunks stored`,
        });
        setDocuments((prev) => {
          const exists = prev.find((d) => d.name === res.data.document_name);
          if (exists) return prev;
          return [...prev, { name: res.data.document_name }];
        });
      } catch (err) {
        setUploadStatus({
          type: "error",
          message: err.response?.data?.detail || "Upload failed. Try again.",
        });
      } finally {
        setUploading(false);
      }
    },
    [setDocuments],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"] },
    multiple: false,
  });

  return (
    <div className="w-72 bg-gray-900 border-r border-gray-800 flex flex-col p-4 gap-4">
      {/* Header */}
      <div className="pt-2 pb-4 border-b border-gray-800">
        <h1 className="text-lg font-semibold text-white tracking-tight">
          📊 FinDoc Agent
        </h1>
        <p className="text-xs text-gray-500 mt-1">
          Financial Document Intelligence
        </p>
      </div>

      {/* Upload Area */}
      <div>
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
          Upload Document
        </p>
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-4 text-center cursor-pointer transition-all
            ${
              isDragActive
                ? "border-blue-500 bg-blue-500/10"
                : "border-gray-700 hover:border-gray-500 hover:bg-gray-800"
            }`}
        >
          <input {...getInputProps()} />
          {uploading ? (
            <div className="flex flex-col items-center gap-2">
              <div className="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
              <p className="text-xs text-gray-400">Processing PDF...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2">
              <span className="text-2xl">📄</span>
              <p className="text-xs text-gray-400">
                {isDragActive ? "Drop it here!" : "Drag & drop a PDF or click"}
              </p>
            </div>
          )}
        </div>

        {/* Upload Status */}
        {uploadStatus && (
          <div
            className={`mt-2 p-2 rounded text-xs ${
              uploadStatus.type === "success"
                ? "bg-green-900/40 text-green-400 border border-green-800"
                : "bg-red-900/40 text-red-400 border border-red-800"
            }`}
          >
            {uploadStatus.message}
          </div>
        )}
      </div>

      {/* Documents List */}
      <div className="flex-1 overflow-y-auto">
        <p className="text-xs font-medium text-gray-400 uppercase tracking-wider mb-2">
          Documents ({documents.length})
        </p>
        {documents.length === 0 ? (
          <p className="text-xs text-gray-600 italic">No documents yet</p>
        ) : (
          <ul className="flex flex-col gap-1">
            {documents.map((doc, i) => (
              <li
                key={i}
                className="flex items-center gap-2 p-2 rounded bg-gray-800 text-xs text-gray-300 truncate"
              >
                <span className="text-blue-400 flex-shrink-0">📄</span>
                <span className="truncate">{doc.name}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Footer */}
      <div className="pt-4 border-t border-gray-800 text-xs text-gray-600">
        Built by{" "}
        <a
          href="https://github.com/rajeevmadiraju"
          target="_blank"
          rel="noreferrer"
          className="text-blue-500 hover:underline"
        >
          Rajeev
        </a>
      </div>
    </div>
  );
}
