import gradio as gr
import pandas as pd
from data_manager import fetch_and_process_data

def build_tab1(year_input, user_id_input):
    
    # ใช้ gr.render เพื่อให้อัปเดตข้อมูลอัตโนมัติเมื่อมีการเปลี่ยนปี หรือ User เปลี่ยน
    @gr.render(inputs=[year_input, user_id_input])
    def render_exec_summary(selected_year, current_user_id):
        
        # 1. ดึงข้อมูลจริงจาก Google Sheets ผ่าน data_manager
        # (ระบบจะทำการ Merge กับหน้า 'รายชื่อ' และกรองตามสิทธิ์ Role/ZIPCODE ให้อัตโนมัติ)
        df = fetch_and_process_data(user_id=current_user_id, year=selected_year)
        
        # 2. คำนวณยอดรวมจริงจาก Dataframe
        if not df.empty:
            # รวมยอดรายได้ทั้งหมด
            total_rev = df['ยอดเงินรวม'].sum() if 'ยอดเงินรวม' in df.columns else df['ยอดเงิน'].sum() if 'ยอดเงิน' in df.columns else 0
            
            # รวมจำนวนชิ้นตามประเภทบริการ (ดึงตามชื่อคอลัมน์ใน Sheet จริง)
            mail_pcs = df['ไปรษณียภัณฑ์_ชิ้น'].sum() if 'ไปรษณียภัณฑ์_ชิ้น' in df.columns else 0
            logis_pcs = df['ขนส่งโลจิสติกส์_ชิ้น'].sum() if 'ขนส่งโลจิสติกส์_ชิ้น' in df.columns else 0
            inter_pcs = df['ระหว่างประเทศ_ชิ้น'].sum() if 'ระหว่างประเทศ_ชิ้น' in df.columns else 0
        else:
            total_rev, mail_pcs, logis_pcs, inter_pcs = 0, 0, 0, 0

        # 3. แสดงผล UI
        with gr.Column():
            gr.Markdown(f"### 📈 สรุปภาพรวมผลประกอบการประจำปี {selected_year}")
            
            # --- กล่อง KPI 4 ใบ (ดึงตัวเลขจริง + สไตล์ Neumorphism) ---
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
            
            # --- กล่อง AI Executive Briefing ---
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🤖 AI Executive Briefing (สรุปวิเคราะห์เชิงลึก)")
                    gr.HTML("""
                    <div style='background-color:#fffbeb; border-left: 5px solid #f59e0b; padding:15px; border-radius:8px; box-shadow: 4px 4px 10px rgba(163,177,198,0.4), -4px -4px 10px rgba(255,255,255, 0.8);'>
                        <p><b>📌 ภาพรวม:</b> ดึงข้อมูลยอดสะสมจริงจาก Google Sheets ประจำปีเลือกสำเร็จ</p>
                        <p><b>⚠️ สัญญาณเตือน:</b> ตรวจสอบกลุ่มลูกค้ารายใหญ่ที่มีการปรับลดปริมาณการส่งกะทันหัน</p>
                        <p><b>💡 ข้อเสนอแนะ:</b> เร่งกระตุ้นยอดขายในพื้นที่บริการของสังกัดที่มีแนวโน้มชะลอตัว</p>
                    </div>
                    """)
            
            gr.Markdown("---")
            gr.Markdown("### 📋 ข้อมูลสถิติลูกค้ารายใหญ่ (ตามสิทธิ์ผู้ใช้งาน)")
            # แสดงตารางข้อมูลจริงที่ถูกกรองตามสิทธิ์แล้ว
            gr.Dataframe(df, interactive=False)
