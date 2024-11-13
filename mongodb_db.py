from pymongo import MongoClient
from db_interface import DBInterface
from utils import generate_api_key  # Import the generate_api_key function
from typing import List, Dict, Optional


class MongoDB(DBInterface):
    def __init__(self, db_uri: str = "mongodb://localhost:27017", db_name: str = "multitenant_chatbot"):
        self.client = MongoClient(db_uri)
        self.db = self.client[db_name]

    def create_tenant(self, name: str, config_settings: Optional[Dict[str, str]] = None) -> Dict:
        api_key = generate_api_key()
        tenants_collection = self.db["tenants"]
        tenant = {"name": name, "api_key": api_key}
        result = tenants_collection.insert_one(tenant)
        tenant_id = result.inserted_id

        settings_collection = self.db["settings"]
        if config_settings:
            for key, value in config_settings.items():
                settings_collection.insert_one({"tenant_id": tenant_id, "setting_key": key, "setting_value": value})

        return {"tenant_id": str(tenant_id), "name": name, "api_key": api_key}

    def add_faq(self, tenant_id: str, question: str, answer: str, embedding: bytes) -> None:
        faqs_collection = self.db["faqs"]
        faqs_collection.insert_one({"tenant_id": tenant_id, "question": question, "answer": answer, "embedding": embedding})

    def get_faqs(self, tenant_id: str) -> List[Dict[str, str]]:
        faqs_collection = self.db["faqs"]
        faqs = faqs_collection.find({"tenant_id": tenant_id})
        return [{"question": faq["question"], "answer": faq["answer"], "embedding": faq["embedding"]} for faq in faqs]

    def get_tenant_by_api_key(self, api_key: str) -> Optional[str]:
        tenants_collection = self.db["tenants"]
        tenant = tenants_collection.find_one({"api_key": api_key})
        return str(tenant["_id"]) if tenant else None

    def initialize_db(self) -> None:
        # MongoDB is schema-less, so no need for specific table creation
        pass
