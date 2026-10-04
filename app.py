import os
import gradio as gr
import spaces
from data_manager import fetch_and_process_data, get_user_info

# นำเข้าฟังก์ชันสร้างหน้าตา UI จากโฟลเดอร์ tabs 
from tabs.tab_1_exec import build_tab1
from tabs.tab_2_risk import build_tab2
from tabs.tab_3_opp import build_tab3
from tabs.tab_4_data import build_tab4

# ==========================================
# 🎨 ส่วนที่ 1: ชุดโค้ด CSS (รวมการตั้งค่า Hover สีแดง)
# ==========================================
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

* { font-family: 'Prompt', sans-serif !important; }

body, .gradio-container {
    background-color: #e0e5ec !important; 
}

/* สไตล์กล่อง KPI แบบ Neumorphism */
.kpi-card {
    background-color: #e0e5ec !important;
    border-radius: 20px !important;
    box-shadow: 7px 7px 14px rgba(163,177,198,0.7), -7px -7px 14px rgba(255,255,255, 0.9) !important;
    padding: 20px !important;
    text-align: center !important;
    margin: 10px !important;
    transition: all 0.3s ease-in-out !important;
}

/* 🖱️ เอฟเฟกต์ Hover: เปลี่ยนพื้นเป็นสีแดง และตัวอักษรเป็นสีขาว */
.kpi-card:hover {
    transform: translateY(-5px) !important;
    background-color: #dc2626 !important; /* สีแดงไปรษณีย์ */
    box-shadow: 10px 10px 20px rgba(220,38,38,0.3), -5px -5px 15px rgba(255,255,255, 0.8) !important;
}

.kpi-card:hover .kpi-title, 
.kpi-card:hover .kpi-value, 
.kpi-card:hover .kpi-icon,
.kpi-card:hover div {
    color: #ffffff !important; /* บังคับอักษรเป็นสีขาว */
}

.kpi-icon { font-size: 35px !important; margin-bottom: 10px !important; }
.kpi-title { font-size: 14px !important; color: #4a5568 !important; font-weight: 500 !important; }
.kpi-value { font-size: 26px !important; color: #1a202c !important; font-weight: 700 !important; margin-top: 5px !important; }

/* 📦 สไตล์กรอบและกล่องทั่วไป */
.wrap, .box, .form, .panel {
    background-color: #e0e5ec !important;
    border: none !important;
    border-radius: 20px !important;
    box-shadow: 9px 9px 16px rgb(163,177,198,0.6), -9px -9px 16px rgba(255,255,255, 0.6) !important;
    padding: 15px !important;
    margin-bottom: 15px !important;
}

/* 🔘 สไตล์ปุ่มกด Tabs */
button {
    background-color: #e0e5ec !important;
    color: #2d3748 !important; 
    font-weight: 600 !important;
    font-size: 16px !important;
    border: none !important;
    border-radius: 15px !important;
    box-shadow: 6px 6px 10px 0 rgba(163, 177, 198, 0.7), -6px -6px 10px 0 rgba(255, 255, 255, 0.8) !important;
    transition: all 0.2s ease-in-out !important;
}
button:hover, button:active, button.selected {
    box-shadow: inset 4px 4px 6px 0 rgba(163, 177, 198, 0.6), inset -4px -4px 6px 0 rgba(255, 255, 255, 0.8) !important;
    color: #dc2626 !important; 
}
"""

# ==========================================
# 🛑 ส่วนที่ 2: ฟังก์ชันหลอกสำหรับ Hugging Face ZeroGPU
# ==========================================
@spaces.GPU
def dummy_gpu_func():
    return "GPU enabled"

_ = dummy_gpu_func()

# ==========================================
# 📝 ส่วนที่ 3: โครงสร้าง Header (ชื่อเรื่อง, เครดิต, สถานะ Login)
# ==========================================
header_html = """
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; padding: 10px;">
    <div>
        <h2 style="margin: 0; color: #1a202c; font-weight: 700; font-size: 22px;">🚀 Dashboard ระบบวิเคราะห์สถิติการใช้บริการไปรษณีย์ของลูกค้ารายใหญ่กลุ่ม A B C และ D ในพื้นที่ ปข.3</h2>
        <p style="margin: 8px 0 0 0; color: #4a5568; font-size: 14px; font-weight: 500;">ผู้ออกแบบระบบโดย : สำนักงานไปรษณีย์เขต 3 | ส่วนการตลาดและบริการลูกค้า</p>
    </div>
    
    <div style="background-color: #e2e8f0; padding: 10px 20px; border-radius: 15px; box-shadow: inset 3px 3px 6px rgba(163,177,198,0.5), inset -3px -3px 6px rgba(255,255,255,0.8); display: flex; align-items: center; gap: 10px; min-width: max-content;">
        <div style="width: 12px; height: 12px; background-color: #16a34a; border-radius: 50%; box-shadow: 0 0 5px #16a34a;"></div>
        <span style="font-weight: 600; color: #2d3748; font-size: 14px;">ผู้ใช้งาน: <span style="color: #2b6cb0;">ADMIN</span></span>
    </div>
</div>
"""
# (โค้ดส่วน custom_css และ dummy_gpu_func คงไว้เหมือนเดิมครับ)

# ==========================================
# 🔐 ฟังก์ชันจัดการสิทธิ์ผู้ใช้งาน (ดึงชื่อคน Login)
# ==========================================
def load_user_profile(request: gr.Request):
    # ถ้ามีการ Login เข้ามา ดึงชื่อ (Username) มาใช้ ถ้าไม่มีให้เป็น ADMIN (สำหรับการรันทดสอบ)
    username = request.username if request else "ADMIN"
    
    # เช็กว่าถ้าเป็นตัวเลข (เช่น 30000) ให้ล็อกสิทธิ์เป็นสาขา ถ้าไม่ใช่ให้เป็นส่วนกลาง
    role = username if username.isnumeric() else "HQ_ADMIN"
    
    # สร้าง HTML Header ใหม่แบบไดนามิกที่แสดงรหัสคน Login จริง
    header = f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; padding: 10px;">
        <div>
            <h2 style="margin: 0; color: #1a202c; font-weight: 700; font-size: 22px;">🚀 Dashboard ระบบวิเคราะห์สถิติการใช้บริการไปรษณีย์ของลูกค้ารายใหญ่กลุ่ม A B C และ D ในพื้นที่ ปข.3</h2>
            <p style="margin: 8px 0 0 0; color: #4a5568; font-size: 14px; font-weight: 500;">ผู้ออกแบบระบบโดย : สำนักงานไปรษณีย์เขต 3 | ส่วนการตลาดและบริการลูกค้า</p>
        </div>
        <div style="background-color: #e2e8f0; padding: 10px 20px; border-radius: 15px; box-shadow: inset 3px 3px 6px rgba(163,177,198,0.5), inset -3px -3px 6px rgba(255,255,255,0.8); display: flex; align-items: center; gap: 10px; min-width: max-content;">
            <div style="width: 12px; height: 12px; background-color: #16a34a; border-radius: 50%; box-shadow: 0 0 5px #16a34a;"></div>
            <span style="font-weight: 600; color: #2d3748; font-size: 14px;">ผู้ใช้งาน: <span style="color: #dc2626;">{username}</span></span>
        </div>
    </div>
    """
    return header, role

# ==========================================
# 🚀 โครงสร้างหน้าเว็บหลัก
# ==========================================
with gr.Blocks(title="Dashboard ปข.3", css=custom_css) as demo:
    
    # ตัวแปรซ่อนสำหรับเก็บ Role ของคนที่ Login
    user_role_state = gr.State("ADMIN")
    
    # 1. กล่อง Header ที่จะเปลี่ยนชื่อตามคน Login
    header_html_box = gr.HTML()
    
    # ตัวเลือกปีงบประมาณจริงจาก Google Sheets
    with gr.Row():
        selected_year = gr.Dropdown(
            choices=["2569", "2568", "2567", "2566"], 
            value="2569", 
            label="📅 เลือกปีงบประมาณข้อมูล", 
            interactive=True
        )
        refresh_btn = gr.Button("🔄 อัปเดตข้อมูลล่าสุดจาก Google Sheets", scale=0)

        
    
    # 3. ส่วนแท็บต่างๆ (รับค่าจาก Dropdown ไปใช้งาน)
    with gr.Tabs():
        with gr.Tab("สรุปผู้บริหาร (Executive)"):
            build_tab1()
        with gr.Tab("วิเคราะห์ความเสี่ยง (Risk)"):
            build_tab2()
        with gr.Tab("โอกาสทางธุรกิจ (Opportunity)"):
            build_tab3()
        with gr.Tab("จัดการข้อมูล (Data)"):
            build_tab4()

    # เมื่อเปิดหน้าเว็บขึ้นมา ให้ทำงานฟังก์ชัน load_user_profile ทันที
    demo.load(
        fn=load_user_profile, 
        inputs=None, 
        outputs=[header_html_box, user_role_state]
    )

if __name__ == "__main__":
    app.launch()
