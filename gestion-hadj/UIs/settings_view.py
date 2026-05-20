from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFrame,
    QLabel,
    QFormLayout,
    QLineEdit,
    QPushButton,
    QMessageBox,
    QFileDialog,
)

from services.database_service import DatabaseService
from services.settings_service import SettingsService


class SettingsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(open("assets/styles/view.qss", encoding="utf-8").read())
        self.service = SettingsService()
        self.db_service = DatabaseService()

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(16)

        title = QLabel("Parametres")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)

        form = QFormLayout()
        self.agency_input = QLineEdit()
        self.season_input = QLineEdit()
        self.admin_password_input = QLineEdit()
        self.admin_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        form.addRow("Nom agence", self.agency_input)
        form.addRow("Saison active", self.season_input)
        form.addRow("Mot de passe admin", self.admin_password_input)
        card_layout.addLayout(form)

        save_btn = QPushButton("Enregistrer les parametres")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.save_settings)
        card_layout.addWidget(save_btn)

        root.addWidget(card)

        backup_card = QFrame()
        backup_card.setObjectName("card")
        backup_layout = QVBoxLayout(backup_card)

        backup_title = QLabel("Sauvegarde de la base de donnees")
        backup_title.setObjectName("cardTitle")
        backup_layout.addWidget(backup_title)

        backup_hint = QLabel(
            "Exportez regulierement votre base pour ne pas perdre vos donnees. "
            "L'import remplace la base actuelle (une copie de securite est creee automatiquement)."
        )
        backup_hint.setWordWrap(True)
        backup_hint.setStyleSheet("color: #5f6b7a; font-size: 12px;")
        backup_layout.addWidget(backup_hint)

        export_btn = QPushButton("Exporter la base de donnees")
        export_btn.setObjectName("primaryButton")
        export_btn.clicked.connect(self.export_database)
        backup_layout.addWidget(export_btn)

        import_btn = QPushButton("Importer une sauvegarde")
        import_btn.setObjectName("primaryButton")
        import_btn.clicked.connect(self.import_database)
        backup_layout.addWidget(import_btn)

        root.addWidget(backup_card)
        root.addStretch()
        self.load_settings()

    def load_settings(self):
        self.agency_input.setText(self.service.get("agency_name", "DAROU SALAM") or "DAROU SALAM")
        self.season_input.setText(self.service.get("season", "HADJ 2027") or "HADJ 2027")
        self.admin_password_input.setText(self.service.get("admin_password", "admin123") or "admin123")

    def save_settings(self):
        agency_name = self.agency_input.text().strip()
        season = self.season_input.text().strip()
        admin_password = self.admin_password_input.text().strip()

        if not agency_name or not season or not admin_password:
            QMessageBox.warning(self, "Validation", "Tous les champs sont obligatoires.")
            return

        self.service.set("agency_name", agency_name)
        self.service.set("season", season)
        self.service.set("admin_password", admin_password)
        QMessageBox.information(self, "Succes", "Parametres enregistres.")

    def export_database(self):
        default_name = f"sauvegarde_hadj_{self.season_input.text().strip() or 'base'}.db"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Exporter la base de donnees",
            default_name,
            "Base SQLite (*.db);;Tous les fichiers (*.*)",
        )
        if not file_path:
            return
        try:
            saved = self.db_service.export_database(file_path)
            QMessageBox.information(self, "Succes", f"Base exportee avec succes:\n{saved}")
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Export impossible:\n{exc}")

    def import_database(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Importer une sauvegarde",
            "",
            "Base SQLite (*.db);;Tous les fichiers (*.*)",
        )
        if not file_path:
            return

        confirm = QMessageBox.warning(
            self,
            "Confirmation",
            "Cette operation remplacera toutes les donnees actuelles par la sauvegarde selectionnee.\n"
            "Une copie de securite de la base actuelle sera creee automatiquement.\n\n"
            "Continuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db_service.import_database(file_path)
            QMessageBox.information(
                self,
                "Succes",
                "Base restauree avec succes.\n"
                "Cliquez sur « Actualiser » sur le tableau de bord ou redemarrez l'application.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Erreur", f"Import impossible:\n{exc}")
