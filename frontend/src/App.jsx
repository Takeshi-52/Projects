// src/App.jsx
import React, { useEffect, useState } from "react";
import MultiUpload from "./components/MultiUpload";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function App() {
  const [images, setImages] = useState([]);

  async function loadList() {
    try {
      const res = await fetch(`${API_BASE}/list`);
      if (!res.ok) throw new Error("Failed to load list");
      const list = await res.json(); // expecting ["/images/xxx.jpg", ...]
      const absolute = list.map(p => (p.startsWith("http") ? p : `${API_BASE}${p}`));
      setImages(absolute.reverse());
    } catch (err) {
      console.error(err);
    }
  }

  useEffect(() => {
    loadList();
  }, []);

  function handleUploaded(urls) {
    setImages(prev => [...urls, ...prev]);
  }

  return (
    // full screen flex center
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="w-full max-w-6xl mx-auto">
        {/* Center column with gap */}
        <div className="flex flex-col items-center gap-8">
          <div className="w-full">
            {/* Upload card centered */}
            <div className="mx-auto" style={{ maxWidth: 920 }}>
              <MultiUpload onUploaded={handleUploaded} />
            </div>
          </div>

          {/* Gallery */}
          <div className="w-full">
            <h2 className="text-2xl font-semibold mb-4 text-center">ภาพทั้งหมด</h2>
            {images.length === 0 ? (
              <div className="text-gray-500 text-center">ยังไม่มีรูปภาพ</div>
            ) : (
              <>
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                  {images.map((src, i) => (
                    <div key={i} className="rounded overflow-hidden shadow-sm bg-white">
                      <div className="relative group">
                        <img
                          src={src}
                          alt={`img-${i}`}
                          className="w-full h-28 object-cover transition-transform duration-200 group-hover:scale-110"
                        />
                        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition"></div>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 text-sm text-gray-500 text-center">แสดงภาพเป็น thumbnail เพื่อความเร็วและอ่านง่าย</div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
