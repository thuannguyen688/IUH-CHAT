from langchain_qdrant import Qdrant
from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from typing import List, Dict, Optional

class QdrantManager:
    _instance = None
    _client = None
    _url = None
    _api_key = None
    def __new__(cls, url: str, api_key: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super(QdrantManager, cls).__new__(cls)
            cls._client = QdrantClient(url, api_key=api_key) if api_key else QdrantClient(url)
            cls._url = url
            cls._api_key = api_key
        return cls._instance

    def __init__(self, url: str, api_key: Optional[str] = None):
        pass

    @classmethod
    def get_instance(cls, url: str, api_key: Optional[str] = None):
        return cls(url, api_key)

    @classmethod
    def upload_data(cls, collection: str, docs, embedded, force_recreate: bool = False) -> Qdrant:
        if cls._client is None:
            raise Exception("QdrantManager has not been initialized. Call get_instance() first.")

        return Qdrant.from_documents(
            docs,
            embedding=embedded,
            url=cls._url,
            collection_name=collection,
            force_recreate=force_recreate,
            api_key=cls._api_key
        )

    @classmethod
    def get_store(cls, collection: str, embedded) -> Qdrant:
        if cls._client is None:
            raise Exception("QdrantManager has not been initialized. Call get_instance() first.")

        return Qdrant.from_existing_collection(
            embedding=embedded,
            collection_name=collection,
            url=cls._url,
            api_key=cls._api_key
        )

    @staticmethod
    def get_retriever(store, search_type: str = 'similarity', k: int = 3):
        return store.as_retriever(search_type=search_type, search_kwargs={'k': k})

    @classmethod
    def get_collections(cls) -> List[Dict]:
        if cls._client is None:
            raise Exception("QdrantManager has not been initialized. Call get_instance() first.")

        collections = cls._client.get_collections()
        detailed_collections = []

        for collection in collections.collections:
            collection_info = cls._client.get_collection(collection.name)
            vector_config = collection_info.config.params.vectors
            points_count = cls._client.count(collection_name=collection.name).count

            detailed_collections.append({
                'name': collection.name,
                'vector_size': vector_config.size,
                'distance_metric': vector_config.distance,
                'points_count': points_count
            })

        return detailed_collections

    @classmethod
    def delete_collection(cls, collection_name: str) -> bool:
        if cls._client is None:
            raise Exception("QdrantManager has not been initialized. Call get_instance() first.")

        try:
            cls._client.delete_collection(collection_name=collection_name)

            collections = cls._client.get_collections()
            return collection_name not in [col.name for col in collections.collections]

        except UnexpectedResponse as e:
            print(f"Lỗi khi xóa collection: {str(e)}")
            return False
        except Exception as e:
            print(f"Lỗi không mong đợi: {str(e)}")
            return False

    @staticmethod
    def get_data_from_store(retriever, question):
        return retriever.invoke(question)