from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QSizePolicy
)
from PySide6.QtCore import Qt

from ui.image_preview import ImagePreview


class KeyDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Encryption Keys")
        self.resize(560, 500)
        self.load_ui()

    def load_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 10)
        layout.setSpacing(8)

        title = QLabel("Phase Keys")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Random phase masks used for encryption / decryption")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        self.key1_box = self.create_image_box("Phase Key 1")
        self.key2_box = self.create_image_box("Phase Key 2")
        key_row.addWidget(self.key1_box, 1)
        key_row.addWidget(self.key2_box, 1)
        layout.addLayout(key_row, 1)

        self.generate_keys_button = QPushButton("✨  Generate New Keys")
        self.generate_keys_button.setObjectName("primaryAction")
        self.generate_keys_button.clicked.connect(self.generate_keys)
        layout.addWidget(self.generate_keys_button)

        key_buttons = QHBoxLayout()
        key_buttons.setSpacing(10)
        self.save_keys_button = QPushButton("Save Keys")
        self.save_keys_button.clicked.connect(self.save_keys)

        self.load_keys_button = QPushButton("Load Keys")
        self.load_keys_button.clicked.connect(self.load_keys)

        key_buttons.addWidget(self.save_keys_button)
        key_buttons.addWidget(self.load_keys_button)
        layout.addLayout(key_buttons)

        self.key_status = QLabel("Status: No keys generated")
        self.key_status.setObjectName("statusLabel")
        self.key_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.key_status)

        layout.addStretch()

        close_button = QPushButton("Close")
        close_button.setObjectName("closeAction")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def create_image_box(self, title):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(4, 8, 4, 4)

        image_label = ImagePreview("No Key")
        image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        image_label.setMinimumSize(0, 0)

        layout.addWidget(image_label)
        group.image_label = image_label
        return group

    def generate_keys(self):
        raise NotImplementedError

    def save_keys(self):
        raise NotImplementedError

    def load_keys(self):
        raise NotImplementedError