import gradio as gr
import pandas as pd
from data_manager import fetch_and_process_data

def build_tab2(year_input, phone_input_state):
    
    @gr.render(inputs=[year_input, phone_input_state])
    def render_risk_analysis(selected_year, current_phone):
        phone = current_phone if current_phone else "admin"
        year = selected_year if selected_year else "2568"
        
        # 1. ดึงข้อมูล
        try:
            df = fetch_and_process_data(phone_number=phone, year=year)
        except Exception as e:
            print(f"Error fetching data in tab2: {e}")
            df = pd.DataFrame()

        # ตัวแปรเก็บจำนวนลูกค้ากลุ่มเสี่ยง
        risk_zero_count = 0
        risk_single_count = 0
        risk_yield_count = 0
        
        df_zero = pd.DataFrame()
        df_single = pd.DataFrame()
        df_yield = pd.DataFrame()

        # 2. ประมวลผลความเสี่ยง
        if not df.empty:
            df['ยอดเงินรวม'] = pd.to_numeric(df['ยอดเงินรวม'], errors='coerce').fillna(0)
            
            if 'ไปรษณียภัณฑ์_บาท' in df.columns:
                df['ไปรษณียภัณฑ์_บาท'] = pd.to_numeric(df['ไปรษณียภัณฑ์_บาท'], errors='coerce').fillna(0)
            else:
                df['ไปรษณียภัณฑ์_บาท'] = 0.0
                
            if 'ขนส่งโลจิสติกส์_บาท' in df.columns:
                df['ขนส่งโลจิสติกส์_บาท'] = pd.to_numeric(df['ขนส่งโลจิสติกส์_บาท'], errors='coerce').fillna(0)
            else:
                df['ขนส่งโลจิสติกส์_บาท'] = 0.0

            # คำนวณชิ้นรวมเพื่อหา Yield
            pcs_cols = [c for c in df.columns if '_ชิ้น' in str(c)]
            df['ชิ้นงานรวม'] = df[pcs_cols].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1) if pcs_cols else 0
            df['เฉลี่ยต่อชิ้น'] = df.apply(lambda row: (row['ยอดเงินรวม'] / row['ชิ้นงานรวม']) if row['ชิ้นงานรวม'] > 0 else 0, axis=1)

            # 🔴 1. Critical Risk (ยอดเป็น 0)
            df_zero = df[df['ยอดเงินรวม'] == 0].copy()
            risk_zero_count = len(df_zero)
            cols_to_show_zero = [c for c in ['รายชื่อลูกค้า', 'กลุ่ม', 'หมวดธุรกิจ', 'สังกัด ปณ.'] if c in df_zero.columns]
            df_zero = df_zero[cols_to_show_zero] if not df_zero.empty else pd.DataFrame({"สถานะ": ["ไม่พบลูกค้ากลุ่มนี้"]})

            # 🟡 2. Dependency Risk (พึ่งพาไปรษณียภัณฑ์ > 90% และไม่มีโลจิสติกส์)
            df_active = df[df['ยอดเงินรวม'] > 0].copy()
            df_active['สัดส่วนไปรษณียภัณฑ์_%'] = (df_active['ไปรษณียภัณฑ์_บาท'] / df_active['ยอดเงินรวม']) * 100
            
            df_single = df_active[(df_active['สัดส่วนไปรษณียภัณฑ์_%'] > 90) & (df_active['ขนส่งโลจิสติกส์_บาท'] == 0)].copy()
            risk_single_count = len(df_single)
            
            if not df_single.empty:
                df_single['ยอดเงินรวม'] = df_single['ยอดเงินรวม'].apply(lambda x: f"{x:,.2f}")
                df_single['สัดส่วนไปรษณียภัณฑ์_%'] = df_single['สัดส่วนไปรษณียภัณฑ์_%'].apply(lambda x: f"{x:.1f}%")
                cols_single = [c for c in ['รายชื่อลูกค้า', 'สังกัด ปณ.', 'ยอดเงินรวม', 'สัดส่วนไปรษณียภัณฑ์_%'] if c in df_single.columns]
                df_single = df_single[cols_single]
            else:
                df_single = pd.DataFrame({"สถานะ": ["ไม่พบลูกค้ากลุ่มนี้"]})

            # 🟠 3. Low Yield (ยอดรวม > 5000 แต่เฉลี่ยต่อชิ้น < 15 บาท)
            df_yield = df_active[(df_active['ยอดเงินรวม'] > 5000) & (df_active['เฉลี่ยต่อชิ้น'] > 0) & (df_active['เฉลี่ยต่อชิ้น'] < 15)].copy()
            risk_yield_count = len(df_yield)
            
            if not df_yield.empty:
                df_yield['ยอดเงินรวม'] = df_yield['ยอดเงินรวม'].apply(lambda x: f"{x:,.2f}")
                df_yield['ชิ้นงานรวม'] = df_yield['ชิ้นงานรวม'].apply(lambda x: f"{x:,.0f}")
                df_yield['เฉลี่ยต่อชิ้น'] = df_yield['เฉลี่ยต่อชิ้น'].apply(lambda x: f"{x:,.2f}")
                cols_yield = [c for c in ['รายชื่อลูกค้า', 'สังกัด ปณ.', 'ชิ้นงานรวม', 'ยอดเงินรวม', 'เฉลี่ยต่อชิ้น'] if c in df_yield.columns]
                df_yield = df_yield[cols_yield]
            else:
                df_yield = pd.DataFrame({"สถานะ": ["ไม่พบลูกค้ากลุ่มนี้"]})

        # 3. สร้าง UI หน้าจอ
        with gr.Column():
            gr.Markdown(f"### 🚨 ระบบเฝ้าระวังความเสี่ยงลูกค้ารายใหญ่ ประจำปี {year}")
            
            with gr.Row():
                gr.HTML(f"""
                    <div class='kpi-card' style='border-top: 5px solid #ef4444;'>
                        <div class='kpi-icon'>🔴</div>
                        <div class='kpi-title' style='color:#ef4444 !important; font-weight:bold !important;'>หยุดใช้บริการ / ยอดเป็น 0</div>
                        <div class='kpi-value'>{risk_zero_count} <span style='font-size:16px;'>ราย</span></div>
                    </div>
                """)
                gr.HTML(f"""
                    <div class='kpi-card' style='border-top: 5px solid #f59e0b;'>
                        <div class='kpi-icon'>🟡</div>
                        <div class='kpi-title' style='color:#f59e0b !important; font-weight:bold !important;'>เสี่ยงพึ่งพาจดหมายอย่างเดียว</div>
                        <div class='kpi-value'>{risk_single_count} <span style='font-size:16px;'>ราย</span></div>
                    </div>
                """)
                gr.HTML(f"""
                    <div class='kpi-card' style='border-top: 5px solid #f97316;'>
                        <div class='kpi-icon'>🟠</div>
                        <div class='kpi-title' style='color:#f97316 !important; font-weight:bold !important;'>กลุ่มต้นทุนสูง (Yield < 15 บ.)</div>
                        <div class='kpi-value'>{risk_yield_count} <span style='font-size:16px;'>ราย</span></div>
                    </div>
                """)

            gr.Markdown("---")
            
            with gr.Row():
                gr.HTML(f"""
                <div style='background-color:#fee2e2; border-left: 6px solid #ef4444; padding:20px; border-radius:8px; box-shadow: 4px 4px 10px rgba(163,177,198,0.4); line-height: 1.8;'>
                    <h4 style='margin-top:0; color:#b91c1c;'>🤖 AI Risk Detector (วิเคราะห์จุดเปราะบาง)</h4>
                    <p style='margin-bottom:10px;'>จากการสแกนฐานข้อมูลลูกค้ารายใหญ่ในสิทธิ์ความรับผิดชอบของคุณ พบจุดที่ต้องเฝ้าระวังด่วนดังนี้:</p>
                    <ul style='margin-bottom:10px; color:#7f1d1d;'>
                        <li>พบลูกค้า VIP จำนวน <b>{risk_zero_count} ราย</b> ที่ไม่มีความเคลื่อนไหวทางบัญชี (ยอด = 0) จำเป็นต้องส่งทีมเข้าพบเพื่อตรวจสอบการใช้บริการคู่แข่ง (Churn Risk)</li>
                        <li>พบลูกค้า <b>{risk_single_count} ราย</b> ที่ผูกพันกับบริการไปรษณียภัณฑ์มากกว่า 90% โดยไม่มีการใช้บริการกลุ่มโลจิสติกส์ ถือเป็นความเสี่ยงระยะยาวหากลูกค้าทำ Digital Transformation</li>
                        <li>ในเชิงความคุ้มค่า (Margin) มี <b>{risk_yield_count} ราย</b> ที่มียอดจัดส่งสูงแต่ค่าเฉลี่ยรายได้ต่อชิ้นต่ำกว่า 15 บาท อาจส่งผลต่อกำไรสุทธิของการปฏิบัติงาน</li>
                    </ul>
                    <p style='margin-bottom:0;'><b>🎯 Action Plan:</b> แนะนำให้ดึงรายชื่อจากตาราง <b>"เสี่ยงพึ่งพาจดหมายอย่างเดียว"</b> เพื่อทำแคมเปญกระตุ้นยอด Logispost หรือ eCo-Post ทันที</p>
                </div>
                """)

            gr.Markdown("---")
            gr.Markdown("### 📋 ตารางเฝ้าระวังลูกค้ากลุ่มเสี่ยง (Watchlist)")
            
            with gr.Accordion("🔴 กลุ่มลูกค้าหยุดใช้บริการ (ยอดเป็น 0 บาท) - ต้องติดตามด่วน", open=True):
                gr.Dataframe(df_zero, interactive=False, max_height=300)
                
            with gr.Accordion("🟡 กลุ่มเปราะบาง (ใช้แต่จดหมาย ไม่ใช้โลจิสติกส์) - โอกาสทำ Cross-selling", open=False):
                gr.Dataframe(df_single, interactive=False, max_height=300)
                
            with gr.Accordion("🟠 กลุ่มต้นทุนสูง (Yield ต่ำกว่า 15 บาท/ชิ้น) - เฝ้าระวังต้นทุน", open=False):
                gr.Dataframe(df_yield, interactive=False, max_height=300)
