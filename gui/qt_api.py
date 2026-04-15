# -*- coding: utf-8 -*-
"""
Qt 抽象层：同一套 GUI 代码可在 PyQt6（新版 macOS）与 PyQt5（兼容 macOS 10.14+）下运行。

选择规则（按顺序）：
1. 环境变量 QT_USER_TOOLS_USE_PYQT5=1 / true / yes  → 强制 PyQt5
2. 环境变量 QT_USER_TOOLS_USE_PYQT5=0 / false / no → 强制 PyQt6
3. 否则：若能 import PyQt6 则用 PyQt6；否则回退 PyQt5

打包「旧版」时请在运行 PyInstaller 前 export QT_USER_TOOLS_USE_PYQT5=1，
并在 venv 中仅安装 requirements-legacy.txt，避免分析阶段误收集 Qt6。
"""

from __future__ import annotations

import os
from typing import Optional


def _env_truthy(name: str) -> Optional[bool]:
    v = os.environ.get(name, "").strip().lower()
    if v in ("1", "true", "yes", "on"):
        return True
    if v in ("0", "false", "no", "off"):
        return False
    return None


def _choose_pyqt5() -> bool:
    forced = _env_truthy("QT_USER_TOOLS_USE_PYQT5")
    if forced is True:
        return True
    if forced is False:
        return False
    try:
        import PyQt6  # noqa: F401

        return False
    except Exception:
        return True


USE_PYQT5: bool = _choose_pyqt5()

if USE_PYQT5:
    from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt5.QtGui import QClipboard, QFont, QGuiApplication, QIcon, QMouseEvent, QPixmap
    from PyQt5.QtWidgets import (
        QApplication,
        QDialog,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QStatusBar,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )

    ALIGN_CENTER = Qt.AlignCenter
    FONT_WEIGHT_BOLD = QFont.Bold
    POINTING_HAND_CURSOR = Qt.PointingHandCursor
    LEFT_MOUSE_BUTTON = Qt.LeftButton
    KEEP_ASPECT_RATIO = Qt.KeepAspectRatio
    SMOOTH_TRANSFORMATION = Qt.SmoothTransformation
    TOOLBUTTON_TEXT_ONLY = Qt.ToolButtonTextOnly
    ICON_WARNING = QMessageBox.Warning
    ICON_INFORMATION = QMessageBox.Information
    STD_YES = QMessageBox.Yes
    STD_NO = QMessageBox.No
    STD_YES_NO = QMessageBox.Yes | QMessageBox.No
    NO_EDIT_TRIGGERS = QTableWidget.NoEditTriggers
    SELECT_ROWS = QTableWidget.SelectRows
    HV_STRETCH = QHeaderView.Stretch
    HV_RESIZE_TO_CONTENTS = QHeaderView.ResizeToContents
    COLOR_GRAY_FOREGROUND = Qt.gray
else:
    from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
    from PyQt6.QtGui import QClipboard, QFont, QGuiApplication, QIcon, QMouseEvent, QPixmap
    from PyQt6.QtWidgets import (
        QApplication,
        QDialog,
        QFileDialog,
        QGridLayout,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QProgressBar,
        QPushButton,
        QScrollArea,
        QStatusBar,
        QTabWidget,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QToolButton,
        QVBoxLayout,
        QWidget,
    )

    ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter
    FONT_WEIGHT_BOLD = QFont.Weight.Bold
    POINTING_HAND_CURSOR = Qt.CursorShape.PointingHandCursor
    LEFT_MOUSE_BUTTON = Qt.MouseButton.LeftButton
    KEEP_ASPECT_RATIO = Qt.AspectRatioMode.KeepAspectRatio
    SMOOTH_TRANSFORMATION = Qt.TransformationMode.SmoothTransformation
    TOOLBUTTON_TEXT_ONLY = Qt.ToolButtonStyle.ToolButtonTextOnly
    ICON_WARNING = QMessageBox.Icon.Warning
    ICON_INFORMATION = QMessageBox.Icon.Information
    STD_YES = QMessageBox.StandardButton.Yes
    STD_NO = QMessageBox.StandardButton.No
    STD_YES_NO = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
    NO_EDIT_TRIGGERS = QTableWidget.EditTrigger.NoEditTriggers
    SELECT_ROWS = QTableWidget.SelectionBehavior.SelectRows
    HV_STRETCH = QHeaderView.ResizeMode.Stretch
    HV_RESIZE_TO_CONTENTS = QHeaderView.ResizeMode.ResizeToContents
    COLOR_GRAY_FOREGROUND = Qt.GlobalColor.gray
