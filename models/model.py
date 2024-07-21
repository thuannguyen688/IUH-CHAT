import datetime
from typing import List, Union
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.text_splitter import RecursiveCharacterTextSplitter


class Model:
    _instance = None
    _embedding_model = None
    _google_chain = None
    _google_api_key = None
    _huggingface_api_key = None
    _embeded_model_name = None

    @classmethod
    def get_current_year(cls):
        return datetime.datetime.now().year

    system_prompt = SystemMessagePromptTemplate.from_template("""
    Bạn là chatbot tư vấn tuyển sinh của Đại học Công nghiệp TP.HCM. Nhiệm vụ của bạn là cung cấp thông tin chính xác và cập nhật nhất về tuyển sinh, thủ tục nhập học, chương trình đào tạo và điểm tuyển sinh dựa trên dữ liệu mới nhất từ nhà trường.

    Hãy tuân thủ các quy tắc sau:
    1. Năm hiện tại là {current_year}. Tất cả thông tin phải liên quan đến năm nay hoặc tương lai, trừ khi được yêu cầu cụ thể về dữ liệu lịch sử.
    2. Trả lời ngắn gọn, chính xác và đúng trọng tâm câu hỏi.
    3. Chỉ sử dụng thông tin từ nguồn dữ liệu chính thức được cung cấp.
    4. Nếu không có thông tin cụ thể, hãy nói rõ và hướng dẫn người hỏi kiểm tra website chính thức của trường.
    5. Khi trả lời về điểm tuyển sinh, phân biệt rõ giữa điểm xét tuyển học bạ (thang 30) và điểm đánh giá năng lực (thang 1000). Cung cấp đầy đủ thông tin liên quan, bao gồm ghi chú của chương trình đào tạo.
    6. Sử dụng ngôn ngữ thân thiện, dễ hiểu cho học sinh và phụ huynh.
    7. Nếu không biết câu trả lời hoặc thông tin không có sẵn, hãy thông báo rõ ràng và hướng dẫn người hỏi truy cập website chính thức của trường để biết thêm thông tin.
    8. Khi trả lời nên chú thích điểm tuyển đó là điểm tuyển học bạ hay đánh giá năng lực.
    9. Khi trả lời hãy liệt kê tất cả điểm và phương thức xét tuyển của ngành được hỏi.
    """)

    human_prompt = HumanMessagePromptTemplate.from_template("""
    Dựa trên thông tin sau đây:

    {context}

    Hãy trả lời câu hỏi sau: {question}
    """)

    prompt = ChatPromptTemplate.from_messages([system_prompt, human_prompt])

    def __new__(cls, google_api_key, huggingface_api_key, embed_model_name):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._google_api_key = google_api_key
            cls._huggingface_api_key = huggingface_api_key
            cls._embeded_model_name = embed_model_name
            cls._init_models()
        return cls._instance

    @classmethod
    def _init_models(cls):
        cls._embedding_model = HuggingFaceInferenceAPIEmbeddings(
            api_key=cls._huggingface_api_key, model_name=cls._embeded_model_name
        )
        cls._google_chain = cls._init_google_chain()


    @classmethod
    def chat(cls, docs: Union[str, List[Document]], question: str) -> str:
        if cls._instance is None:
            raise Exception("Model hasn't been initialized")

        response = cls._google_chain.invoke({
            "context": docs,
            "question": question,
            "current_year": cls.get_current_year()
        })

        return cls.postprocess_response(response)

    @classmethod
    def postprocess_response(cls, response: str) -> str:
        # Loại bỏ các câu không cần thiết hoặc lặp lại
        sentences = response.split('. ')
        unique_sentences = list(dict.fromkeys(sentences))

        # Thêm nhắc nhở về việc kiểm tra thông tin
        reminder = "\n\nLưu ý: Để có thông tin chính xác và cập nhật nhất, vui lòng kiểm tra tại website chính thức: https://tuyensinh.iuh.edu.vn/ hoặc liên hệ trực tiếp với phòng Tuyển sinh."

        return '. '.join(unique_sentences) + reminder

    @classmethod
    def _init_google_chain(cls, temperature: float = 0.3):
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=temperature,
                max_output_tokens=2048,
                top_p=0.9,
                top_k=40,
                max_retries=3,
                google_api_key=cls._google_api_key
            )
            return create_stuff_documents_chain(llm, cls.prompt)
        except Exception as e:
            print(f"Error initializing Google chain: {str(e)}")
            return None

    # Các phương thức khác giữ nguyên

    @classmethod
    def get_embedding_model(cls):
        if cls._instance is None:
            raise Exception("Model hasn't been initialized")
        if cls._embedding_model is None:
            cls._embedding_model = HuggingFaceInferenceAPIEmbeddings(
                api_key=cls._huggingface_api_key, model_name=cls._embeded_model_name
            )
        return cls._embedding_model

    @classmethod
    def get_chain(cls):
        if cls._instance is None:
            raise Exception("Model hasn't been initialized")
        if cls._google_chain is None:
            cls._google_chain = cls._init_google_chain()
        return cls._google_chain
    @classmethod
    def embedding_query(cls, question):
        return cls.get_embedding_model().embed_query(question)

    @classmethod
    def embedding_document(cls, document):
        return cls.get_embedding_model().embed_documents(document)