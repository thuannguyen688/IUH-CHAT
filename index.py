import streamlit as st
from config import QDRANT_CONFIG, MONGODB_CONFIG, MODEL_CONFIG
from database import QdrantManager, MongoManager
from ui import *
from models import Model
from style import custom_css
from data import Data
import socket

class Main:
    @staticmethod
    def initialize():
        if "initialized" not in st.session_state:
            st.session_state.chat_collection = MONGODB_CONFIG["CHAT_HISTORY"]
            st.session_state.login_collection =  MONGODB_CONFIG["LOGIN_HISTORY"]
            st.session_state.ban_collection = MONGODB_CONFIG["BAN_COLLECTION"]
            st.session_state.mode_chat = MODEL_CONFIG["CHAT"]
            st.session_state.model_embed = MODEL_CONFIG["EMBEDDED"]
            st.session_state.chat_db = MONGODB_CONFIG["CHAT_DB"]
            st.session_state.mongodb = MongoManager.initialize(MONGODB_CONFIG["URI"], MONGODB_CONFIG["DATABASE"])
            st.session_state.qdrant_db = QdrantManager.get_instance(QDRANT_CONFIG["URL"], QDRANT_CONFIG["API_KEY"])
            if "messages" not in st.session_state:
                st.session_state.messages = []
            st.session_state.model = Model(MODEL_CONFIG["API_KEY"])
            st.session_state.embedding_model = st.session_state.model.get_embedding_model()
            st.session_state.current_data = st.session_state.mongodb.find_one(MONGODB_CONFIG["CHAT_DB"], {"key": "DATABASE_CONFIG"})["selected_db"]
            st.session_state.store_qdrant = st.session_state.qdrant_db.get_store(st.session_state.current_data, st.session_state.embedding_model)
            st.session_state.retriever = st.session_state.qdrant_db.get_retriever(st.session_state.store_qdrant)
            st.session_state.ip = socket.gethostbyname(socket.gethostname())
            st.session_state.initialized = True
            st.session_state.Data = Data




    @staticmethod
    def display():
        st.set_page_config(page_title="IUH - Truy vấn dữ liệu", page_icon="🏫")
        st.markdown(custom_css, unsafe_allow_html=True)
        Main.initialize()

        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
        if "user_role" not in st.session_state:
            st.session_state.user_role = None

        if not st.session_state.logged_in:
            Login.show(st.session_state.mongodb, MONGODB_CONFIG["ACCOUNT"], MONGODB_CONFIG["LOGIN_HISTORY"],
                                  MONGODB_CONFIG["BAN_COLLECTION"], st.session_state.ip)
        else:
            Main.build_navigation()


    @staticmethod
    def build_navigation():
        Main.initialize()
        menu_items = ["Trang chủ", "Quản lý", "Upload PDF", "Xem bộ sưu tập", "Chatbot"] if st.session_state.user_role == "admin" else ["Trang chủ", "Chatbot"]
        page = Main.create_sidebar_menu(menu_items)

        match page:
            case "Trang chủ":
                Home.show()
            case "Quản lý":
                    st.html("<h2 class='centered-title'>QUẢN LÝ HỆ THỐNG</h2>")
                    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Tổng quan", "Biểu đồ", "Tài khoản", "Tin nhắn", "Thông tin"])
                    with tab1:
                        General.show()
                    with tab2:
                        TimeProcessVisualize.show()
                    with tab3:
                        AccountManager.show()
                    with tab4:
                        SearchMessageManager.show()
                    with tab5:
                        SystemInfoManager.show()
            case "Upload PDF":
                Upload.show()
            case "Xem bộ sưu tập":
                Collections.show()
            case "Chatbot":
                Chat.show()

    @staticmethod
    def create_sidebar_menu(items):
        if "current_page" not in st.session_state:
            st.session_state.current_page = items[0]

        for item in items:
            if st.sidebar.button(item, key=item, help=f"Chuyển đến {item}", use_container_width=True):
                st.session_state.current_page = item

        if st.sidebar.button("Đăng xuất", key="logout", help="Đăng xuất khỏi hệ thống", use_container_width=True, type="primary"):
            Login.logout()
            st.session_state.current_page = "Trang chủ"
            if "chat_history" in st.session_state:
                del st.session_state.chat_history

        return st.session_state.current_page

if __name__ == "__main__":
    Main.display()
