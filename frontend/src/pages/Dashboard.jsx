import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export default function Dashboard() {
  const [passImages, setPassImages] = useState([]);
  const [failImages, setFailImages] = useState([]);

  async function loadImages() {
    const pass = await fetch(`${API_BASE}/brightness-pass`).then(r => r.json());
    const fail = await fetch(`${API_BASE}/brightness-fail`).then(r => r.json());

    // convert to absolute URL
    setPassImages(pass.map(p => API_BASE + p));
    setFailImages(fail.map(f => API_BASE + f));
  }

  useEffect(() => {
    loadImages();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <h1 className="text-3xl font-bold mb-6 text-center">
        Dashboard สถานะรูปภาพ
      </h1>

      <div className="flex justify-center mb-6">
        <button
          className="px-6 py-2 bg-blue-600 text-white rounded shadow hover:bg-blue-700"
          onClick={loadImages}
        >
          Refresh
        </button>
      </div>

      {/* Pass Section */}
      <section className="mb-10">
        <h2 className="text-2xl font-semibold mb-3 text-green-600">
          ✔ รูปที่ผ่าน ({passImages.length})
        </h2>

        {passImages.length === 0 ? (
          <p className="text-gray-500">ยังไม่มีรูปที่ผ่าน</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
            {passImages.map((url, i) => (
              <div key={i} className="rounded overflow-hidden bg-white shadow">
                <img src={url} className="w-full h-32 object-cover" />
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Fail Section */}
      <section>
        <h2 className="text-2xl font-semibold mb-3 text-red-600">
          ✖ รูปที่ไม่ผ่าน ({failImages.length})
        </h2>

        {failImages.length === 0 ? (
          <p className="text-gray-500">ยังไม่มีรูปที่ไม่ผ่าน</p>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-4">
            {failImages.map((url, i) => (
              <div key={i} className="rounded overflow-hidden bg-white shadow">
                <img src={url} className="w-full h-32 object-cover" />
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
