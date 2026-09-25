from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QLabel, QPushButton, QFileDialog, QMessageBox, QFrame, QSizePolicy,
    QApplication, QRadioButton, QButtonGroup, QInputDialog
)
from PySide6.QtCore import Qt

from ui.key_dialog import KeyDialog
from ui.comparison_dialog import ComparisonDialog
from ui.steps_dialog import StepsDialog
from ui.key_sensitivity_dialog import KeySensitivityDialog
from ui.image_preview import ImagePreview
from ui.styles import MAIN_STYLESHEET, LIGHT_STYLESHEET
from image_handler import ContinuousImage


from crypto import encrypt, decrypt, save_cipher, load_cipher
from arnold_dct import encrypt as encrypt_arnold, decrypt as decrypt_arnold, encryption_steps, decryption_steps, save_cipher_png, load_cipher_png
from dwt_chaotic import encrypt as encrypt_dwt, decrypt as decrypt_dwt, encryption_steps as dwt_encryption_steps, save_cipher as save_dwt_cipher, load_cipher as load_dwt_cipher
from PySide6.QtGui import QImage, QPixmap
from PIL import Image
import numpy as np
import time

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.original_image = None
        self.encrypted_image = None
        self.cipher_input = None
        self.recovered_image = None
        self.key1 = None
        self.key2 = None
        self.dwt_key = "image-encryptor-dwt"
        self.dark_theme_enabled = True
        self.scheme = "drpe"
        self.arnold_cipher_metadata = None
        self.arnold_diffusion_key = "image-encryptor"

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
        main_layout.addWidget(self.build_scheme_selector())
        main_layout.addWidget(self.build_encryption_group(), 1)
        main_layout.addWidget(self.build_decryption_group(), 1)

    def build_scheme_selector(self):
        card = QFrame()
        card.setObjectName("workflowCard")
        layout = QHBoxLayout(card)
        layout.addWidget(QLabel("Active scheme:"))
        self.scheme_group = QButtonGroup(self)
        self.drpe_radio = QRadioButton("Classic DRPE")
        self.arnold_radio = QRadioButton("Arnold + DCT")
        self.dwt_radio = QRadioButton("DWT")
        if self.scheme == 'drpe':
            self.drpe_radio.setChecked(True)
        elif self.scheme =='arnold':
            self.arnold_radio.setChecked(True)
        elif self.scheme =='dwt':
            self.dwt_radio.setChecked(True)
        self.scheme_group.addButton(self.drpe_radio)
        self.scheme_group.addButton(self.arnold_radio)
        self.scheme_group.addButton(self.dwt_radio)
        self.drpe_radio.toggled.connect(self.on_scheme_changed)
        self.arnold_radio.toggled.connect(self.on_scheme_changed)
        self.dwt_radio.toggled.connect(self.on_scheme_changed)
        layout.addWidget(self.drpe_radio)
        layout.addWidget(self.arnold_radio)
        layout.addWidget(self.dwt_radio)
        layout.addStretch()
        return card

    def on_scheme_changed(self):
        if self.drpe_radio.isChecked():
            self.scheme = "drpe"
        elif self.arnold_radio.isChecked():
            self.scheme = "arnold"
        else:
            self.scheme = "dwt"
        self._clear_images()

    def _clear_images(self):
        self.encrypted_image = None
        self.cipher_input = None
        self.recovered_image = None
        self.encrypted_image_box.image_label.clear_image()
        self.cipher_input_box.image_label.clear_image()
        self.recovered_image_box.image_label.clear_image()

    def build_header(self):
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 2, 2, 2)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Image Encryptor")
        title.setObjectName("appTitle")

        # subtitle = QLabel("Fourier-domain encryption / Double Random Phase Encoding")
        # subtitle.setObjectName("appSubtitle")

        title_box.addWidget(title)
        # title_box.addWidget(subtitle)

        header_layout.addLayout(title_box)
        header_layout.addStretch()

        button_box = QHBoxLayout()
        button_box.setSpacing(8)
        self.keys_button = QPushButton("Encryption Keys")
        self.keys_button.setObjectName("headerAction")
        self.keys_button.clicked.connect(self.open_key_dialog)

        self.theme_button = QPushButton("Light Theme")
        self.theme_button.setObjectName("headerAction")
        self.theme_button.clicked.connect(self.toggle_theme)

        self.compare_button = QPushButton("Compare schemes")
        self.compare_button.setObjectName("headerAction")
        self.compare_button.clicked.connect(self.open_comparison_dialog)

        self.sensitivity_button = QPushButton("Key sensitivity")
        self.sensitivity_button.setObjectName("headerAction")
        self.sensitivity_button.clicked.connect(self.open_key_sensitivity_dialog)

        button_box.addWidget(self.keys_button)
        button_box.addWidget(self.compare_button)
        button_box.addWidget(self.sensitivity_button)
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
        self.encrypt_steps_button = self.create_button("Show steps", self.show_encryption_steps)
        self.populate_workflow(row, self.original_image_box, self.load_image_button,
                               self.encrypt_button, self.encrypted_image_box,
                               self.save_cipher_button, self.encrypt_steps_button,
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
        self.decrypt_steps_button = self.create_button("Show steps", self.show_decryption_steps)
        self.populate_workflow(row, self.cipher_input_box, self.load_cipher_button,
                               self.decrypt_button, self.recovered_image_box,
                               self.save_recovered_button, self.decrypt_steps_button,
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
    def populate_workflow(row, input_box, load_button, action, output_box, save_button, step_button,
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
            footer.addWidget(description, 1)
            footer.addWidget(button, 0, Qt.AlignVCenter)
            footer.addWidget(step_button, 0, Qt.AlignVCenter)
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
        if self.scheme == "dwt":
            value, ok = QInputDialog.getText(
                self,
                "DWT key",
                "Enter the master secret key for the DWT method:",
                text=self.dwt_key,
            )
            if ok:
                self.dwt_key = str(value)
            self.clear_recovered()
            return

        image_shape = None if self.original_image is None else self.original_image.image.shape
        if self.cipher_input is not None:
            image_shape = self.cipher_input.shape
        dialog = KeyDialog(image_shape, self.key1, self.key2, self)
        dialog.exec()

        if dialog.result() == KeyDialog.Accepted:
            self.key1 = dialog.key1
            self.key2 = dialog.key2
            self.clear_recovered()

    def open_comparison_dialog(self):
        if self.original_image is None:
            QMessageBox.warning(self, "Cannot compare", "Load an image first.")
            return
        ComparisonDialog(
            self.original_image.image,
            self.key1,
            self.key2,
            self.dwt_key,
            self,
        ).exec()

    def open_key_sensitivity_dialog(self):
        if self.scheme == "dwt":
            QMessageBox.information(self, "Key sensitivity", "The DWT scheme uses a deterministic master key; the sensitivity demo is not available for this method.")
            return
        if self.encrypted_image is None and self.cipher_input is None:
            QMessageBox.warning(self, "Cannot demonstrate sensitivity", "Encrypt or load a cipher first.")
            return
        if self.scheme == "drpe" and (self.key1 is None or self.key2 is None):
            QMessageBox.warning(self, "Cannot demonstrate sensitivity", "Generate the active DRPE keys first.")
            return
        cipher = self.cipher_input if self.cipher_input is not None else self.encrypted_image
        KeySensitivityDialog(
            None if self.original_image is None else self.original_image.image,
            cipher, self.scheme,
            self.key1, self.key2, self.arnold_cipher_metadata,
            self.arnold_diffusion_key, self,
        ).exec()

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
        self._clear_images()

    def encrypt(self):
        if self.original_image is None:
            QMessageBox.warning(self, "Cannot encrypt", "Load an image first.")
            return

        if self.scheme == "drpe" and (self.key1 is None or self.key2 is None):
            QMessageBox.warning(
                self,
                "Cannot encrypt",
                "Generate encryption keys first.",
            )
            return

        try:
            if self.scheme == "arnold":
                self.encrypted_image, self.arnold_cipher_metadata = encrypt_arnold(
                    self.original_image.image, diffusion_key=self.arnold_diffusion_key
                )
            elif self.scheme == "dwt":
                self.encrypted_image = encrypt_dwt(self.original_image.image, self.dwt_key)
            else:
                self.encrypted_image = encrypt(self.original_image.image, self.key1, self.key2)
        except ValueError as error:
            QMessageBox.warning(self, "Cannot encrypt", str(error))
            return

        preview = self.ciphertext_to_pixmap_rgb(self.encrypted_image)
        self.encrypted_image_box.image_label.set_image(preview)

    @staticmethod
    def ciphertext_to_pixmap_rgb(ciphertext):
        values = np.asarray(ciphertext, dtype=np.float64)
        if values.ndim == 3 and values.shape[2] == 3:
            return MainWindow.image_to_pixmap(np.clip(values, 0.0, 1.0))

        magnitude = np.abs(values)
        if magnitude.ndim == 1:
            metadata = getattr(ciphertext, "metadata", {})
            display_shape = tuple(metadata.get("padded_shape", ()))
            if display_shape and int(np.prod(display_shape)) == magnitude.size:
                magnitude = magnitude.reshape(display_shape)
            else:
                magnitude = magnitude.reshape(1, -1)

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
            "cipher.png",
            "PNG images (*.png)",
        )
        if not file_path:
            return

        try:
            if self.scheme == "arnold":
                save_cipher_png(file_path, self.encrypted_image, self.arnold_cipher_metadata)
            elif self.scheme == "dwt":
                save_dwt_cipher(file_path, self.encrypted_image)
            else:
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
            "PNG images (*.png)"
        )
        if not file_path:
            return

        try:
            png_text = Image.open(file_path).text
            if self.scheme != "dwt" and "dwt_encoding" in png_text:
                raise ValueError("This is a DWT cipher. Select the DWT scheme before loading it.")
            if self.scheme == "dwt" and "dwt_encoding" not in png_text:
                raise ValueError("This is not a DWT cipher. Select the scheme used to create this PNG.")
            if self.scheme == "arnold":
                ciphertext, self.arnold_cipher_metadata = load_cipher_png(file_path)
            elif self.scheme == "dwt":
                ciphertext = load_dwt_cipher(file_path)
            else:
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
        if self.scheme == "drpe" and (self.key1 is None or self.key2 is None):
            QMessageBox.warning(self, "Cannot decrypt", "Load the original encryption keys first.")
            return
        try:
            if self.scheme == "arnold":
                if self.arnold_cipher_metadata is None:
                    QMessageBox.warning(self, "Cannot decrypt", "Encrypt with the Arnold scheme in this session first.")
                    return
                self.recovered_image = decrypt_arnold(
                    self.cipher_input, self.arnold_cipher_metadata,
                    diffusion_key=self.arnold_diffusion_key,
                )
            elif self.scheme == "dwt":
                self.recovered_image = decrypt_dwt(self.cipher_input, self.dwt_key)
            else:
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

    def show_encryption_steps(self):
        if self.original_image is None:
            QMessageBox.warning(self, "Cannot show steps", "Load an image first.")
            return
        if self.scheme == "arnold":
            steps, _ = encryption_steps(
                self.original_image.image, diffusion_key=self.arnold_diffusion_key
            )
        elif self.scheme == "dwt":
            steps = dwt_encryption_steps(self.original_image.image, self.dwt_key)
        else:
            cipher = self.encrypted_image if self.encrypted_image is not None else encrypt(self.original_image.image, self.key1, self.key2)
            masked = self.original_image.image * (self.key1[..., None] if self.original_image.image.ndim == 3 else self.key1)
            spectrum = np.fft.fft2(masked, axes=(0, 1))
            scrambled = spectrum * (self.key2[..., None] if spectrum.ndim == 3 else self.key2)
            steps = [("Original", self.original_image.image), ("After phase key 1", np.abs(masked)), ("2-D Fourier transform", np.abs(spectrum)), ("After phase key 2", np.abs(scrambled)), ("Inverse Fourier transform / cipher", np.abs(cipher))]
        StepsDialog("Encryption steps", steps, self).exec()

    def show_decryption_steps(self):
        if self.cipher_input is None and self.encrypted_image is None:
            QMessageBox.warning(self, "Cannot show steps", "Encrypt or load a cipher first.")
            return
        cipher = self.cipher_input if self.cipher_input is not None else self.encrypted_image
        if self.scheme == "arnold":
            if self.arnold_cipher_metadata is None:
                QMessageBox.warning(self, "Cannot show steps", "The Arnold cipher metadata is unavailable.")
                return
            steps = decryption_steps(
                cipher, self.arnold_cipher_metadata,
                diffusion_key=self.arnold_diffusion_key,
            )
        elif self.scheme == "dwt":
            image = np.asarray(cipher, dtype=np.float64)
            ll1, lh1, hl1, hh1 = encrypt_dwt.__globals__["haar_dwt2"](image)
            ll2, lh2, hl2, hh2 = encrypt_dwt.__globals__["haar_dwt2"](ll1)
            steps = [
                ("Ciphertext", image),
                ("Level-1 DWT", np.concatenate([ll1, hl1], axis=1)),
                ("Level-2 DWT on LL1", np.concatenate([ll2, hl2], axis=1)),
                ("Recovered image", np.abs(decrypt_dwt(cipher, self.dwt_key))),
            ]
        else:
            spectrum = np.fft.fft2(cipher, axes=(0, 1))
            unmasked = spectrum * np.conj(self.key2[..., None] if cipher.ndim == 3 else self.key2)
            partially_recovered = np.fft.ifft2(unmasked, axes=(0, 1))
            unmasked_image = partially_recovered * np.conj(self.key1[..., None] if cipher.ndim == 3 else self.key1)
            steps = [("Ciphertext", np.abs(cipher)), ("2-D Fourier transform", np.abs(spectrum)), ("Remove phase key 2", np.abs(unmasked)), ("Inverse Fourier transform", np.abs(partially_recovered)), ("Remove phase key 1 / recovered image", np.abs(unmasked_image))]
        StepsDialog("Decryption steps", steps, self).exec()
