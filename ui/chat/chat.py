import streamlit as st
import os
import time
import sys
from datetime import datetime
class Chat:
    _mongodb = None
    _chat_collection = None
    _qdrant_db = None
    _current_data = None
    _retriever = None
    _chat_chain = None
    _model = None
    _ip = None
    def __new__(cls, mongodb, chat_collection, qdrant_db, current_data, retriever, model, ip):
        if not cls._current_data:
            cls._mongodb = mongodb
            cls._chat_collection = chat_collection
            cls._qdrant_db = qdrant_db
            cls._current_data = current_data
            cls._retriever = retriever
            cls._model = model
            cls._ip = ip
        if 'messages' not in st.session_state:
            st.session_state.messages = []

    def __init__(self):
        pass


    @classmethod
    def get_answer(cls, question):
        start = time.time()
        docs = cls._qdrant_db.get_data_from_store(cls._retriever, question)
        result = cls._model.chat(docs, question)
        processing_time = time.time() - start
        cls.save_chat_result(question, result, processing_time)
        return result, processing_time, docs


    @classmethod
    def save_chat_result(cls, question, answer, processing_time):
        chat_record = {
            "question": question,
            "answer": answer,
            "processing_time": processing_time,
            "input_word_count": len(question.split()),
            "output_word_count": len(answer.split()),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": cls._ip,
        }
        cls._mongodb.insert_one(cls._chat_collection, chat_record)


    @staticmethod
    def display_chat_history():
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    @classmethod
    def process_user_input(cls, prompt):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            message_placeholder = st.empty()
            with st.spinner('Đang xử lý câu hỏi...'):
                answer, processing_time, docs = cls.get_answer(prompt)
            message_placeholder.markdown(answer)
            st.caption(f"Xử lý hoàn tất trong {processing_time:.2f} giây!")

        st.session_state.messages.append({"role": "assistant", "content": answer, "processing_time": processing_time})


    @classmethod
    def normal(cls):
        st.html("<h1 class='centered-title'>HỆ THỐNG TRUY XUẤT DỮ LIỆU</h1>")
        cls.display_chat_history()

        if prompt := st.chat_input("Nhập câu hỏi của bạn"):
            cls.process_user_input(prompt)

    @staticmethod
    def maintenance():
        st.title("🚧 Trang Web Đang Bảo Trì 🚧")
        st.header("Xin lỗi vì sự bất tiện này!")
        st.write("""
        Chúng tôi đang tiến hành bảo trì hệ thống để cải thiện dịch vụ.
        Trang web sẽ sớm hoạt động trở lại.

        Vui lòng quay lại sau. Cảm ơn sự kiên nhẫn của bạn!
        """)
    @classmethod
    def show(cls):
        if cls._current_data == "" or cls._current_data is None:
            cls.maintenance()
        else:
            cls.normal()



