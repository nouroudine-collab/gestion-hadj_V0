from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class PersonToPrevent:
    fullname: str

@dataclass
class Pilgrim:
    lname: str
    fname: str
    sex: str
    birth_date: str | None
    birth_place: str
    passport: str
    deliv_date: str
    total_cost: int

    @property
    def full_name(self) -> str:
        """Retourne le nom complet formaté"""
        return f"{self.lname.upper()} {self.fname.capitalize()}"

@dataclass
class Payment:
    pilgrim_id: int
    amount: int
    type: str  # cash, mobile_money, bank
    date: str
    note:str | None

    def format_amount(self) -> str:
        """Retourne le montant avec séparateur de milliers (ex: 3 000 000)"""
        return f"{self.amount}".replace(",", " ")

@dataclass
class Account:
    name: str
    balance: int
    number: int|None
    bank: str|None
    status: str = "active"

@dataclass
class Expense:
    amount: int
    date: str
    motif: str|None
    source_account_id: int

@dataclass
class Invoice:
    id: int | None
    payment_id: int
    pilgrim_id: int
    date: str