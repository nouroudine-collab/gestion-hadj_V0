from PySide6.QtWidgets import QVBoxLayout, QPushButton, QFrame
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QEvent, QTimer, Signal

class SideBar(QFrame):
    page_changed = Signal(int)
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sideBar")
        self.setFixedWidth(200) # Largeur par défaut
        
        
        self.sidebar_layout = QVBoxLayout(self)
        self.sidebar_layout.setContentsMargins(5, 20, 5, 20)
        self.sidebar_layout.setSpacing(10)
        
        
        
        self.setStyleSheet(open(file="assets/styles/sidebar.qss", mode="r").read())
        # Bouton Toggle (Le "Hamburger")
        self.toggle_btn = QPushButton("☰")
        self.toggle_btn.setObjectName("toggle_btn")
        self.toggle_btn.setFixedSize(40, 40)
        self.toggle_btn.clicked.connect(self.toggle_sidebar)
        self.sidebar_layout.addWidget(self.toggle_btn)

        self.nav_data = [
                {"id": "dashboard", "text": "📊Tableau de Bord", "index": 0},
                {"id": "pilgrim", "text": "👤 Pèlerins", "index": 1},
                {"id": "payments", "text": "💰 Versements", "index": 2},
                {"id": "expenses", "text": "💸 Dépenses", "index": 3},
                {"id": "settings", "text": "⚙ Parametres", "index": 4},
                {"id": "confirmed", "text": "✅ Departs confirmes", "index": 5},
        ]
        
        self.buttons = {}
        
        for item in self.nav_data:
            btn = QPushButton(item["text"])
            btn.setCheckable(True) # Permet de rester "enfoncé" visuellement
            btn.setObjectName("navButton")
            btn.clicked.connect(lambda _, idx=item["index"], b=btn: self.on_nav_click(idx, b))
                    
            self.sidebar_layout.addWidget(btn)
            self.buttons[item["id"]] = btn
        
        self.sidebar_layout.addStretch()
        
        # État initial
        self.is_collapsed = False
        self.auto_hide_mode = False 
        self.is_currently_visible = True
    def on_nav_click(self, index, clicked_button):
        """Gère le clic sur un bouton de navigation"""
        for btn in self.buttons.values():
            btn.setChecked(False)
        clicked_button.setChecked(True)
                
        # 2. Émettre le signal pour changer la page dans le QStackedWidget
        self.page_changed.emit(index)
    def toggle_sidebar(self):
        # Définir les dimensions cible
        start_width = self.width()
        end_width = 20 if not self.is_collapsed else 200
        
        # Création de l'animation
        self.animation: QPropertyAnimation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(300) # 300ms pour la fluidité
        self.animation.setStartValue(start_width)
        self.animation.setEndValue(end_width)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuart) # Effet d'accélération/freinage

        # On anime aussi le maximumWidth pour éviter les blocages
        self.max_animation: QPropertyAnimation = QPropertyAnimation(self, b"maximumWidth")
        self.max_animation.setDuration(300)
        self.max_animation.setStartValue(start_width)
        self.max_animation.setEndValue(end_width)
        self.max_animation.setEasingCurve(QEasingCurve.Type.InOutQuart)

        # Lancer le groupe d'animations
        self.group:QParallelAnimationGroup = QParallelAnimationGroup()
        self.group.addAnimation(self.animation)
        self.group.addAnimation(self.max_animation)
        self.group.start()

        # Inverser l'état
        self.is_collapsed: bool = not self.is_collapsed
        
        # Optionnel : Cacher le texte des boutons quand c'est réduit
        self.update_button_texts(collapsed=self.is_collapsed)
    def handle_toggle_click(self):
        """Alterne entre mode fixe et mode Auto-Hide"""
        self.auto_hide_mode = not self.auto_hide_mode
        if self.auto_hide_mode:
            self.animate_sidebar(end_width=0)
            self.update_button_texts(collapsed=True)
        else:
            self.animate_sidebar(200)
            self.update_button_texts(collapsed=False)
    def animate_sidebar(self, end_width):
        self.group = QParallelAnimationGroup()
        for prop in [b"minimumWidth", b"maximumWidth"]:
            anim:QPropertyAnimation = QPropertyAnimation(self, prop)
            anim.setDuration(300)
            anim.setEndValue(end_width)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.group.addAnimation(anim)
            self.group.start()
            self.is_currently_visible = (end_width > 0)
    def update_button_texts(self, collapsed):
        """Réduit le texte aux émojis en mode collapse"""
        for item in self.nav_data:
            btn = self.buttons[item["id"]]
            btn.setText(item["text"][0] if collapsed else item["text"])

    def eventFilter(self, watched, event):
        """Logique Auto-Hide : détection de la souris au bord gauche"""
        if self.auto_hide_mode:
            if event.type() == QEvent.Type.MouseMove:
                if event.pos().x() < 10 and not self.is_currently_visible:
                    self.animate_sidebar(200)
            elif event.type() == QEvent.Type.Leave:
                # Si on quitte la barre, on attend un peu avant de fermer
                if self.is_currently_visible and not self.underMouse():
                    QTimer.singleShot(500, self.check_auto_collapse)
        return super().eventFilter(watched, event)

    def check_auto_collapse(self):
        if self.auto_hide_mode and not self.underMouse():
            self.animate_sidebar(0)