import sqlite3
from database.models import Payment
from services.settings_service import SettingsService

class PaymentService:
    def __init__(self, db_path="data/app.db"):
        self.db_path = db_path

    # --- CREATE (Déjà fait, mais optimisé) ---
    def add_payment(self, payment: Payment):
        """Ajoute un versement avec controles metier.

        Regles:
        - maximum 5 tranches par pelerin
        - montant positif
        - pas de depassement du cout total du pelerin
        """
        if payment.amount <= 0:
            return False, "Le montant du versement doit etre superieur a 0."

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT total_cost FROM pilgrims WHERE id = ?", (payment.pilgrim_id,))
            row = cursor.fetchone()
            if not row:
                return False, "Pelerin introuvable."
            total_cost = int(row[0] or 0)

            cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM payments WHERE pilgrim_id = ?", (payment.pilgrim_id,))
            count_row = cursor.fetchone()
            tranches_count = int(count_row[0] or 0)
            already_paid = int(count_row[1] or 0)

            if tranches_count >= 5:
                return False, "Le nombre maximal de 5 tranches est atteint pour ce pelerin."

            if already_paid + payment.amount > total_cost:
                remain = max(total_cost - already_paid, 0)
                return False, f"Montant trop eleve. Reliquat disponible: {remain:,} FCFA.".replace(",", " ")

            cursor.execute(
                "INSERT INTO payments (pilgrim_id, amount, type, date, note) VALUES (?, ?, ?, ?, ?)",
                (payment.pilgrim_id, payment.amount, payment.type, payment.date, payment.note),
            )
            conn.commit()
        return True, "Versement enregistre avec succes."

    # --- READ (Single & All) ---
    def get_payment_by_id(self, payment_id: int):
        query = "SELECT * FROM payments WHERE id = ?"
        result = self._fetch_one(query, (payment_id,))
        return Payment(**dict(result)) if result else None

    def get_all_payments(self):
        query = """
        SELECT
            v.id,
            v.date,
            p.id,
            (p.lname || ' ' || p.fname) as pelerin,
            v.amount,
            v.type,
            v.note
        FROM payments v
        JOIN pilgrims p ON v.pilgrim_id = p.id
        ORDER BY v.date DESC, v.id DESC
        """
        results = self._fetch_all(query)
        return results

    # --- UPDATE ---
    def update_payment(self, payment_id: int, data_to_update: dict):
        """
        data_to_update: dict contenant uniquement les champs à modifier.
        Ex: {"lname": "TRAORE", "total_cost": 3500000}
        """
        if not data_to_update:
            return False

        # 1. On construit dynamiquement la partie "SET" de la requête
        # On crée une liste de "colonne = ?"
        fields = [f"{key} = ?" for key in data_to_update.keys()]
        query = f"UPDATE payments SET {', '.join(fields)} WHERE id = ?"
        
        # 2. On prépare les valeurs dans le même ordre
        values = list(data_to_update.values())
        values.append(payment_id) # On ajoute l'ID pour le WHERE
        
        # 3. Exécution
        return self._execute_query(query, tuple(values))

    # --- DELETE ---
    def delete_payment(self, payment_id: int):
        query = "DELETE FROM payments WHERE id = ?"
        return self._execute_query(query, (payment_id,))

    def delete_payment_secure(self, payment_id: int, admin_password: str) -> tuple[bool, str]:
        if not SettingsService(self.db_path).check_admin_password(admin_password):
            return False, "Mot de passe administrateur incorrect."
        if not payment_id:
            return False, "Versement invalide."
        ok = self.delete_payment(payment_id)
        if ok:
            return True, "Versement supprime avec succes."
        return False, "Suppression du versement impossible."

    # --- HELPERS (Pour éviter de répéter le code SQLite)
    def _execute_query(self, query, params=()):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.cursor().execute(query, params)
            conn.commit()
            return True
        except Exception as e:
            print(f"Database Error: {e}")
            return False

    def _fetch_all(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(query, params).fetchall()

    def _fetch_one(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(query, params).fetchone()

    def fetch_pilgrims(self):
        try:
            query = "SELECT id, (lname || ' ' || fname) AS full_name, passport FROM pilgrims"
            return self._fetch_all(query)
        except Exception as e:
            print(f"Database Error: {e}")
            return []

    def get_pilgrim_balance(self, pilgrim_id: int) -> dict:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(total_cost, 0) FROM pilgrims WHERE id = ?", (pilgrim_id,))
            row = cursor.fetchone()
            total_cost = int(row[0] or 0) if row else 0
            cursor.execute("SELECT COALESCE(SUM(amount), 0), COUNT(*) FROM payments WHERE pilgrim_id = ?", (pilgrim_id,))
            pay_row = cursor.fetchone()
            total_paid = int(pay_row[0] or 0)
            tranche_count = int(pay_row[1] or 0)
            remain = max(total_cost - total_paid, 0)
            return {
                "total_cost": total_cost,
                "total_paid": total_paid,
                "remain": remain,
                "tranche_count": tranche_count,
            }