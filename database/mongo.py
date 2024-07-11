from pymongo import MongoClient


class MongoManager:
    _instance = None
    _client = None
    _db = None

    @classmethod
    def initialize(cls, uri, db_name):
        if cls._instance is None:
            cls._instance = cls(uri, db_name)
        return cls._instance

    def __init__(self, uri, db_name):
        if MongoManager._client is None:
            MongoManager._client = MongoClient(uri)
            MongoManager._db = MongoManager._client[db_name]

    @classmethod
    def get_collection(cls, collection_name):
        if cls._instance is None:
            raise Exception("MongoManager has not been initialized. Call initialize() first.")
        return cls._db[collection_name]

    @classmethod
    def insert_one(cls, collection_name, document):
        return cls.get_collection(collection_name).insert_one(document)

    @classmethod
    def insert_many(cls, collection_name, documents):
        return cls.get_collection(collection_name).insert_many(documents)

    @classmethod
    def find_one(cls, collection_name, query):
        return cls.get_collection(collection_name).find_one(query)

    @classmethod
    def find_many(cls, collection_name, query):
        return list(cls.get_collection(collection_name).find(query))

    @classmethod
    def update_one(cls, collection_name, query, new_values):
        return cls.get_collection(collection_name).update_one(query, {"$set": new_values})

    @classmethod
    def update_many(cls, collection_name, query, new_values):
        return cls.get_collection(collection_name).update_many(query, {"$set": new_values})

    @classmethod
    def delete_one(cls, collection_name, query):
        return cls.get_collection(collection_name).delete_one(query)

    @classmethod
    def delete_many(cls, collection_name, query):
        return cls.get_collection(collection_name).delete_many(query)

    @classmethod
    def close_connection(cls):
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None

