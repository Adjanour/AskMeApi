from typing import List, Dict, Optional
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.db_interface import DBInterface
from app.utils import generate_api_key  # Import the generate_api_key function

uri = "mongodb+srv://adjanour:xpN8EjMWNPLaZWaY@cluster0.lrshh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


class MongoDB(DBInterface):
    def __init__(self, db_uri: str = uri, db_name: str = "multitenant_chatbot"):
        self.client = AsyncIOMotorClient(db_uri)
        self.db = self.client[db_name]

    async def create_tenant(self, name: str, config_settings: Optional[Dict[str, str]] = None) -> Dict:
        api_key = generate_api_key()
        tenants_collection = self.db["tenants"]
        tenant = {"name": name, "api_key": api_key}
        result = await tenants_collection.insert_one(tenant)
        tenant_id = result.inserted_id

        settings_collection = self.db["settings"]
        if config_settings:
            for key, value in config_settings.items():
                await settings_collection.insert_one(
                    {"tenant_id": tenant_id, "setting_key": key, "setting_value": value})

        return {"tenant_id": str(tenant_id), "name": name, "api_key": api_key}

    async def add_faq(self, tenant_id: str, question: str, answer: str, embedding: bytes) -> None:
        faqs_collection = self.db["faqs"]
        await faqs_collection.insert_one(
            {"tenant_id": tenant_id, "question": question, "answer": answer, "embedding": embedding}
        )

    async def get_faqs(self, tenant_id: str) -> List[Dict[str, str]]:
        faqs_collection = self.db["faqs"]
        faqs_cursor = faqs_collection.find({"tenant_id": tenant_id})
        faqs = await faqs_cursor.to_list(length=None)  # Convert cursor to list
        return [{"question": faq["question"], "answer": faq["answer"], "embedding": faq["embedding"]} for faq in faqs]

    async def get_tenant_by_api_key(self, api_key: str) -> Optional[str]:
        tenants_collection = self.db["tenants"]
        tenant = await tenants_collection.find_one({"api_key": api_key})
        return str(tenant["_id"]) if tenant else None

    async def initialize_db(self) -> None:
        # MongoDB is schema-less, so no need for specific table creation
        pass
