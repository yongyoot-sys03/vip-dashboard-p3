import gradio as gr

def build_tab4(role="ADMIN"):
    # เช็กสิทธิ์การมองเห็น
    is_visible = role in ["ADMIN", "REG03", "MANAGER"]
    
    with gr.Column(visible=is_visible):
        gr.Markdown("### 🗄️ ฐานข้อมูลลูกค้ารายใหญ่ ปข.3 (Smart Data Center)")
        
        # สร้างกล่องพื้นหลังสไตล์ Neumorphism (รอใส่ตารางข้อมูล)
        gr.HTML("""
            <div style='background-color: #e0e5ec; border-radius: 20px; box-shadow: 9px 9px 16px rgba(163,177,198,0.6), -9px -9px 16px rgba(255,255,255, 0.6); padding: 30px; text-align: center; margin-top: 20px;'>
                <h2 style='color: #718096;'>🚧 กำลังพัฒนาระบบจัดการฐานข้อมูล 🚧</h2>
                <p style='color: #a0aec0;'>ส่วนนี้จะใช้สำหรับเชื่อมต่อ Google Sheets, อัปเดตข้อมูล และแสดงตารางสถิติแบบ Real-time</p>
            </div>
        """)
