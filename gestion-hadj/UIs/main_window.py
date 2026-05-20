from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget
)
from PySide6.QtCore import Qt
from UIs.pilgrim_view import PilgrimView
from UIs.expense_view import ExpenseView
from UIs.payment_view import PaymentView
from UIs.dashboard import DashboardView
from UIs.settings_view import SettingsView
from UIs.confirmed_departure_view import ConfirmedDepartureView
from UIs.sidebar import SideBar

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Darou Salam")
        self.resize(1000, 600)

        # Main container
        container = QWidget()
        self.setCentralWidget(container)

        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        self.sidebar = SideBar(self)

        # Content area
        self.stack = QStackedWidget()
        self.stack.setObjectName("contentArea")
        # pages
        self.dashboard_page = DashboardView()
        self.pilgrim_page = PilgrimView()
        self.payment_page = PaymentView()
        self.expense_page = ExpenseView()
        self.settings_page = SettingsView()
        self.confirmed_page = ConfirmedDepartureView()
        # Add pages to stack
        self.stack.addWidget(self.dashboard_page)
        self.stack.addWidget(self.pilgrim_page)
        self.stack.addWidget(self.payment_page)
        self.stack.addWidget(self.expense_page)
        self.stack.addWidget(self.settings_page)
        self.stack.addWidget(self.confirmed_page)
        
        # Layout
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.stack)
        self.sidebar.page_changed.connect(self.stack.setCurrentIndex)
        
        

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(200)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(15, 20, 15, 20)
        layout.setSpacing(15)

        title = QLabel("Darou Salam")
        title.setObjectName("appTitle")

        btn_pilgrims = QPushButton("Pilgrims")
        btn_versements = QPushButton("versements")
        btn_depenses = QPushButton("depenses")
        btn_factures = QPushButton("factures")
        btn_badges = QPushButton("badges")
        btn_parametres = QPushButton("parametres")

        btn_pilgrims.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_versements.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_depenses.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        btn_parametres.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        btn_factures.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        btn_badges.clicked.connect(lambda: self.stack.setCurrentIndex(5))

        layout.addWidget(title)
        layout.addSpacing(5)
        layout.addWidget(btn_pilgrims)
        layout.addWidget(btn_versements)
        layout.addWidget(btn_depenses)
        layout.addWidget(btn_parametres)
        layout.addWidget(btn_factures)
        layout.addWidget(btn_badges)
        layout.addStretch()

        return sidebar