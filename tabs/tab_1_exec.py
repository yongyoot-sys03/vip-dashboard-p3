import gradio as gr

def render(role):
    visible = role in ["ADMIN", "REG03", "MANAGER"]
    
    with gr.Tab("📊 Executive Summary", visible=visible):
        gr.Markdown("### 📈 สรุปภาพรวมผลประกอบการรายปี")
        
        # --- กล่อง KPI 4 ใบ (ใช้ HTML + CSS เพื่อให้มีมิตินูน) ---
        with gr.Row():
            gr.HTML("""
                <div class='kpi-card'>
                    <div class='kpi-icon'>💰</div>
                    <div class='kpi-title'>รายได้รวมทั้งหมด (บาท)</div>
                    <div class='kpi-value'>15,420,000</div>
                    <div style='color:#16a34a; font-size:12px; margin-top:8px;'>▲ เติบโต 12% YoY</div>
                </div>
            """)
            gr.HTML("""
                <div class='kpi-card'>
                    <div class='kpi-icon'>✉️</div>
                    <div class='kpi-title'>ไปรษณียภัณฑ์ (ชิ้น)</div>
                    <div class='kpi-value'>1,250,300</div>
                    <div style='color:#16a34a; font-size:12px; margin-top:8px;'>▲ เติบโต 5% YoY</div>
                </div>
            """)
            gr.HTML("""
                <div class='kpi-card'>
                    <div class='kpi-icon'>📦</div>
                    <div class='kpi-title'>ขนส่งและโลจิสติกส์ (ชิ้น)</div>
                    <div class='kpi-value'>42,500</div>
                    <div style='color:#dc2626; font-size:12px; margin-top:8px;'>▼ ลดลง 3% YoY</div>
                </div>
            """)
            gr.HTML("""
                <div class='kpi-card'>
                    <div class='kpi-icon'>✈️</div>
                    <div class='kpi-title'>ระหว่างประเทศ (ชิ้น)</div>
                    <div class='kpi-value'>8,900</div>
                    <div style='color:#16a34a; font-size:12px; margin-top:8px;'>▲ เติบโต 25% YoY</div>
                </div>
            """)
        
        gr.Markdown("---")
        
        # --- กล่อง AI สรุป ---
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 🤖 AI Executive Briefing (สรุปวิเคราะห์เชิงลึก)")
                gr.HTML("""
                <div style='background-color:#fffbeb; border-left: 5px solid #f59e0b; padding:15px; border-radius:8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
                    <p><b>📌 ภาพรวม:</b> รายได้หลักมาจาก 'บริการไปรษณียภัณฑ์' คิดเป็น 75% ของรายได้ทั้งหมด ขับเคลื่อนโดยกลุ่ม 'สินเชื่อ'</p>
                    <p><b>⚠️ สัญญาณเตือน:</b> พบลูกค้ารายใหญ่ 2 รายในหมวด 'ประกันภัย' มียอดใช้บริการโลจิสติกส์ลดลงอย่างมีนัยสำคัญ</p>
                    <p><b>💡 ข้อเสนอแนะ:</b> ควรจัดแคมเปญกระตุ้นยอด eCo-Post ในกลุ่มลูกค้าสินเชื่อ (B836)</p>
                </div>
                """)
