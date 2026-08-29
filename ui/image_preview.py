from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt


class ImagePreview(QLabel):
    """
    A QLabel subclass that displays an image scaled to fit its
    current size, always preserving aspect ratio, and re-scales
    automatically whenever the widget is resized (e.g. when the
    window grows).
    """

    def __init__(self, placeholder_text="No Image", parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._placeholder_text = placeholder_text

        self.setObjectName("imagePreview")
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(0, 0)
        self.setText(self._placeholder_text)

    def set_image(self, source):
        """
        Set the preview image.
        `source` can be a file path (str) or an existing QPixmap.
        """
        if isinstance(source, QPixmap):
            pixmap = source
        else:
            pixmap = QPixmap(source)

        if pixmap.isNull():
            self._pixmap = None
            self.setText(self._placeholder_text)
            return

        self._pixmap = pixmap
        self._update_scaled_pixmap()

    def clear_image(self):
        self._pixmap = None
        self.setText(self._placeholder_text)
        self.setPixmap(QPixmap())

    def _update_scaled_pixmap(self):
        if self._pixmap is None:
            return
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled)

    def resizeEvent(self, event):
        self._update_scaled_pixmap()
        super().resizeEvent(event)