import re
import streamlit as st
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
import pytz

class Login:
    _vietnam_tz = pytz.timezone('Asia/Ho_Chi_Minh')

    @staticmethod
    def show(mongo_db, account, login_history, ban_collection, ip):
        st.html('''<style>

        section {
            display: flex;
            justify-content: center;
            align-items: center;
        }


        .stButton>button {
            width: 100%;
        }
        </style>''')


        if 'show_register' not in st.session_state:
            st.session_state.show_register = False

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.session_state.show_register:
                Login.show_register_form(mongo_db, account)
            else:
                Login.show_login_form(mongo_db, account, login_history, ban_collection, ip)

        if 'registration_success' in st.session_state and st.session_state.registration_success:
            st.session_state.registration_success = False
            st.session_state.show_register = False
            st.success("Đăng ký thành công! Vui lòng đăng nhập.")
            st.rerun()

    @staticmethod
    def show_login_form(mongo_db, account, login_history, ban_collection, ip):
        st.html("<h1 style='text-align: center'>ĐĂNG NHẬP</h1>")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            col1, col2 = st.columns(2)
            with col1:
                submit_button = st.form_submit_button("Đăng nhập")
            with col2:
                register_button = st.form_submit_button("Đăng ký")

        if submit_button:
            Login.login(mongo_db, account, login_history, ban_collection, username, password, ip)
        elif register_button:
            st.session_state.show_register = True
            st.rerun()

    @staticmethod
    def show_register_form(mongo_db, account):
        st.html("<h1 style='text-align: center'>ĐĂNG KÝ</h1>")
        with st.form("register_form"):

            new_username = st.text_input("Tên đăng nhập mới")
            new_password = st.text_input("Mật khẩu mới", type="password")
            confirm_password = st.text_input("Xác nhận mật khẩu", type="password")
            col1, col2 = st.columns(2)
            with col1:
                register_button = st.form_submit_button("Đăng ký")
            with col2:
                login_button = st.form_submit_button("Đăng nhập")

        if register_button:
            Login.register(mongo_db, account, new_username, new_password, confirm_password)
        elif login_button:
            st.session_state.show_register = False
            st.rerun()

    @classmethod
    def login(cls, mongo_db, account, login_history, ban_collection, username, password, ip):
        if Login.check_banned_user(mongo_db, ban_collection, username):
            st.error("Tài khoản của bạn đã bị cấm. Vui lòng liên hệ quản trị viên.")
            return

        user = mongo_db.find_one(account, {"username": username})
        if user and check_password_hash(user['password'], password):
            st.session_state.logged_in = True
            st.session_state.user_role = user['role']
            st.session_state.username = username
            if Login.save_login_info(mongo_db, login_history, username, user['role'], ip):
                if user['role'] == 'admin':
                    st.success("Đăng nhập admin thành công!")
                    st.session_state.show_admin = True
                else:
                    st.success("Đăng nhập thành công!")
                st.rerun()
        else:
            st.error("Thông tin đăng nhập không chính xác")



    @classmethod
    def register(cls, mongo_db, account, new_username, new_password, confirm_password):
        if new_username.replace(" ", "") == "" or new_password.replace(" ", "") == "":
            st.error("Tên đăng nhập và mật khẩu không được trống")
        elif len(new_username) < 5:
            st.error("Tên đăng nhập phải có ít nhất 5 ký tự")
        elif not re.match(r'^(?=.*[A-Za-z])(?=.*\d)(?=.*[@$!%*#?&])[A-Za-z\d@$!%*#?&]{8,}$', new_password):
            st.error("Mật khẩu phải có ít nhất 8 ký tự, bao gồm chữ cái, chữ số và ký tự đặc biệt")
        elif new_password != confirm_password:
            st.error("Mật khẩu xác nhận không khớp!")
        elif mongo_db.find_one(account, {"username": new_username}):
            st.error("Tên đăng nhập đã tồn tại!")
        else:
            hashed_password = generate_password_hash(new_password)
            new_user = {
                "username": new_username,
                "password": hashed_password,
                "role": "user",
                "created_at": datetime.now(cls._vietnam_tz).strftime("%Y-%m-%d %H:%M:%S"),
            }
            mongo_db.insert_one(account, new_user)
            st.session_state.registration_success = True
            st.rerun()

    @classmethod
    def save_login_info(cls, mongo_db, login_history, username, role, ip):
        login_info = {
            "username": username,
            "role": role,
            "ip_address": ip,
            "timestamp": datetime.now(cls._vietnam_tz).strftime("%Y-%m-%d %H:%M:%S %Z")
        }
        mongo_db.insert_one(login_history, login_info)
        return True

    @staticmethod
    def logout():
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

    @staticmethod
    def check_banned_user(mongo_db, ban_collection, username):
        banned_user = mongo_db.find_one(ban_collection, {"username": username})
        return banned_user is not None
