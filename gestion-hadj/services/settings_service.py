import sqlite3


class SettingsService:
    def __init__(self, db_path: str = "data/app.db"):
        self.db_path = db_path

    def get(self, key: str, default: str | None = None) -> str | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT valeur FROM parametres WHERE cle = ?", (key,))
            row = cursor.fetchone()
            if row:
                return row[0]
            return default

    def set(self, key: str, value: str) -> bool:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO parametres(cle, valeur) VALUES (?, ?)
                ON CONFLICT(cle) DO UPDATE SET valeur = excluded.valeur
                """,
                (key, value),
            )
            conn.commit()
        return True

    def check_admin_password(self, password: str) -> bool:
        saved = self.get("admin_password", "admin123")
        return password == saved
