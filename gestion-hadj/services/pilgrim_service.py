import sqlite3
from sqlite3 import Connection, Cursor
from database.models import Pilgrim, PersonToPrevent
from services.settings_service import SettingsService
db_path = "data/app.db"
def get_connection() -> Connection:
    return sqlite3.connect(db_path)
def insert_pilgrim(data):
    
    connection: Connection = get_connection()
    cursor: Cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT id
            FROM pilgrims
            WHERE UPPER(lname) = UPPER(?) AND UPPER(fname) = UPPER(?) AND birth_date = ?
            """,
            (data["lname"], data["fname"], data["birth_date"]),
        )
        duplicate = cursor.fetchone()
        if duplicate:
            return False, "Doublon detecte: ce pelerin existe deja (nom, prenom, date de naissance)."

        person_to_prevent = PersonToPrevent(
            fullname = data["fullname"]
        )
        cursor.execute("""
            INSERT INTO persons_to_prevent(fullname) VALUES (?) ;
            """, (person_to_prevent.fullname,)
        )
        pilgrim = Pilgrim(
            lname=data["lname"],
            fname=data["fname"],
            sex=data["sex"],
            birth_date=data["birth_date"],
            birth_place=data["birth_place"],
            passport=data["passport"],
            deliv_date=data["deliv_date"],
            total_cost=data["total_cost"]
        )
        person_to_prevent_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO pilgrims(lname, fname, sex, birth_date, birth_place, passport, deliv_date, total_cost, person_to_prevent_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (pilgrim.lname, pilgrim.fname, pilgrim.sex, pilgrim.birth_date, pilgrim.birth_place, pilgrim.passport, pilgrim.deliv_date, pilgrim.total_cost, person_to_prevent_id)
        )
        pilgrim_id = cursor.lastrowid
        cursor.execute("""
            INSERT INTO numbers(pilgrim_id, number) VALUES (?, ?)
        """, (pilgrim_id, data["number1"])
        )
        if data["number2"]:
            cursor.execute("""
                INSERT INTO numbers(pilgrim_id, number) VALUES (?, ?)
            """, (pilgrim_id, data["number2"])
            )
        connection.commit()
        print(f"Pelerin {pilgrim_id} insere avec succes")
        return True, "Pelerin enregistre avec succes."
    except sqlite3.Error as e:
        print(f"Erreur lors de l'insertion du pelerin: {e}")
        print("annulation totale de la transaction")
        if connection:
            connection.rollback()
        raise e
    finally:
        if connection:
            connection.close()
    
def update_pilgrim(update)->None:
    pass

def del_pilgrim(pilgrim_id:int, admin_password: str | None = None)-> tuple[bool, str]:
    connection: Connection = get_connection()
    cursor: Cursor = connection.cursor()
    if not pilgrim_id:
        return False, "Pelerin invalide."
    try:
        if admin_password is None or not SettingsService(db_path).check_admin_password(admin_password):
            return False, "Mot de passe administrateur incorrect."
        cursor.execute("SELECT person_to_prevent_id FROM pilgrims WHERE id = ?", (pilgrim_id,))
        row = cursor.fetchone()
        person_to_prevent_id = row[0] if row else None
        cursor.execute("DELETE FROM payments WHERE pilgrim_id = ?", (pilgrim_id,))
        cursor.execute("DELETE FROM numbers WHERE pilgrim_id = ?", (pilgrim_id,))
        cursor.execute("DELETE FROM pilgrims WHERE id = ?", (pilgrim_id,))
        if person_to_prevent_id:
            cursor.execute("DELETE FROM persons_to_prevent WHERE id = ?", (person_to_prevent_id,))
        connection.commit()
        print(f"Pelerin {pilgrim_id} supprimé avec succès")
        return True, "Pelerin supprime avec succes."
    except sqlite3.Error as e:
        print(f"Erreur lors de la suppression du pèlerin: {e}")
        connection.rollback()
        raise e
    finally:
        connection.close()

def fetch_pilgrims():
    connection: Connection = get_connection()
    cursor: Cursor = connection.cursor()
    try:
        cursor.execute("""
            SELECT 
                p.id, p.lname, p.fname, p.sex, p.birth_date, p.birth_place, p.passport, p.deliv_date,
                COALESCE(v_stats.nbre_vrsmt, 0),
                COALESCE(v_stats.total_versé, 0),
                p.total_cost - COALESCE(v_stats.total_versé, 0),
                q.fullname,
                (SELECT number FROM numbers WHERE pilgrim_id = p.id LIMIT 1) as tel1,
                (SELECT number FROM numbers WHERE pilgrim_id = p.id LIMIT 1 OFFSET 1) as tel2
            FROM pilgrims p
            LEFT JOIN persons_to_prevent q ON p.person_to_prevent_id = q.id
            LEFT JOIN (
                SELECT pilgrim_id, COUNT(id) AS nbre_vrsmt, SUM(amount) AS total_versé
                FROM payments GROUP BY pilgrim_id
            ) v_stats ON p.id = v_stats.pilgrim_id
        """)
        data = cursor.fetchall()
        connection.commit()
        return data
    except sqlite3.Error as e:
        print(f"Erreur lors de la récupération des pèlerins: {e}")
        raise e
    finally:
        connection.close()


def fetch_confirmed_departures():
    connection: Connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor: Cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT
                p.id,
                p.lname,
                p.fname,
                p.birth_date,
                p.passport,
                COALESCE((SELECT number FROM numbers WHERE pilgrim_id = p.id LIMIT 1), '-') AS tel1,
                p.departure_confirmed_date
            FROM pilgrims p
            WHERE COALESCE(p.departure_confirmed, 0) = 1
            ORDER BY p.departure_confirmed_date DESC, p.id DESC
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        connection.close()


def set_departure_confirmed(pilgrim_id: int, confirmed: bool, date_value: str | None = None) -> tuple[bool, str]:
    connection: Connection = get_connection()
    cursor: Cursor = connection.cursor()
    try:
        cursor.execute(
            """
            UPDATE pilgrims
            SET departure_confirmed = ?, departure_confirmed_date = ?
            WHERE id = ?
            """,
            (1 if confirmed else 0, date_value if confirmed else None, pilgrim_id),
        )
        connection.commit()
        if cursor.rowcount == 0:
            return False, "Pelerin introuvable."
        return True, "Depart confirme." if confirmed else "Confirmation retiree."
    except sqlite3.Error as e:
        connection.rollback()
        return False, f"Erreur SQL: {e}"
    finally:
        connection.close()


def fetch_pilgrim_details(pilgrim_id: int):
    """Retourne les informations complètes d'un pèlerin pour les documents (reçu/badge)."""
    connection: Connection = get_connection()
    connection.row_factory = sqlite3.Row
    cursor: Cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT
                p.id,
                p.lname,
                p.fname,
                p.sex,
                p.birth_date,
                p.birth_place,
                p.passport,
                p.deliv_date,
                p.total_cost,
                q.fullname as contact_urgence,
                COALESCE((SELECT number FROM numbers WHERE pilgrim_id = p.id LIMIT 1), '-') as tel1,
                COALESCE(v_stats.total_verse, 0) as total_verse
            FROM pilgrims p
            LEFT JOIN persons_to_prevent q ON p.person_to_prevent_id = q.id
            LEFT JOIN (
                SELECT pilgrim_id, SUM(amount) AS total_verse
                FROM payments
                GROUP BY pilgrim_id
            ) v_stats ON p.id = v_stats.pilgrim_id
            WHERE p.id = ?
            """,
            (pilgrim_id,),
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        connection.close()