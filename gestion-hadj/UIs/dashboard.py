import os
import sqlite3

from PySide6.QtWidgets import (
    QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QPushButton, QListWidget, QListWidgetItem, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPixmap
from UIs.add_pilgrim import PilgrimForm
from UIs.add_payment import PaymentForm
from UIs.add_expense import ExpenseForm
from services.settings_service import SettingsService

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("dashboardView")
        self.setStyleSheet(open("assets/styles/dashboard.qss").read())
        
        # Layout Principal
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(25)

        # --- 1. HEADER (logo + entreprise) ---
        self.settings = SettingsService()
        header_row = QHBoxLayout()

        brand_box = QHBoxLayout()
        brand_box.setSpacing(14)
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(72, 72)
        self.logo_label.setScaledContents(True)
        self._load_company_logo()

        brand_text = QVBoxLayout()
        brand_text.setSpacing(2)
        self.company_label = QLabel()
        self.company_label.setStyleSheet(
            "font-size: 22px; font-weight: bold; color: #1B5E20;"
        )
        self.season_label = QLabel()
        self.season_label.setStyleSheet("font-size: 13px; color: #5f6b7a;")
        brand_text.addWidget(self.company_label)
        brand_text.addWidget(self.season_label)
        self._refresh_brand_labels()

        brand_box.addWidget(self.logo_label)
        brand_box.addLayout(brand_text)

        self.header_label = QLabel("Tableau de Bord")
        self.header_label.setObjectName("dashboardTitle")
        self.refresh_btn = QPushButton("Actualiser")
        self.refresh_btn.setObjectName("primaryButton")
        self.refresh_btn.setFixedHeight(36)
        self.refresh_btn.setStyleSheet(
            "QPushButton {background-color:#1A4A8E; color:white; border-radius:8px; padding:8px 14px; font-weight:600;}"
            "QPushButton:hover {background-color:#2563b8;}"
        )
        self.refresh_btn.clicked.connect(self.refresh_dashboard)
        header_row.addLayout(brand_box)
        header_row.addStretch()
        header_row.addWidget(self.header_label)
        header_row.addStretch()
        header_row.addWidget(self.refresh_btn)
        self.main_layout.addLayout(header_row)

        # --- 2. STATS CARDS (GRID) ---
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(20)
        
        self.card_pilgrims = self.create_stat_card("Pèlerins Inscrits", "0", "#3498db")
        self.card_payments = self.create_stat_card("Total Encaissé", "0 FCFA", "#2ecc71")
        self.card_expenses = self.create_stat_card("Total Reliquat", "0 FCFA", "#e67e22")
        self.recette_card = self.create_stat_card("Dépenses", "0 FCFA", "#e74c3c")
        self.card_vols = self.create_stat_card("Taux de Recouvrement", "0%", "#9b59b6")
        

        self.stats_grid.addWidget(self.card_pilgrims, 0, 0)
        self.stats_grid.addWidget(self.card_payments, 0, 1)
        self.stats_grid.addWidget(self.card_expenses, 0, 2)
        self.stats_grid.addWidget(self.recette_card, 0, 3)
        self.stats_grid.addWidget(self.card_vols, 0, 4)
        self.main_layout.addLayout(self.stats_grid)

        # --- 3. SECTION BASSE (ACTIONS & TRANSACTIONS) ---
        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(20)

        # --- Quick Actions ---
        self.actions_box = QFrame()
        self.actions_box.setObjectName("contentCard")
        self.actions_box.setFixedWidth(280)
        self.actions_layout = QVBoxLayout(self.actions_box)
        
        self.act_title = QLabel("Actions Rapides")
        self.act_title.setObjectName("cardTitle")
        self.actions_layout.addWidget(self.act_title)

        self.btn_add_p = self.create_action_btn("Nouveau Pèlerin")
        self.btn_add_v = self.create_action_btn("Encaisser Versement")
        self.btn_add_d = self.create_action_btn("Sortie de Caisse")

        self.btn_add_d.clicked.connect(self.showExpenseDialog)
        self.btn_add_p.clicked.connect(self.showPilgrimDialog)
        self.btn_add_v.clicked.connect(self.showPaymentDialog)

        for btn in [self.btn_add_p, self.btn_add_v, self.btn_add_d]:
            self.actions_layout.addWidget(btn)
        self.actions_layout.addStretch()

        # --- Recent Transactions (FIXED) ---
        self.trans_box = QFrame()
        self.trans_box.setObjectName("contentCard")
        self.trans_layout = QVBoxLayout(self.trans_box)

        self.trans_title = QLabel("Dernières Opérations")
        self.trans_title.setObjectName("cardTitle")
        self.trans_layout.addWidget(self.trans_title)

        self.trans_list = QListWidget()
        self.trans_list.setSpacing(8)  # Increased spacing
        self.trans_list.setObjectName("recentList")
        
        # Fix 1: Set uniform item sizes
        self.trans_list.setUniformItemSizes(False)  # Allow different heights
        
        # Fix 2: Set size policy to expand
        self.trans_list.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Load real data or test data
        self.load_recent_transactions()

        self.trans_layout.addWidget(self.trans_list)
        self.bottom_layout.addWidget(self.actions_box)
        self.bottom_layout.addWidget(self.trans_box)
        
        # Fix 3: Set proper stretch factors
        self.bottom_layout.setStretchFactor(self.actions_box, 1)
        self.bottom_layout.setStretchFactor(self.trans_box, 2)
        
        self.main_layout.addLayout(self.bottom_layout)
        self.update_stats()

    def refresh_dashboard(self):
        """Rafraichit les KPIs et les dernieres operations."""
        self._refresh_brand_labels()
        self.load_recent_transactions()
        self.update_stats()

    def _load_company_logo(self):
        logo_path = os.path.join("assets", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(
                72, 72, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            self.logo_label.setPixmap(pixmap)
        else:
            self.logo_label.setText("")
            self.logo_label.setFixedSize(0, 0)

    def _refresh_brand_labels(self):
        agency = self.settings.get("agency_name", "DAROU SALAM") or "DAROU SALAM"
        season = self.settings.get("season", "HADJ 2027") or "HADJ 2027"
        self.company_label.setText(agency)
        self.season_label.setText(season)
    
    def load_recent_transactions(self):
        """Load transactions from database or use test data"""
        # Clear existing items
        self.trans_list.clear()
        try:
            with sqlite3.connect("data/app.db") as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT 'Versement' as type_op, (p.lname || ' ' || p.fname) as label, pay.amount, pay.date
                    FROM payments pay
                    JOIN pilgrims p ON p.id = pay.pilgrim_id
                    UNION ALL
                    SELECT 'Depense' as type_op, e.motif as label, e.amount, e.date
                    FROM expenses e
                    ORDER BY date DESC
                    LIMIT 6
                    """
                )
                rows = cursor.fetchall()
                for type_op, label, amount, date in rows:
                    display_type = "Versement" if type_op == "Versement" else "Dépense"
                    self.add_recent_op(display_type, label or "-", f"{int(amount):,}".replace(",", " "), date)
        except Exception:
            self.add_recent_op("Versement", "Aucune operation", "0", "-")
    
    def add_recent_op(self, type_op, label, amount, date):
        """Add a properly formatted transaction item"""
        item = QListWidgetItem(self.trans_list)
        
        # Create custom widget
        widget = QWidget()
        widget.setObjectName("transactionItem")
        
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(12)
        
        # Icon/Indicator
        icon = "●"
        color = "#2ecc71" if type_op == "Versement" else "#e74c3c"
        
        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        lbl_icon.setFixedWidth(25)
        
        # Info container (vertical layout for name and date)
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(4)
        
        lbl_name = QLabel(label)
        lbl_name.setStyleSheet("font-weight: bold; font-size: 13px; color: #2c3e50;")
        
        lbl_date = QLabel(date)
        lbl_date.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        
        info_layout.addWidget(lbl_name)
        info_layout.addWidget(lbl_date)
        
        # Amount
        lbl_amount = QLabel(f"{amount} FCFA")
        lbl_amount.setStyleSheet(f"font-weight: bold; font-size: 14px; color: {color};")
        lbl_amount.setMinimumWidth(120)
        lbl_amount.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        # Add to layout
        layout.addWidget(lbl_icon)
        layout.addWidget(info_container, 1)  # Give stretch factor
        layout.addWidget(lbl_amount)
        
        # Set widget size hint to ensure proper display
        widget.setLayout(layout)
        
        # Calculate proper size hint
        widget.adjustSize()
        item.setSizeHint(QSize(widget.sizeHint().width(), 65))  # Fixed height
        
        self.trans_list.setItemWidget(item, widget)
    
    def refresh_transactions(self):
        """Refresh the transaction list from database"""
        self.load_recent_transactions()
    
    def showExpenseDialog(self):
        dialog = ExpenseForm(parent=self)
        if dialog.exec():  # If saved successfully
            self.refresh_transactions()  # Refresh the list
            self.update_stats()  # Update stats
    
    def showPaymentDialog(self):
        dialog = PaymentForm(parent=self)
        if dialog.exec():
            self.refresh_transactions()
            self.update_stats()
    
    def showPilgrimDialog(self):
        dialog = PilgrimForm(parent=self)
        if dialog.exec():
            self.refresh_transactions()
            self.update_stats()

    def update_stats(self):
        """Update statistics from database"""
        try:
            with sqlite3.connect("data/app.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM pilgrims")
                total_pilgrims = cursor.fetchone()[0] or 0

                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments")
                total_payments = int(cursor.fetchone()[0] or 0)

                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM expenses")
                total_expenses = int(cursor.fetchone()[0] or 0)

                cursor.execute("SELECT COALESCE(SUM(total_cost), 0) FROM pilgrims")
                total_target = int(cursor.fetchone()[0] or 0)

                total_reliquat = max(total_target - total_payments, 0)
                taux = 0.0
                if total_target > 0:
                    taux = (total_payments / total_target) * 100

                self.card_pilgrims.findChildren(QLabel)[1].setText(str(total_pilgrims))
                self.card_payments.findChildren(QLabel)[1].setText(f"{total_payments:,} FCFA".replace(",", " "))
                self.card_expenses.findChildren(QLabel)[1].setText(f"{total_reliquat:,} FCFA".replace(",", " "))
                self.recette_card.findChildren(QLabel)[1].setText(f"{total_expenses:,} FCFA".replace(",", " "))
                self.card_vols.findChildren(QLabel)[1].setText(f"{taux:.1f}%")
        except Exception:
            return
    
    def create_stat_card(self, title, value, color):
        card = QFrame()
        card.setObjectName("statCard")
        card.setFixedHeight(120)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        
        t_lbl = QLabel(title)
        t_lbl.setObjectName("statTitle")
        v_lbl = QLabel(value)
        v_lbl.setObjectName("statValue")
        v_lbl.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        
        layout.addWidget(t_lbl)
        layout.addWidget(v_lbl)
        layout.addStretch()
        
        # Border left
        card.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: white;
                border-radius: 12px;
                border-left: 5px solid {color};
            }}
        """)
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 30))
        shadow.setOffset(0, 4)
        card.setGraphicsEffect(shadow)
        
        return card

    def create_action_btn(self, text):
        btn = QPushButton(text)
        btn.setObjectName("actionBtn")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setFixedHeight(45)
        btn.setStyleSheet("""
            QPushButton#actionBtn {
                text-align: left;
                padding-left: 15px;
                font-size: 13px;
                border-radius: 8px;
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
            }
            QPushButton#actionBtn:hover {
                background-color: #e9ecef;
                border-color: #1A4A8E;
            }
        """)
        return btn