import gradio as gr
import pandas as pd
from data_manager import fetch_and_process_data

def build_tab1(year_input, phone_input_state):
    
    @gr.render(inputs=[year_input, phone_input_state])
    def render_exec_summary(selected_year, current_phone):
        phone = current_phone if current_phone else "admin"
        year = selected_year if selected_year else "2568"
        
        try:
            df = fetch_and_process_data(phone_number=phone, year=year)
        except Exception as e:
            print(f"Error fetching data in tab1: {e}")
            df = pd.DataFrame()

        # กำหนดค่าเริ่มต้น
        total_rev, mail_pcs, mail_baht, logis_pcs, logis_baht, inter_pcs, inter_baht = [0.0] * 7

        if not df.empty:
            total_rev = pd.to_numeric(df['ยอดเงินรวม'], errors='coerce').sum() if 'ยอดเงินรวม' in df.columns else 0.0
            
            mail_pcs = pd.to_numeric(df['ไปรษณียภัณฑ์_ชิ้น'], errors='coerce').sum() if 'ไปรษณียภัณฑ์_ชิ้น' in df.columns else 0.0
            mail_baht = pd.to_numeric(df['ไปรษณียภัณฑ์_บาท'], errors='coerce').sum() if 'ไปรษณียภัณฑ์_บาท' in df.columns else 0.0
            
            logis_pcs = pd.to_numeric(df['ขนส่งโลจิสติกส์_ชิ้น'], errors='coerce').sum() if 'ขนส่งโลจิสติกส์_ชิ้น' in df.columns else 0.0
            logis_baht = pd.to_numeric(df['ขนส่งโลจิสติกส์_บาท'], errors='coerce').sum() if 'ขนส่งโลจิสติกส์_บาท' in df.columns else 0.0
            
            inter_pcs = pd.to_numeric(df['ระหว่างประเทศ_ชิ้น'], errors='coerce').sum() if 'ระหว่างประเทศ_ชิ้น' in df.columns else 0.0
            inter_baht = pd.to_numeric(df['ระหว่างประเทศ_บาท'], errors='coerce').sum() if 'ระหว่างประเทศ_บาท' in df.columns else 0.0

        # คำนวณค่าเฉลี่ยต่อชิ้น (Yield) ป้องกันการหารด้วย 0
        mail_avg = (mail_baht / mail_pcs) if mail_pcs > 0 else 0.0
        logis_avg = (logis_baht / logis_pcs) if logis_pcs > 0 else 0.0
        inter_avg = (inter_baht / inter_pcs) if inter_pcs > 0 else 0.0

        # เตรียมข้อมูลให้ AI วิเคราะห์
        service_revs = {"ไปรษณียภัณฑ์": mail_baht, "โลจิสติกส์": logis_baht, "ระหว่างประเทศ": inter_baht}
        best_service = max(service_revs, key=service_revs.get) if total_rev > 0 else "ไม่มีข้อมูล"
        best_rev = service_revs.get(best_service, 0)
        best_pct = (best_rev / total_rev * 100) if total_rev > 0 else 0.0

        yields = {"ไปรษณียภัณฑ์": mail_avg, "โลจิสติกส์": logis_avg, "ระหว่างประเทศ": inter_avg}
        best_yield = max(yields, key=yields.get) if any(yields.values()) else "ไม่มีข้อมูล"
        best_yield_val = yields.get(best_yield, 0)

        # เริ่มส่วนแสดงผล UI
        with gr.Column():
            gr.Markdown(f"### 📈 สรุปภาพรวมผลประกอบการประจำปี {year}")
            
            # --- 1. กล่องรายได้รวมขนาดใหญ่ ---
            with gr.Row():
                gr.HTML(f"""
                    <div class='kpi-card' style='background-color:#1a202c !important; border-bottom: 5px solid #dc2626;'>
                        <div class='kpi-icon'>💰</div>
                        <div class='kpi-title' style='color:#cbd5e1 !important;'>รายได้สะสมรวมทั้งหมด (Total Revenue)</div>
                        <div class='kpi-value' style='color:white !important; font-size: 34px !important;'>{total_rev:,.2f} <span style='font-size:18px;'>บาท</span></div>
                    </div>
                """)

            # --- 2. Grid แยกหมวดหมู่ ชิ้น / บาท / เฉลี่ย ---
            gr.Markdown("#### 📊 เจาะลึกสถิติแยกตามประเภทบริการ")
            with gr.Row():
                gr.HTML(f"""
                    <div class='kpi-card'>
                        <div class='kpi-icon'>✉️</div>
                        <div class='kpi-title' style='font-size:16px !important; font-weight:bold !important;'>กลุ่มไปรษณียภัณฑ์</div>
                        <hr style='border: 1px solid #e2e8f0; margin: 12px 0;'>
                        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:14px;'>
                            <span style='color:#475569;'>📦 ปริมาณงาน:</span> <b style='color:#1e293b;'>{mail_pcs:,.0f} ชิ้น</b>
                        </div>
                        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:14px;'>
                            <span style='color:#475569;'>💵 รายได้:</span> <b style='color:#1e293b;'>{mail_baht:,.2f} บาท</b>
                        </div>
                        <div style='display:flex; justify-content:space-between; font-size:15px;'>
                            <span style='color:#16a34a; font-weight:bold;'>📈 เฉลี่ย:</span> <b style='color:#16a34a;'>{mail_avg:,.2f} บ./ชิ้น</b>
                        </div>
                    </div>
                """)
                gr.HTML(f"""
                    <div class='kpi-card'>
                        <div class='kpi-icon'>📦</div>
                        <div class='kpi-title' style='font-size:16px !important; font-weight:bold !important;'>กลุ่มโลจิสติกส์</div>
                        <hr style='border: 1px solid #e2e8f0; margin: 12px 0;'>
                        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:14px;'>
                            <span style='color:#475569;'>📦 ปริมาณงาน:</span> <b style='color:#1e293b;'>{logis_pcs:,.0f} ชิ้น</b>
                        </div>
                        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:14px;'>
                            <span style='color:#475569;'>💵 รายได้:</span> <b style='color:#1e293b;'>{logis_baht:,.2f} บาท</b>
                        </div>
                        <div style='display:flex; justify-content:space-between; font-size:15px;'>
                            <span style='color:#16a34a; font-weight:bold;'>📈 เฉลี่ย:</span> <b style='color:#16a34a;'>{logis_avg:,.2f} บ./ชิ้น</b>
                        </div>
                    </div>
                """)
                gr.HTML(f"""
                    <div class='kpi-card'>
                        <div class='kpi-icon'>✈️</div>
                        <div class='kpi-title' style='font-size:16px !important; font-weight:bold !important;'>กลุ่มระหว่างประเทศ</div>
                        <hr style='border: 1px solid #e2e8f0; margin: 12px 0;'>
                        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:14px;'>
                            <span style='color:#475569;'>📦 ปริมาณงาน:</span> <b style='color:#1e293b;'>{inter_pcs:,.0f} ชิ้น</b>
                        </div>
                        <div style='display:flex; justify-content:space-between; margin-bottom:8px; font-size:14px;'>
                            <span style='color:#475569;'>💵 รายได้:</span> <b style='color:#1e293b;'>{inter_baht:,.2f} บาท</b>
                        </div>
                        <div style='display:flex; justify-content:space-between; font-size:15px;'>
                            <span style='color:#16a34a; font-weight:bold;'>📈 เฉลี่ย:</span> <b style='color:#16a34a;'>{inter_avg:,.2f} บ./ชิ้น</b>
                        </div>
                    </div>
                """)
            
            gr.Markdown("---")
            
            # --- 3. AI Executive Briefing (วิเคราะห์เชิงลึก) ---
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 🤖 AI Executive Briefing (สรุปวิเคราะห์เชิงลึกข้อมูลลูกค้ารายใหญ่ ปข.3)")
                    gr.HTML(f"""
                    <div style='background-color:#fffbeb; border-left: 6px solid #f59e0b; padding:20px; border-radius:8px; box-shadow: 4px 4px 10px rgba(163,177,198,0.4); line-height: 1.8;'>
                        <p style='margin-bottom:10px;'><b>📌 โครงสร้างรายได้ (Revenue Composition):</b> จากฐานข้อมูลลูกค้ารายใหญ่ปี {year} ทำยอดรวมได้ <b>{total_rev:,.2f} บาท</b> โดยบริการที่เป็นเส้นเลือดใหญ่ (Core Business) ของ ปข.3 คือ <b>{best_service}</b> ซึ่งสร้างรายได้ถึง {best_rev:,.2f} บาท หรือคิดเป็นสัดส่วนมหาศาลถึง <b>{best_pct:.1f}%</b> ของรายได้ทั้งหมด</p>
                        <p style='margin-bottom:10px;'><b>💎 คุณภาพรายได้และผลตอบแทน (Yield Analysis):</b> เมื่อเจาะลึกค่าเฉลี่ยต่อชิ้น พบว่าบริการ <b>{best_yield}</b> ให้ผลตอบแทนสูงที่สุดที่ <b>{best_yield_val:,.2f} บาท/ชิ้น</b> แสดงให้เห็นว่าเป็นกลุ่มบริการ High-Margin ที่คุ้มค่าต่อต้นทุนการจัดการขนส่งอย่างมาก</p>
                        <p style='margin-bottom:10px;'><b>⚠️ สัญญาณเตือนเชิงโครงสร้าง (Risk Warning):</b> หากสัดส่วนพึ่งพาบริการใดบริการหนึ่งสูงกว่า 75% ระบบประเมินว่าเป็นความเสี่ยงทางธุรกิจ ควรระวังผลกระทบหากลูกค้ารายใหญ่ในกลุ่มดังกล่าวมีการปรับเปลี่ยนวิธีการจัดส่ง หรือถูกแทรกแซงจากคู่แข่ง</p>
                        <p style='margin-bottom:0;'><b>💡 ข้อเสนอแนะเชิงกลยุทธ์ (Strategic Recommendations):</b> เพื่อการเติบโตอย่างยั่งยืน ควรทำ Cross-Selling นำเสนอบริการโลจิสติกส์ครบวงจร (Logispost Solution) ให้กับกลุ่มลูกค้าไปรษณียภัณฑ์เดิม เพื่อขยายเพดานค่าเฉลี่ยต่อชิ้น (Ticket Size) และผลักดันโปรโมชั่น eCo-Post เพื่อตีกรอบรักษาฐานลูกค้าเดิมให้อยู่กับไปรษณีย์ไทยต่อไป</p>
                    </div>
                    """)
            
            gr.Markdown("---")
            gr.Markdown("### 📋 ตารางข้อมูลสถิติลูกค้ารายใหญ่แบบเจาะลึก (ตามสิทธิ์ผู้ใช้งาน)")
            
            # ตารางแสดงข้อมูล
            if not df.empty:
                gr.Dataframe(df, interactive=False)
            else:
                gr.Dataframe(pd.DataFrame({"สถานะ": ["ไม่พบข้อมูล หรือกำลังเชื่อมต่อฐานข้อมูล Google Sheets..."]}), interactive=False)
