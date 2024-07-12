import streamlit as st
import os
import time
import sys
from datetime import datetime
import pytz

class Chat:

    @staticmethod
    def get_answer(question):
        try:
            start = time.time()
            docs = st.session_state.qdrant_db.get_data_from_store(st.session_state.retriever, question)
            result = st.session_state.model.chat(docs, question)
            processing_time = time.time() - start
            Chat.save_chat_result(question, result, processing_time)
            return result, processing_time, docs
        except:
            return "Hệ thống vừa cập nhật vui lòng đăng nhập lại", 0, ""

    @staticmethod
    def save_chat_result(question, answer, processing_time):
        vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')
        chat_record = {
            "question": question,
            "answer": answer,
            "processing_time": processing_time,
            "input_word_count": len(question.split()),
            "output_word_count": len(answer.split()),
            "timestamp": datetime.now(vietnam_tz).strftime("%Y-%m-%d %H:%M:%S"),
            "username": st.session_state.username,
        }
        st.session_state.mongodb.insert_one(st.session_state.chat_collection, chat_record)

    @staticmethod
    def display_chat_history():
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    @staticmethod
    def process_user_input(prompt):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner('Đang xử lý câu hỏi...'):
                answer, processing_time, docs = Chat.get_answer(prompt)
            message_placeholder.markdown(answer)
            st.caption(f"Xử lý hoàn tất trong {processing_time:.2f} giây!")

        st.session_state.messages.append({"role": "assistant", "content": answer, "processing_time": processing_time})

    @staticmethod
    def normal():
        st.html("<h1 class='centered-title'>HỆ THỐNG TRUY XUẤT DỮ LIỆU</h1>")
        Chat.display_chat_history()

        if prompt := st.chat_input("Nhập câu hỏi của bạn"):
            Chat.process_user_input(prompt)

    @staticmethod
    def maintenance():
        st.title("🚧 Trang Web Đang Bảo Trì 🚧")
        st.header("Xin lỗi vì sự bất tiện này!")
        st.write("""
        Chúng tôi đang tiến hành bảo trì hệ thống để cải thiện dịch vụ.
        Trang web sẽ sớm hoạt động trở lại.

        Vui lòng quay lại sau. Cảm ơn sự kiên nhẫn của bạn!
        """)

    @staticmethod
    def show():
        if st.session_state.current_data == "" or st.session_state.current_data is None:
            Chat.maintenance()
        else:
            Chat.normal()
