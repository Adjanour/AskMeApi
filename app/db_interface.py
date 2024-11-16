from typing import List, Dict, Optional
from abc import ABC, abstractmethod

from numpy import ndarray


class DBInterface(ABC):

    @abstractmethod
    async def create_tenant(self, name: str, config_settings: Optional[Dict[str, str]] = None) -> Dict:
        pass

    @abstractmethod
    async def add_faq(self, tenant_id: str, question: str, answer: str, embedding: bytes) -> None:
        pass

    @abstractmethod
    async def get_faqs(self, tenant_id: str) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    async def get_tenant_by_api_key(self, api_key: str) -> Optional[str]:
        pass

    @abstractmethod
    async def add_faq_bulk(self, tenant_id: str, faqs: List[Dict[str, str]], embeddings: ndarray) -> None:
        pass

    @abstractmethod
    async def initialize_db(self) -> None:
        pass
