import React, { useState } from 'react';
import MultiUpload from './components/MultiUpload';
import Dashboard from './pages/Dashboard'; 

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
          <Dashboard data={uploadedData} onReset={handleReset} />
        )}
      </main>
    </div>
  );
}

export default App;