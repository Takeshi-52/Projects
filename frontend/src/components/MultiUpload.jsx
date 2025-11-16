// src/components/MultiUpload.jsx
import React, { useState, useRef, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function MultiUpload({ onUploaded }) {
  const [files, setFiles] = useState([]); // { file, preview }
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
    const list = Array.from(candidateFiles).filter(f => f.type.startsWith("image/"));
    if (list.length === 0) {
      setError("ไม่มีไฟล์ภาพที่รองรับ");
      return;
    }

    // New behavior: use only first 20 from selection, replace previous files
    let toAdd = list;
    let skipped = 0;

    if (list.length > MAX_FILES) {
      toAdd = list.slice(0, MAX_FILES);
      skipped = list.length - MAX_FILES;
    }

    // revoke old previews and replace with new selection
    files.forEach(f => {
      try { URL.revokeObjectURL(f.preview); } catch {}
    });

    const mapped = toAdd.map(f => ({ file: f, preview: URL.createObjectURL(f) }));
    setFiles(mapped);

    if (skipped > 0) {
      setError(`เลือกภาพมากเกินไป — เพิ่มเฉพาะ ${MAX_FILES} รูปแรก`);
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

  function removeIndex(i) {
    try { URL.revokeObjectURL(files[i].preview); } catch {}
    setFiles(prev => prev.filter((_, idx) => idx !== i));
  }

  function clearAll() {
    files.forEach(f => {
      try { URL.revokeObjectURL(f.preview); } catch {}
    });
    setFiles([]);
    setProgress(0);
    setError("");
    setInfo("");
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
        const percent = Math.round((e.loaded / e.total) * 100);
        setProgress(percent);
      }
    };

    xhr.onload = () => {
      if (xhr.status === 200) {
        try {
          const res = JSON.parse(xhr.responseText);
          const urls = (res.files || []).map(x => x.url.startsWith("http") ? x.url : `${API_BASE}${x.url}`);
          onUploaded && onUploaded(urls);
          clearAll();
          setInfo("อัปโหลดเรียบร้อย");
        } catch (err) {
          setError("ตอบกลับจากเซิร์ฟเวอร์ไม่ถูกต้อง");
        }
      } else {
        setError(`Upload failed: ${xhr.status}`);
      }
    };

    xhr.onerror = () => setError("Network error while uploading");
    xhr.send(form);
  }

  return (
    // card centered with max width
    <div className="bg-white rounded-lg shadow p-6 mx-auto" style={{ maxWidth: 920 }}>
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-lg font-semibold">Upload หลายรูป <span className="text-sm text-gray-500">(สูงสุด {MAX_FILES})</span></h3>
        <div className="text-sm text-gray-600">{files.length}/{MAX_FILES}</div>
      </div>

      {/* toast / messages */}
      <div className="mb-3">
        {error && (
          <div className="p-2 bg-red-50 border border-red-200 text-red-700 rounded mb-2">
            {error}
          </div>
        )}
        {info && (
          <div className="p-2 bg-green-50 border border-green-200 text-green-700 rounded mb-2">
            {info}
          </div>
        )}
      </div>

      <div
        onDrop={onDrop}
        onDragOver={(e) => e.preventDefault()}
        className="border-2 border-dashed border-gray-300 rounded-md p-6 flex flex-col items-center justify-center text-center cursor-pointer hover:bg-gray-50"
        onClick={() => inputRef.current?.click()}
      >
        <p className="text-gray-600 mb-2">ลากแล้ววางไฟล์ที่นี่ หรือ คลิกเพื่อเลือกไฟล์</p>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={(e) => { e.stopPropagation(); inputRef.current?.click(); }}
            className="bg-blue-600 text-white px-4 py-2 rounded"
          >
            เลือกรูป
          </button>
          <span className="text-sm text-gray-500">หรือวางไฟล์ลงตรงนี้</span>
        </div>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          onChange={onFileChange}
          className="hidden"
        />
      </div>

      {files.length > 0 && (
        <>
          <div className="mt-4 flex items-center justify-between">
            <div className="text-sm text-gray-600">Preview ({files.length})</div>
            <div className="flex gap-2">
              <button onClick={clearAll} className="text-sm text-red-600 hover:underline">ล้างทั้งหมด</button>
            </div>
          </div>

          <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-6 gap-3 mt-3">
            {files.map((f, i) => (
              <div key={i} className="relative border rounded overflow-hidden">
                <img src={f.preview} alt="" className="w-full h-28 object-cover" />
                <button
                  onClick={() => removeIndex(i)}
                  className="absolute top-1 right-1 bg-black bg-opacity-60 text-white text-xs px-2 py-0.5 rounded"
                >
                  ลบ
                </button>
              </div>
            ))}
          </div>
        </>
      )}

      {/* progress */}
      {progress > 0 && (
        <div className="mt-4">
          <div className="w-full bg-gray-200 h-2 rounded">
            <div className="h-2 bg-green-500" style={{ width: `${progress}%` }} />
          </div>
          <div className="text-sm text-gray-600 mt-1">{progress}%</div>
        </div>
      )}

      <div className="mt-4 flex gap-3">
        <button
          disabled={files.length === 0}
          onClick={uploadAll}
          className={`px-4 py-2 rounded text-white ${files.length === 0 ? "bg-gray-300" : "bg-blue-600 hover:bg-blue-700"}`}
        >
          Upload ทั้งหมด
        </button>
        <button onClick={() => { setFiles(prev => prev.slice(0, 5)); }} className="px-4 py-2 rounded border">ตัวอย่าง: เก็บ 5</button>
      </div>
    </div>
  );
}
