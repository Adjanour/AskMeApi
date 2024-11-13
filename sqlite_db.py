import sqlite3
from db_interface import DBInterface
from utils import generate_api_key  # Import the generate_api_key function
from typing import List, Dict, Optional


class SQLiteDB(DBInterface):
    def __init__(self, db_name: str = "multitenant_chatbot.db"):
        self.db_name = db_name

    def _get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row  # To access columns by name
        return conn

    def create_tenant(self, name: str, config_settings: Optional[Dict[str, str]] = None) -> Dict:
        api_key = generate_api_key()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO tenants (name, api_key) VALUES (?, ?)", (name, api_key))
            tenant_id = cursor.lastrowid  # Get the generated tenant ID for later use

            if config_settings:
                for key, value in config_settings.items():
                    cursor.execute("INSERT INTO settings (tenant_id, setting_key, setting_value) VALUES (?, ?, ?)",
                                   (tenant_id, key, value))

            conn.commit()

        return {"tenant_id": tenant_id, "name": name, "api_key": api_key}

    def add_faq(self, tenant_id: int, question: str, answer: str, embedding: bytes) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO faqs (tenant_id, question, answer, embedding) VALUES (?, ?, ?, ?)",
                           (tenant_id, question, answer, embedding))
            conn.commit()

    def get_faqs(self, tenant_id: int) -> List[Dict[str, str]]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT question, answer, embedding FROM faqs WHERE tenant_id=?", (tenant_id,))
            return [{"question": row["question"], "answer": row["answer"], "embedding": row["embedding"]} for row in cursor.fetchall()]

    def get_tenant_by_api_key(self, api_key: str) -> Optional[int]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM tenants WHERE api_key=?", (api_key,))
            tenant = cursor.fetchone()
            return tenant[0] if tenant else None

    def initialize_db(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS tenants (id INTEGER PRIMARY KEY, name TEXT, api_key TEXT UNIQUE)")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS faqs (
                    id INTEGER PRIMARY KEY, 
                    tenant_id INTEGER, 
                    question TEXT, 
                    answer TEXT, 
                    embedding BLOB, 
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE)
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY, 
                    tenant_id INTEGER, 
                    setting_key TEXT, 
                    setting_value TEXT, 
                    FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE)
            """)
            conn.commit()
