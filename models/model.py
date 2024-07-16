from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings

class Model:
    _instance = None
    _embedding_model = None
    _google_chain = None
    _google_api_key = None
    _huggingface_api_key = None
    _embeded_model_name = None
    prompt = ChatPromptTemplate.from_messages([
        HumanMessagePromptTemplate.from_template("""
        Bạn là chatbot tư vấn tuyển sinh của Đại học Công nghiệp TP.HCM. Nhiệm vụ của bạn là cung cấp thông tin chính xác về tuyển sinh, thủ tục nhập học và chương trình đào tạo dựa trên dữ liệu cập nhật từ nhà trường.
        1. Trả lời đúng với yêu cầu, đi thẳng vào trọng tâm câu hỏi.
        2. Chỉ cung cấp thông tin từ nguồn dữ liệu chính thức của trường.
        3. Nếu không có thông tin, trả lời: "Xin lỗi, hiện tại tôi không có thông tin về vấn đề này. Bạn có thể liên hệ trực tiếp với phòng Tuyển sinh để được hỗ trợ chi tiết hơn."
        4. Không suy diễn hay thêm thông tin ngoài dữ liệu được cung cấp.
        5. Đối với các câu hỏi về thời hạn hoặc quy định cụ thể, luôn nhắc nhở người hỏi kiểm tra lại thông tin trên website chính thức là: https://tuyensinh.iuh.edu.vn/ hoặc liên hệ trực tiếp với trường bằng điện thoại. Với chi nhánh Hồ Chí Minh qua các số: (028) 3895 5858; (028) 3985 1932; (028) 3985 1917. Chi nhánh Quãng Ngãi: (0255) 625 0075; (0255) 222 2135; 0916 222 135. để có thông tin chính xác và cập nhật nhất.
        6. Sử dụng ngôn ngữ thân thiện, dễ hiểu và phù hợp với đối tượng là học sinh, phụ huynh quan tâm đến tuyển sinh.
        7. Nếu câu hỏi không rõ ràng, hãy yêu cầu người hỏi cung cấp thêm thông tin để có thể trả lời chính xác hơn.
        8. Nếu được hỏi về ngành có được trường đào tạo không thì hãy dự trên kết quả từ cơ sở dữ liệu nếu có hãy trả lời là có và các thông tin liên quan đến nó
        Ngữ cảnh: {context}
        Câu hỏi: {question}
        """)
    ])


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
        cls._embedding_model =  HuggingFaceInferenceAPIEmbeddings(
            api_key=cls._huggingface_api_key, model_name=cls._embeded_model_name
        )
        cls._google_chain = cls._init_google_chain()

    # @classmethod
    # def chat(cls, docs, question, chat_history):
    #     if cls._instance is None:
    #         raise Exception("Model hasn't been initialized")
    #     return cls._google_chain.invoke({
    #         "context": docs,
    #         "question": question,
    #         "chat_history": chat_history
    #     })
    @classmethod
    def chat(cls, docs, question):
        if cls._instance is None:
            raise Exception("Model hasn't been initialized")
        return cls._google_chain.invoke({
            "context": docs,
            "question": question,
        })

    @classmethod
    def _init_google_chain(cls, temperature: float = 0.4):
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=temperature,
            max_tokens=1000,
            top_p=0.95,
            top_k=64,
            max_retries=2,
            google_api_key=cls._google_api_key
        )
        return create_stuff_documents_chain(llm, cls.prompt)

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