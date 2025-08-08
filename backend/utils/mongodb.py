import collections
from pymongo import MongoClient
from typing import Optional
import os


def get_mongo_client(url: Optional[str] = None) -> MongoClient:
    uri = uri or os.getenv("MONGO_URI", "your-mongodb-atlas-uri")
    return MongoClient(uri)


def get_mongo_collection(db_name: str, collection_name: str):
    client = get_mongo_client()
    db = client[db_name]
    return db[collection_name]


if __name__ == "__main__":
    collections = get_mongo_collection("test", "test")
    print(collections)