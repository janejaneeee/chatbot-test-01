import streamlit as st
from google import genai
from google.genai import types
import os

# --- 1. ตั้งค่าหน้าจอ ---
st.set_page_config(page_title="Recipe Expert AI", layout="centered")
st.title("👨‍🍳 Dr. Dee - ที่ปรึกษาการแปรรูป")

# --- 2. ดึง API Key ---
try:
    API_KEY = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("กรุณาใส่ GOOGLE_API_KEY ในหน้า Settings > Secrets ของ Streamlit Cloud")
    st.stop()

client = genai.Client(api_key=API_KEY)

# --- 3. การจัดการไฟล์ฐานข้อมูล (File API) ---
# ใช้ Session State เพื่อให้ upload ไฟล์แค่ครั้งเดียว ไม่ต้อง upload ใหม่ทุกครั้งที่แชท
if "file_uri" not in st.session_state:
    with st.spinner("กำลังเตรียมฐานข้อมูลสูตรอาหาร..."):
        try:
            # เปลี่ยนชื่อไฟล์ให้ตรงกับที่คุณอัปโหลดขึ้น GitHub
            file_name = "recipes.md" 
            
            if os.path.exists(file_name):
                # อัปโหลดไฟล์ขึ้น Google Server (ประหยัด Token ได้มหาศาล)
                uploaded_file = client.files.upload(file=file_name)
                st.session_state.file_uri = uploaded_file.uri
            else:
                st.error(f"ไม่พบไฟล์ {file_name} บน GitHub")
                st.stop()
        except Exception as e:
            st.error(f"เกิดข้อผิดพลาดในการโหลดไฟล์: {e}")
            st.stop()

# --- 4. ระบบแชท ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# แสดงประวัติการสนทนา
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ส่วนรับคำถาม
if prompt := st.chat_input("ถามสูตรได้เลย..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # ส่งคำถามไปยัง Gemini โดยอ้างอิงจากไฟล์ที่อัปโหลดไว้
        response = client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents=[
                # แนบไฟล์แบบอ้างอิง URI (ไม่กินโควตา Token ในส่วน Prompt)
                {"file_data": {"file_uri": st.session_state.file_uri, "mime_type": "text/plain"}},
                prompt
            ],
            config={"system_instruction": "คุณคือเชฟผู้เชี่ยวชาญ ตอบคำถามโดยใช้ข้อมูลจากไฟล์ที่แนบมาเท่านั้น"}
        )
        
        st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})
