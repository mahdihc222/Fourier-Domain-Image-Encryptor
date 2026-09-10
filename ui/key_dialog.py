from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QSizePolicy, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

from ui.image_preview import ImagePreview


from PySide6.QtGui import QImage, QPixmap
import numpy as np
from crypto import generate_phase_mask, save_keys as save_key_file, load_keys as load_key_file

class KeyDialog(QDialog):

    def __init__(self, image_shape=None, key1=None, key2=None, parent=None):
        super().__init__(parent)
        self.image_shape = image_shape
        self.key1 = key1
        self.key2 = key2
        self.setWindowTitle("Encryption Keys")
        self.resize(560, 500)
        self.load_ui()

        if self.key1 is not None and self.key2 is not None:
            self.update_key_previews()
            self.key_status.setText("Status: Keys ready")

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
        image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        image_label.setMinimumSize(0, 0)

        layout.addWidget(image_label)
        group.image_label = image_label
        return group

    def generate_keys(self):
        if self.image_shape is None:
            self.key_status.setText("Status: Load an image first")
            return

        height, width = self.image_shape[:2]
        key_shape = (height, width)
        self.key1 = generate_phase_mask(key_shape)
        self.key2 = generate_phase_mask(key_shape)

        self.update_key_previews()
        self.key_status.setText(f"Status: Keys ready ({height} x {width})")

    def update_key_previews(self):
        self.key1_box.image_label.set_image(self.phase_to_pixmap(self.key1))
        self.key2_box.image_label.set_image(self.phase_to_pixmap(self.key2))

    @staticmethod
    def phase_to_pixmap(key):
        """
        This conversion is only for the UI.
        """
        phase = np.angle(key) # -pi to pi
        preview = ((phase + np.pi) / (2.0 * np.pi) * 255.0).astype(np.uint8)
        height, width = preview.shape
        image = QImage(
            preview.data,
            width,
            height,
            preview.strides[0],
            QImage.Format_Grayscale8,
        ).copy()
        return QPixmap.fromImage(image)

    def save_keys(self):
        if self.key1 is None or self.key2 is None:
            self.key_status.setText("Status: Generate keys first")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Encryption Keys",
            "keys.npz",
            "NumPy archives (*.npz)",
        )
        if not file_path:
            return

        try:
            save_key_file(file_path, self.key1, self.key2)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Could not save keys", str(error))
            return

        self.key_status.setText(f"Status: Keys saved to {file_path}")

    def load_keys(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Encryption Keys",
            "",
            "NumPy archives (*.npz)",
        )
        if not file_path:
            return

        try:
            key1, key2 = load_key_file(file_path)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Could not load keys", str(error))
            return

        if self.image_shape is not None:
            expected_shape = tuple(self.image_shape[:2])
            if key1.shape != expected_shape:
                QMessageBox.warning(
                    self,
                    "Incompatible keys",
                    "The loaded keys do not match the loaded image dimensions.",
                )
                return

        self.key1 = key1
        self.key2 = key2
        self.update_key_previews()
        self.key_status.setText(f"Status: Keys loaded from {file_path}")