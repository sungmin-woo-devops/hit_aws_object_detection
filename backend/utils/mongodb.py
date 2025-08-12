import collections
from pymongo import MongoClient
from typing import Optional
import os


def get_mongo_client(url: Optional[str] = None) -> MongoClient:
    uri = url or os.getenv("MONGO_URI", "mongodb+srv://admin:admin@cluster0.zqz7z.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
    return MongoClient(uri)


def get_mongo_collection(db_name: str, collection_name: str):
    client = get_mongo_client()
    db = client[db_name]
    return db[collection_name]


if __name__ == "__main__":
    collections = get_mongo_collection("test", "test")
    print(collections)