import React, { useState, useEffect } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js';
import { Doughnut } from 'react-chartjs-2';

ChartJS.register(ArcElement, Tooltip, Legend);

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

// --- Helper Functions สำหรับจัดการสีและข้อความ ---
const getReasonTag = (reason) => {
    if (!reason || reason === 'ผ่านเกณฑ์') return { text: 'ผ่านเกณฑ์', color: 'bg-green-100 text-green-700' };
    
    const mainReason = reason.split('(')[0].trim();
    
    if (mainReason.includes('เบลอ')) return { text: mainReason, color: 'bg-red-100 text-red-800' };
    if (mainReason.includes('หลับตา') || mainReason.includes('หน้าเอียง')) return { text: mainReason, color: 'bg-orange-100 text-orange-800' };
    if (mainReason.includes('อ้าปาก')) return { text: mainReason, color: 'bg-pink-100 text-pink-800' };
    if (mainReason.includes('OVEREXPOSED') || mainReason.includes('UNDEREXPOSED') || mainReason.includes('Very Bright') || mainReason.includes('Very Dark')) return { text: 'แสงไม่เหมาะสม', color: 'bg-yellow-100 text-yellow-800' };
    if (mainReason.includes('Artifact')) return { text: 'ไม่ใช่บุคคลจริง', color: 'bg-gray-200 text-gray-800' };
    
    return { text: mainReason, color: 'bg-red-100 text-red-800' };
};

const getDetailText = (reason) => {
    if (!reason || reason === 'ผ่านเกณฑ์') return null;
    const match = reason.match(/\((.*?)\)/);
    return match ? match[1] : reason; 
};

export default function Dashboard({ data, onReset }) {
  const [filter, setFilter] = useState('all');
  const [selectedImage, setSelectedImage] = useState(null);
  
  // State สำหรับระบบ Classify
  const [isClassifying, setIsClassifying] = useState(false);
  const [classificationData, setClassificationData] = useState(null); // เก็บผลลัพธ์แยกหมวดหมู่

  if (!data || !data.files) {
    return (
      <div className="text-center py-20 animate-fade-in">
        <p className="text-gray-500 mb-4">ไม่พบข้อมูลการวิเคราะห์</p>
        <button onClick={onReset} className="px-6 py-2 bg-indigo-600 text-white rounded-lg shadow hover:bg-indigo-700">
          กลับไปหน้าอัปโหลด
        </button>
      </div>
    );
  }

  const images = data.files;
  
  // สถิติตัวเลขพื้นฐาน
  const total = images.length;
  const passedCount = images.filter(img => img.status === 'Passed').length;
  const rejectedCount = total - passedCount;
  const passedPercent = total > 0 ? Math.round((passedCount / total) * 100) : 0;

  // จัดกลุ่มสาเหตุที่ตกเกณฑ์ (Defect Analysis)
  const defectCounts = {};
  images.forEach(img => {
    if (img.status === 'Rejected') {
      const tag = getReasonTag(img.defect_reason).text;
      defectCounts[tag] = (defectCounts[tag] || 0) + 1;
    }
  });
  const defectEntries = Object.entries(defectCounts).sort((a, b) => b[1] - a[1]);

  // ฟังก์ชันยิง API จำแนกภาพ
  const handleClassify = async () => {
    setIsClassifying(true);
    try {
        const response = await fetch(`${API_BASE}/classify-passed`, { method: 'POST' });
        const result = await response.json();
        
        if (result.data) {
            setClassificationData(result.data); // บันทึกผลลัพธ์ลง State
            alert("จำแนกภาพเรียบร้อยแล้ว! หมวดหมู่จะปรากฏในรายละเอียดของแต่ละภาพ");
        }
    } catch (error) {
        console.error("Classification error:", error);
        alert("เกิดข้อผิดพลาดในการจำแนกภาพ (อย่าลืมเช็คว่า Backend รันอยู่ไหม)");
    } finally {
        setIsClassifying(false);
    }
  };

  // รวมข้อมูลรูปภาพเดิม เข้ากับ ข้อมูลหมวดหมู่ใหม่ (ถ้ากดปุ่มจำแนกแล้ว)
  const displayImages = images.map(img => {
      let finalCategory = null;
      let finalClsReason = null;
      if (classificationData && img.status === 'Passed') {
          const clsMatch = classificationData.find(c => c.filename === img.filename);
          if (clsMatch) {
              finalCategory = clsMatch.category;
              finalClsReason = clsMatch.reason;
          }
      }
      return { ...img, category: finalCategory, clsReason: finalClsReason };
  });

  // กรองรูปภาพตามปุ่ม (All, Passed, Rejected)
  const filteredImages = displayImages.filter(img => {
    if (filter === 'all') return true;
    if (filter === 'passed') return img.status === 'Passed';
    if (filter === 'rejected') return img.status === 'Rejected';
    return true;
  });

  // เตรียมข้อมูลกราฟโดนัท (อัปเดตอัตโนมัติถ้ามีการจำแนกภาพแล้ว)
  let doughnutLabels = ['รอจำแนกภาพ (Unclassified)'];
  let doughnutDataValues = [passedCount];
  let doughnutColors = ['#E5E7EB']; // สีเทา (รอจำแนก)

  if (classificationData && classificationData.length > 0) {
      const counts = {};
      classificationData.forEach(c => {
          counts[c.category] = (counts[c.category] || 0) + 1;
      });
      doughnutLabels = Object.keys(counts);
      doughnutDataValues = Object.values(counts);
      
      // ตั้งสีให้แต่ละหมวดหมู่ (วิทยากรสีน้ำเงิน, รอจำแนกสีเหลือง/เทา)
      doughnutColors = doughnutLabels.map(label => {
          if (label === 'วิทยากร') return '#3B82F6'; // Blue
          if (label === 'รูปหมู่') return '#10B981'; // Emerald
          if (label === 'บรรยากาศ') return '#06B6D4'; // Cyan
          return '#F59E0B'; // Amber (สำหรับ อื่นๆ/รอจำแนก)
      });
  }

  const doughnutChartData = {
    labels: doughnutLabels,
    datasets: [{
      data: doughnutDataValues,
      backgroundColor: doughnutColors,
      borderWidth: 0,
    }],
  };
  const doughnutOptions = { plugins: { legend: { display: false } }, cutout: '70%', maintainAspectRatio: false };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 animate-fade-in bg-gray-50 min-h-screen">
      
      {/* ส่วนหัว */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 tracking-tight">สรุปผลการวิเคราะห์</h2>
          <p className="text-sm text-gray-500 mt-1">ประมวลผลเสร็จสิ้น {total} ภาพ</p>
        </div>
        
        <div className="flex space-x-3 mt-4 sm:mt-0">
            {/* ปุ่มจำแนกหมวดหมู่ (จะโชว์เฉพาะตอนที่มีรูป Passed) */}
            {passedCount > 0 && (
                <button 
                    onClick={handleClassify} 
                    disabled={isClassifying}
                    className="bg-emerald-500 text-white px-5 py-2.5 rounded-xl hover:bg-emerald-600 font-medium transition shadow-sm disabled:opacity-50 flex items-center"
                >
                    {isClassifying ? (
                        <span className="animate-pulse">⏳ กำลังจำแนกภาพ...</span>
                    ) : (
                        <span>จำแนกภาพ</span>
                    )}
                </button>
            )}

            {/* ปุ่มอัปโหลดชุดใหม่ */}
            <button onClick={onReset} className="bg-indigo-600 text-white px-5 py-2.5 rounded-xl hover:bg-indigo-700 font-medium transition shadow-sm flex items-center">
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"></path></svg>
                อัปโหลดชุดใหม่
            </button>
        </div>
      </div>

      {/* Grid กราฟและสถิติ */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* สาเหตุที่ถูกคัดออก */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
            <h3 className="font-bold text-gray-800 mb-6">สาเหตุที่ถูกคัดออก (Defect Analysis)</h3>
            <div className="space-y-5 max-h-[200px] overflow-y-auto pr-2">
                {defectEntries.length > 0 ? (
                    defectEntries.map(([reason, count], idx) => (
                        <div key={idx}>
                            <div className="flex justify-between text-sm mb-2 font-medium text-gray-700">
                                <span>{reason}</span>
                                <span>{count} ภาพ</span>
                            </div>
                            <div className="w-full bg-gray-100 rounded-full h-2.5">
                                <div className="bg-red-400 h-2.5 rounded-full" style={{ width: `${(count/total)*100}%` }}></div>
                            </div>
                        </div>
                    ))
                ) : (
                    <div className="h-full flex items-center justify-center text-gray-400 py-10">ไม่พบข้อผิดพลาดเลย 🎉</div>
                )}
            </div>
        </div>

        {/* สัดส่วนรูปแบบภาพ (Doughnut Chart) */}
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex flex-col">
            <h3 className="font-bold text-gray-800 mb-4">สัดส่วนภาพที่ผ่านเกณฑ์ (Classification)</h3>
            <div className="flex items-center flex-grow">
                <div className="w-32 h-32 relative flex-shrink-0">
                    {passedCount > 0 ? (
                        <Doughnut data={doughnutChartData} options={doughnutOptions} />
                    ) : (
                        <div className="w-full h-full rounded-full border-8 border-gray-100"></div>
                    )}
                    <div className="absolute inset-0 flex items-center justify-center flex-col">
                        <span className="text-xl font-bold text-gray-700">{passedCount}</span>
                        <span className="text-[10px] text-gray-400">PASSED</span>
                    </div>
                </div>
                
                {/* Custom Legend ของกราฟโดนัท */}
                <div className="ml-8 space-y-3 flex-grow justify-center">
                    {passedCount === 0 ? (
                        <div className="text-sm text-gray-500 italic">ไม่มีรูปผ่านเกณฑ์</div>
                    ) : !classificationData ? (
                        <div className="text-sm text-gray-500 italic flex items-center">
                            <span className="w-3 h-3 rounded-full bg-gray-200 mr-2"></span> รอการกดปุ่มจำแนกภาพ...
                        </div>
                    ) : (
                        doughnutLabels.map((label, idx) => (
                            <div key={idx} className="flex justify-between text-sm text-gray-600">
                                <div className="flex items-center">
                                    <span className="w-3 h-3 rounded-full mr-3" style={{ backgroundColor: doughnutColors[idx] }}></span>
                                    <span>{label}</span>
                                </div>
                                <span className="font-medium">{doughnutDataValues[idx]} ภาพ</span>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
      </div>

      {/* รายการภาพ */}
      <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 mb-10">
        <div className="flex flex-col sm:flex-row justify-between items-center mb-6">
            <h3 className="font-bold text-gray-800 text-lg">รายการภาพ (Image List)</h3>
            <div className="flex bg-gray-100 p-1 rounded-xl mt-4 sm:mt-0">
                <button onClick={() => setFilter('all')} className={`px-4 py-1.5 text-sm rounded-lg transition ${filter === 'all' ? 'bg-gray-800 text-white shadow' : 'text-gray-600 hover:bg-gray-200'}`}>ทั้งหมด</button>
                <button onClick={() => setFilter('passed')} className={`px-4 py-1.5 text-sm rounded-lg transition ${filter === 'passed' ? 'bg-white text-gray-800 shadow' : 'text-gray-600 hover:bg-gray-200'}`}>เฉพาะผ่าน</button>
                <button onClick={() => setFilter('rejected')} className={`px-4 py-1.5 text-sm rounded-lg transition ${filter === 'rejected' ? 'bg-white text-gray-800 shadow' : 'text-gray-600 hover:bg-gray-200'}`}>เฉพาะไม่ผ่าน</button>
            </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-5">
          {filteredImages.map((img, idx) => {
            const isPassed = img.status === 'Passed';
            const tagInfo = getReasonTag(img.defect_reason);
            const subDetail = getDetailText(img.defect_reason);

            return (
                <div 
                    key={idx} 
                    onClick={() => setSelectedImage(img)}
                    className={`cursor-pointer group flex flex-col rounded-2xl overflow-hidden shadow-sm border-2 transition-all hover:-translate-y-1 hover:shadow-lg ${isPassed ? 'border-transparent hover:border-indigo-200 bg-white' : 'border-red-100 hover:border-red-300 bg-red-50/20'}`}
                >
                    {/* ภาพ Thumbnail */}
                    <div className="relative h-44 bg-gray-200 overflow-hidden">
                        <img src={`${API_BASE}${img.url}`} alt={img.filename} className="w-full h-full object-cover group-hover:scale-105 transition duration-500" />
                        <span className={`absolute top-3 right-3 text-xs px-3 py-1 rounded-lg font-bold shadow-sm ${isPassed ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                            {isPassed ? 'Passed' : 'Rejected'}
                        </span>
                    </div>
                    
                    {/* รายละเอียดการ์ด */}
                    <div className="p-4 flex flex-col flex-grow">
                        <div className="flex justify-between items-start mb-3 gap-2">
                            <span className={`text-[11px] font-bold px-2.5 py-1.5 rounded-lg ${tagInfo.color}`}>
                                {tagInfo.text}
                            </span>
                            
                            {/* ป้ายหมวดหมู่ AI (โชว์ถ้ารูปนี้มี Category จากการ Classify แล้ว) */}
                            {img.category && (
                                <span className={`text-[11px] font-bold px-2.5 py-1.5 rounded-lg ${img.category === 'วิทยากร' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'}`}>
                                    {img.category}
                                </span>
                            )}
                        </div>
                        <div className="text-xs text-gray-400 truncate mb-2">{img.filename}</div>
                        
                        <div className="mt-auto space-y-1">
                            {isPassed ? (
                                <p className="text-[11px] text-gray-500 truncate">
                                    {img.clsReason ? `Detail: ${img.clsReason}` : `Score: ${img.score}`}
                                </p>
                            ) : (
                                <>
                                    <p className="text-[11px] font-medium text-red-800 truncate">Reason: {tagInfo.text}</p>
                                    <p className="text-[11px] text-red-500 truncate">{subDetail ? `Detail: ${subDetail}` : ''}</p>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            );
          })}
        </div>
        
        {filteredImages.length === 0 && (
            <div className="text-center py-10 text-gray-400">ไม่มีรูปภาพในหมวดหมู่นี้</div>
        )}
      </div>

      {/* ========================================== */}
      {/* MODAL POPUP สำหรับดูรูปขนาดใหญ่และรายละเอียด */}
      {/* ========================================== */}
      {selectedImage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in" onClick={() => setSelectedImage(null)}>
            <div className="bg-white rounded-2xl overflow-hidden max-w-4xl w-full flex flex-col md:flex-row shadow-2xl" onClick={e => e.stopPropagation()}>
                
                {/* ส่วนรูปภาพซ้ายมือ */}
                <div className="md:w-2/3 bg-gray-900 flex items-center justify-center relative min-h-[300px]">
                    <img src={`${API_BASE}${selectedImage.url}`} alt="Enlarged" className="max-w-full max-h-[70vh] object-contain" />
                    <button 
                        onClick={() => setSelectedImage(null)}
                        className="absolute top-4 right-4 bg-black/50 text-white w-8 h-8 rounded-full flex items-center justify-center hover:bg-red-500 transition md:hidden"
                    >
                        ✕
                    </button>
                </div>

                {/* ส่วนรายละเอียดขวามือ */}
                <div className="md:w-1/3 p-6 flex flex-col">
                    <div className="flex justify-between items-start mb-6 hidden md:flex">
                        <h3 className="text-xl font-bold text-gray-900">รายละเอียด</h3>
                        <button onClick={() => setSelectedImage(null)} className="text-gray-400 hover:text-red-500 transition text-xl font-bold">✕</button>
                    </div>

                    <div className="space-y-4">
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">ชื่อไฟล์</p>
                            <p className="font-medium text-gray-800 break-all">{selectedImage.filename}</p>
                        </div>
                        
                        <div>
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">สถานะ</p>
                            <span className={`inline-flex px-3 py-1 rounded-lg text-sm font-bold ${selectedImage.status === 'Passed' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                                {selectedImage.status}
                            </span>
                        </div>

                        {/* หมวดหมู่ภาพ (ถ้าถูก Classify แล้ว) */}
                        {selectedImage.category && (
                            <div>
                                <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">หมวดหมู่ภาพ</p>
                                <span className="inline-flex px-3 py-1 rounded-lg text-sm font-bold bg-blue-100 text-blue-700">
                                    {selectedImage.category}
                                </span>
                                <p className="text-xs text-gray-500 mt-2">{selectedImage.clsReason}</p>
                            </div>
                        )}

                        <div className="bg-gray-50 p-4 rounded-xl border">
                            <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">ผลการประมวลผลพื้นฐาน</p>
                            <p className="text-sm font-medium text-gray-800 mb-1">
                                {selectedImage.status === 'Passed' ? '✔ ตรวจสอบคุณภาพผ่าน' : `✘ ${getReasonTag(selectedImage.defect_reason).text}`}
                            </p>
                            {selectedImage.status === 'Rejected' && (
                                <p className="text-xs text-red-600 mt-2">{selectedImage.defect_reason}</p>
                            )}
                        </div>
                    </div>

                    <div className="mt-auto pt-6">
                        {/* ลิงก์ไปดูรูปต้นฉบับ (ไม่มีกรอบ) */}
                        <a 
                            href={`${API_BASE}/images/original/${selectedImage.filename}`} 
                            target="_blank" 
                            rel="noreferrer"
                            className="w-full block text-center bg-gray-100 text-gray-700 py-2.5 rounded-xl font-medium hover:bg-gray-200 transition"
                        >
                            เปิดรูปเต็ม
                        </a>
                    </div>
                </div>
            </div>
        </div>
      )}

    </div>
  );
}