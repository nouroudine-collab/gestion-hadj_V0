from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QInputDialog,
    QStyledItemDelegate,
    QTableView,
    QVBoxLayout,
    QWidget,
)
from datetime import datetime
def _fmt_date(value: str) -> str:
    if not value:
        return "-"
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y")
    except Exception:
        return str(value)


from services.pilgrim_service import del_pilgrim, fetch_pilgrims
from UIs.add_pilgrim import PilgrimForm


class PilgrimView(QWidget):
    def __init__(self):
        super().__init__()

        root: QVBoxLayout = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(20)
        self.setStyleSheet(open("assets/styles/view.qss").read())

        # ===== Top Bar =====
        top_bar: QHBoxLayout = QHBoxLayout()

        title: QLabel = QLabel("Pelerins")
        title.setObjectName("pageTitle")

        add_btn: QPushButton = QPushButton("+ Inscrire un pelerin")
        add_btn.clicked.connect(self.add_pilgrim)
        add_btn.setObjectName("primaryButton")

        del_btn: QPushButton = QPushButton("Supprimer pelerin")
        del_btn.clicked.connect(self.delete_selected_pilgrim)
        del_btn.setObjectName("primaryButton")

        top_bar.addWidget(title)
        top_bar.addStretch()
        top_bar.addWidget(del_btn)
        top_bar.addWidget(add_btn)

        # ===== CARD =====
        card: QFrame = QFrame()
        card.setObjectName("card")

        card_layout: QVBoxLayout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(15)

        # ===== SEARCH =====
        search: QLineEdit = QLineEdit()
        search.setPlaceholderText(
            "Rechercher un pelerin par nom, montant ou mode de paiement..."
        )
        search.setObjectName("searchInput")

        # ===== TABLE =====
        self.table: QTableView = QTableView()
        self.table.setItemDelegate(CustomTableViewDelegate(self))
        #table.doubleClicked.connect(self.open_menu)
        self.table.verticalHeader().setVisible(True)
        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.DoubleClicked)
        self.table.setAlternatingRowColors(True)
        self.table.setObjectName("table")
        self.model: QStandardItemModel = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(
            [
                "ID",
                "Nom",
                "Prénom",
                "Sexe",
                "Date naiss",
                "Lieu naiss",
                "Passport",
                "date deliv",
                "total versé",
                "nbre vrsmt",
                "reliquat",
                "Personne à prev",
                "numero 1",
                "numero 2",
            ]
        )
        header: QHeaderView = self.table.horizontalHeader()
        header.setObjectName("tableHeader")
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        # header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(9, QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(10, QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(11, QHeaderView.ResizeMode.Stretch)
        # header.setSectionResizeMode(12, QHeaderView.ResizeMode.ResizeToContents)
        # header.setSectionResizeMode(13, QHeaderView.ResizeMode.ResizeToContents)
        
        

        proxy: QSortFilterProxyModel = QSortFilterProxyModel()
        proxy.setSourceModel(self.model)
        proxy.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        proxy.setFilterKeyColumn(-1)

        self.proxy = proxy
        self.table.setModel(self.proxy)
        search.textChanged.connect(proxy.setFilterFixedString)
        self.load_pilgrims()

        # ===== ADD TO CARD =====
        card_layout.addWidget(search)
        card_layout.addWidget(self.table)

        # ===== ROOT =====
        root.addLayout(top_bar)
        root.addWidget(card)
    

    def load_pilgrims(self):
        pilgrims = fetch_pilgrims()
        self.model.removeRows(0, self.model.rowCount())
        for row, p in enumerate(pilgrims):
            self.model.setItem(row, 0, QStandardItem(str(p[0])))
            self.model.setItem(row, 1, QStandardItem(str(p[1])))
            self.model.setItem(row, 2, QStandardItem(str(p[2])))
            self.model.setItem(row, 3, QStandardItem(str(p[3])))
            self.model.setItem(row, 4, QStandardItem(_fmt_date(p[4])))
            self.model.setItem(row, 5, QStandardItem(str(p[5])))
            self.model.setItem(row, 6, QStandardItem(str(p[6])))
            self.model.setItem(row, 7, QStandardItem(_fmt_date(p[7])))
            self.model.setItem(row, 8, QStandardItem(str(p[9])))
            self.model.setItem(row, 9, QStandardItem(str(p[8])))
            self.model.setItem(row, 10, QStandardItem(str(p[10])))
            self.model.setItem(row, 11, QStandardItem(str(p[11])))
            self.model.setItem(row, 12, QStandardItem(str(p[12])))
            self.model.setItem(row, 13, QStandardItem(str(p[13])))

    def add_pilgrim(self):
        dialog = PilgrimForm(self)
        if dialog.exec():
            self.load_pilgrims()

    def delete_selected_pilgrim(self):
        selection = self.table.selectionModel()
        if not selection or not selection.hasSelection():
            QMessageBox.warning(self, "Selection requise", "Selectionnez un pelerin a supprimer.")
            return

        proxy_index = selection.selectedRows()[0]
        source_index = self.proxy.mapToSource(proxy_index)
        pilgrim_id_item = self.model.item(source_index.row(), 0)
        if pilgrim_id_item is None:
            QMessageBox.critical(self, "Erreur", "Impossible d'identifier le pelerin selectionne.")
            return

        pilgrim_id = int(pilgrim_id_item.text())
        password, ok = QInputDialog.getText(
            self,
            "Confirmation administrateur",
            "Saisissez le mot de passe admin:",
            QLineEdit.EchoMode.Password,
        )
        if not ok:
            return

        success, message = del_pilgrim(pilgrim_id, admin_password=password)
        if success:
            QMessageBox.information(self, "Succes", message)
            self.load_pilgrims()
        else:
            QMessageBox.warning(self, "Suppression refusee", message)
            
class CustomTableViewDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        
    def createEditor(self, parent, option, index):
        editor = QLineEdit(parent)
        # Get the cell's current text
        text = index.data(Qt.ItemDataRole.DisplayRole)
        if text:
            editor.setText(str(text))
        # Style the editor
        editor.setStyleSheet("""
        QLineEdit {
            border: 2px solid #3498db;
            border-radius: 2px;
            background: white;
            padding: 2px;
            margin: 0px;
        }
        """)
        # Calculate optimal width based on content
        font_metrics = editor.fontMetrics()
        text_width = font_metrics.horizontalAdvance(str(text))+10
        cell_width = option.rect.width()
        if text_width > cell_width:
            # Expand the editor if text is wider than cell
            editor.setMinimumWidth(text_width)
        else:
            editor.setMinimumWidth(cell_width)
        return editor
    def updateEditorGeometry(self, editor, option, index):
        # Let the editor use its size hint
        rect = option.rect
        size_hint = editor.sizeHint()

        if size_hint.width() > rect.width():
            rect.setWidth(size_hint.width())

        editor.setGeometry(rect)