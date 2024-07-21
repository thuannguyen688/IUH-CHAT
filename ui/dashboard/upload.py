import os
import time
import streamlit as st
from qdrant_client.http.exceptions import UnexpectedResponse
from langchain_community.document_loaders import PyPDFLoader, WebBaseLoader, CSVLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from bs4 import BeautifulSoup
import re
from langchain.schema import Document


class Upload:
    MAX_FILE_SIZE_MB = 5
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_FILE_TYPE = "pdf"

    @staticmethod
    def get_temp_filename(collection_name, typefile):
        return f"{collection_name}_{int(time.time())}.{typefile}"

    @classmethod
    def show(cls):
        st.title("UPLOAD DATA")
        tab1, tab2, tab3 = st.tabs(["PDF", "WEB", "CSV"])

        with tab1:
            cls.upload_pdf_ui()
        with tab2:
            cls.upload_web_ui()
        with tab3:
            cls.upload_csv_ui()

    @classmethod
    def upload_pdf_ui(cls):
        st.info(f"Note: Maximum file size is {Upload.MAX_FILE_SIZE_MB}MB.")
        uploaded_file = st.file_uploader(f"Choose a {Upload.ALLOWED_FILE_TYPE} file", type=Upload.ALLOWED_FILE_TYPE,
                                         accept_multiple_files=False)
        cls._handle_file_upload(uploaded_file, "pdf")

    @classmethod
    def upload_csv_ui(cls):
        st.info(f"Note: Maximum file size is {Upload.MAX_FILE_SIZE_MB}MB.")
        uploaded_file = st.file_uploader(f"Choose a CSV file", type=["csv"],
                                         accept_multiple_files=False)
        cls._handle_file_upload(uploaded_file, "csv")

    @classmethod
    def upload_web_ui(cls):
        st.info("Enter a URL to scrape and upload.")
        url = st.text_input("Enter URL")
        if url:
            cls.initialize_session_state()
            cls.show_database_options("web", url)

    @classmethod
    def _handle_file_upload(cls, uploaded_file, file_type):
        if uploaded_file:
            file_size_mb = uploaded_file.size / (1024 * 1024)
            st.caption(f"File size: {file_size_mb:.2f} MB")
            if uploaded_file.size > Upload.MAX_FILE_SIZE_BYTES:
                st.error(f"File is too large. Please upload a file smaller than {Upload.MAX_FILE_SIZE_MB}MB.")
            else:
                cls.initialize_session_state()
                cls.show_database_options(file_type, uploaded_file)

    @classmethod
    def show_database_options(cls, upload_type, data):
        tab1, tab2 = st.tabs(["Create new database", "Add to existing database"])

        with tab1:
            cls._new_database_form(upload_type, data)

        with tab2:
            cls._existing_database_form(upload_type, data)

    @classmethod
    def _new_database_form(cls, upload_type, data):
        with st.form("new_database_form"):
            new_collection_name = st.text_input("Enter new database name", "")
            col1, col2 = st.columns([2.5, 5.5])
            with col1:
                submit_new = st.form_submit_button("Upload to new database")
            with col2:
                refresh_new = st.form_submit_button("Refresh")

            if submit_new:
                if new_collection_name.strip() in st.session_state.collection_names:
                    st.error("Database name already exists")
                elif new_collection_name.strip():
                    cls.process_upload(upload_type, data, new_collection_name.strip())

            if refresh_new:
                st.rerun()

    @classmethod
    def _existing_database_form(cls, upload_type, data):
        with st.form("existing_database_form"):
            if not st.session_state.existing_collections:
                st.warning("No existing databases. Please create a new one.")
            else:
                collection_options = [f"{col['name']} ({col['points_count']} documents)" for col in
                                      st.session_state.existing_collections]
                selected_collection = st.selectbox("Select database:", collection_options)

            col1, col2 = st.columns([3, 5.5])
            with col1:
                submit_existing = st.form_submit_button("Upload to selected database")
            with col2:
                refresh_existing = st.form_submit_button("Refresh")

            if submit_existing and selected_collection:
                collection_name = selected_collection.split(" (")[0]
                cls.process_upload(upload_type, data, collection_name)

            if refresh_existing:
                st.rerun()

    @classmethod
    def process_upload(cls, upload_type, data, collection_name):
        with st.spinner('Processing...'):
            start_time = time.time()
            temp_filename = None
            try:
                if upload_type == "pdf":
                    temp_filename = cls.get_temp_filename(collection_name, Upload.ALLOWED_FILE_TYPE)
                    content = cls._process_file(data, temp_filename, cls.process_pdf)
                elif upload_type == "web":
                    content = cls.process_web(data)
                elif upload_type == "csv":
                    temp_filename = cls.get_temp_filename(collection_name, 'csv')
                    content = cls._process_file(data, temp_filename, cls.process_csv)
                else:
                    raise ValueError("Invalid upload type")

                if isinstance(content, Exception):
                    raise content

                model = st.session_state.embedding_model
                st.session_state.qdrant_db.upload_data(collection_name, content, model)

                processing_time = time.time() - start_time
                st.success(f"Processing completed in {processing_time:.2f} seconds!")
                cls._update_session_state()

            except (UnexpectedResponse, TimeoutError, ConnectionError) as e:
                st.error(f"Connection error to server: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")
            finally:
                if temp_filename and os.path.exists(temp_filename):
                    try:
                        os.remove(temp_filename)
                    except Exception as e:
                        st.warning(f"Could not delete temporary file: {str(e)}")

    @staticmethod
    def _process_file(data, temp_filename, process_func):
        with open(temp_filename, "wb") as f:
            f.write(data.getbuffer())
        return process_func(temp_filename)

    @staticmethod
    def initialize_session_state():
        if 'existing_collections' not in st.session_state:
            st.session_state.existing_collections = st.session_state.qdrant_db.get_collections()
        if 'collection_names' not in st.session_state:
            st.session_state.collection_names = [col["name"].strip() for col in st.session_state.existing_collections]

    @staticmethod
    def _update_session_state():
        st.session_state.existing_collections = st.session_state.qdrant_db.get_collections()
        st.session_state.collection_names = [col["name"].strip() for col in st.session_state.existing_collections]

    @classmethod
    def process_pdf(cls, file_path):
        try:
            data = PyPDFLoader(file_path).load()
            text_split = cls._split_text(data)
            if not text_split:
                raise ValueError("No content extracted from PDF")
            return text_split
        except Exception as e:
            return e

    @classmethod
    def process_web(cls, url):
        try:
            os.environ["USER_AGENT"] = "MyAgent"
            loader = WebBaseLoader(url)
            loader.requests_kwargs = {'verify': False}
            html_content = loader.scrape('html.parser')
            for element in html_content(['script', 'style', 'meta', 'link', 'comment', 'a']):
                element.decompose()

            text = html_content.get_text(separator='\n', strip=True)
            text = cls._clean_text(text)

            data = [Document(page_content=text, metadata={"source": url})]
            text_split = cls._split_text(data)
            if not text_split:
                raise ValueError("No content extracted from web page")
            return text_split
        except Exception as e:
            return e

    @classmethod
    def process_csv(cls, file_path):
        try:
            # Try different encodings
            encodings = ['utf-8', 'iso-8859-1', 'cp1252']
            data = []

            for encoding in encodings:
                try:
                    loader = CSVLoader(file_path, encoding=encoding)
                    data = loader.load()
                    if data:
                        break
                except UnicodeDecodeError:
                    continue

            if not data:
                raise ValueError("Unable to read the CSV file with supported encodings")

            # Extract column names
            with open(file_path, 'r', encoding= encoding) as f:
                header = f.readline().strip().split(',')

            # Process each row
            processed_data = []
            for doc in data:
                content = doc.page_content
                metadata = doc.metadata

                # Split the content into key-value pairs
                pairs = content.split(',')

                # Create a dictionary of all fields
                fields = {header[i]: pairs[i].strip() for i in range(min(len(header), len(pairs)))}

                # Create a more detailed page content
                detailed_content = "\n".join([f"{k}: {v}" for k, v in fields.items()])

                # Update metadata with all fields for better searchability
                metadata.update(fields)

                # Create a new document with detailed content and enhanced metadata
                processed_data.append(Document(page_content=detailed_content, metadata=metadata))

            text_split = cls._split_text(processed_data)
            if not text_split:
                raise ValueError("No content extracted from CSV after splitting")
            return text_split

        except Exception as e:
            return ValueError(f"Error processing CSV file: {str(e)}")

    @staticmethod
    def _clean_text(text):
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^a-zA-Z0-9À-ỹ\s.,!?]', '', text)
        text = re.sub(r'\n\s*\n', '\n', text)
        return text.strip()

    @staticmethod
    def _split_text(data, chunk_size: int = 1000, chunk_overlap: int = 200):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", " ", ".", ",", "\u200b", "\uff0c", "\u3001", "\uff0e", "\u3002", ""]
        )
        return text_splitter.split_documents(data)