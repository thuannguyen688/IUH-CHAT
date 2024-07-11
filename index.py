import streamlit as st
from config import QDRANT_CONFIG, MONGODB_CONFIG, MODEL_CONFIG
from database import QdrantManager, MongoManager
from ui import Collections, Manager, Upload, Chat, Login, Home
from models import Model
from style import custom_css
from data import Data
import socket


class Main:
    _initialized = False
    _qdrant_db = None
    _mongo_db = None
    _model = None
    _current_data = None
    _store_qdrant = None
    _retriever = None
    _ip = None
    _embedding_model = None

    @classmethod
    # @st.cache_resource
    def initialize(cls):
        if not cls._initialized:
            cls._qdrant_db = QdrantManager.get_instance(QDRANT_CONFIG["URL"], QDRANT_CONFIG["API_KEY"])
            cls._mongo_db = MongoManager.initialize(MONGODB_CONFIG["URI"], MONGODB_CONFIG["DATABASE"])
            cls._model = Model(MODEL_CONFIG["API_KEY"])
            cls._embedding_model = cls._model.get_embedding_model()
            cls._current_data = cls._mongo_db.find_one(MONGODB_CONFIG["CHAT_DB"], {"key": "DATABASE_CONFIG"})["selected_db"]
            cls._store_qdrant = cls._qdrant_db.get_store(cls._current_data, cls._embedding_model)
            cls._retriever = cls._qdrant_db.get_retriever(cls._store_qdrant)
            cls._ip = socket.gethostbyname(socket.gethostname())
            cls._initialized = True

    @classmethod
    def config_ui(cls):
        cls.initialize()
        Manager(
            cls._mongo_db,
            MONGODB_CONFIG["CHAT_HISTORY"],
            MONGODB_CONFIG["LOGIN_HISTORY"],
            MONGODB_CONFIG["BAN_COLLECTION"],
            MODEL_CONFIG["CHAT"],
            MODEL_CONFIG["EMBEDDED"],
            cls._ip
        )
        Collections(cls._qdrant_db, cls._mongo_db, MONGODB_CONFIG["CHAT_DB"])
        Upload(cls._qdrant_db, cls._embedding_model, Data)
        Chat(cls._mongo_db, MONGODB_CONFIG["CHAT_HISTORY"], cls._qdrant_db, cls._current_data, cls._retriever,
             cls._model, cls._ip)

    @classmethod
    def display(cls):
        st.set_page_config(page_title="IUH - Truy vấn dữ liệu", page_icon="🏫")
        st.markdown(custom_css, unsafe_allow_html=True)
        cls.config_ui()

        if "logged_in" not in st.session_state:
            st.session_state.logged_in = False
        if "user_role" not in st.session_state:
            st.session_state.user_role = None

        if not st.session_state.logged_in:
            Login.show(cls._mongo_db, MONGODB_CONFIG["ACCOUNT"], MONGODB_CONFIG["LOGIN_HISTORY"], MONGODB_CONFIG["BAN_COLLECTION"], cls._ip)
        else:
            cls.build_navigation()

    @classmethod
    def build_navigation(cls):
        cls.initialize()
        if st.session_state.user_role == "admin":
            menu_items = ["Trang chủ", "Quản lý", "Upload PDF", "Xem bộ sưu tập", "Chatbot"]
        else:  # guest
            menu_items = ["Trang chủ", "Chatbot"]

        page = cls.create_sidebar_menu(menu_items)

        match page:
            case "Trang chủ":
                Home.show()
            case "Quản lý":
                Manager.show()
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
