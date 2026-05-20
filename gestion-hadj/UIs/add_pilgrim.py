
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QDateEdit, QFrame, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import QDate, QRegularExpression
from PySide6.QtGui import QIntValidator, QRegularExpressionValidator
from services.pilgrim_service import insert_pilgrim

class PilgrimForm(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        style_path = "assets/styles/pilgrim_form.qss"
        try:
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
            print("Stylesheet loaded successfully")
        except Exception as e:
            print(f"Error loading stylesheet: {e}")
            # Fallback: set basic background
            self.setStyleSheet("QDialog { background-color: #f5f7fa; }")
       
        self.setWindowTitle("Nouveau Dossier Pèlerin")
        self.setFixedWidth(850)
        self.setMinimumHeight(600)
        self.setObjectName("PilgrimDialog")
        

        # Layout Principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Header stylisé
        header_container = QWidget()
        header_container.setObjectName("headerContainer")
        header_layout = QVBoxLayout(header_container)
        
        header = QLabel("Fiche d'Inscription Pèlerin")
        header.setObjectName("headerLabel")
        header_layout.addWidget(header)
        
        subheader = QLabel("Remplissez les informations personnelles et les contacts d'urgence")
        subheader.setObjectName("subHeaderLabel")
        header_layout.addWidget(subheader)
        
        main_layout.addWidget(header_container)

        # 2. Zone de contenu avec ScrollArea (au cas où l'écran est petit)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        content_widget = QWidget()
        content_widget.setObjectName("contentWidget")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(25, 20, 25, 20)
        content_layout.setSpacing(20)

        # Grille du formulaire
        form_grid = QGridLayout()
        form_grid.setSpacing(15)
        form_grid.setHorizontalSpacing(30)

        # --- SECTION 1 : ÉTAT CIVIL (Colonne Gauche) ---
        section_id = QLabel("IDENTITÉ")
        section_id.setProperty("class", "sectionTitle")
        form_grid.addWidget(section_id, 0, 0, 1, 2)

        # Nom
        lbl_nom = QLabel("Nom :")
        lbl_nom.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_nom, 1, 0)
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("ex: TRAORE")
        form_grid.addWidget(self.nom_input, 1, 1)

        # Prénom
        lbl_prenom = QLabel("Prénom :")
        lbl_prenom.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_prenom, 2, 0)
        self.prenom_input = QLineEdit()
        self.prenom_input.setPlaceholderText("ex: Adam")
        form_grid.addWidget(self.prenom_input, 2, 1)

        # Sexe
        lbl_sexe = QLabel("Sexe :")
        lbl_sexe.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_sexe, 3, 0)
        self.sexe_combo = QComboBox()
        self.sexe_combo.addItems(["M", "F"])
        form_grid.addWidget(self.sexe_combo, 3, 1)

        # Birth Date
        lbl_birth = QLabel("Date de Naissance :")
        lbl_birth.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_birth, 4, 0)
        self.birth_date_edit = QDateEdit()
        self.birth_date_edit.setDate(QDate(1900, 1, 1))
        self.birth_date_edit.setDateRange(QDate(1950, 1, 1), QDate.currentDate())
        self.birth_date_edit.setDisplayFormat("dd/MM/yyyy")
        self.birth_date_edit.setCalendarPopup(True)
        form_grid.addWidget(self.birth_date_edit, 4, 1)
        
        # Birth Place
        lbl_birth_place = QLabel("Lieu de Naissance :")
        lbl_birth_place.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_birth_place, 5, 0)
        self.birth_place_input = QLineEdit()
        self.birth_place_input.setPlaceholderText("ex: Bobo Dioulasso")
        form_grid.addWidget(self.birth_place_input, 5, 1)

        # Passeport
        lbl_pass = QLabel("N° Passeport :")
        lbl_pass.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_pass, 6, 0)
        self.passport_input = QLineEdit()
        self.passport_input.setPlaceholderText("ex: A0123456")
        form_grid.addWidget(self.passport_input, 6, 1)

        # Date Délivrance
        lbl_deliv = QLabel("Délivré le :")
        lbl_deliv.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_deliv, 7, 0)
        self.date_deliv = QDateEdit()
        self.date_deliv.setDate(QDate(2000, 1, 1))
        self.date_deliv.setDateRange(QDate(2010, 1, 1), QDate.currentDate())
        self.date_deliv.setDisplayFormat("dd/MM/yyyy")
        self.date_deliv.setCalendarPopup(True)
        form_grid.addWidget(self.date_deliv, 7, 1)

        # --- SECTION 2 : FINANCES & URGENCE (Colonne Droite) ---
        section_fin = QLabel("FINANCE & URGENCE")
        section_fin.setProperty("class", "sectionTitle")
        form_grid.addWidget(section_fin, 0, 2, 1, 2)

        # Coût Total
        lbl_cost = QLabel("Cout total (FCFA):")
        lbl_cost.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_cost, 1, 2)
        self.total_cost = QLineEdit()
        self.total_cost.setText("3 280 000")
        self.total_cost.setReadOnly(True)
        self.total_cost.setPlaceholderText("3 280 000")
        form_grid.addWidget(self.total_cost, 1, 3)

        # Contact Urgence
        lbl_emergency = QLabel("Personne à prevenir :")
        lbl_emergency.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_emergency, 2, 2)
        self.emergency_name = QLineEdit()
        self.emergency_name.setPlaceholderText("Nom complet")
        form_grid.addWidget(self.emergency_name, 2, 3)

        # Téléphone 1
        lbl_tel1 = QLabel("Téléphone 1 :")
        lbl_tel1.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_tel1, 3, 2)
        self.num1 = QLineEdit()
        self.num1.setValidator(QRegularExpressionValidator(QRegularExpression(r"^(\+226)?\s?\d{8}$")))
        self.num1.setPlaceholderText("+226 ...")
        form_grid.addWidget(self.num1, 3, 3)

        # Téléphone 2
        lbl_tel2 = QLabel("Téléphone 2 :")
        lbl_tel2.setProperty("class", "formLabel")
        form_grid.addWidget(lbl_tel2, 4, 2)
        self.num2 = QLineEdit()
        self.num2.setValidator(QRegularExpressionValidator(QRegularExpression(r"^(\+226)?\s?\d{8}$")))
        form_grid.addWidget(self.num2, 4, 3)

        content_layout.addLayout(form_grid)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # 3. Pied de page avec boutons
        footer_line = QFrame()
        footer_line.setFrameShape(QFrame.Shape.HLine)
        footer_line.setObjectName("separator")
        main_layout.addWidget(footer_line)

        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(25, 15, 25, 25)
        buttons_layout.setSpacing(12)
        self.cancel_btn = QPushButton("Annuler")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.submit_btn = QPushButton("Enregistrer")
        self.submit_btn.setObjectName("submitBtn")
        self.submit_btn.clicked.connect(self.submit)
        self.submit_btn.setFixedHeight(45)

        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.submit_btn)
        main_layout.addLayout(buttons_layout)

    
    def submit(self):
        """Validation et fermeture."""
        self.nom_input.setStyleSheet("")
        self.prenom_input.setStyleSheet("")
        self.emergency_name.setStyleSheet("")
        self.passport_input.setStyleSheet("")

        valid = True
        if not self.nom_input.text():
            self.nom_input.setStyleSheet("border: 2px solid #C62828;")
            valid = False
        if not self.prenom_input.text():
            self.prenom_input.setStyleSheet("border: 2px solid #C62828;")
            valid = False
        if not self.emergency_name.text():
            self.emergency_name.setStyleSheet("border: 2px solid #C62828;")
            valid = False

        if valid:
            data = {
                "lname": self.nom_input.text().upper(),
                "fname": self.prenom_input.text().capitalize(),
                "sex": self.sexe_combo.currentText(),
                "birth_date": self.birth_date_edit.date().toString("yyyy-MM-dd"),
                "birth_place": self.birth_place_input.text(),
                "passport": self.passport_input.text(),
                "deliv_date": self.date_deliv.date().toString("yyyy-MM-dd"),
                "total_cost": int(self.total_cost.text().replace(" ", "")),
                "fullname": self.emergency_name.text(),
                "number1": self.num1.text(),
                "number2": self.num2.text()
            }
            try:
                success, message = insert_pilgrim(data)
                if success:
                    QMessageBox.information(self, "Succes", message)
                    self.accept()
                else:
                    QMessageBox.warning(self, "Attention", message)
            except Exception as exc:
                QMessageBox.critical(self, "Erreur", f"Enregistrement impossible:\n{exc}")