import gradio as gr
import pandas as pd
from data_manager import fetch_and_process_data

def build_tab1(year_input, phone_input_state):
    
    @gr.render(inputs=[year_input, phone_input_state])
    def render_exec_summary(selected_year, current_phone):
        phone = current_phone if current_phone else "admin"
        year = selected_year if selected_year else "2569"
        
        # 1. ดึงข้อมูลจริงจาก Google Sheets
        try:
            df = fetch_and_process_data(phone_number=phone, year=year)
        except Exception as e:
            df = pd.DataFrame()

        total_rev = 0.0
        mail_pcs = 0.0
        logis_pcs = 0.0
        inter_pcs = 0.0

        # 2. คำนวณยอดเงินและจำนวนชิ้นจาก Dataframe
        if not df.empty:
            # คำนวณยอดเงินรวมทั้งหมด
            if 'ยอดเงินรวม' in df.columns:
                total_rev = df['ยอดเงินรวม'].sum()
            else:
                # กรณีหาคอลัมน์ 'ยอดเงินรวม' ไม่เจอ ให้รวมคอลัมน์สุดท้ายของ dataframe
                total_rev = pd.to_numeric(df.iloc[:, -1], errors='coerce').sum()

            # คำนวณจำนวนชิ้นไปรษณียภัณฑ์
            if 'ไปรษณียภัณฑ์_ชิ้น' in df.columns:
                mail_pcs = df['ไปรษณียภัณฑ์_ชิ้น'].sum()

            # คำนวณคอลัมน์ชิ้นอื่นๆ หากมีข้อมูล
            logis_cols = [c for c in df.columns if 'โลจิสติกส์' in str(c)]
            if logis_cols:
                logis_pcs = pd.to_numeric(df[logis_cols[0]], errors='coerce').sum()

            inter_cols = [c for c in df.columns if 'ต่างประเทศ' in str(c) or 'ระหว่างประเทศ' in str(c)]
            if inter_cols:
                inter_pcs = pd.to_numeric(df[inter_cols[0]], errors='coerce').sum()

        # 3. แสดงผลหน้าจอ UI
        with gr.Column():
            gr.Markdown(f"### 📈 สรุปภาพรวมผลประกอบการประจำปี {year}")
            
            # --- กล่อง KPI 4 ใบ ---
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
            
            # --- AI Executive Briefing ---
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🤖 AI Executive Briefing (สรุปวิเคราะห์เชิงลึก)")
                    gr.HTML(f"""
                    <div style='background-color:#fffbeb; border-left: 5px solid #f59e0b; padding:15px; border-radius:8px; box-shadow: 4px 4px 10px rgba(163,177,198,0.4), -4px -4px 10px rgba(255,255,255, 0.8);'>
                        <p><b>📌 ภาพรวม:</b> ดึงข้อมูลสถิติงบประมาณปี {year} รวมทั้งสิ้น <b>{total_rev:,.2f} บาท</b> สำเร็จ</p>
                        <p><b>⚠️ สัญญาณเตือน:</b> ตรวจสอบกลุ่มลูกค้ารายใหญ่ที่มีการปรับลดปริมาณการส่งกะทันหัน</p>
                        <p><b>💡 ข้อเสนอแนะ:</b> เร่งกระตุ้นยอดขายในพื้นที่บริการของสังกัดที่มีแนวโน้มชะลอตัว</p>
                    </div>
                    """)
            
            gr.Markdown("---")
            gr.Markdown("### 📋 ข้อมูลสถิติลูกค้ารายใหญ่ (ตามสิทธิ์ผู้ใช้งาน)")
            
            # ตารางแสดงข้อมูล
            if not df.empty:
                gr.Dataframe(df, interactive=False)
            else:
                gr.Dataframe(pd.DataFrame({"สถานะ": ["ไม่พบข้อมูล หรือกำลังเชื่อมต่อฐานข้อมูล Google Sheets..."]}), interactive=False)
