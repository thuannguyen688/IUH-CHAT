import streamlit as st
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash

class Login:
    @staticmethod
    def show(mongo_db, account, login_history, ban_collection, ip):
        st.html('''<style>
        [data-baseweb="tab-border"] {
            display: none;
            
        }
        section {
            display: flex;
            justify-content: center;
            align-items: center;
        }
         [data-baseweb="tab-list"] {
            margin-left: auto;
            width: fit-content;
        }


        header {
            display:none !important;
        }

        </style>''')
        st.html("<h3 class='centered-title'>HỆ THỐNG TRUY XUẤT DỮ LIỆU</h3>")
        tab1, tab2 = st.tabs(["Đăng nhập", "Đăng ký"])
        with tab1:
            Login.show_login_form(mongo_db, account, login_history, ban_collection, ip)

        with tab2:
            Login.show_register_form(mongo_db, account)

    @staticmethod
    def show_login_form(mongo_db, account, login_history, ban_collection, ip):
        # st.subheader("LOGIN")
        with st.form("login_form"):
            username = st.text_input("Tên đăng nhập")
            password = st.text_input("Mật khẩu", type="password")
            submit_button = st.form_submit_button("Đăng nhập")

        if submit_button:
            Login.login(mongo_db, account, login_history, ban_collection, username, password, ip)

    @staticmethod
    def show_register_form(mongo_db, account):
        # st.subheader("REGISTER")
        with st.form("register_form"):
            new_username = st.text_input("Tên đăng nhập mới")
            new_password = st.text_input("Mật khẩu mới", type="password")
            confirm_password = st.text_input("Xác nhận mật khẩu", type="password")
            register_button = st.form_submit_button("Đăng ký")

        if register_button:
            Login.register(mongo_db, account, new_username, new_password, confirm_password)

    @staticmethod
    def login(mongo_db, account, login_history, ban_collection, username, password, ip):
        if Login.check_banned_ip(mongo_db, ban_collection, username):
            st.error("Tài khoản của bạn đã bị cấm. Vui lòng liên hệ quản trị viên.")
            return

        user = mongo_db.find_one(account, {"username": username})
        if user and check_password_hash(user['password'], password):
            st.session_state.logged_in = True
            st.session_state.user_role = user['role']
            if Login.save_login_info(mongo_db, login_history, username, user['role'], ip):
                if user['role'] == 'admin':
                    st.success("Đăng nhập admin thành công!")
                    st.session_state.show_admin = True
                else:
                    st.success("Đăng nhập thành công!")
                st.rerun()
        else:
            st.error("Thông tin đăng nhập không chính xác")

    @staticmethod
    def register(mongo_db, account, new_username, new_password, confirm_password):
        if new_username.replace(" ", "") == "" or new_password.replace(" ", "") == "":
            st.error("Tên đăng nhập và mật khẩu không được trống")
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
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            mongo_db.insert_one(account, new_user)
            st.success("Đăng ký thành công! Bạn có thể đăng nhập ngay bây giờ.")
            st.session_state.show_register = False
            st.rerun()

    @staticmethod
    def save_login_info(mongo_db, login_history, username, role, ip):
        login_info = {
            "username": username,
            "role": role,
            "ip_address": ip,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        mongo_db.insert_one(login_history, login_info)
        return True

    @staticmethod
    def logout():
        for key in ['logged_in', 'user_role', 'current_page', 'show_register', 'show_admin', 'chat_history']:
            st.session_state.pop(key, None)
        st.rerun()

    @staticmethod
    def check_banned_ip(mongo_db, ban_collection, username):
        banned_ip = mongo_db.find_one(ban_collection, {"username": username})
        return banned_ip is not None