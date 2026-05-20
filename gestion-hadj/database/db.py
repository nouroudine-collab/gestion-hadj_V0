import sqlite3

def get_connection():
    return sqlite3.connect("data/app.db")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    try:
        _ = cursor.execute("""
            CREATE TABLE IF NOT EXISTS pilgrims(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lname TEXT NOT NULL,
                fname TEXT NOT NULL,
                sex TEXT CHECK (sex IN ('M', 'F')),
                birth_date TEXT,
                birth_place TEXT,
                passport TEXT,
                deliv_date TEXT,
                total_cost INTEGER,
                person_to_prevent_id INTEGER,
                created_at TEXT,
                modified_at TEXT,
                FOREIGN KEY (person_to_prevent_id) REFERENCES persons_to_prevent(id)
            )
        """)
        _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS persons_to_prevent (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fullname TEXT NOT NULL,
            pilgrim_id INTEGER,
            FOREIGN KEY(pilgrim_id) REFERENCES pilgrims(id)
        )
        """)
        _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS numbers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL,
            pilgrim_id INTEGER,
            FOREIGN KEY(pilgrim_id) REFERENCES pilgrims(id)
        )
        """)
        
        _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            number TEXT,
            balance INTEGER,
            bank TEXT,
            status TEXT
        )
        """)
        
        _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pilgrim_id INTEGER,
            amount INTEGER,
            type TEXT CHECK(type in ("cash", "mobile_money", "bank")),
            date TEXT,
            note TEXT,
            FOREIGN KEY(pilgrim_id) REFERENCES pilgrims(id)
        )
        """)
        _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount INTEGER,
            date TEXT,
            motif TEXT,
            source_account_id INTEGER,
            FOREIGN KEY (source_account_id) REFERENCES accounts(id)
        )
        """)
        
        _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payment_id INTEGER,
            pilgrim_id INTEGER,
            date TEXT,
            FOREIGN KEY(pilgrim_id) REFERENCES pilgrims(id),
            FOREIGN KEY(payment_id) REFERENCES payments(id)
        )
        """)
        _ = cursor.execute("""
        CREATE TABLE IF NOT EXISTS parametres (
            cle TEXT PRIMARY KEY,
            valeur TEXT
        )
        """)
        cursor.execute(
            "INSERT OR IGNORE INTO parametres(cle, valeur) VALUES ('admin_password', 'admin123')"
        )
        cursor.execute(
            "INSERT OR IGNORE INTO parametres(cle, valeur) VALUES ('agency_name', 'DAROU SALAM')"
        )
        cursor.execute(
            "INSERT OR IGNORE INTO parametres(cle, valeur) VALUES ('season', 'HADJ 2027')"
        )
        # Migration douce: colonnes de confirmation depart si absentes
        cursor.execute("PRAGMA table_info(pilgrims)")
        existing_cols = {row[1] for row in cursor.fetchall()}
        if "departure_confirmed" not in existing_cols:
            cursor.execute("ALTER TABLE pilgrims ADD COLUMN departure_confirmed INTEGER DEFAULT 0")
        if "departure_confirmed_date" not in existing_cols:
            cursor.execute("ALTER TABLE pilgrims ADD COLUMN departure_confirmed_date TEXT")

        print("Tables created successfully")
        conn.commit()
        
    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        raise e
    finally:
        conn.close()