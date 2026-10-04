import os
import gradio as gr
import spaces

# นำเข้าแท็บต่างๆ ของคุณ (ปรับให้ตรงกับชื่อไฟล์จริงของคุณ)
from tabs.tab_1_exec import build_tab1
from tabs.tab_2_risk import build_tab2
from tabs.tab_3_opp import build_tab3
from tabs.tab_4_data import build_tab4

# ==========================================
# 🎨 ส่วนที่ 1: ชุดโค้ด CSS สำหรับตกแต่ง UI ให้มีมิติ นูน และทันสมัย
# ==========================================
custom_css = """
/* นำเข้าฟอนต์ Prompt จาก Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;500;600;700&display=swap');

/* บังคับให้ทุกส่วนใช้ฟอนต์ Prompt และปรับสีพื้นหลังให้สบายตา */
* {
    font-family: 'Prompt', sans-serif !important;
}

body, .gradio-container {
    background-color: #e0e5ec !important; /* สีเทาอมฟ้าอ่อนๆ พื้นฐานของ Neumorphism */
}

/* 📦 สไตล์กรอบและกล่อง (Frames/Cards) ให้ดูนูนขึ้นมา */
.wrap, .box, .form, .panel {
    background-color: #e0e5ec !important;
    border: none !important;
    border-radius: 20px !important;
    box-shadow: 9px 9px 16px rgb(163,177,198,0.6), -9px -9px 16px rgba(255,255,255, 0.6) !important;
    padding: 15px !important;
    margin-bottom: 15px !important;
}

/* 🔘 สไตล์ปุ่มกด (Buttons) ให้นูนลอยขึ้นมา */
button {
    background-color: #e0e5ec !important;
    color: #2d3748 !important; /* สีตัวหนังสือเข้มชัดเจน */
    font-weight: 600 !important;
    font-size: 16px !important;
    border: none !important;
    border-radius: 15px !important;
    box-shadow: 6px 6px 10px 0 rgba(163, 177, 198, 0.7), -6px -6px 10px 0 rgba(255, 255, 255, 0.8) !important;
    transition: all 0.2s ease-in-out !important;
}

/* เอฟเฟกต์เวลากดปุ่ม หรือเอาเมาส์ชี้ (ยุบตัวลงไป) */
button:hover, button:active {
    box-shadow: inset 4px 4px 6px 0 rgba(163, 177, 198, 0.6), inset -4px -4px 6px 0 rgba(255, 255, 255, 0.8) !important;
    color: #2b6cb0 !important; /* เปลี่ยนเป็นสีน้ำเงินเข้มตอนชี้ */
}

/* 📝 สไตล์ตัวหนังสือให้คมชัด มีเฉดเงาบางๆ */
h1, h2, h3, Markdown {
    color: #1a202c !important;
    text-shadow: 1px 1px 2px rgba(255,255,255,0.8) !important;
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
# 🚀 ส่วนที่ 3: โครงสร้างหน้าเว็บหลัก (ใส่ css=custom_css เข้าไป)
# ==========================================
with gr.Blocks(title="VIP Dashboard P3", css=custom_css) as demo:
    
    gr.Markdown("# 🚀 VIP Dashboard P3: ระบบวิเคราะห์สถิติลูกค้ารายใหญ่")
    
    with gr.Tabs():
        with gr.Tab("สรุปผู้บริหาร (Executive)"):
            build_tab1()
            
        with gr.Tab("วิเคราะห์ความเสี่ยง (Risk)"):
            build_tab2()
            
        with gr.Tab("โอกาสทางธุรกิจ (Opportunity)"):
            build_tab3()
            
        with gr.Tab("จัดการข้อมูล (Data)"):
            build_tab4()

if __name__ == "__main__":
    demo.launch()
