from datetime import datetime

from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from services.pilgrim_service import fetch_pilgrims, fetch_confirmed_departures, set_departure_confirmed
from services.report_service import ReportService


class ConfirmedDepartureView(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(open("assets/styles/view.qss", encoding="utf-8").read())

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(14)

        top = QHBoxLayout()
        title = QLabel("Departs confirmes")
        title.setObjectName("pageTitle")
        top.addWidget(title)
        top.addStretch()
        self.confirm_btn = QPushButton("Confirmer le depart")
        self.confirm_btn.setObjectName("primaryButton")
        self.confirm_btn.clicked.connect(self.confirm_selected)
        self.unconfirm_btn = QPushButton("Retirer confirmation")
        self.unconfirm_btn.setObjectName("primaryButton")
        self.unconfirm_btn.clicked.connect(self.unconfirm_selected)
        self.export_btn = QPushButton("Exporter liste confirmee")
        self.export_btn.setObjectName("primaryButton")
        self.export_btn.clicked.connect(self.export_confirmed_list)
        top.addWidget(self.confirm_btn)
        top.addWidget(self.unconfirm_btn)
        top.addWidget(self.export_btn)
        root.addLayout(top)

        # All pilgrims table
        all_card = QFrame()
        all_card.setObjectName("card")
        all_layout = QVBoxLayout(all_card)
        all_layout.addWidget(QLabel("Tous les pelerins"))
        self.search_all = QLineEdit()
        self.search_all.setPlaceholderText("Rechercher...")
        all_layout.addWidget(self.search_all)
        self.all_model = QStandardItemModel()
        self.all_model.setHorizontalHeaderLabels(["ID", "Nom", "Prenom", "CNIB/Passeport", "Date naissance"])
        self.all_proxy = QSortFilterProxyModel()
        self.all_proxy.setSourceModel(self.all_model)
        self.all_proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.all_proxy.setFilterKeyColumn(-1)
        self.search_all.textChanged.connect(self.all_proxy.setFilterFixedString)
        self.all_table = QTableView()
        self.all_table.setModel(self.all_proxy)
        self.all_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        all_layout.addWidget(self.all_table)
        root.addWidget(all_card)

        # Confirmed table
        conf_card = QFrame()
        conf_card.setObjectName("card")
        conf_layout = QVBoxLayout(conf_card)
        conf_layout.addWidget(QLabel("Pelerins avec depart confirme"))
        self.conf_model = QStandardItemModel()
        self.conf_model.setHorizontalHeaderLabels(
            ["ID", "Nom", "Prenom", "Date naissance", "CNIB/Passeport", "Telephone", "Date confirmation"]
        )
        self.conf_table = QTableView()
        self.conf_table.setModel(self.conf_model)
        self.conf_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        conf_layout.addWidget(self.conf_table)
        root.addWidget(conf_card)

        self.load_all_pilgrims()
        self.load_confirmed()

    def load_all_pilgrims(self):
        self.all_model.removeRows(0, self.all_model.rowCount())
        for row_idx, p in enumerate(fetch_pilgrims()):
            self.all_model.setItem(row_idx, 0, QStandardItem(str(p[0])))
            self.all_model.setItem(row_idx, 1, QStandardItem(str(p[1] or "-")))
            self.all_model.setItem(row_idx, 2, QStandardItem(str(p[2] or "-")))
            self.all_model.setItem(row_idx, 3, QStandardItem(str(p[6] or "-")))
            self.all_model.setItem(row_idx, 4, QStandardItem(str(p[4] or "-")))

    def load_confirmed(self):
        self.conf_model.removeRows(0, self.conf_model.rowCount())
        for row_idx, p in enumerate(fetch_confirmed_departures()):
            self.conf_model.setItem(row_idx, 0, QStandardItem(str(p.get("id", "-"))))
            self.conf_model.setItem(row_idx, 1, QStandardItem(str(p.get("lname", "-"))))
            self.conf_model.setItem(row_idx, 2, QStandardItem(str(p.get("fname", "-"))))
            self.conf_model.setItem(row_idx, 3, QStandardItem(str(p.get("birth_date", "-"))))
            self.conf_model.setItem(row_idx, 4, QStandardItem(str(p.get("passport", "-"))))
            self.conf_model.setItem(row_idx, 5, QStandardItem(str(p.get("tel1", "-"))))
            self.conf_model.setItem(row_idx, 6, QStandardItem(str(p.get("departure_confirmed_date", "-"))))

    def _selected_all_pilgrim_id(self):
        sel = self.all_table.selectionModel()
        if not sel or not sel.hasSelection():
            return None
        proxy_idx = sel.selectedRows()[0]
        source_idx = self.all_proxy.mapToSource(proxy_idx)
        return int(self.all_model.item(source_idx.row(), 0).text())

    def confirm_selected(self):
        pilgrim_id = self._selected_all_pilgrim_id()
        if not pilgrim_id:
            QMessageBox.warning(self, "Selection requise", "Selectionnez un pelerin dans la liste du haut.")
            return
        date_txt, ok = QInputDialog.getText(
            self,
            "Date de confirmation",
            "Date (AAAA-MM-JJ):",
            text=datetime.now().strftime("%Y-%m-%d"),
        )
        if not ok:
            return
        success, message = set_departure_confirmed(pilgrim_id, True, date_txt.strip() or datetime.now().strftime("%Y-%m-%d"))
        if success:
            self.load_confirmed()
            QMessageBox.information(self, "Succes", message)
        else:
            QMessageBox.warning(self, "Erreur", message)

    def unconfirm_selected(self):
        sel = self.conf_table.selectionModel()
        if not sel or not sel.hasSelection():
            QMessageBox.warning(self, "Selection requise", "Selectionnez un pelerin confirme.")
            return
        pilgrim_id = int(self.conf_model.item(sel.selectedRows()[0].row(), 0).text())
        success, message = set_departure_confirmed(pilgrim_id, False)
        if success:
            self.load_confirmed()
            QMessageBox.information(self, "Succes", message)
        else:
            QMessageBox.warning(self, "Erreur", message)

    def export_confirmed_list(self):
        output_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter la liste des departs confirmes", "departs_confirmes.xlsx", "Excel Files (*.xlsx)"
        )
        if not output_path:
            return
        ReportService().export_confirmed_departures_excel(output_path)
        QMessageBox.information(self, "Succes", f"Liste exportee:\n{output_path}")
