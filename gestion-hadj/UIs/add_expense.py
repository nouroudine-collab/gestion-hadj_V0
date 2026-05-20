from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QDateEdit, QFrame, QMessageBox
)
from PySide6.QtCore import QRegularExpression, QDate
from PySide6.QtGui import QRegularExpressionValidator
from services.account_service import AccountService
from services.expense_service import ExpenseService
from database.models import Expense

class ExpenseForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Enregistrer une Dépense")
        self.setFixedWidth(500)
        self.setFixedHeight(500)
        self.setObjectName("ExpenseDialog")
        
        # Chargement du style (Réutilisation de ton fichier QSS)
        try:
            with open("assets/styles/expense_form.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            print("Note: expense_form.qss non trouve, style par defaut applique.")

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(25, 25, 25, 25)

        # 1. Header stylized
        header = QLabel("Détails de la Dépense")
        header.setObjectName("headerLabel")
        main_layout.addWidget(header)

        # 2. Form grid
        form_layout = QGridLayout()
        form_layout.setSpacing(15)
        form_layout.setVerticalSpacing(15)


        # --- Amount ---
        amount_label = QLabel("Montant :")
        amount_label.setProperty("class", "formLabel")
        form_layout.addWidget(amount_label, 1, 0)
        
        self.amount_input = MoneyInput()
        self.amount_input.setObjectName("amountInput")
        
        
        amount_container = QHBoxLayout()
        amount_container.addWidget(self.amount_input)
        currency_label = QLabel("FCFA")
        currency_label.setObjectName("currencyLabel")
        amount_container.addWidget(currency_label)
        form_layout.addLayout(amount_container, 1, 1)

        # --- Date ---
        date_label = QLabel("Date :")
        date_label.setProperty("class", "formLabel")
        form_layout.addWidget(date_label, 3, 0)
        
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setMaximumDate(QDate.currentDate())
        form_layout.addWidget(self.date_input, 3, 1)
        
        # --- Motif / Titre ---
        motif_label = QLabel("Motif:")
        motif_label.setProperty("class", "formLabel")
        form_layout.addWidget(motif_label, 0, 0)
        
        self.motif_input = QLineEdit()
        self.motif_input.setPlaceholderText("Ex: Location de bus, Vaccins...")
        form_layout.addWidget(self.motif_input, 0, 1)
        
        # --- Compte Source (Chargement dynamique) ---
        acc_label = QLabel("Compte Source :")
        acc_label.setProperty("class", "formLabel")
        form_layout.addWidget(acc_label, 2, 0)
        
        self.account_combo = QComboBox()
        self.load_accounts() # On remplit la liste
        form_layout.addWidget(self.account_combo, 2, 1)


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
        
        self.submit_btn = QPushButton("Enregistrer la dépense")
        self.submit_btn.setObjectName("submitBtn")
        self.submit_btn.clicked.connect(self.submit)
        self.submit_btn.setFixedHeight(40)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.submit_btn)
        main_layout.addLayout(buttons_layout)

    def load_accounts(self):
        """Récupération sécurisée des comptes."""
        try:
            service = AccountService("data/app.db")
            accounts = service.fetch_accounts()
            for acc in accounts:
                self.account_combo.addItem(f"{acc[1]} ({acc[2]})", acc[0])
        except Exception as e:
            print(f"Erreur DB : {e}")

    def submit(self):
        """Logique de validation rigoureuse."""
        # Reset style
        self.amount_input.setStyleSheet("")
        self.motif_input.setStyleSheet("")

        if not self.amount_input.text() or not self.motif_input.text():
            if not self.amount_input.text():
                self.amount_input.setStyleSheet("border: 2px solid #C62828;")
            if not self.motif_input.text():
                self.motif_input.setStyleSheet("border: 2px solid #C62828;")
            return
        
        try:
            amount = int(self.amount_input.text().replace(" ", ""))
            if amount <= 0:
                raise ValueError
            date = self.date_input.date().toString("yyyy-MM-dd")
            motif = self.motif_input.text()
            source_account_id = self.account_combo.currentData()
            expense = Expense(amount=amount, date=date, motif=motif, source_account_id=source_account_id)
            ExpenseService("data/app.db").add_expense(expense)
        except ValueError:
            self.amount_input.setStyleSheet("border: 2px solid #C62828;")
            return
        QMessageBox.information(self, "Succes", "Depense ajoutee avec succes.")
        self.accept()
class MoneyInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("amountInput")
        self.setPlaceholderText("Ex: 50 000")
        regex = QRegularExpression(r"^[0-9 ]*$")
        self.setValidator(QRegularExpressionValidator(regex, self))
        self.setEchoMode(QLineEdit.EchoMode.Normal)
        self.textChanged.connect(self._handle_format)
    def _handle_format(self, text):
        raw = text.replace(" ", "")
        if not raw:
            return

        try:
            formatted = "{:,}".format(int(raw)).replace(",", " ")
            
            # Block signals to prevent infinite recursion
            self.blockSignals(True)
            pos = self.cursorPosition()
            old_len = len(text)
            
            self.setText(formatted)
            
            # Adjust cursor position so it doesn't jump to the end
            new_len = len(formatted)
            self.setCursorPosition(pos + (new_len - old_len))
            
            self.blockSignals(False)
        except ValueError:
            pass

    def get_value(self):
        return int(self.text().replace(" ", "")) if self.text() else 0