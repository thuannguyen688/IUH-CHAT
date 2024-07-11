import os
import time
import streamlit as st
from qdrant_client.http.exceptions import UnexpectedResponse
class Upload:
    MAX_FILE_SIZE_MB = 5
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_FILE_TYPE = "pdf"
    _qdrant = None
    _model_embed = None
    _data = None


    def __new__(cls, qdrant, model_embed, data):
        cls._qdrant = qdrant
        cls._model_embed = model_embed
        cls._data = data

    @classmethod
    def get_temp_filename(cls, collection_name):
        return f"{collection_name}_{int(time.time())}.{cls.ALLOWED_FILE_TYPE}"

    @classmethod
    def process_and_upload_file(cls, file_path, collection_name):
        pdf_content = cls._data.process_pdf(file_path)
        model = cls._model_embed
        cls._qdrant.upload_data(collection_name, pdf_content, model)

    @classmethod
    def initialize_session_state(cls):
        if 'existing_collections' not in st.session_state:
            st.session_state.existing_collections = cls._qdrant.get_collections()
        if 'collection_names' not in st.session_state:
            st.session_state.collection_names = [col["name"].strip() for col in st.session_state.existing_collections]

    @classmethod
    def show(cls):
        st.title("UPLOAD DATABASE")
        st.info(f"Lưu ý: Kích thước file tối đa là {cls.MAX_FILE_SIZE_MB}MB.")

        uploaded_file = st.file_uploader(f"Chọn file {cls.ALLOWED_FILE_TYPE}", type=cls.ALLOWED_FILE_TYPE,
                                         accept_multiple_files=False)

        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.caption(f"Kích thước file: {file_size_mb:.2f} MB")

            if uploaded_file.size > cls.MAX_FILE_SIZE_BYTES:
                st.error(f"File quá lớn. Vui lòng tải lên file có kích thước nhỏ hơn {cls.MAX_FILE_SIZE_MB}MB.")
            else:
                cls.initialize_session_state()

                tab1, tab2 = st.tabs(["Tạo database mới", "Thêm vào database có sẵn"])

                with tab1:
                    with st.form("new_database_form"):
                        new_collection_name = st.text_input("Nhập tên cơ sở dữ liệu mới", "")
                        col1, col2 = st.columns([2.5,5.5])
                        with col1:
                            submit_new = st.form_submit_button("Upload vào database mới")
                        with col2:
                            refresh_new = st.form_submit_button("Refresh")

                        if submit_new:
                            if new_collection_name.strip() in st.session_state.collection_names:
                                st.error("Tên cơ sở dữ liệu đã tồn tại")
                            elif new_collection_name.strip():
                                cls.process_upload(uploaded_file, new_collection_name.strip())

                        if refresh_new:
                            st.rerun()

                with tab2:
                    with st.form("existing_database_form"):
                        if not st.session_state.existing_collections:
                            st.warning("Không có database nào hiện có. Vui lòng tạo database mới.")
                        else:
                            collection_options = [f"{col['name']} ({col['points_count']} documents)" for col in
                                                  st.session_state.existing_collections]
                            selected_collection = st.selectbox("Chọn database:", collection_options)

                        col1, col2 = st.columns([3,5.5])
                        with col1:
                            submit_existing = st.form_submit_button("Upload vào database đã chọn")
                        with col2:
                            refresh_existing = st.form_submit_button("Refresh")

                        if submit_existing:
                            collection_name = selected_collection.split(" (")[0]
                            cls.process_upload(uploaded_file, collection_name)

                        if refresh_existing:
                            st.rerun()



    @classmethod
    def process_upload(cls, uploaded_file, collection_name):
        temp_filename = cls.get_temp_filename(collection_name)
        try:
            with open(temp_filename, "wb") as f:
                f.write(uploaded_file.getbuffer())

            with st.spinner('Đang xử lý...'):
                start_time = time.time()
                try:
                    cls.process_and_upload_file(temp_filename, collection_name)
                    processing_time = time.time() - start_time
                    st.success(f"Xử lý hoàn tất trong {processing_time:.2f} giây!")
                    # Cập nhật lại danh sách collection sau khi upload thành công
                    st.session_state.existing_collections = cls._qdrant.get_collections()
                    st.session_state.collection_names = [col["name"].strip() for col in
                                                         st.session_state.existing_collections]
                except (UnexpectedResponse, TimeoutError, ConnectionError) as e:
                    st.error("Lỗi kết nối đến máy chủ. Vui lòng thử lại sau.")
                except Exception as e:
                    st.error("Đã xảy ra lỗi không mong muốn. Vui lòng thử lại sau.")
                    st.write(e)
        except Exception as e:
            st.error("Đã xảy ra lỗi khi xử lý file. Vui lòng thử lại sau.")
            st.write(e)
        finally:
            if os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except Exception as e:
                    st.warning(f"Không thể xóa file tạm thời: {str(e)}")
