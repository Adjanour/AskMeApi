import pickle
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorClient
from numpy import ndarray
from pymongo.errors import DuplicateKeyError
from app.db_interface import DBInterface
from app.utils import generate_api_key

uri = "mongodb+srv://adjanour:xpN8EjMWNPLaZWaY@cluster0.lrshh.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"


class MongoDBAsync(DBInterface):
    def __init__(self, db_uri: str = uri, db_name: str = "multitenant_chatbot"):
        self.client = AsyncIOMotorClient(db_uri)
        self.db = self.client[db_name]

    async def initialize_db(self) -> None:
        # Create indexes for faster queries
        await self.db["tenants"].create_index("api_key", unique=True)
        await self.db["faqs"].create_index("tenant_id")
        await self.db["embeddings"].create_index("tenant_id")

    async def create_tenant(self, name: str, config_settings: Optional[Dict[str, str]] = None) -> Dict:
        api_key = generate_api_key()
        tenants_collection = self.db["tenants"]
        tenant = {"name": name, "api_key": api_key}

        try:
            result = await tenants_collection.insert_one(tenant)
            tenant_id = result.inserted_id

            if config_settings:
                settings_collection = self.db["settings"]
                settings = [
                    {"tenant_id": tenant_id, "setting_key": key, "setting_value": value}
                    for key, value in config_settings.items()
                ]
                await settings_collection.insert_many(settings)

            return {"tenant_id": str(tenant_id), "name": name, "api_key": api_key}
        except DuplicateKeyError:
            raise ValueError("A tenant with the same API key already exists.")

    async def add_faq(self, tenant_id: str, question: str, answer: str, embedding: bytes) -> None:
        faqs_collection = self.db["faqs"]
        print("adding faq", tenant_id, question, answer, embedding)

        # Insert FAQ document with the embedding directly included
        await faqs_collection.insert_one(
            {
                "tenant_id": tenant_id,
                "question": question,
                "answer": answer,
                "embedding": embedding  # Store embedding directly in the FAQ document
            }
        )
        return None

    async def add_faq_bulk(self, tenant_id: str, faqs: List[Dict[str, str]], embeddings: ndarray) -> None:
        faqs_collection = self.db["faqs"]

        # Prepare the list of documents to insert
        bulk_data = []
        for faq, embedding in zip(faqs, embeddings):
            bulk_data.append({
                "tenant_id": tenant_id,
                "question": faq["question"],
                "answer": faq["answer"],
                "embedding": pickle.dumps(embedding)  # Embed directly with the FAQ
            })

        # Perform the bulk insert
        if bulk_data:
            await faqs_collection.insert_many(bulk_data)
        return None

    async def get_faqs(self, tenant_id: str) -> List[Dict[str, str]]:
        faqs_collection = self.db["faqs"]

        # Retrieve all FAQs for the given tenant
        faqs = await faqs_collection.find({"tenant_id": tenant_id}).to_list(length=None)

        return faqs

    async def get_tenant_by_api_key(self, api_key: str) -> Optional[str]:
        tenants_collection = self.db["tenants"]
        tenant = await tenants_collection.find_one({"api_key": api_key})
        return str(tenant["_id"]) if tenant else None
