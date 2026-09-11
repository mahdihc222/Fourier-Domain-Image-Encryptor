"""Shared theme tokens keep the main window and dialogs consistent."""


def build_stylesheet(*, background, surface, canvas, text, muted, border, hover, accent_soft):
    return f"""
    QWidget {{
        color: {text};
        font-family: "Segoe UI";
        font-size: 13px;
    }}
    QMainWindow, QDialog {{ background: {background}; }}
    QLabel {{ background: transparent; }}
    QFrame#workflowCard {{
        background: {surface}; border: 1px solid {border}; border-radius: 14px;
    }}
    QLabel#appTitle {{ font-size: 28px; font-weight: 700; }}
    QLabel#appSubtitle {{ color: {muted}; font-size: 12px; }}
    QLabel#sectionTitle {{ font-size: 17px; font-weight: 600; }}
    QLabel#previewTitle {{ color: {muted}; font-size: 12px; font-weight: 600; }}
    QLabel#imagePreview {{
        background: {canvas}; border: 1px solid {border}; border-radius: 10px;
        color: {muted}; padding: 12px; font-size: 13px;
    }}
    QPushButton {{
        background: {surface}; border: 1px solid {border}; border-radius: 8px;
        padding: 9px 16px; font-weight: 600; min-height: 18px;
    }}
    QPushButton:hover {{ background: {hover}; border-color: #6485a3; }}
    QPushButton:pressed {{ background: {accent_soft}; }}
    QPushButton:focus {{ border: 1px solid #6485a3; }}
    QPushButton:disabled {{ color: {muted}; background: {canvas}; }}
    QPushButton#primaryAction {{
        background: #365f80; color: #ffffff; border: 1px solid #477394;
        padding: 12px 16px; font-size: 14px;
    }}
    QPushButton#primaryAction:hover {{ background: #426f91; }}
    QPushButton#primaryAction:pressed {{ background: #294a65; }}
    QPushButton#headerAction, QPushButton#closeAction {{ background: transparent; }}
    QPushButton#headerAction:hover, QPushButton#closeAction:hover {{ background: {hover}; }}
    QGroupBox {{
        background: {surface}; border: 1px solid {border}; border-radius: 10px;
        margin-top: 14px; padding: 12px; font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin; left: 12px; padding: 0 5px; color: {muted};
    }}
    QLabel#sectionSmall {{ padding: 4px 0; }}
    QLabel#statusLabel {{ color: {muted}; padding: 8px; }}
    QLabel#pipelineChip {{
        background: {canvas}; border: 1px solid {border}; border-radius: 8px;
        padding: 8px; font-weight: 600;
    }}
    QLabel#pipelineArrow {{ color: #6485a3; font-size: 18px; }}
    QToolTip {{ background: {surface}; color: {text}; border: 1px solid {border}; padding: 6px; }}
    """


MAIN_STYLESHEET = build_stylesheet(
    background="#191b1e", surface="#23262a", canvas="#1c1f22",
    text="#eceeef", muted="#a5abb2", border="#393e44",
    hover="#2c3238", accent_soft="#293b49",
)

LIGHT_STYLESHEET = build_stylesheet(
    background="#f0f1f2", surface="#ffffff", canvas="#f7f8f9",
    text="#282d32", muted="#66717b", border="#d7dce0",
    hover="#e9eef2", accent_soft="#dce6ee",
)
