import React, { useState } from 'react';
import MultiUpload from './components/MultiUpload';
// ถ้าคุณสร้างไฟล์ Dashboard แยกไว้แล้ว ให้เปิดคอมเมนต์บรรทัดล่างนี้ครับ
// import Dashboard from './pages/Dashboard'; 

function App() {
  // เริ่มต้นมาให้อยู่หน้า 'upload' เสมอ
  const [currentPage, setCurrentPage] = useState('upload');
  
  // State สำหรับเก็บข้อมูลที่ส่งกลับมาจาก Backend เมื่ออัปโหลดเสร็จ
  const [uploadedData, setUploadedData] = useState(null);

  // ฟังก์ชันนี้จะทำงานเมื่อกด "เริ่มการตรวจสอบ" และ API โหลดเสร็จ 100%
  const handleUploadComplete = (urls, responseData) => {
    console.log("อัปโหลดสำเร็จ ได้ URLs:", urls);
    setUploadedData(responseData); // เก็บข้อมูลผลการวิเคราะห์
    setCurrentPage('dashboard');   // เปลี่ยนเส้นทางไปหน้า Dashboard อัตโนมัติ
  };

  // ฟังก์ชันสำหรับกลับมาหน้าอัปโหลดใหม่
  const handleReset = () => {
    setUploadedData(null);
    setCurrentPage('upload');
  }

  return (
    <div className="min-h-screen bg-gray-100 font-sans text-gray-800">
      
      {/* Navbar ด้านบน (ตัดปุ่มสลับหน้าออกแล้ว) */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <i className="fa-solid fa-camera-retro text-indigo-600 text-2xl mr-3"></i>
              <span className="font-bold text-xl tracking-tight text-gray-900">ระบบคัดกรองภาพ</span>
            </div>
            {/* พื้นที่ว่างด้านขวา เผื่อใส่อื่นๆ ในอนาคต เช่น ชื่อ User */}
          </div>
        </div>
      </nav>

      {/* ส่วนเนื้อหาหลัก */}
      <main className="py-8">
        
        {/* แสดงหน้า Upload */}
        {currentPage === 'upload' && (
          <MultiUpload onUploaded={handleUploadComplete} />
        )}

        {/* แสดงหน้า Dashboard เมื่ออัปโหลดเสร็จ */}
        {currentPage === 'dashboard' && (
          // TODO: แทนที่ตรงนี้ด้วย <Dashboard data={uploadedData} onReset={handleReset} /> ในอนาคต
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center animate-fade-in">
             <div className="bg-white p-12 rounded-xl shadow-sm">
                <i className="fa-solid fa-chart-pie text-6xl text-indigo-300 mb-4"></i>
                <h2 className="text-2xl font-bold text-gray-700">หน้า Dashboard (ผลลัพธ์)</h2>
                <p className="text-gray-500 mt-2">ระบบเปลี่ยนหน้าอัตโนมัติ! ข้อมูลจาก Backend พร้อมแสดงผลที่นี่</p>
                
                {/* ปุ่มสำหรับกลับไปเริ่มใหม่ */}
                <button 
                  onClick={handleReset}
                  className="mt-8 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition shadow"
                >
                  <i className="fa-solid fa-arrow-left mr-2"></i> อัปโหลดภาพชุดใหม่
                </button>
             </div>
          </div>
        )}

      </main>

    </div>
  );
}

export default App;