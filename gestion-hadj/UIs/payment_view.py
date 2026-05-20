from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QTableView, QFrame, QHeaderView, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItemModel, QStandardItem

from services.payment_service import PaymentService
from .add_payment import PaymentForm
from .pilgrim_view import CustomTableViewDelegate

class PaymentView(QWidget):
    def __init__(self) ->None:
        super().__init__()

        self.main_layout: QVBoxLayout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(15)
        self.setStyleSheet(open(file="assets/styles/view.qss").read())
        # --- HEADER ---
        self.setup_header()
        
        # --- TABLE CARD ---
        self.card_frame: QFrame = QFrame()
        self.card_frame.setObjectName("card")
        self.card_layout: QVBoxLayout = QVBoxLayout(self.card_frame)

        self.search_input:QLineEdit = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Rechercher par nom, montant ou mode de paiement...")
        self.search_input.setFixedHeight(40)
        self.card_layout.addWidget(self.search_input)

        self.setup_table()
        
        self.main_layout.addWidget(self.top_bar_widget)
        self.main_layout.addWidget(self.card_frame)

        self.load_payments()

    def setup_header(self) -> None:
        self.top_bar_widget: QFrame = QFrame()
        self.top_bar_widget.setObjectName("topBarContainer")
        self.top_bar_layout: QHBoxLayout = QHBoxLayout(self.top_bar_widget)

        self.title: QLabel = QLabel("Historique des Versements")
        self.title.setObjectName("pageTitle")
        self.top_bar_layout.addWidget(self.title)

        self.top_bar_layout.addStretch()

        self.add_btn: QPushButton = QPushButton("+ Nouveau Versement")
        self.add_btn.setObjectName("primaryButton")
        self.add_btn.setMinimumWidth(180)
        _ = self.add_btn.clicked.connect(self.open_payment_form)
        self.delete_btn: QPushButton = QPushButton("Supprimer Versement")
        self.delete_btn.setObjectName("primaryButton")
        self.delete_btn.clicked.connect(self.delete_selected_payment)
        self.top_bar_layout.addWidget(self.delete_btn)
        self.top_bar_layout.addWidget(self.add_btn)

    def setup_table(self) -> None:
        self.table: QTableView = QTableView()
        delegate = CustomTableViewDelegate(self.table)
        self.table.setItemDelegate(delegate)        
        self.model: QStandardItemModel = QStandardItemModel()
        self.model.setHorizontalHeaderLabels([
            "ID Versement", "Date", "Id Pelerin", "Pelerin", "Montant", "Mode de Paiement", "Note"
        ])
        
        self.proxy_model: QSortFilterProxyModel = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setFilterKeyColumn(-1)

        self.table.setModel(self.proxy_model)
        _ = self.search_input.textChanged.connect(self.proxy_model.setFilterFixedString)

        # --- OPTIMISATION DES COLONNES ---
        header: QHeaderView = self.table.horizontalHeader()
        
        # On donne des comportements différents selon la donnée
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.table.setAlternatingRowColors(True)
        self.card_layout.addWidget(self.table)

    def load_payments(self) -> None:
        payments = PaymentService(db_path="data/app.db").get_all_payments()
        self.model.removeRows(0, self.model.rowCount())  # Clear existing data
        
        for payment in payments:
            row = self.model.rowCount()
            self.model.insertRow(row)
            self.model.setItem(row, 0, QStandardItem(str(payment[0])))   # payment id
            self.model.setItem(row, 1, QStandardItem(str(payment[1])))   # date
            self.model.setItem(row, 2, QStandardItem(str(payment[2])))   # pilgrim id
            self.model.setItem(row, 3, QStandardItem(str(payment[3])))   # pilgrim name
            self.model.setItem(row, 4, QStandardItem(str(payment[4])))   # amount
            self.model.setItem(row, 5, QStandardItem(str(payment[5])))   # type
            self.model.setItem(row, 6, QStandardItem(str(payment[6])))   # note
            
    def open_payment_form(self) -> None:
        dialog: PaymentForm = PaymentForm(parent=self)
        if dialog.exec(): # .exec() renvoie 1 (True) si accept() est appelé
            self.load_payments()

    def delete_selected_payment(self) -> None:
        selection = self.table.selectionModel()
        if not selection or not selection.hasSelection():
            QMessageBox.warning(self, "Selection requise", "Selectionnez un versement a supprimer.")
            return

        proxy_index = selection.selectedRows()[0]
        source_index = self.proxy_model.mapToSource(proxy_index)
        payment_id_item = self.model.item(source_index.row(), 0)
        if payment_id_item is None:
            QMessageBox.critical(self, "Erreur", "Impossible d'identifier le versement selectionne.")
            return

        payment_id = int(payment_id_item.text())
        password, ok = QInputDialog.getText(
            self,
            "Confirmation administrateur",
            "Saisissez le mot de passe admin:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return

        success, message = PaymentService("data/app.db").delete_payment_secure(payment_id, password)
        if success:
            QMessageBox.information(self, "Succes", message)
            self.load_payments()
        else:
            QMessageBox.warning(self, "Suppression refusee", message)