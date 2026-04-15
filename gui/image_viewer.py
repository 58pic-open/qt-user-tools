#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
图片查看器 - 点击图片放大查看
"""

from gui.qt_api import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QWidget,
    QPixmap,
    QMouseEvent,
    ALIGN_CENTER,
    POINTING_HAND_CURSOR,
    LEFT_MOUSE_BUTTON,
)


class ImageViewerDialog(QDialog):
    """图片查看对话框"""
    
    def __init__(self, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.original_pixmap = pixmap
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("查看图片")
        self.setMinimumSize(800, 600)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setAlignment(ALIGN_CENTER)
        
        # 图片标签
        img_label = QLabel()
        img_label.setPixmap(self.original_pixmap)
        img_label.setAlignment(ALIGN_CENTER)
        img_label.setStyleSheet("background-color: #f5f5f5; padding: 10px;")
        
        scroll_area.setWidget(img_label)
        layout.addWidget(scroll_area)
        
        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #1890ff;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 30px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #40a9ff;
            }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)


class ClickableImageLabel(QLabel):
    """可点击的图片标签"""
    
    def __init__(self, original_pixmap: QPixmap, thumbnail_pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.original_pixmap = original_pixmap
        self.thumbnail_pixmap = thumbnail_pixmap
        self.setPixmap(thumbnail_pixmap)
        self.setAlignment(ALIGN_CENTER)
        self.setStyleSheet("""
            QLabel {
                background-color: white;
                padding: 5px;
                border-radius: 4px;
                border: 2px solid #e0e0e0;
            }
            QLabel:hover {
                border-color: #1890ff;
                cursor: pointer;
            }
        """)
        self.setCursor(POINTING_HAND_CURSOR)
        self.setToolTip("点击查看大图")
    
    def mousePressEvent(self, event):
        """点击事件"""
        if event.button() == LEFT_MOUSE_BUTTON:
            viewer = ImageViewerDialog(self.original_pixmap, self.parent())
            viewer.exec()
