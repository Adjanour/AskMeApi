from typing import List, Dict, Optional
from abc import ABC, abstractmethod


class DBInterface(ABC):

    @abstractmethod
    async def create_tenant(self, name: str, config_settings: Optional[Dict[str, str]] = None) -> Dict:
        pass

    @abstractmethod
    async def add_faq(self, tenant_id: int, question: str, answer: str, embedding: bytes) -> None:
        pass

    @abstractmethod
    async def get_faqs(self, tenant_id: int) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    async def get_tenant_by_api_key(self, api_key: str) -> Optional[int]:
        pass

    @abstractmethod
    def initialize_db(self) -> None:
        pass
