"""Separate comparison window for the two supported encryption schemes."""
import time
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from arnold_dct import encrypt as encrypt_arnold, decrypt as decrypt_arnold
from crypto import encrypt as encrypt_drpe, decrypt as decrypt_drpe
from comparison_metrics import summarize


class ComparisonDialog(QDialog):
    """Run both schemes on the same image and show a metrics table."""

    def __init__(self, image, key1, key2, parent=None):
        super().__init__(parent)
        self.image, self.key1, self.key2 = image, key1, key2
        self.setWindowTitle("Scheme comparison")
        self.resize(760, 520)
        layout = QVBoxLayout(self)
        title = QLabel("Encryption scheme comparison")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Metric", "Classic DRPE", "Arnold + DCT + diffusion"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
        self._run()

    def _run(self):
        started = time.perf_counter()
        drpe_cipher = encrypt_drpe(self.image, self.key1, self.key2)
        drpe_plain = decrypt_drpe(drpe_cipher, self.key1, self.key2)
        drpe = summarize(self.image, drpe_cipher, drpe_plain, time.perf_counter() - started)
        started = time.perf_counter()
        arnold_cipher, metadata = encrypt_arnold(self.image)
        arnold_plain = decrypt_arnold(arnold_cipher, metadata)
        arnold = summarize(self.image, arnold_cipher, arnold_plain, time.perf_counter() - started)
        rows = [(name, drpe[name], arnold[name]) for name in ("MSE", "PSNR (dB)", "Entropy (bits/pixel)", "Correlation", "Runtime (ms)")]
        self.table.setRowCount(len(rows))
        for index, (name, first, second) in enumerate(rows):
            self.table.setItem(index, 0, QTableWidgetItem(name))
            self.table.setItem(index, 1, QTableWidgetItem(f"{first:.6f}"))
            self.table.setItem(index, 2, QTableWidgetItem(f"{second:.6f}"))
