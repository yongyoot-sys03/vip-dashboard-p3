import gradio as gr

def check_status():
    return "✅ เซิร์ฟเวอร์ทำงานสมบูรณ์แล้ว! ไม่มี Error แล้วครับ"

with gr.Blocks() as demo:
    gr.Markdown("# 🚀 ทดสอบระบบ VIP Dashboard P3")
    out = gr.Textbox(label="สถานะระบบ")
    btn = gr.Button("คลิกเพื่อเช็กสถานะ")
    btn.click(fn=check_status, outputs=out)

demo.launch()
