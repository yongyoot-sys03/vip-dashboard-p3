import gradio as gr

def greet(name):
    return f"ระบบพร้อมทำงานแล้ว คุณ {name}!"

demo = gr.Interface(
    fn=greet,
    inputs=gr.Textbox(label="ชื่อของคุณ"),
    outputs=gr.Textbox(label="ผลลัพธ์"),
    title="HF Test Dashboard"
)

if __name__ == "__main__":
    demo.launch()
