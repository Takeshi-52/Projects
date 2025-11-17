// src/App.jsx
import React, { useEffect, useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";

import MultiUpload from "./components/MultiUpload";
import Dashboard from "./pages/Dashboard";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function HomePage() {
  const [images, setImages] = useState([]);
  const [passImages, setPassImages] = useState([]);
  const [failImages, setFailImages] = useState([]);
  const [loading, setLoading] = useState(false);

  const [progress, setProgress] = useState(0);
  const [processedCount, setProcessedCount] = useState(0);

  async function loadList() {
    try {
      const res = await fetch(`${API_BASE}/list`);
      if (!res.ok) throw new Error("Failed to load list");

      const list = await res.json();
      const absolute = list.map((p) =>
        p.startsWith("http") ? p : `${API_BASE}${p}`
      );

      setImages(absolute.reverse());
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    loadList();
  }, []);

  function handleUploaded(urls) {
    setImages((prev) => [...urls, ...prev]);
  }

  /* ---------------------------------------------------------------------- */
  /* ⭐ Run filter brightness with progress bar */
  /* ---------------------------------------------------------------------- */
  async function runFilter() {
    if (images.length === 0) {
      alert("ยังไม่มีภาพให้คัดกรอง");
      return;
    }

    setLoading(true);
    setProgress(0);
    setProcessedCount(0);

    const total = images.length;

    // ส่งภาพเข้า API ทีละภาพ
    for (let i = 0; i < images.length; i++) {
      const imgUrl = images[i];
      const filename = imgUrl.split("/").pop();

      let blob;
      try {
        blob = await fetch(imgUrl).then(r => r.blob());
      } catch (e) {
        console.warn("โหลดภาพไม่ได้:", imgUrl);
        continue;   // ข้ามภาพที่โหลดไม่ได้
      }

      if (!blob || blob.size === 0) {
        console.warn("Blob ว่าง:", filename);
        continue;
      }

      const form = new FormData();
      form.append("file", blob, filename);

      await fetch(`${API_BASE}/check-brightness`, {
        method: "POST",
        body: form,
      });

      // update progress
      const done = i + 1;
      setProcessedCount(done);
      setProgress(Math.round((done / total) * 100));
    }


    // โหลดผลจาก backend (แก้ path ให้ตรง)
    const pass = await fetch(`${API_BASE}/images/brightness_pass`).then(r => r.json());
    const fail = await fetch(`${API_BASE}/images/brightness_fail`).then(r => r.json());
    const resized = await fetch(`${API_BASE}/images/resized`).then(r => r.json());

    setPassImages(pass.map(x => `${API_BASE}/images/brightness_pass${x}`));
    setFailImages(fail.map(x => `${API_BASE}/images/brightness_fail${x}`));

    setLoading(false);
    setProgress(100);

    alert("คัดกรองภาพเสร็จแล้ว");
  }

  /* ---------------------------------------------------------------------- */

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="flex gap-6">

        {/* LEFT COLUMN — UPLOAD 30% */}
        <div className="basis-4/12">
          <div className="bg-white shadow rounded-xl p-6">
            <MultiUpload onUploaded={handleUploaded} />
          </div>
        </div>

        {/* RIGHT COLUMN — GALLERY 70% */}
        <div className="basis-8/12">
          <div className="bg-white shadow rounded-xl p-4">

            <h2 className="text-xl font-semibold mb-3 text-center">
              ภาพที่อัปโหลดทั้งหมด
            </h2>

            {images.length === 0 ? (
              <div className="text-center text-gray-500 py-6">
                ยังไม่มีรูปภาพ
              </div>
            ) : (
              <>
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {images.map((src, i) => (
                    <div key={i} className="rounded-lg overflow-hidden bg-white shadow-sm">
                      <img src={src} alt={`img-${i}`} className="w-full h-32 object-cover" />
                    </div>
                  ))}
                </div>

                {/* Filter Button */}
                <div className="mt-6">
                  <button
                    className={`px-4 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700 w-full ${loading ? "opacity-60 cursor-not-allowed" : ""
                      }`}
                    onClick={runFilter}
                    disabled={loading}
                  >
                    {loading ? "กำลังคัดกรอง..." : "คัดกรองคุณภาพของภาพ"}
                  </button>

                  {/* Progress Bar */}
                  {loading && (
                    <div className="mt-4">
                      <div className="w-full bg-gray-200 h-3 rounded">
                        <div
                          className="h-3 bg-green-500 rounded"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <p className="text-center text-sm text-gray-600 mt-2">
                        {processedCount} / {images.length} ภาพ ({progress}%)
                      </p>
                    </div>
                  )}
                </div>
              </>
            )}

            {/* PASS / FAIL SECTION */}
            {(passImages.length > 0 || failImages.length > 0) && (
              <div className="mt-10">

                <h3 className="text-lg font-bold text-green-700 mb-2">
                  ✅ ภาพที่ผ่าน ({passImages.length})
                </h3>
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3 mb-8">
                  {passImages.map((src, i) => (
                    <img key={i} src={src} className="w-full h-28 object-cover rounded" />
                  ))}
                </div>

                <h3 className="text-lg font-bold text-red-700 mb-2">
                  ❌ ภาพที่ไม่ผ่าน ({failImages.length})
                </h3>
                <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {failImages.map((src, i) => (
                    <img key={i} src={src} className="w-full h-28 object-cover rounded" />
                  ))}
                </div>

              </div>
            )}

          </div>
        </div>

      </div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/dashboard" element={<Dashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
