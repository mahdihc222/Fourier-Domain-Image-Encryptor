MAIN_STYLESHEET = """
QWidget {
    background-color: #1e1f26;
    color: #e6e6ec;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #1e1f26;
}

/* ---------- Group Boxes ---------- */
QGroupBox {
    border: None;
    border-radius: 4px;
    margin-top: 10px;
    padding: 6px 4px 4px 4px;
    background-color: #24252f;
    font-weight: 600;
    font-size: 12px;
    color: #a9abc9;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #8f92ff;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* ---------- Image Preview Labels ---------- */
QLabel#imagePreview {
    border: 2px dashed #3c3e57;
    border-radius: 5px;
    background-color: #191a22;
    color: #6a6d8c;
    font-size: 13px;
}

/* ---------- Titles ---------- */
QLabel#appTitle {
    font-size: 26px;
    font-weight: 800;
    color: #ffffff;
    padding: 4px 0px;
}

QLabel#appSubtitle {
    font-size: 13px;
    color: #8f92ff;
    font-weight: 500;
    padding-bottom: 6px;
}

QLabel#sectionSmall {
    color: #cfcfe6;
    font-size: 13px;
}

QLabel#statusLabel {
    color: #9a9cc0;
    font-style: italic;
    padding: 6px;
}

/* ---------- Buttons ---------- */
QPushButton {
    background-color: #2c2e3f;
    color: #e6e6ec;
    border: 1px solid #3c3e57;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #383a52;
    border: 1px solid #5457c9;
}

QPushButton:pressed {
    background-color: #23243a;
}

/* Primary action buttons (Encrypt / Decrypt) */
QPushButton#primaryAction {
    background-color: #5457c9;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    font-size: 14px;
    font-weight: 700;
    padding: 12px 18px;
}

QPushButton#primaryAction:hover {
    background-color: #6567e0;
}

QPushButton#primaryAction:pressed {
    background-color: #4547aa;
}

/* Secondary header buttons (Keys / Processing) */
QPushButton#headerAction {
    background-color: transparent;
    border: 1px solid #3c3e57;
    border-radius: 4px;
    color: #c7c9ff;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton#headerAction:hover {
    background-color: #2c2e3f;
    border: 1px solid #8f92ff;
}

/* Danger / close buttons */
QPushButton#closeAction {
    background-color: transparent;
    border: 1px solid #3c3e57;
    color: #a9abc9;
}

QPushButton#closeAction:hover {
    background-color: #3a2530;
    border: 1px solid #c96a6a;
    color: #ffb4b4;
}

/* ---------- Pipeline stage chips ---------- */
QLabel#pipelineChip {
    border: 1px solid #3c3e57;
    border-radius: 4px;
    background-color: #191a22;
    color: #c7c9ff;
    font-weight: 600;
    padding: 4px;
}

QLabel#pipelineArrow {
    color: #5457c9;
    font-size: 18px;
    font-weight: 700;
}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {
    background: #1e1f26;
    width: 10px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #3c3e57;
    border-radius: 3px;
    min-height: 20px;
}
QScrollBar::handle:vertical:hover {
    background: #5457c9;
}
"""


LIGHT_STYLESHEET = """
QWidget {
    background-color: #f4f5f9;
    color: #242634;
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
}

QMainWindow, QDialog {
    background-color: #f4f5f9;
}

/* ---------- Group Boxes ---------- */
QGroupBox {
    border: none;
    border-radius: 4px;
    margin-top: 10px;
    padding: 6px 4px 4px 4px;
    background-color: #ffffff;
    font-weight: 600;
    font-size: 12px;
    color: #5b6078;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 4px;
    color: #3f429f;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* ---------- Image Preview Labels ---------- */
QLabel#imagePreview {
    border: 2px dashed #b7bad1;
    border-radius: 5px;
    background-color: #f8f9fc;
    color: #7a7f99;
    font-size: 13px;
}

/* ---------- Titles ---------- */
QLabel#appTitle {
    font-size: 26px;
    font-weight: 800;
    color: #20222e;
    padding: 4px 0px;
}

QLabel#appSubtitle {
    font-size: 13px;
    color: #4548ad;
    font-weight: 500;
    padding-bottom: 6px;
}

QLabel#sectionSmall {
    color: #42465a;
    font-size: 13px;
}

QLabel#statusLabel {
    color: #686d86;
    font-style: italic;
    padding: 6px;
}

/* ---------- Buttons ---------- */
QPushButton {
    background-color: #ffffff;
    color: #292c3b;
    border: 1px solid #c9cbda;
    border-radius: 4px;
    padding: 8px 16px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #eeeefe;
    border: 1px solid #686be0;
}

QPushButton:pressed {
    background-color: #dedffc;
}

/* Primary action buttons (Encrypt / Decrypt) */
QPushButton#primaryAction {
    background-color: #5457c9;
    color: #ffffff;
    border: none;
    border-radius: 5px;
    font-size: 14px;
    font-weight: 700;
    padding: 12px 18px;
}

QPushButton#primaryAction:hover {
    background-color: #6567e0;
}

QPushButton#primaryAction:pressed {
    background-color: #4547aa;
}

/* Secondary header buttons (Keys / Processing / Theme) */
QPushButton#headerAction {
    background-color: transparent;
    border: 1px solid #bfc2d4;
    border-radius: 4px;
    color: #393c91;
    padding: 8px 14px;
    font-weight: 600;
}

QPushButton#headerAction:hover {
    background-color: #ececfa;
    border: 1px solid #686be0;
}

/* Danger / close buttons */
QPushButton#closeAction {
    background-color: transparent;
    border: 1px solid #c9cbda;
    color: #686d86;
}

QPushButton#closeAction:hover {
    background-color: #fff0f1;
    border: 1px solid #c85c67;
    color: #a43742;
}

/* ---------- Pipeline stage chips ---------- */
QLabel#pipelineChip {
    border: 1px solid #c9cbda;
    border-radius: 4px;
    background-color: #f8f9fc;
    color: #393c91;
    font-weight: 600;
    padding: 4px;
}

QLabel#pipelineArrow {
    color: #4548ad;
    font-size: 18px;
    font-weight: 700;
}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {
    background: #f0f1f6;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #bfc2d4;
    border-radius: 3px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #686be0;
}
"""
