import streamlit as st
from datetime import datetime


class Collections:
    _qdrant = None
    _mongodb = None
    _chat_db = None

    def __new__(cls, qdrant, mongodb, chat_db):
        if not cls._mongodb or not cls._qdrant:
            cls._qdrant = qdrant
            cls._mongodb = mongodb
            cls._chat_db = chat_db


    @classmethod
    def get_collections(cls):
        try:
            return [{
                'DatabaseName': col['name'],
                'Document Count': col['points_count'],
                'Vector Size': col['vector_size'],
                'Distance Metric': col['distance_metric']
            } for col in cls._qdrant.get_collections()]
        except Exception as e:
            st.error(f"Lỗi khi lấy thông tin collections: {str(e)}")
            return None

    @classmethod
    def update_selected_database(cls, database_name):
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            result = cls._mongodb.update_one(
                cls._chat_db,
                {"key": "DATABASE_CONFIG"},
                {
                    "selected_db": database_name,
                    "update_time": current_time
                }
            )
            if result.modified_count > 0:
                st.success(f"Đã cập nhật SELECTED_DATABASE thành {database_name}")
            elif result.upserted_id:
                st.success(f"Đã tạo mới và cập nhật SELECTED_DATABASE thành {database_name}")
            else:
                st.warning("Không có thay đổi nào được thực hiện")
            return result
        except Exception as e:
            st.error(f"Lỗi khi cập nhật database cho chat bot: {str(e)}")
            return None

    @classmethod
    def get_selected_database(cls):
        try:
            result = cls._mongodb.find_one(cls._chat_db, {"key": "DATABASE_CONFIG"})
            if result:
                return result.get('selected_db')
            else:
                # Nếu không tìm thấy, tạo mới với giá trị mặc định
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                default_config = {
                    "key": "DATABASE_CONFIG",
                    "selected_db": None,
                    "create_time": current_time,
                    "update_time": current_time
                }
                cls._mongodb.insert_one(cls._chat_db, default_config)
                return None
        except Exception as e:
            st.error(f"Lỗi khi lấy SELECTED_DATABASE: {str(e)}")
            return None

    @classmethod
    def display_collection(cls, col, current_collection):
        with st.expander(f"{col['DatabaseName']} - {col['Document Count']} documents"):
            st.write(f"Vector Size: {col['Vector Size']}")
            st.write(f"Distance Metric: {col['Distance Metric']}")

            col1, col2, col3 = st.columns([6, 3, 3])

            if current_collection != col['DatabaseName']:
                if col1.button("Chọn làm Database cho Chatbot", key=f"select_{col['DatabaseName']}"):
                    result = cls.update_selected_database(col['DatabaseName'])
                    if result.modified_count > 0 or result.upserted_id:
                        st.success(f"Đã cập nhật SELECTED_DATABASE thành {col['DatabaseName']}")
                        st.rerun()
                    else:
                        st.warning("Không có thay đổi nào được thực hiện")

                delete_key = f"delete_{col['DatabaseName']}"
                confirm_key = f"confirm_{col['DatabaseName']}"

                if delete_key not in st.session_state:
                    st.session_state[delete_key] = False

                if col2.button("Xóa Collection", key=f"delete_button_{col['DatabaseName']}", type="secondary"):
                    st.session_state[delete_key] = True

                if st.session_state[delete_key]:
                    @st.experimental_dialog("Xác nhận xóa collection")
                    def confirm_delete():
                        with st.form(key=f"delete_form_{col['DatabaseName']}"):
                            st.write(f"Bạn có chắc chắn muốn xóa collection '{col['DatabaseName']}'?")
                            confirmation_input = st.text_input("Nhập tên collection để xác nhận:", key=confirm_key)

                            col1, col2 = st.columns([2.5,6])
                            with col1:
                                submit = st.form_submit_button("Xác nhận xóa")
                            with col2:
                                cancel = st.form_submit_button("Hủy")

                            if submit:
                                if confirmation_input == col['DatabaseName']:
                                    if cls._qdrant.delete_collection(col['DatabaseName']):
                                        st.success(f"Đã xóa collection: {col['DatabaseName']}")
                                        st.session_state.collections_changed = True
                                        st.session_state[delete_key] = False
                                        st.rerun()
                                    else:
                                        st.error("Có lỗi xảy ra khi xóa collection")
                                else:
                                    st.error("Tên collection không khớp. Vui lòng nhập chính xác để xóa.")

                            if cancel:
                                st.session_state[delete_key] = False
                                st.rerun()

                    confirm_delete()

                    # Nếu người dùng đóng dialog mà không nhấn nút nào
                    if st.session_state[delete_key]:
                        st.session_state[delete_key] = False
            else:
                col1.info("Database đang được sử dụng cho Chatbot")

    @classmethod
    def show(cls):
        st.html("<h1 class='centered-title'>QUẢN LÝ DỮ LIỆU</h1>")
        collections = cls.get_collections()
        if collections is None:
            if st.button("Làm mới"):
                st.rerun()
        elif not collections:
            st.warning("Không có cơ sỡ dữ liệu")
        else:
            current_collection = cls.get_selected_database()
            for col in collections:
                cls.display_collection(col, current_collection)
            st.write(f"Database hiện tại cho Chatbot: **{current_collection}**")







