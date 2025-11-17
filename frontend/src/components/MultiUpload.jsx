// src/components/MultiUpload.jsx
import React, { useState, useRef, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function MultiUpload({ onUploaded }) {
  const [files, setFiles] = useState([]);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [progress, setProgress] = useState(0);
  const inputRef = useRef(null);
  const MAX_FILES = 20;

  useEffect(() => {
    if (!error) return;
    const t = setTimeout(() => setError(""), 4000);
    return () => clearTimeout(t);
  }, [error]);

  useEffect(() => {
    if (!info) return;
    const t = setTimeout(() => setInfo(""), 3000);
    return () => clearTimeout(t);
  }, [info]);

  function addFiles(candidateFiles) {
    const list = Array.from(candidateFiles).filter((f) =>
      f.type.startsWith("image/")
    );
    if (list.length === 0) {
      setError("ไม่มีไฟล์ภาพที่รองรับ");
      return;
    }

    let toAdd = list;
    let skipped = 0;

    if (list.length > MAX_FILES) {
      toAdd = list.slice(0, MAX_FILES);
      skipped = list.length - MAX_FILES;
    }

    files.forEach((f) => {
      try {
        URL.revokeObjectURL(f.preview);
      } catch {}
    });

    const mapped = toAdd.map((f) => ({
      file: f,
      preview: URL.createObjectURL(f),
    }));
    setFiles(mapped);

    if (skipped > 0) {
      setError(`เลือกรูปมากเกินไป — เพิ่มเฉพาะ ${MAX_FILES} รูปแรก`);
    } else {
      setInfo(`เพิ่มรูป ${toAdd.length} รูป`);
    }
  }

  function onFileChange(e) {
    addFiles(e.target.files);
    e.target.value = "";
  }

  function onDrop(e) {
    e.preventDefault();
    addFiles(e.dataTransfer.files);
  }

  function clearAll() {
    files.forEach((f) => {
      try {
        URL.revokeObjectURL(f.preview);
      } catch {}
    });
    setFiles([]);
    setProgress(0);
    setError("");
    setInfo("");
  }

  function removeIndex(i) {
    try {
      URL.revokeObjectURL(files[i].preview);
    } catch {}
    setFiles((prev) => prev.filter((_, idx) => idx !== i));
  }

  function uploadAll() {
    if (files.length === 0) return;

    setError("");
    setProgress(0);

    const form = new FormData();
    files.forEach((f) => form.append("files", f.file));

    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_BASE}/upload-multi`);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        setProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        try {
          const res = JSON.parse(xhr.responseText);
          const urls = (res.files || []).map((x) =>
            x.url.startsWith("http") ? x.url : `${API_BASE}${x.url}`
          );
          onUploaded && onUploaded(urls);
          clearAll();
          setInfo("อัปโหลดสำเร็จ 🎉");
        } catch {
          setError("เกิดข้อผิดพลาดจากเซิร์ฟเวอร์");
        }
      } else {
        setError(`Upload failed: ${xhr.status}`);
      }
    };

    xhr.onerror = () => setError("Network error");
    xhr.send(form);
  }

  return (
    <div className="w-full min-h-screen flex items-center justify-center bg-gray-100 py-10">
      <div
        className="bg-white rounded-xl shadow-lg p-8 w-full"
        style={{ maxWidth: "960px" }}
      >
        {/* HEADER */}
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-2xl font-bold text-gray-700 tracking-tight">
            อัปโหลดหลายรูป
          </h3>
          <div className="text-sm text-gray-500">{files.length}/{MAX_FILES}</div>
        </div>

        {/* TOASTS */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded-lg shadow-sm animate-fade-in">
            {error}
          </div>
        )}
        {info && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 text-green-700 rounded-lg shadow-sm animate-fade-in">
            {info}
          </div>
        )}

        {/* UPLOAD AREA */}
        <div
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => inputRef.current?.click()}
          className="border-2 border-dashed border-gray-300 rounded-xl p-10 text-center cursor-pointer bg-gray-50 hover:bg-gray-100 transition-all"
        >
          <p className="text-gray-700 text-lg mb-3">ลากรูปมาวาง หรือคลิกเพื่อเลือกไฟล์</p>
          <button
            className="bg-blue-600 text-white px-6 py-2 rounded-lg shadow hover:bg-blue-700 transition"
          >
            เลือกรูปภาพ
          </button>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={onFileChange}
            className="hidden"
          />
        </div>

        {/* PREVIEW GRID */}
        {files.length > 0 && (
          <>
            <div className="mt-6 flex justify-between items-center">
              <div className="text-lg font-medium text-gray-700">
                Preview
              </div>
              <button
                onClick={clearAll}
                className="text-red-600 hover:underline text-sm"
              >
                ล้างทั้งหมด
              </button>
            </div>

            <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-4 mt-4">
              {files.map((f, i) => (
                <div key={i} className="relative group rounded-lg shadow overflow-hidden">
                  <img
                    src={f.preview}
                    className="w-full h-28 object-cover transform group-hover:scale-105 transition"
                  />
                  <button
                    onClick={() => removeIndex(i)}
                    className="absolute top-1 right-1 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition"
                  >
                    ลบ
                  </button>
                </div>
              ))}
            </div>
          </>
        )}

        {/* PROGRESS BAR */}
        {progress > 0 && (
          <div className="mt-6">
            <div className="w-full h-2 bg-gray-200 rounded">
              <div
                className="h-2 bg-green-500 rounded transition-all"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            <div className="text-sm text-gray-600 mt-1">{progress}%</div>
          </div>
        )}

<div className="mt-4 flex gap-3">
  <button
    disabled={files.length === 0}
    onClick={uploadAll}
    className={`px-4 py-2 rounded text-white ${
      files.length === 0 ? "bg-gray-300" : "bg-blue-600 hover:bg-blue-700"
    }`}
  >
    Upload ทั้งหมด
  </button>
</div>

      </div>
    </div>
  );
}
