// src/components/MultiUpload.jsx
import React, { useState, useRef, useEffect } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function MultiUpload({ onUploaded }) {
  const [files, setFiles] = useState([]);
  const [error, setError] = useState("");
  const [info, setInfo] = useState("");
  const [progress, setProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false); // เพิ่ม State เช็คว่ากำลังอัปโหลดหรือไม่
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

    // เช็คจำนวนไฟล์รวมกับของเดิมที่มีอยู่
    const totalFiles = files.length + list.length;
    
    if (totalFiles > MAX_FILES) {
      const allowedCount = MAX_FILES - files.length;
      toAdd = list.slice(0, allowedCount);
      skipped = list.length - allowedCount;
    }

    const mapped = toAdd.map((f) => ({
      file: f,
      preview: URL.createObjectURL(f),
    }));
    
    setFiles((prev) => [...prev, ...mapped]);

    if (skipped > 0) {
      setError(`จำกัดสูงสุด ${MAX_FILES} ภาพ — ข้ามไป ${skipped} ภาพ`);
    } else {
      setInfo(`เพิ่มรูปสำเร็จ ${toAdd.length} รูป`);
    }
  }

  function onFileChange(e) {
    addFiles(e.target.files);
    e.target.value = "";
  }

  function onDrop(e) {
    e.preventDefault();
    if (!isUploading) addFiles(e.dataTransfer.files);
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
    setIsUploading(true);

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
      setIsUploading(false);
      if (xhr.status === 200) {
        try {
          const res = JSON.parse(xhr.responseText);
          // ส่ง URLs หรือข้อมูลผลลัพธ์กลับไปที่ Parent Component (Dashboard)
          const urls = (res.files || []).map((x) =>
            x.url.startsWith("http") ? x.url : `${API_BASE}${x.url}`
          );
          onUploaded && onUploaded(urls, res); // ส่ง res ไปด้วยเผื่อมีข้อมูลวิเคราะห์
          clearAll();
          setInfo("อัปโหลดและตรวจสอบสำเร็จ 🎉");
        } catch {
          setError("เกิดข้อผิดพลาดในการอ่านข้อมูลจากเซิร์ฟเวอร์");
        }
      } else {
        setError(`อัปโหลดล้มเหลว: รหัส ${xhr.status}`);
      }
    };

    xhr.onerror = () => {
      setIsUploading(false);
      setError("เกิดข้อผิดพลาดในการเชื่อมต่อ (Network error)");
    };
    
    xhr.send(form);
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 lg:px-8 animate-fade-in">
      <div className="bg-white rounded-xl shadow-lg p-8">
        
        {/* HEADER */}
        <div className="mb-6 flex justify-between items-end">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">อัปโหลดภาพ</h2>
            <p className="text-gray-500 mt-1">ระบบคัดกรองภาพถ่ายด้วย AI</p>
          </div>
          <div className="text-sm font-medium text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
            {files.length} / {MAX_FILES} ภาพ
          </div>
        </div>

        {/* TOASTS (Error / Info) */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border-l-4 border-red-500 text-red-700 rounded shadow-sm flex items-center">
            <i className="fa-solid fa-circle-exclamation mr-2"></i> {error}
          </div>
        )}
        {info && (
          <div className="mb-4 p-3 bg-green-50 border-l-4 border-green-500 text-green-700 rounded shadow-sm flex items-center">
            <i className="fa-solid fa-circle-check mr-2"></i> {info}
          </div>
        )}

        {/* UPLOAD AREA (Dropzone) */}
        <div
          onDrop={onDrop}
          onDragOver={(e) => e.preventDefault()}
          onClick={() => !isUploading && inputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-12 transition-all text-center ${
            isUploading 
              ? "border-gray-300 bg-gray-50 cursor-not-allowed opacity-60" 
              : "border-indigo-300 bg-indigo-50 hover:bg-indigo-100 cursor-pointer group"
          }`}
        >
          <div className="flex flex-col items-center justify-center pointer-events-none">
            <i className={`fa-solid fa-cloud-arrow-up text-5xl mb-4 transition-transform ${isUploading ? 'text-gray-400' : 'text-indigo-500 group-hover:scale-110'}`}></i>
            <p className={`text-lg font-medium ${isUploading ? 'text-gray-500' : 'text-indigo-900'}`}>
              ลากไฟล์มาวางที่นี่ หรือ คลิกเพื่อเลือกไฟล์
            </p>
            <p className={`text-sm mt-2 ${isUploading ? 'text-gray-400' : 'text-indigo-600'}`}>
              รองรับไฟล์ .JPG, .PNG (สูงสุด {MAX_FILES} ภาพ/ครั้ง)
            </p>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            multiple
            onChange={onFileChange}
            className="hidden"
            disabled={isUploading}
          />
        </div>

        {/* PREVIEW GRID */}
        {files.length > 0 && (
          <div className="mt-8">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-gray-700">ภาพที่เลือก ({files.length})</h3>
              {!isUploading && (
                <button onClick={clearAll} className="text-red-500 hover:text-red-700 text-sm font-medium transition">
                  <i className="fa-solid fa-trash-can mr-1"></i> ล้างทั้งหมด
                </button>
              )}
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-4">
              {files.map((f, i) => (
                <div key={i} className="relative group rounded-lg shadow-sm border border-gray-200 overflow-hidden bg-gray-100 aspect-square">
                  <img
                    src={f.preview}
                    alt="preview"
                    className="w-full h-full object-cover transform group-hover:scale-110 transition duration-300"
                  />
                  {!isUploading && (
                    <button
                      onClick={() => removeIndex(i)}
                      className="absolute top-2 right-2 bg-red-500 text-white w-7 h-7 rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-red-600 shadow-md"
                    >
                      <i className="fa-solid fa-xmark"></i>
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* PROGRESS BAR (แสดงเมื่อกำลังอัปโหลด) */}
        {isUploading && (
          <div className="mt-8 text-left bg-indigo-50 p-5 rounded-lg border border-indigo-100 shadow-inner">
            <div className="flex justify-between mb-2">
              <span className="text-sm font-bold text-indigo-800 flex items-center">
                <i className="fa-solid fa-spinner fa-spin mr-2"></i> กำลังอัปโหลดและประมวลผลด้วย AI...
              </span>
              <span className="text-sm font-bold text-indigo-800">{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 mb-4 overflow-hidden">
              <div
                className="bg-indigo-600 h-3 rounded-full transition-all duration-300 ease-out"
                style={{ width: `${progress}%` }}
              ></div>
            </div>
            
            {/* Mockup สถานะย่อย เพื่อความสวยงาม */}
            <div className="space-y-2 text-sm text-gray-600">
              <p className={`flex items-center ${progress > 10 ? 'text-green-600' : ''}`}>
                <i className={`fa-solid fa-${progress > 10 ? 'check' : 'circle-notch fa-spin'} w-5`}></i> อัปโหลดไฟล์ภาพ
              </p>
              <p className={`flex items-center ${progress > 50 ? 'text-green-600' : progress > 10 ? 'text-indigo-600' : 'text-gray-400'}`}>
                <i className={`fa-solid fa-${progress > 50 ? 'check' : progress > 10 ? 'spinner fa-spin' : 'minus'} w-5`}></i> วิเคราะห์คุณภาพภาพ (Blur, Light)
              </p>
              <p className={`flex items-center ${progress === 100 ? 'text-green-600' : progress > 50 ? 'text-indigo-600' : 'text-gray-400'}`}>
                 <i className={`fa-solid fa-${progress === 100 ? 'check' : progress > 50 ? 'spinner fa-spin' : 'minus'} w-5`}></i> จำแนกหมวดหมู่ด้วย YOLO
              </p>
            </div>
          </div>
        )}

        {/* SUBMIT BUTTON */}
        <div className="mt-8">
          <button
            onClick={uploadAll}
            disabled={files.length === 0 || isUploading}
            className={`w-full font-bold py-3 px-4 rounded-lg transition-all flex justify-center items-center text-lg ${
              files.length === 0
                ? "bg-gray-200 text-gray-400 cursor-not-allowed"
                : isUploading
                ? "bg-indigo-400 text-white cursor-wait"
                : "bg-indigo-600 text-white hover:bg-indigo-700 shadow-md hover:shadow-lg"
            }`}
          >
            {isUploading ? (
              <>
                <i className="fa-solid fa-circle-notch fa-spin mr-2"></i> กำลังประมวลผล...
              </>
            ) : (
              <>
                <i className="fa-solid fa-wand-magic-sparkles mr-2"></i> เริ่มการตรวจสอบ
              </>
            )}
          </button>
        </div>

      </div>
    </div>
  );
}
