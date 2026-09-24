"""Interactive wrong-key demonstration for both encryption schemes."""
import numpy as np
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QDoubleSpinBox, QGroupBox, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap

from ui.image_preview import ImagePreview
from crypto import decrypt as decrypt_drpe
from arnold_dct import decrypt as decrypt_arnold


class KeySensitivityDialog(QDialog):
    """Decrypt an existing cipher with a deliberately changed memory-only key."""

    def __init__(self, image, ciphertext, scheme, key1=None, key2=None,
                 metadata=None, diffusion_key="image-encryptor", parent=None):
        super().__init__(parent)
        self.image = None if image is None else np.asarray(image, dtype=float)
        self.ciphertext = ciphertext
        self.scheme = scheme
        self.key1 = key1
        self.key2 = key2
        self.metadata = metadata
        self.diffusion_key = diffusion_key
        self.changed_key1 = None
        self.changed_diffusion_key = None
        self.setWindowTitle("Key sensitivity demonstration")
        self.resize(640, 680)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Small key change demonstration")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        note = QLabel(
            "This window never loads or saves keys. It changes a copy of the active key "
            "and decrypts the current cipher with that copy."
        )
        note.setWordWrap(True)
        note.setObjectName("appSubtitle")
        layout.addWidget(note)

        controls = QGroupBox("Controlled key change")
        controls_layout = QVBoxLayout(controls)
        if self.scheme == "drpe":
            controls_layout.addWidget(QLabel("Keys to perturb:"))
            self.key_target = QComboBox()
            self.key_target.addItems(["Key 1", "Key 2", "Both keys"])
            self.key_target.setCurrentText("Both keys")
            controls_layout.addWidget(self.key_target)
            controls_layout.addWidget(QLabel("Maximum phase change per selected-key element (radians):"))
            self.amount = QDoubleSpinBox()
            self.amount.setRange(0.000001, np.pi)
            self.amount.setDecimals(6)
            self.amount.setSingleStep(0.001)
            self.amount.setValue(1.5)
            controls_layout.addWidget(self.amount)
            change_text = "Change phase key 1 and decrypt"
        else:
            controls_layout.addWidget(QLabel("Diffusion key: one-character change"))
            controls_layout.addWidget(QLabel(f"Original key: {self.diffusion_key}"))
            change_text = "Change diffusion key and decrypt"
        self.change_button = QPushButton(change_text)
        self.change_button.setObjectName("primaryAction")
        self.change_button.clicked.connect(self._decrypt_with_changed_key)
        controls_layout.addWidget(self.change_button)
        layout.addWidget(controls)

        self.status = QLabel("No changed-key decryption run yet")
        self.status.setObjectName("statusLabel")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        result_row = QHBoxLayout()
        self.original_preview = ImagePreview("Original unavailable")
        self.preview = ImagePreview("Changed-key result")
        for preview in (self.original_preview, self.preview):
            preview.setMinimumHeight(260)
            preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            result_row.addWidget(preview, 1)
        layout.addLayout(result_row, 1)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def _decrypt_with_changed_key(self):
        if self.scheme == "drpe":
            rng = np.random.default_rng(0)
            phase_noise = rng.uniform(
                -self.amount.value(), self.amount.value(), size=self.key1.shape
            )
            self.changed_key1 = self.key1.copy()
            self.changed_key2 = self.key2.copy()
            target = self.key_target.currentText()
            if target in ("Key 1", "Both keys"):
                self.changed_key1 *= np.exp(1j * phase_noise)
            if target in ("Key 2", "Both keys"):
                self.changed_key2 *= np.exp(1j * rng.uniform(
                    -self.amount.value(), self.amount.value(), size=self.key2.shape
                ))
            recovered = decrypt_drpe(self.ciphertext, self.changed_key1, self.changed_key2)
            change_description = f"{target} changed by at most {self.amount.value():.6f} rad per element"
        else:
            self.changed_diffusion_key = f"{self.diffusion_key}x"
            recovered = decrypt_arnold(
                self.ciphertext, self.metadata,
                diffusion_key=self.changed_diffusion_key,
            )
            change_description = "diffusion key changed by one character"
        if self.image is not None:
            self.original_preview.set_image(self._array_to_pixmap(self.image))
        self.preview.set_image(self._array_to_pixmap(recovered))
        if self.image is None:
            self.status.setText(f"Wrong-key result: {change_description}. Original image was not loaded, so comparison metrics are unavailable.")
            return
        if self.image.shape != recovered.shape:
            self.status.setText(
                f"Wrong-key result: {change_description}. The loaded plaintext shape "
                f"{self.image.shape} does not match the cipher result shape "
                f"{recovered.shape}, so comparison metrics are unavailable."
            )
            return
        mse = float(np.mean((self.image - recovered) ** 2))
        correlation = float(np.corrcoef(self.image.ravel(), recovered.ravel())[0, 1])
        self.status.setText(f"Wrong-key result: {change_description}. MSE: {mse:.6f}; correlation with original: {correlation:.6f}")

    @staticmethod
    def _array_to_pixmap(array):
        pixels = np.clip(np.asarray(array, dtype=float), 0.0, 1.0)
        pixels = np.rint(pixels * 255.0).astype(np.uint8)
        if pixels.ndim == 3:
            image = QImage(pixels.data, pixels.shape[1], pixels.shape[0], pixels.strides[0], QImage.Format_RGB888).copy()
        else:
            image = QImage(pixels.data, pixels.shape[1], pixels.shape[0], pixels.strides[0], QImage.Format_Grayscale8).copy()
        return QPixmap.fromImage(image)
