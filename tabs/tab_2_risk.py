import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
        
        fallback_df = pd.DataFrame({"สถานะ": ["ไม่พบข้อมูล หรือกำลังโหลดข้อมูล..."]})
        df_zero = fallback_df.copy()
        df_single = fallback_df.copy()
        df_yield = fallback_df.copy()

        df_zero_temp = pd.DataFrame()
        df_single_temp = pd.DataFrame()
        df_yield_temp = pd.DataFrame()

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
            df_zero_temp = df[df['ยอดเงินรวม'] == 0].copy()
            risk_zero_count = len(df_zero_temp)
            cols_to_show_zero = [c for c in ['รายชื่อลูกค้า', 'กลุ่ม', 'หมวดธุรกิจ', 'สังกัด ปณ.'] if c in df_zero_temp.columns]
            df_zero = df_zero_temp[cols_to_show_zero] if not df_zero_temp.empty else pd.DataFrame({"สถานะ": ["ไม่พบลูกค้ากลุ่มนี้"]})

            # 🟡 2. Dependency Risk (พึ่งพาไปรษณียภัณฑ์ > 90% และไม่มีโลจิสติกส์)
            df_active = df[df['ยอดเงินรวม'] > 0].copy()
            df_active['สัดส่วนไปรษณียภัณฑ์_%'] = (df_active['ไปรษณียภัณฑ์_บาท'] / df_active['ยอดเงินรวม']) * 100
            
            df_single_temp = df_active[(df_active['สัดส่วนไปรษณียภัณฑ์_%'] > 90) & (df_active['ขนส่งโลจิสติกส์_บาท'] == 0)].copy()
            risk_single_count = len(df_single_temp)
            
            if not df_single_temp.empty:
                df_single_temp['ยอดเงินรวม'] = df_single_temp['ยอดเงินรวม'].apply(lambda x: f"{x:,.2f}")
                df_single_temp['สัดส่วนไปรษณียภัณฑ์_%'] = df_single_temp['สัดส่วนไปรษณียภัณฑ์_%'].apply(lambda x: f"{x:.1f}%")
                cols_single = [c for c in ['รายชื่อลูกค้า', 'สังกัด ปณ.', 'ยอดเงินรวม', 'สัดส่วนไปรษณียภัณฑ์_%'] if c in df_single_temp.columns]
                df_single = df_single_temp[cols_single]
            else:
                df_single = pd.DataFrame({"สถานะ": ["ไม่พบลูกค้ากลุ่มนี้"]})

            # 🟠 3. Low Yield (ยอดรวม > 5000 แต่เฉลี่ยต่อชิ้น < 15 บาท)
            df_yield_temp = df_active[(df_active['ยอดเงินรวม'] > 5000) & (df_active['เฉลี่ยต่อชิ้น'] > 0) & (df_active['เฉลี่ยต่อชิ้น'] < 15)].copy()
            risk_yield_count = len(df_yield_temp)
            
            if not df_yield_temp.empty:
                df_yield_temp_format = df_yield_temp.copy()
                df_yield_temp_format['ยอดเงินรวม'] = df_yield_temp_format['ยอดเงินรวม'].apply(lambda x: f"{x:,.2f}")
                df_yield_temp_format['ชิ้นงานรวม'] = df_yield_temp_format['ชิ้นงานรวม'].apply(lambda x: f"{x:,.0f}")
                df_yield_temp_format['เฉลี่ยต่อชิ้น'] = df_yield_temp_format['เฉลี่ยต่อชิ้น'].apply(lambda x: f"{x:,.2f}")
                cols_yield = [c for c in ['รายชื่อลูกค้า', 'สังกัด ปณ.', 'ชิ้นงานรวม', 'ยอดเงินรวม', 'เฉลี่ยต่อชิ้น'] if c in df_yield_temp_format.columns]
                df_yield = df_yield_temp_format[cols_yield]
            else:
                df_yield = pd.DataFrame({"สถานะ": ["ไม่พบลูกค้ากลุ่มนี้"]})

        # ==========================================
        # 📊 สร้างกราฟ Plotly และแปลงเป็น HTML
        # ==========================================
        
        # --- กราฟ 1 ---
        fig1 = go.Figure(data=[go.Bar(
            x=['ยอดเป็น 0', 'พึ่งพาจดหมายอย่างเดียว', 'กลุ่มต้นทุนสูง (Yield < 15)'],
            y=[risk_zero_count, risk_single_count, risk_yield_count],
            text=[f"{risk_zero_count} ราย", f"{risk_single_count} ราย", f"{risk_yield_count} ราย"],
            textposition='auto',
            marker_color=['#ef4444', '#f59e0b', '#f97316'],
            textfont=dict(size=14, color='white', weight='bold')
        )])
        fig1.update_layout(title='📊 เปรียบเทียบจำนวนลูกค้ากลุ่มเสี่ยง', yaxis_title='จำนวนลูกค้า (ราย)', template='plotly_white', height=380, margin=dict(l=40, r=40, t=60, b=40))

        # --- กราฟ 2 ---
        if not df_yield_temp.empty:
            df_plot2 = df_yield_temp.sort_values('เฉลี่ยต่อชิ้น', ascending=True).head(10)
            fig2 = px.bar(df_plot2, x='เฉลี่ยต่อชิ้น', y='รายชื่อลูกค้า', orientation='h', text='เฉลี่ยต่อชิ้น', title='📉 Top 10 ลูกค้ากลุ่มต้นทุนสูง (Yield ต่ำสุด)', color_discrete_sequence=['#f97316'])
            fig2.update_traces(texttemplate=' %{text:.2f} บ.', textposition='outside', textfont=dict(size=12, weight='bold'))
            fig2.update_layout(yaxis={'categoryorder':'total descending'}, xaxis_title='ค่าเฉลี่ยรายได้ต่อชิ้น (บาท)', yaxis_title='', template='plotly_white', height=380, margin=dict(l=20, r=40, t=60, b=40))
        else:
            fig2 = go.Figure()
            fig2.update_layout(title='📉 ไม่มีข้อมูลลูกค้ากลุ่มต้นทุนสูง', template='plotly_white', height=380)

        # 🎯 แปลง Figure เป็น HTML string พร้อมโหลดไลบรารี CDN อัตโนมัติ
        plot1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})
        plot2_html = fig2.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

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
            
            # 📈 แสดงผลกราฟผ่าน HTML แทน gr.Plot
            with gr.Row():
                with gr.Column():
                    gr.HTML(f"<div style='border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; background: white;'>{plot1_html}</div>")
                with gr.Column():
                    gr.HTML(f"<div style='border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; background: white;'>{plot2_html}</div>")

            gr.Markdown("---")
            
            with gr.Row():
                gr.HTML(f"""
                <div style='background-color:#fee2e2; border-left: 6px solid #ef4444; padding:20px; border-radius:8px; box-shadow: 4px 4px 10px rgba(163,177,198,0.4); line-height: 1.8;'>
                    <h4 style='margin-top:0; color:#b91c1c; font-size: 18px;'>🤖 AI Risk Detector (สรุปวิเคราะห์จุดเปราะบางเชิงลึก)</h4>
                    <p style='margin-bottom:12px; font-size: 15px;'>ระบบ Machine Learning และ Data Analytics ได้ทำการสแกนฐานข้อมูลลูกค้ารายใหญ่ในสิทธิ์ความรับผิดชอบของคุณ พบจุดที่ต้องเฝ้าระวังอย่างเร่งด่วนดังนี้:</p>
                    
                    <ul style='margin-bottom:15px; color:#7f1d1d; font-size: 15px;'>
                        <li style='margin-bottom:8px;'><b>🛑 ปัญหา Churn Rate (ลูกค้าหาย):</b> พบลูกค้า VIP จำนวน <b>{risk_zero_count} ราย</b> ที่ไม่มีความเคลื่อนไหวทางบัญชีหรือยอดเป็น 0 ซึ่งถือเป็น <b>Critical Risk</b> ทีมขายต้องเร่งตรวจสอบว่าลูกค้าเปลี่ยนไปใช้บริการขนส่งของเอกชนรายอื่นหรือไม่ และรีบยื่นข้อเสนอพิเศษเพื่อดึงลูกค้ากลับมา</li>
                        <li style='margin-bottom:8px;'><b>⚠️ ความเสี่ยงด้านโครงสร้าง (Dependency Risk):</b> พบลูกค้า <b>{risk_single_count} ราย</b> ที่ผูกพันรายได้กับบริการจดหมายเพียงอย่างเดียว (>90%) หากในอนาคตหน่วยงานเหล่านี้ปรับเปลี่ยนนโยบายเป็น e-Document หรือ Paperless รายได้ส่วนนี้ของ ปข.3 จะหายไปทันที จึงจำเป็นต้องกระจายความเสี่ยง (Diversify) ทันที</li>
                        <li style='margin-bottom:8px;'><b>📉 ปัญหาอัตรากำไร (Margin Squeeze):</b> จากกราฟ Top 10 Low Yield พบว่ามีลูกค้า <b>{risk_yield_count} ราย</b> ที่มียอดปริมาณชิ้นงานสูงมาก แต่ให้ค่าเฉลี่ยรายได้ต่อชิ้น <b>ต่ำกว่า 15 บาท</b> ซึ่งเมื่อหักลบต้นทุนการขนส่งและการคัดแยกแล้ว อาจเสี่ยงทำให้ ปข.3 ขาดทุนกำไรในเชิงปฏิบัติการ (Operational Loss)</li>
                    </ul>
                    
                    <div style='background-color: white; padding: 15px; border-radius: 8px; border-left: 4px solid #16a34a;'>
                        <p style='margin-bottom:0; color: #16a34a; font-size: 15px;'><b>🎯 Action Plan ที่ควรทำทันที:</b> <br>
                        1. มอบหมายหัวหน้า ปณ. ลงพื้นที่เจรจากับลูกค้า <b>{risk_single_count} ราย</b> เพื่อทำ Cross-selling เสนอบริการ Logispost, EMS หรือ eCo-Post ควบคู่ไปกับจดหมาย<br>
                        2. ประเมินการปรับโครงสร้างราคาหรือทำ Bulk Discount ใหม่ให้กับกลุ่มลูกค้า Yield ต่ำ เพื่อผลักดันให้รายได้ต่อชิ้นขยับขึ้นไปแตะจุดคุ้มทุน (Break-even)</p>
                    </div>
                </div>
                """)

            gr.Markdown("---")
            gr.Markdown("### 📋 ตารางเฝ้าระวังลูกค้ากลุ่มเสี่ยง (Watchlist)")
            
            with gr.Accordion("🔴 กลุ่มลูกค้าหยุดใช้บริการ (ยอดเป็น 0 บาท) - ต้องติดตามด่วน", open=True):
                gr.Dataframe(df_zero, interactive=False)
                
            with gr.Accordion("🟡 กลุ่มเปราะบาง (ใช้แต่จดหมาย ไม่ใช้โลจิสติกส์) - โอกาสทำ Cross-selling", open=False):
                gr.Dataframe(df_single, interactive=False)
                
            with gr.Accordion("🟠 กลุ่มต้นทุนสูง (Yield ต่ำกว่า 15 บาท/ชิ้น) - เฝ้าระวังต้นทุน", open=False):
                gr.Dataframe(df_yield, interactive=False)
