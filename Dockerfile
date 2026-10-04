FROM python:3.10-slim

WORKDIR /code

# ติดตั้ง Dependencies
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt

# ก๊อปปี้ไฟล์ทั้งหมดในโปรเจกต์
COPY . .

# กำหนด Port สำหรับ Hugging Face Spaces
EXPOSE 7860

# สั่งรันแอปพลิเคชัน
CMD ["python", "app.py"]
