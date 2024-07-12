from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class Data:
    def __init__(self):
        pass
    @staticmethod
    def process_pdf(file_path, chunk_size: int = 1000, chunk_overlap: int = 400):
        try:
            data = PyPDFLoader(file_path)
            data = data.load()
            text_split = RecursiveCharacterTextSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                separators=[
                    "\n\n",
                    "\n",
                    " ",
                    ".",
                    ",",
                    "\u200b",  # Zero-width space
                    "\uff0c",  # Fullwidth comma
                    "\u3001",  # Ideographic comma
                    "\uff0e",  # Fullwidth full stop
                    "\u3002",  # Ideographic full stop
                    "",
                ]
            )
            text_split = text_split.split_documents(data)
            return text_split
        except Exception as e:
            return e



