import gradio as gr
import pandas as pd
from data_manager import fetch_and_process_data

def build_tab1(year_input, phone_input_state):
    
    @gr.render(inputs=[year_input, phone_input_state])
    def render_exec_summary(selected_year, current_phone):
        phone = current_phone if current_phone else "admin"
        year = selected_year if selected_year else "2569"
        
        try:
            df = fetch_and_process_data(phone_number=phone, year=year)
        except Exception as e:
            df = pd.DataFrame()

        total_rev, mail_pcs, logis_pcs, inter_pcs = 0, 0, 0, 0

        if not df.empty:
            rev_col = [c for c in df.columns if 'ยอดเงิน' in c or 'บาท' in c]
            if rev_col:
                total_rev = pd.to_numeric(df[rev_col[0]], errors='coerce').sum()
                
            mail_col = [c for c in df.columns if 'ไปรษณียภัณฑ์' in c or 'จดหมาย' in c]
            if mail_col:
                mail_pcs = pd.to_numeric(df[mail_col[0]], errors='coerce').sum()

            logis_col = [c for c in df.columns if 'โลจิสติกส์' in c or 'พัสดุ' in c]
            if logis_col:
                logis_pcs = pd.to_numeric(df[logis_col[0]], errors='coerce').sum()

            inter_col = [c for c in df.columns if 'ต่างประเทศ' in c or 'ระหว่างประเทศ' in c]
            if inter_col:
                inter_pcs = pd.to_numeric(df[inter_col[0]], errors='coerce').sum()

        with gr.Column():
            gr.Markdown(f"### 📈 สรุปภาพรวมผลประกอบการประจำปี {year}")
            
            with gr.Row():
                gr.HTML(f"""
                    <div class='kpi-card'>
                        <div class='kpi-icon'>💰</div>
                        <div class='kpi-title'>รายได้รวมทั้งหมด (บาท)</div>
                        <div class='kpi-value'>{total_rev:,.2f}</div>
                    </div>
                """)
                gr.HTML(f"""
                    <div class='kpi-card'>
                        <div class='kpi-icon'>✉️</div>
                        <div class='kpi-title'>ไปรษณียภัณฑ์ (ชิ้น)</div>
                        <div class='kpi-value'>{mail_pcs:,.0f}</div>
                    </div>
                """)
                gr.HTML(f"""
                    <div class='kpi-card'>
                        <div class='kpi-icon'>📦</div>
                        <div class='kpi-title'>ขนส่งและโลจิสติกส์ (ชิ้น)</div>
                        <div class='kpi-value'>{logis_pcs:,.0f}</div>
                    </div>
                """)
                gr.HTML(f"""
                    <div class='kpi-card'>
                        <div class='kpi-icon'>✈️</div>
                        <div class='kpi-title'>ระหว่างประเทศ (ชิ้น)</div>
                        <div class='kpi-value'>{inter_pcs:,.0f}</div>
                    </div>
                """)
            
            gr.Markdown("---")
            
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🤖 AI Executive Briefing (สรุปวิเคราะห์เชิงลึก)")
                    gr.HTML("""
                    <div style='background-color:#fffbeb; border-left: 5px solid #f59e0b; padding:15px; border-radius:8px; box-shadow: 4px 4px 10px rgba(163,177,198,0.4), -4px -4px 10px rgba(255,255,255, 0.8);'>
                        <p><b>📌 ภาพรวม:</b> ดึงข้อมูลยอดสะสมจาก Google Sheets ประจำปีเลือกสำเร็จ</p>
                        <p><b>⚠️ สัญญาณเตือน:</b> ตรวจสอบกลุ่มลูกค้ารายใหญ่ที่มีการปรับลดปริมาณการส่งกะทันหัน</p>
                        <p><b>💡 ข้อเสนอแนะ:</b> เร่งกระตุ้นยอดขายในพื้นที่บริการของสังกัดที่มีแนวโน้มชะลอตัว</p>
                    </div>
                    """)
            
            gr.Markdown("---")
            gr.Markdown("### 📋 ข้อมูลสถิติลูกค้ารายใหญ่ (ตามสิทธิ์ผู้ใช้งาน)")
            gr.Dataframe(df if not df.empty else pd.DataFrame({"ข้อความ": ["ไม่พบข้อมูล หรือไม่มีสิทธิ์เข้าถึง"]}), interactive=False)
