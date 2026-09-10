from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QFileDialog, QMessageBox, QFrame, QSizePolicy,
    QApplication
)
from PySide6.QtCore import Qt

from ui.key_dialog import KeyDialog
from ui.processing_dialog import ProcessingDialog
from ui.image_preview import ImagePreview
from ui.styles import MAIN_STYLESHEET, LIGHT_STYLESHEET
from image_handler import ContinuousImage


from crypto import encrypt, save_cipher
from PySide6.QtGui import QImage, QPixmap
import numpy as np

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.original_image = None
        self.encrypted_image = None
        self.recovered_image = None
        self.key1 = None
        self.key2 = None
        self.dark_theme_enabled = True

        self.setWindowTitle("Fourier-Domain Image Encryption")
        self.resize(1100, 780)
        self.load_ui()

    def load_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(3)

        main_layout.addLayout(self.build_header())
        main_layout.addWidget(self.build_encryption_group(), 1)
        main_layout.addWidget(self.build_decryption_group(), 1)

    def build_header(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 2, 2, 2)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Fourier-Domain Image Encryptor")
        title.setObjectName("appTitle")

        subtitle = QLabel("Double Random Phase Encoding")
        subtitle.setObjectName("appSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        button_box = QHBoxLayout()
        button_box.setSpacing(4)
        self.keys_button = QPushButton("Encryption Keys")
        self.keys_button.setObjectName("headerAction")
        self.keys_button.clicked.connect(self.open_key_dialog)

        self.processing_button = QPushButton("Processing")
        self.processing_button.setObjectName("headerAction")
        self.processing_button.clicked.connect(self.open_processing_dialog)

        self.theme_button = QPushButton("Light Theme")
        self.theme_button.setObjectName("headerAction")
        self.theme_button.clicked.connect(self.toggle_theme)

        button_box.addWidget(self.keys_button)
        button_box.addWidget(self.processing_button)
        button_box.addWidget(self.theme_button)

        header_layout.addLayout(button_box)
        return header_layout

    def build_encryption_group(self):
        group = QGroupBox("ENCRYPTION")
        layout = QVBoxLayout(group)
        layout.setSpacing(1)
        # layout.setContentsMargins(3, 3, 3, 3)

        row = QHBoxLayout()
        row.setSpacing(8)

        original_column = QVBoxLayout()
        self.original_image_box = self.create_image_box("Original Image")
        self.load_image_button = QPushButton("Load Image")
        self.load_image_button.clicked.connect(self.load_image)
        original_column.addWidget(self.original_image_box, 1)
        original_column.addWidget(self.load_image_button, alignment=Qt.AlignCenter)

        encrypt_column = QVBoxLayout()
        encrypt_column.addStretch()
        self.encrypt_button = QPushButton("ENCRYPT")
        self.encrypt_button.setObjectName("primaryAction")
        self.encrypt_button.setMinimumSize(120, 44)
        self.encrypt_button.clicked.connect(self.encrypt)
        encrypt_column.addWidget(self.encrypt_button)
        encrypt_column.addStretch()

        encrypted_column = QVBoxLayout()
        self.encrypted_image_box = self.create_image_box("Encrypted Image")
        self.save_cipher_button = QPushButton("Save Cipher")
        self.save_cipher_button.clicked.connect(self.save_cipher)
        encrypted_column.addWidget(self.encrypted_image_box, 1)
        encrypted_column.addWidget(self.save_cipher_button, alignment=Qt.AlignCenter)

        row.addLayout(original_column, 1)
        row.addLayout(encrypt_column)
        row.addLayout(encrypted_column, 1)

        layout.addLayout(row, 1)

        return group

    def build_decryption_group(self):
        group = QGroupBox("DECRYPTION")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)
        layout.setContentsMargins(6, 10, 6, 6)

        row = QHBoxLayout()
        row.setSpacing(8)

        cipher_column = QVBoxLayout()
        self.cipher_input_box = self.create_image_box("Encrypted Image")
        self.load_cipher_button = QPushButton("Load Cipher")
        self.load_cipher_button.clicked.connect(self.load_cipher)
        cipher_column.addWidget(self.cipher_input_box, 1)
        cipher_column.addWidget(self.load_cipher_button, alignment=Qt.AlignCenter)

        decrypt_column = QVBoxLayout()
        decrypt_column.addStretch()
        self.decrypt_button = QPushButton("DECRYPT")
        self.decrypt_button.setObjectName("primaryAction")
        self.decrypt_button.setMinimumSize(120, 44)
        self.decrypt_button.clicked.connect(self.decrypt)
        decrypt_column.addWidget(self.decrypt_button)
        decrypt_column.addStretch()

        recovered_column = QVBoxLayout()
        self.recovered_image_box = self.create_image_box("Recovered Image")
        self.save_recovered_button = QPushButton("Save Recovered Image")
        self.save_recovered_button.clicked.connect(self.save_recovered)
        recovered_column.addWidget(self.recovered_image_box, 1)
        recovered_column.addWidget(self.save_recovered_button, alignment=Qt.AlignCenter)

        row.addLayout(cipher_column, 1)
        row.addLayout(decrypt_column)
        row.addLayout(recovered_column, 1)

        layout.addLayout(row, 1)

        return group

    def create_image_box(self, title, placeholder_text="No Image"):
        group = QGroupBox(title)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(4, 8, 4, 4)

        image_label = ImagePreview(placeholder_text)
        image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        image_label.setMinimumSize(0, 0)

        layout.addWidget(image_label)
        group.image_label = image_label
        return group

    # Dialog launchers
    def open_key_dialog(self):
        image_shape = None if self.original_image is None else self.original_image.image.shape
        dialog = KeyDialog(image_shape, self.key1, self.key2, self)
        dialog.exec()

        # QDialog.Accepted means the user closed the dialog with its Close
        if dialog.result() == KeyDialog.Accepted:
            self.key1 = dialog.key1
            self.key2 = dialog.key2

    def open_processing_dialog(self):
        dialog = ProcessingDialog(self)
        dialog.exec()

    def toggle_theme(self):
        self.dark_theme_enabled = not self.dark_theme_enabled
        app = QApplication.instance()

        if self.dark_theme_enabled:
            app.setStyleSheet(MAIN_STYLESHEET)
            self.theme_button.setText("Light Theme")
        else:
            app.setStyleSheet(LIGHT_STYLESHEET)
            self.theme_button.setText("Dark Theme")

    # Action handlers
    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not file_path:
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", "Could not load the image.")
            return

        self.original_image_box.image_label.set_image(pixmap)
        self.original_image = ContinuousImage(file_path)

    def encrypt(self):
        if self.original_image is None:
            QMessageBox.warning(self, "Cannot encrypt", "Load an image first.")
            return

        if self.key1 is None or self.key2 is None:
            QMessageBox.warning(
                self,
                "Cannot encrypt",
                "Generate encryption keys first.",
            )
            return

        try:
            self.encrypted_image = encrypt(
                self.original_image.image,
                self.key1,
                self.key2,
            )
        except ValueError as error:
            QMessageBox.warning(self, "Cannot encrypt", str(error))
            return

        preview = self.ciphertext_to_pixmap_rgb(self.encrypted_image)
        self.encrypted_image_box.image_label.set_image(preview)

    @staticmethod
    def ciphertext_to_pixmap_rgb(ciphertext):
        magnitude = np.abs(np.asarray(ciphertext))

        maximum = np.max(magnitude)
        if maximum > 0:
            magnitude /= maximum

        preview = np.clip(magnitude * 255.0, 0.0, 255.0).astype(np.uint8)

        if preview.ndim == 3 and preview.shape[2] == 3:
            height, width, _ = preview.shape
            image = QImage(
                preview.data,
                width,
                height,
                preview.strides[0],
                QImage.Format_RGB888,
            ).copy()
        else:
            height, width = preview.shape[:2]
            image = QImage(
                preview.data,
                width,
                height,
                preview.strides[0],
                QImage.Format_Grayscale8,
            ).copy()

        return QPixmap.fromImage(image)

    def save_cipher(self):
        if self.encrypted_image is None or isinstance(self.encrypted_image, str):
            QMessageBox.warning(
                self,
                "Cannot save cipher",
                "Encrypt an image first.",
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Encrypted Cipher",
            "cipher.npz",
            "NumPy archives (*.npz)",
        )
        if not file_path:
            return

        try:
            save_cipher(file_path, self.encrypted_image)
        except (OSError, ValueError) as error:
            QMessageBox.critical(self, "Could not save cipher", str(error))
            return

        QMessageBox.information(
            self,
            "Cipher saved",
            f"Encrypted data saved to:\n{file_path}",
        )


    def load_cipher(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Encrypted Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if not file_path:
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Error", "Could not load the image.")
            return

        self.cipher_input_box.image_label.set_image(pixmap)
        self.encrypted_image = file_path

    def decrypt(self):
        raise NotImplementedError

    def save_recovered(self):
        raise NotImplementedError
