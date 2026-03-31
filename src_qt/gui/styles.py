"""Application-wide Qt stylesheet (dark, modern)."""

DARK_APPLICATION_STYLESHEET = """
QMainWindow, QWidget {
    background-color: #1a1d24;
    color: #e4e6eb;
    font-size: 13px;
}
QLabel {
    color: #c8ccd6;
    background: transparent;
}
QGroupBox {
    font-weight: 600;
    border: 1px solid #3a4150;
    border-radius: 10px;
    margin-top: 14px;
    padding: 12px 8px 8px 8px;
    background-color: #22262f;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    color: #8ab4ff;
}
QPushButton {
    background-color: #2f3644;
    color: #e8eaef;
    border: 1px solid #4a5263;
    border-radius: 8px;
    padding: 10px 14px;
    min-height: 22px;
}
QPushButton:hover {
    background-color: #3d4658;
    border-color: #5c677d;
}
QPushButton:pressed {
    background-color: #252a33;
}
QPushButton:disabled {
    color: #6d7380;
    background-color: #282c34;
}
QCheckBox {
    spacing: 10px;
    color: #d8dce6;
}
QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    border: 1px solid #4a5263;
    background-color: #2a2f3a;
}
QCheckBox::indicator:checked {
    background-color: #3d5a99;
    border-color: #6b8cce;
}
QSpinBox {
    background-color: #2a2f3a;
    color: #e8eaef;
    border: 1px solid #4a5263;
    border-radius: 6px;
    padding: 6px 8px;
    min-height: 22px;
}
QSpinBox::up-button, QSpinBox::down-button {
    width: 18px;
    background-color: #353b48;
    border-left: 1px solid #4a5263;
}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #454d5e;
}
"""
