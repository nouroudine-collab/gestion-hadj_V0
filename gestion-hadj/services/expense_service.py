import sqlite3
from database.models import Expense

class ExpenseService:
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_all_expenses(self):
        query = "SELECT e.date, e.amount, (a.name || ' ' || a.bank) AS compte, e.motif FROM expenses e JOIN accounts a ON e.source_account_id = a.id"
        return self._fetch_all(query)
    
    def _execute_query(self, query, params=()):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(query, params)
                conn.commit()
                
                return True
        except Exception as e:
            print(f"Database Error: {e}")
            return False
    def _fetch_one(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(query, params).fetchone()    
    def _fetch_all(self, query, params=()):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            return conn.execute(query, params).fetchall()
       
    def add_expense(self, expense: Expense):
        query = "INSERT INTO expenses (amount, date, motif, source_account_id) VALUES (?, ?, ?, ?)"
        return self._execute_query(query, (expense.amount, expense.date, expense.motif, expense.source_account_id))

    def get_expense_by_id(self, expense_id: int):
        query = "SELECT * FROM expenses WHERE id = ?"
        result = self._fetch_one(query, (expense_id,))
        return Expense(**dict(result)) if result else None

    def update_expense(self, expense: Expense):
        query = """
            UPDATE expenses 
            SET amount = ?, date = ?, motif = ?, source_account_id = ?
            WHERE id = ?
        """
        expense_id = getattr(expense, "id", None)
        if expense_id is None:
            return False
        return self._execute_query(query, (expense.amount, expense.date, expense.motif, expense.source_account_id, expense_id))

    def delete_expense(self, expense_id: int):
        query = "DELETE FROM expenses WHERE id = ?"
        return self._execute_query(query, (expense_id,))