import sqlite3
from fastapi import Depends
from utils import generate_api_key  # Import the generate_api_key function


# Function to get a new database connection for each request
def get_db():
    conn = sqlite3.connect("../multitenant_chatbot.db")
    conn.row_factory = sqlite3.Row  # To access columns by name (e.g. row['name'])
    try:
        yield conn
    finally:
        conn.close()


# Create tables if they don’t exist
def initialize_db():
    # You'll need to call this function at app startup to create tables if they don't exist
    with sqlite3.connect("../multitenant_chatbot.db") as conn:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS tenants (id INTEGER PRIMARY KEY, name TEXT, api_key TEXT UNIQUE)")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS faqs (id INTEGER PRIMARY KEY, tenant_id INTEGER, question TEXT, answer TEXT, "
            "embedding BLOB, FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE)"
        )
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS settings (id INTEGER PRIMARY KEY, tenant_id INTEGER, setting_key TEXT, "
            "setting_value TEXT, FOREIGN KEY (tenant_id) REFERENCES tenants(id) ON DELETE CASCADE)"
        )
        conn.commit()


# Function to create a new tenant
def create_tenant(name: str, config_settings: dict = None, conn: sqlite3.Connection = Depends(get_db)):
    api_key = generate_api_key()
    cursor = conn.cursor()

    # Insert new tenant with generated API key
    cursor.execute(
        "INSERT INTO tenants (name, api_key) VALUES (?, ?)",
        (name, api_key)
    )
    tenant_id = cursor.lastrowid  # Get the generated tenant ID for later use

    # Insert config settings for the tenant if provided
    if config_settings:
        for key, value in config_settings.items():
            cursor.execute(
                "INSERT INTO settings (tenant_id, setting_key, setting_value) VALUES (?, ?, ?)",
                (tenant_id, key, value)
            )
    conn.commit()

    return {"tenant_id": tenant_id, "name": name, "api_key": api_key}


# Add FAQ for a tenant
def add_faq(tenant_id, question, answer, embedding, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO faqs (tenant_id, question, answer, embedding) VALUES (?, ?, ?, ?)",
                   (tenant_id, question, answer, embedding))
    conn.commit()


# Retrieve FAQs for a tenant
def get_faqs(tenant_id, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer, embedding FROM faqs WHERE tenant_id=?", (tenant_id,))
    return cursor.fetchall()


# Retrieve tenant by API key
def get_tenant_by_api_key(api_key: str, conn: sqlite3.Connection = Depends(get_db)):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tenants WHERE api_key=?", (api_key,))
    tenant = cursor.fetchone()
    return tenant[0] if tenant else None
