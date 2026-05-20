import sqlite3
from database.models import Account
class AccountService:
    def __init__(self, db_path):
        self.db_path = db_path
    def fetch_accounts(self):
        with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row # Accès par nom de colonne
                cursor = conn.cursor()
                cursor.execute("SELECT id, name, bank FROM accounts")
                rows = cursor.fetchall()
                print(f"Fetched {len(rows)} accounts")
                return rows