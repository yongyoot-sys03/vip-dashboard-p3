import gradio as gr
from tabs import tab_1_exec, tab_2_risk, tab_3_opp, tab_4_data

# --- 🎨 Custom CSS ตกแต่งให้พรีเมียม มีมิติ แสงเงา ---
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Prompt:wght@300;400;600;700&display=swap');

/* เปลี่ยนฟอนต์ทั้งหน้าเป็น Prompt */
* {
    font-family: 'Prompt', sans-serif !important;
}

/* ตกแต่ง Header หลัก (แถบสีเข้มด้านบน) */
.header-banner {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    color: white !important;
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.2);
    text-align: center;
    margin-bottom: 20px;
    border-bottom: 4px solid #38bdf8;
}
.header-banner h1 {
    color: white !important;
    margin: 0;
    font-weight: 700;
}

/* ตกแต่งกล่องสถานะ (กรอบนูน) */
.status-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    padding: 10px 20px;
    border-radius: 12px;
    box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);
    color: #475569;
    font-weight: 600;
    text-align: right;
}

/* สไตล์กล่อง KPI แบบมีมิตินูน (Neumorphism) */
.kpi-card {
    background: linear-gradient(145deg, #ffffff, #f0f4f8);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 6px 6px 14px #d1d9e6, -6px -6px 14px #ffffff;
    border: 1px solid #e2e8f0;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-5px);
    box-shadow: 8px 8px 20px #c8d0e0, -8px -8px 20px #ffffff;
}
.kpi-icon {
    font-size: 32px;
    margin-bottom: 10px;
}
.kpi-title {
    font-size: 14px;
    color: #64748b;
    font-weight: 600;
}
.kpi-value {
    font-size: 26px;
    color: #0284c7;
    font-weight: 700;
    margin-top: 5px;
}
"""

def get_user_status(request: gr.Request):
    if request:
        params = dict(request.query_params)
        user_id = params.get("user_id", "Unknown")
        role = params.get("role", "ADMIN").upper()
    else:
        user_id, role = "Unknown", "ADMIN"
        
    status_html = f"<div class='status-box'>👤 ผู้ใช้งาน: <span style='color:#0284c7;'>{user_id}</span> | 🔑 สิทธิ์: <span style='color:#ea580c;'>{role}</span></div>"
    return status_html, role

# --- โครงสร้างแอปหลัก ---
with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as app:
    
    # 🌟 ส่วน Header
    with gr.Row():
        gr.HTML(
            "<div class='header-banner'>"
            "<h1>🚀 ระบบวิเคราะห์สถิติลูกค้ารายใหญ่ สังกัด ปข.3</h1>"
            "<p style='color:#94a3b8; margin-top:5px;'>DATA-DRIVEN DASHBOARD FOR EXECUTIVE & SALES</p>"
            "</div>"
        )
    
    # 🌟 ส่วนสถานะ User
    with gr.Row():
        status_display = gr.HTML("<div class='status-box'>⏳ กำลังตรวจสอบสิทธิ์...</div>")
    
    current_role = "ADMIN"
    
    # 🌟 ดึง UI แท็บต่างๆ
    tab_1_exec.render(current_role)
    tab_2_risk.render(current_role)
    tab_3_opp.render(current_role)
    tab_4_data.render(current_role)

    # โหลด URL ตอนเปิดเว็บ
    app.load(get_user_status, inputs=None, outputs=[status_display])

if __name__ == "__main__":
    app.launch()
