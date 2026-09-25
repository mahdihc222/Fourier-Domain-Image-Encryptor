"""Separate comparison window for the two supported encryption schemes."""
import time
import numpy as np
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from arnold_dct import encrypt as encrypt_arnold, decrypt as decrypt_arnold
from crypto import encrypt as encrypt_drpe, decrypt as decrypt_drpe, generate_phase_mask
from dwt_chaotic import encrypt as encrypt_dwt, decrypt as decrypt_dwt
from comparison_metrics import summarize


class ComparisonDialog(QDialog):
    """Run both schemes on the same image and show a metrics table."""

    def __init__(self, image, key1=None, key2=None, dwt_key="image-encryptor-dwt", parent=None):
        super().__init__(parent)
        self.image, self.key1, self.key2, self.dwt_key = image, key1, key2, dwt_key
        self.setWindowTitle("Scheme comparison")
        self.resize(760, 520)
        layout = QVBoxLayout(self)
        title = QLabel("Encryption scheme comparison")
        title.setObjectName("appTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels([
            "Metric", "Classic DRPE", "Arnold + DCT + diffusion", "DWT + chaotic permutation"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close)
        self._run()

    def _run(self):
        image_shape = self.image.shape[:2]
        key1 = self.key1 if self.key1 is not None else generate_phase_mask(image_shape, seed=1)
        key2 = self.key2 if self.key2 is not None else generate_phase_mask(image_shape, seed=2)
        started = time.perf_counter()
        drpe_cipher = encrypt_drpe(self.image, key1, key2)
        drpe_plain = decrypt_drpe(drpe_cipher, key1, key2)
        drpe = summarize(self.image, drpe_cipher, drpe_plain, time.perf_counter() - started)
        started = time.perf_counter()
        arnold_cipher, metadata = encrypt_arnold(self.image)
        arnold_plain = decrypt_arnold(arnold_cipher, metadata)
        arnold = summarize(self.image, arnold_cipher, arnold_plain, time.perf_counter() - started)
        started = time.perf_counter()
        dwt_cipher = encrypt_dwt(self.image, self.dwt_key)
        dwt_plain = decrypt_dwt(dwt_cipher, self.dwt_key)
        dwt = summarize(self.image, dwt_cipher, dwt_plain, time.perf_counter() - started)
        rows = [(name, drpe[name], arnold[name], dwt[name]) for name in ("MSE", "PSNR (dB)", "Entropy (bits/pixel)", "Correlation", "Runtime (ms)")]
        self.table.setRowCount(len(rows))
        for index, (name, first, second, third) in enumerate(rows):
            self.table.setItem(index, 0, QTableWidgetItem(name))
            self.table.setItem(index, 1, QTableWidgetItem(f"{first:.6f}"))
            self.table.setItem(index, 2, QTableWidgetItem(f"{second:.6f}"))
            self.table.setItem(index, 3, QTableWidgetItem(f"{third:.6f}"))
