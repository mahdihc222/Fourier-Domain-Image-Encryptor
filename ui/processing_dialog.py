from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton
)
from PySide6.QtCore import Qt


class ProcessingDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Processing Details")
        self.resize(800, 640)
        self.load_ui()

    def load_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        title = QLabel("DRPE Pipeline")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Double Random Phase Encoding — signal flow")
        subtitle.setObjectName("appSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addWidget(self.build_pipeline_row([
            "Image", "K1", "2D CFT", "K2", "Inverse CFT", "Cipher"
        ]))

        layout.addWidget(self.build_stage_group(
            "Encryption",
            [
                "1.  f(x,y) × K₁(x,y)",
                "2.  2D Fourier Transform",
                "3.  F(u,v) × K₂(u,v)",
                "4.  Inverse 2D Fourier Transform",
            ],
        ))

        layout.addWidget(self.build_stage_group(
            "Decryption",
            [
                "1.  Cipher → 2D Fourier Transform",
                "2.  × K₂* (conjugate)",
                "3.  Inverse 2D Fourier Transform",
                "4.  × K₁* (conjugate) → Original",
            ],
        ))

        refresh_button = QPushButton("Refresh Preview")
        refresh_button.setObjectName("primaryAction")
        refresh_button.clicked.connect(self.refresh_preview)
        layout.addWidget(refresh_button)

        close_button = QPushButton("Close")
        close_button.setObjectName("closeAction")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    def build_pipeline_row(self, stage_names):
        container = QGroupBox("PIPELINE STAGES")
        row = QHBoxLayout(container)
        row.setSpacing(10)

        for i, name in enumerate(stage_names):
            box = QLabel(name)
            box.setObjectName("pipelineChip")
            box.setAlignment(Qt.AlignCenter)
            box.setMinimumSize(95, 55)
            row.addWidget(box)
            if i != len(stage_names) - 1:
                arrow = QLabel("→")
                arrow.setObjectName("pipelineArrow")
                arrow.setAlignment(Qt.AlignCenter)
                row.addWidget(arrow)

        return container

    def build_stage_group(self, title, lines):
        group = QGroupBox(title.upper())
        layout = QVBoxLayout(group)
        layout.setSpacing(6)
        for line in lines:
            label = QLabel(line)
            label.setObjectName("sectionSmall")
            layout.addWidget(label)
        return group

    def refresh_preview(self):
        raise NotImplementedError