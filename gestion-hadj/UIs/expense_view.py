from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QTableView, QFrame, QHeaderView
)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItem, QStandardItemModel
from services.expense_service import ExpenseService
from UIs.add_expense import ExpenseForm
from UIs.pilgrim_view import CustomTableViewDelegate

from datetime import datetime

class ExpenseView(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        self.setStyleSheet(open("assets/styles/view.qss").read())

        top_bar = QHBoxLayout()
        self.load_btn = QPushButton("Actualiser")
        self.load_btn.setObjectName("primaryButton")
        self.load_btn.clicked.connect(self.load_expenses)
        top_bar.addWidget(self.load_btn)
        
        title = QLabel("Depenses")
        title.setObjectName("pageTitle")

        self.add_btn = QPushButton("+ Nouvelle depense")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.clicked.connect(self.add_expense)

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(self.add_btn)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Rechercher une depense...")

        self.table = QTableView()
        delegate = CustomTableViewDelegate(self.table)
        self.table.setItemDelegate(delegate)        
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "Date", "Montant", "Nom compte", "Motif" 
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        self.table.setModel(self.proxy)

        self.search.textChanged.connect(self.proxy.setFilterFixedString)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.addWidget(self.search)
        card_layout.addWidget(self.table)

        layout.addLayout(top_bar)
        layout.addWidget(card)
        self.load_expenses()

    def load_expenses(self):
        expenses = ExpenseService("data/app.db").get_all_expenses()
        self.model.removeRows(0, self.model.rowCount())
        for row, expense in enumerate(expenses):
            self.model.setItem(row, 0, QStandardItem(datetime.strptime(expense[0], "%Y-%m-%d").strftime("%d/%m/%Y")))
            self.model.setItem(row, 1, QStandardItem(str(expense[1])))
            self.model.setItem(row, 2, QStandardItem(str(expense[2])))
            self.model.setItem(row, 3, QStandardItem(expense[3]))
    def add_expense(self):
        dialog = ExpenseForm(self)
        if dialog.exec():
           self.load_expenses()