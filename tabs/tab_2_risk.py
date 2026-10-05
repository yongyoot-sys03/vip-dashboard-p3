import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from data_manager import fetch_and_process_data

def build_tab2(year_input, phone_input_state):
    
    @gr.render(inputs=[year_input, phone_input_state])
    def render_risk_analysis(selected_year, current_phone):
        phone = current_phone if current_phone else "admin"
        # หากดึงปี 2569 แล้วค้าง แนะนำให้ทดสอบด้วยปี 2568 ที่มีข้อมูลชัวร์ๆ ก่อนครับ
        year = selected_year if selected_year else "2568"
        
        try:
            df = fetch_and_process_data(phone_number=phone, year=year)
        except Exception as e:
            df = pd.DataFrame()

        risk_zero_count = 0
        risk_single_count = 0
        risk_yield_count = 0
        
        fallback_df = pd.DataFrame({"สถานะ": ["ไม่พบข้อมูล"]})
        df_zero = fallback_df.copy()
        df_single = fallback_df.copy()
        df_yield = fallback_df.copy()

        df_zero_temp = pd.DataFrame()
        df_single_temp = pd.DataFrame()
        df_yield_temp = pd.DataFrame()

        if not df.empty:
            df['ยอดเงินรวม'] = pd.to_numeric(df['ยอดเงินรวม'], errors='coerce').fillna(0)
            df['ไปรษณียภัณฑ์_บาท'] = pd.to_numeric(df.get('ไปรษณียภัณฑ์_บาท', 0), errors='coerce').fillna(0)
            df['ขนส่งโลจิสติกส์_บาท'] = pd.to_numeric(df.get('ขนส่งโลจิสติกส์_บาท', 0), errors='coerce').fillna(0)

            pcs_cols = [c for c in df.columns if '_ชิ้น' in str(c)]
            df['ชิ้นงานรวม'] = df[pcs_cols].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1) if pcs_cols else 0
            df['เฉลี่ยต่อชิ้น'] = df.apply(lambda row: (row['ยอดเงินรวม'] / row['ชิ้นงานรวม']) if row['ชิ้นงานรวม'] > 0 else 0, axis=1)

            # 1. Critical Risk
            df_zero_temp = df[df['ยอดเงินรวม'] == 0].copy()
            risk_zero_count = len(df_zero_temp)
            cols_to_show_zero = [c for c in ['รายชื่อลูกค้า', 'กลุ่ม', 'หมวดธุรกิจ', 'สังกัด ปณ.'] if c in df_zero_temp.columns]
            df_zero = df_zero_temp[cols_to_show_zero] if not df_zero_temp.empty else fallback_df.copy()

            # 2. Dependency Risk
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
                df_single = fallback_df.copy()

            # 3. Low Yield
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
                df_yield = fallback_df.copy()

        # ==========================================
        # 📊 การแปลงกราฟ Plotly เป็น HTML (หลีกเลี่ยงบั๊กค้าง)
        # ==========================================
        
        # กราฟ 1
        fig1 = go.Figure(data=[go.Bar(
            x=['ยอดเป็น 0', 'พึ่งพาจดหมาย', 'ต้นทุนสูง (<15บ.)'],
            y=[risk_zero_count, risk_single_count, risk_yield_count],
            text=[f"{risk_zero_count} ราย", f"{risk_single_count} ราย", f"{risk_yield_count} ราย"],
            textposition='auto',
            marker_color=['#ef4444', '#f59e0b', '#f97316']
        )])
        fig1.update_layout(title='📊 เปรียบเทียบจำนวนลูกค้ากลุ่มเสี่ยง', template='plotly_white', height=350, margin=dict(l=20, r=20, t=50, b=20))
        plot1_html = fig1.to_html(full_html=False, include_plotlyjs='cdn')

        # กราฟ 2
        if not df_yield_temp.empty:
            df_plot2 = df_yield_temp.sort_values('เฉลี่ยต่อชิ้น', ascending=True).head(10)
            fig2 = px.bar(df_plot2, x='เฉลี่ยต่อชิ้น', y='รายชื่อลูกค้า', orientation='h', text='เฉลี่ยต่อชิ้น', title='📉 Top 10 ลูกค้าต้นทุนสูง (Yield ต่ำสุด)', color_discrete_sequence=['#f97316'])
            fig2.update_layout(yaxis={'categoryorder':'total descending'}, template='plotly_white', height=350, margin=dict(l=20, r=20, t=50, b=20))
            plot2_html = fig2.to_html(full_html=False, include_plotlyjs='cdn')
        else:
            plot2_html = "<div style='text-align:center; padding:50px; color:gray;'>ไม่มีข้อมูลลูกค้ากลุ่มต้นทุนสูง</div>"

        # ==========================================
        # 🖥️ สร้าง UI
        # ==========================================
        with gr.Column():
            gr.Markdown(f"### 🚨 ระบบเฝ้าระวังความเสี่ยงลูกค้ารายใหญ่ ประจำปี {year}")
            
            with gr.Row():
                gr.HTML(f"""
                    <div class='kpi-card' style='border-top: 5px solid #ef4444;'>
                        <div class='kpi-icon'>🔴</div>
                        <div class='kpi-title' style='color:#ef4444 !important;'>หยุดใช้บริการ / ยอดเป็น 0</div>
                        <div class='kpi-value'>{risk_zero_count} <span style='font-size:16px;'>ราย</span></div>
                    </div>
                """)
                gr.HTML(f"""
                    <div class='kpi-card' style='border-top: 5px solid #f59e0b;'>
                        <div class='kpi-icon'>🟡</div>
                        <div class='kpi-title' style='color:#f59e0b !important;'>เสี่ยงพึ่งพาจดหมายอย่างเดียว</div>
                        <div class='kpi-value'>{risk_single_count} <span style='font-size:16px;'>ราย</span></div>
                    </div>
                """)
                gr.HTML(f"""
                    <div class='kpi-card' style='border-top: 5px solid #f97316;'>
                        <div class='kpi-icon'>🟠</div>
                        <div class='kpi-title' style='color:#f97316 !important;'>กลุ่มต้นทุนสูง (Yield < 15 บ.)</div>
                        <div class='kpi-value'>{risk_yield_count} <span style='font-size:16px;'>ราย</span></div>
                    </div>
                """)

            gr.Markdown("---")
            
            # โชว์กราฟด้วย HTML
            with gr.Row():
                with gr.Column():
                    gr.HTML(plot1_html)
                with gr.Column():
                    gr.HTML(plot2_html)

            gr.Markdown("---")
            gr.Markdown("### 📋 ตารางเฝ้าระวังลูกค้ากลุ่มเสี่ยง (Watchlist)")
            with gr.Accordion("🔴 กลุ่มลูกค้าหยุดใช้บริการ (ยอดเป็น 0 บาท) - ต้องติดตามด่วน", open=True):
                gr.Dataframe(df_zero, interactive=False)
            with gr.Accordion("🟡 กลุ่มเปราะบาง (ใช้แต่จดหมาย ไม่ใช้โลจิสติกส์) - โอกาสทำ Cross-selling", open=False):
                gr.Dataframe(df_single, interactive=False)
            with gr.Accordion("🟠 กลุ่มต้นทุนสูง (Yield ต่ำกว่า 15 บาท/ชิ้น) - เฝ้าระวังต้นทุน", open=False):
                gr.Dataframe(df_yield, interactive=False)
