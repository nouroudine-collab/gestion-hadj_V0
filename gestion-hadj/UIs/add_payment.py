from PySide6.QtWidgets import (
    QCompleter, QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QDateEdit, QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, QDate
from datetime import datetime
from services.payment_service import PaymentService
from services.report_service import ReportService
from database.models import Payment
from UIs.add_expense import MoneyInput

class PaymentForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Nouveau Versement")
        self.setFixedWidth(500)
        self.setFixedHeight(500)
        self.setObjectName("PaymentDialog")
        
        
        self.setStyleSheet(open("assets/styles/payment_form.qss", "r").read())

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # 1. Header stylized
        header = QLabel("Détails de la Transaction")
        header.setObjectName("headerLabel")
        main_layout.addWidget(header)

        # 2. Form grid
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        form_layout.setVerticalSpacing(15)

        # --- Pilgrim (With search) ---
        pilgrim_label = QLabel("Pèlerin :")
        pilgrim_label.setProperty("class", "formLabel")
        form_layout.addWidget(pilgrim_label, 0, 0)
        
        pilgrims = PaymentService().fetch_pilgrims()
        
        self.pilgrim_input = QComboBox()
        for pilgrim in pilgrims:
            p_id, p_full_name, p_passport = pilgrim
            self.pilgrim_input.addItem(f"{p_id} | {p_full_name} ({p_passport})", p_id)
        self.pilgrim_input.setEditable(True)
        self.pilgrim_input.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = self.pilgrim_input.completer()
        if completer:
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.pilgrim_input.setPlaceholderText("Chercher par nom...")
        form_layout.addWidget(self.pilgrim_input, 0, 1)
        self.balance_label = QLabel("")
        self.balance_label.setStyleSheet("color:#1A4A8E; font-weight:600;")
        form_layout.addWidget(self.balance_label, 0, 2)
        self.pilgrim_input.currentIndexChanged.connect(self.update_balance_hint)

        # --- Amount ---
        amount_label = QLabel("Montant :")
        amount_label.setProperty("class", "formLabel")
        form_layout.addWidget(amount_label, 1, 0)
        
        self.amount_input = MoneyInput()
        self.amount_input.setObjectName("amountInput")
        self.amount_input.setPlaceholderText("Ex: 3 000 000")
        
        amount_container = QHBoxLayout()
        amount_container.addWidget(self.amount_input)
        currency_label = QLabel("FCFA")
        currency_label.setObjectName("currencyLabel")
        amount_container.addWidget(currency_label)
        form_layout.addLayout(amount_container, 1, 1)

        # --- Payment Method ---
        method_label = QLabel("Mode :")
        method_label.setProperty("class", "formLabel")
        form_layout.addWidget(method_label, 2, 0)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["cash", "bank", "mobile_money"])
        form_layout.addWidget(self.type_combo, 2, 1)

        # --- Date ---
        date_label = QLabel("Date :")
        date_label.setProperty("class", "formLabel")
        form_layout.addWidget(date_label, 3, 0)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addWidget(self.date_input, 3, 1)

        # --- Note ---
        note_label = QLabel("Note :")
        note_label.setProperty("class", "formLabel")
        form_layout.addWidget(note_label, 4, 0)
        
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Référence, N° de chèque...")
        form_layout.addWidget(self.note_input, 4, 1)

        main_layout.addLayout(form_layout)

        # 3. Separator line
        line = QFrame()
        line.setObjectName("separator")
        line.setFrameShape(QFrame.Shape.HLine)
        main_layout.addWidget(line)

        # 4. Action buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(10)
        
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.submit_btn = QPushButton("Enregistrer et imprimer")
        self.submit_btn.setObjectName("submitBtn")
        self.submit_btn.clicked.connect(self.submit)
        self.submit_btn.setFixedHeight(40)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.submit_btn)
        main_layout.addLayout(buttons_layout)
        self.update_balance_hint()

    def update_balance_hint(self):
        pilgrim_id = self.pilgrim_input.currentData()
        if not pilgrim_id:
            self.balance_label.setText("")
            return
        bal = PaymentService().get_pilgrim_balance(int(pilgrim_id))
        msg = (
            f"Verse: {bal['total_paid']:,} | Reste: {bal['remain']:,} | Tranches: {bal['tranche_count']}/5"
            .replace(",", " ")
        )
        self.balance_label.setText(msg)

    def submit(self):
        # Validation logic
        if not self.amount_input.text() or not self.pilgrim_input.currentText():
            self.amount_input.setStyleSheet("border: 2px solid #C62828;")
            return
        
        try:
            pilgrim_id = self.pilgrim_input.currentData()
            amount = int(self.amount_input.text().replace(" ", ""))
            if amount <= 0:
                raise ValueError
            type = self.type_combo.currentText()
            date = self.date_input.date()
            note = self.note_input.text()
            payment = Payment(pilgrim_id=pilgrim_id, amount=amount, type=type, date=date.toString("yyyy-MM-dd"), note=note)
            success, message = PaymentService().add_payment(payment)
            if not success:
                QMessageBox.warning(self, "Validation", message)
                return
            default_name = f"recu_{pilgrim_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            output_path, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer le recu PDF",
                default_name,
                "PDF Files (*.pdf)",
            )
            if output_path:
                ReportService().generate_a4_dual_receipt(pilgrim_id=pilgrim_id, output_path=output_path)
                QMessageBox.information(self, "Succes", f"{message}\nRecu genere:\n{output_path}")
            else:
                QMessageBox.information(self, "Succes", message)
        except ValueError:
            self.amount_input.setStyleSheet("border: 2px solid #C62828;")
            return
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Versement enregistre, mais impression impossible:\n{exc}")
            return

        self.accept()