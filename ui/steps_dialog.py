"""Scrollable viewer for the intermediate images of one operation."""
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QPushButton, QSizePolicy
from PySide6.QtCore import Qt

from ui.image_preview import ImagePreview
from PySide6.QtGui import QImage, QPixmap
import numpy as np


class StepsDialog(QDialog):
    """Display each named processing stage in a vertical scroll area."""

    def __init__(self, title, steps, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(760, 820)
        layout = QVBoxLayout(self)
        heading = QLabel(title)
        heading.setObjectName("appTitle")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        for name, array in steps:
            label = QLabel(name)
            label.setObjectName("sectionTitle")
            content_layout.addWidget(label)
            preview = ImagePreview("No stage image")
            preview.setMinimumHeight(220)
            preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            preview.set_image(self._array_to_pixmap(array))
            content_layout.addWidget(preview)
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    @staticmethod
    def _array_to_pixmap(array):
        values = np.abs(array) if np.iscomplexobj(array) else array
        values = np.asarray(values, dtype=float)
        if values.ndim == 3 and values.shape[2] == 3:
            pixels = np.clip(values / (values.max() or 1.0), 0.0, 1.0)
            pixels = np.rint(pixels * 255).astype(np.uint8)
            image = QImage(pixels.data, pixels.shape[1], pixels.shape[0], pixels.strides[0], QImage.Format_RGB888).copy()
        else:
            pixels = np.clip(values / (values.max() or 1.0), 0.0, 1.0)
            pixels = np.rint(pixels * 255).astype(np.uint8)
            image = QImage(pixels.data, pixels.shape[1], pixels.shape[0], pixels.strides[0], QImage.Format_Grayscale8).copy()
        return QPixmap.fromImage(image)
