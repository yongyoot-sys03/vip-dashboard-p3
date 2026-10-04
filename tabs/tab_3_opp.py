import gradio as gr

def build_tab3(role="ADMIN"):
    # เช็กสิทธิ์การมองเห็น
    is_visible = role in ["ADMIN", "REG03", "MANAGER"]
    
    with gr.Column(visible=is_visible):
        gr.Markdown("### 🎯 โอกาสในการขายเพิ่ม (Opportunity & Growth)")
        
        # สร้างกล่องพื้นหลังสไตล์ Neumorphism (รอใส่ข้อมูล ML / กราฟ)
        gr.HTML("""
            <div style='background-color: #e0e5ec; border-radius: 20px; box-shadow: 9px 9px 16px rgba(163,177,198,0.6), -9px -9px 16px rgba(255,255,255, 0.6); padding: 30px; text-align: center; margin-top: 20px;'>
                <h2 style='color: #718096;'>🚧 กำลังพัฒนาระบบแนะนำโอกาสเติบโต 🚧</h2>
                <p style='color: #a0aec0;'>ส่วนนี้จะแสดงข้อมูล Cross-sell / Up-sell และการคาดการณ์ยอดขายจากโมเดล ML</p>
            </div>
        """)
