import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/app.db")


class DatabaseService:
    """Sauvegarde et restauration de la base SQLite."""

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)

    def export_database(self, dest_path: str) -> str:
        if not self.db_path.exists():
            raise FileNotFoundError("Aucune base de donnees trouvee.")
        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(self.db_path, dest)
        return str(dest)

    def import_database(self, source_path: str) -> str:
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError("Fichier de sauvegarde introuvable.")

        conn = sqlite3.connect(source)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='parametres'"
            )
            if cursor.fetchone() is None:
                raise ValueError("Le fichier selectionne n'est pas une base valide.")
        finally:
            conn.close()

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if self.db_path.exists():
            backup_name = f"app.db.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.db_path, self.db_path.parent / backup_name)

        shutil.copy2(source, self.db_path)
        return str(self.db_path)
