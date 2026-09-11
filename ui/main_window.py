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


from crypto import encrypt, decrypt, save_cipher, load_cipher
from PySide6.QtGui import QImage, QPixmap
import numpy as np

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.original_image = None
        self.encrypted_image = None
        self.cipher_input = None
        self.recovered_image = None
        self.key1 = None
        self.key2 = None
        self.dark_theme_enabled = True

        self.setWindowTitle("Fourier-Domain Image Encryption")
        self.resize(1120, 820)
        self.setMinimumSize(900, 700)
        self.load_ui()

    def load_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(28, 24, 28, 24)
        main_layout.setSpacing(20)

        main_layout.addLayout(self.build_header())
        main_layout.addWidget(self.build_encryption_group(), 1)
        main_layout.addWidget(self.build_decryption_group(), 1)

    def build_header(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 2, 2, 2)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Image Encryptor")
        title.setObjectName("appTitle")

        subtitle = QLabel("Fourier-domain encryption / Double Random Phase Encoding")
        subtitle.setObjectName("appSubtitle")

        title_box.addWidget(title)
        title_box.addWidget(subtitle)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        button_box = QHBoxLayout()
        button_box.setSpacing(8)
        self.keys_button = QPushButton("Encryption Keys")
        self.keys_button.setObjectName("headerAction")
        self.keys_button.clicked.connect(self.open_key_dialog)

        self.processing_button = QPushButton("How it works")
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
        group, row = self.create_workflow_card("Encrypt an image")
        self.original_image_box = self.create_image_box(
            "Original image", "Start with an image\nPNG, JPG, BMP or WebP"
        )
        self.encrypted_image_box = self.create_image_box(
            "Encrypted result", "Your encrypted preview\nwill appear here"
        )
        self.load_image_button = self.create_button("Load image", self.load_image)
        self.save_cipher_button = self.create_button("Save cipher", self.save_cipher)
        self.encrypt_button = self.create_button("Encrypt", self.encrypt, primary=True)
        self.populate_workflow(row, self.original_image_box, self.load_image_button,
                               self.encrypt_button, self.encrypted_image_box,
                               self.save_cipher_button,
                               "Set phase keys.", "Save your cipher.")
        return group

    def build_decryption_group(self):
        group, row = self.create_workflow_card("Recover an image")
        self.cipher_input_box = self.create_image_box(
            "Cipher input", "Load a saved cipher\nto recover its image"
        )
        self.recovered_image_box = self.create_image_box(
            "Recovered image", "Your recovered image\nwill appear here"
        )
        self.load_cipher_button = self.create_button("Load cipher", self.load_cipher)
        self.save_recovered_button = self.create_button("Save image", self.save_recovered)
        self.decrypt_button = self.create_button("Decrypt", self.decrypt, primary=True)
        self.populate_workflow(row, self.cipher_input_box, self.load_cipher_button,
                               self.decrypt_button, self.recovered_image_box,
                               self.save_recovered_button,
                               "Use original keys.", "Save your image.")
        return group

    @staticmethod
    def create_button(text, handler, primary=False):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.clicked.connect(handler)
        if primary:
            button.setObjectName("primaryAction")
            button.setFixedWidth(132)
        return button

    @staticmethod
    def create_workflow_card(title):
        card = QFrame()
        card.setObjectName("workflowCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 10, 20, 12)
        layout.setSpacing(6)
        heading = QHBoxLayout()
        heading.setSpacing(12)
        text = QVBoxLayout()
        text.setSpacing(3)
        title_label = QLabel(title)
        title_label.setObjectName("sectionTitle")
        text.addWidget(title_label)
        heading.addLayout(text)
        heading.addStretch()
        layout.addLayout(heading)
        row = QHBoxLayout()
        row.setSpacing(20)
        layout.addLayout(row, 1)
        return card, row

    @staticmethod
    def populate_workflow(row, input_box, load_button, action, output_box, save_button,
                          input_hint, output_hint):
        for box, button, hint in ((input_box, load_button, input_hint),
                                  (output_box, save_button, output_hint)):
            column = QVBoxLayout()
            column.setSpacing(6)
            column.addWidget(box, 1)
            footer = QHBoxLayout()
            footer.setSpacing(10)
            description = QLabel(hint)
            description.setObjectName("appSubtitle")
            description.setWordWrap(True)
            description.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
            # Equal side widths keep the button centered beneath its preview.
            footer.addWidget(description, 1)
            footer.addWidget(button, 0, Qt.AlignVCenter)
            footer.addWidget(QWidget(), 1)
            column.addLayout(footer)
            if box is output_box:
                row.addWidget(action, 0, Qt.AlignVCenter)
            row.addLayout(column, 1)

    def create_image_box(self, title, placeholder_text="No image"):
        group = QWidget()
        layout = QVBoxLayout(group)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        label = QLabel(title)
        label.setObjectName("previewTitle")
        layout.addWidget(label)
        image_label = ImagePreview(placeholder_text)
        image_label.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        layout.addWidget(image_label, 1)
        group.image_label = image_label
        return group

    def open_key_dialog(self):
        image_shape = None if self.original_image is None else self.original_image.image.shape
        if self.cipher_input is not None:
            image_shape = self.cipher_input.shape
        dialog = KeyDialog(image_shape, self.key1, self.key2, self)
        dialog.exec()

        if dialog.result() == KeyDialog.Accepted:
            self.key1 = dialog.key1
            self.key2 = dialog.key2
            self.clear_recovered()

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
        self.encrypted_image = None
        self.encrypted_image_box.image_label.clear_image()

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

        return MainWindow.image_to_pixmap(magnitude)

    @staticmethod
    def image_to_pixmap(pixels):
        preview = np.ascontiguousarray(
            np.rint(np.clip(pixels, 0.0, 1.0) * 255.0).astype(np.uint8)
        )

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
            self, "Select Encrypted Cipher", "",
            "NumPy archives (*.npz)"
        )
        if not file_path:
            return

        try:
            ciphertext = load_cipher(file_path)
        except (OSError, ValueError, EOFError) as error:
            QMessageBox.warning(self, "Could not load cipher", str(error))
            return

        self.cipher_input = ciphertext
        self.cipher_input_box.image_label.set_image(
            self.ciphertext_to_pixmap_rgb(ciphertext)
        )
        self.clear_recovered()

    def clear_recovered(self):
        self.recovered_image = None
        self.recovered_image_box.image_label.clear_image()

    def decrypt(self):
        self.clear_recovered()
        if self.cipher_input is None:
            QMessageBox.warning(self, "Cannot decrypt", "Load a saved cipher first.")
            return
        if self.key1 is None or self.key2 is None:
            QMessageBox.warning(self, "Cannot decrypt", "Load the original encryption keys first.")
            return
        try:
            self.recovered_image = decrypt(self.cipher_input, self.key1, self.key2)
        except ValueError as error:
            QMessageBox.warning(self, "Cannot decrypt", str(error))
            return
        self.recovered_image_box.image_label.set_image(
            self.image_to_pixmap(self.recovered_image)
        )

    def save_recovered(self):
        if self.recovered_image is None:
            QMessageBox.warning(self, "Cannot save image", "Decrypt a cipher first.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Recovered Image", "recovered.png", "PNG images (*.png)"
        )
        if not file_path:
            return
        if not file_path.lower().endswith(".png"):
            file_path += ".png"
        if not self.image_to_pixmap(self.recovered_image).save(file_path, "PNG"):
            QMessageBox.critical(self, "Could not save image", "Failed to write the PNG file.")
