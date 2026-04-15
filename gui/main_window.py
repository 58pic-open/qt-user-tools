#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口
包含问题卡片网格、工具箱、状态栏
"""

import os
import sys
import platform

from gui.qt_api import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QStatusBar,
    QMessageBox,
    Qt,
    pyqtSignal,
    QTimer,
    QThread,
    QFont,
    QIcon,
    ALIGN_CENTER,
    FONT_WEIGHT_BOLD,
    POINTING_HAND_CURSOR,
    ICON_INFORMATION,
)

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.widgets.problem_card import ProblemCard

# 问题定义（从diagnose.py复用）
PROBLEMS = {
    'preview': {
        'title': '预览图问题',
        'description': '无法显示/加载慢',
    },
    'js': {
        'title': '样式问题',
        'description': '页面样式异常',
    },
    'icon': {
        'title': '主站样式',
        'description': '样式丢失',
    },
    'download': {
        'title': '下载问题',
        'description': '无法访问',
    },
    'cloud': {
        'title': '云设计问题',
        'description': '首页无法访问',
    },
    'unbind_preview': {
        'title': '卡片加载异常',
        'description': '显示标签但无内容',
    },
    'main_site': {
        'title': '主站打不开',
        'description': '网站无法访问',
    },
    'download_fail': {
        'title': '下载失败',
        'description': '网络错误/中断',
    },
    'safari_cache': {
        'title': 'Safari无法打开',
        'description': 'macOS Safari浏览器问题',
    },
}


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 定义信号
    problem_fix_requested = pyqtSignal(str)  # 问题修复请求
    tool_requested = pyqtSignal(str)  # 工具请求
    info_collect_requested = pyqtSignal()  # 信息收集请求
    
    def __init__(self):
        super().__init__()
        self.hosts_worker = None  # 保存线程引用，用于清理
        
        # 设置基本窗口属性
        self.setWindowTitle("千图网问题解决工具 V0.0.1")
        self.setMinimumSize(1000, 700)
        
        # 立即初始化UI（但状态更新延后）
        self.init_ui()
        
        # 延迟更新状态栏，让窗口先显示，提升启动速度
        # 分阶段更新：先显示窗口，再异步更新状态
        QTimer.singleShot(200, self.update_status_quick)  # 快速更新（延迟200ms，不阻塞）
        QTimer.singleShot(1500, self.update_status_async)  # 异步更新（后台线程，延迟更久）
    
    def init_ui(self):
        """初始化UI"""
        # 创建中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)  # 减少间距
        main_layout.setContentsMargins(20, 15, 20, 15)  # 减少上下边距
        
        # 标题
        title_label = QLabel("🎨 千图网问题解决工具")
        title_label.setFont(QFont("Arial", 20, FONT_WEIGHT_BOLD))
        title_label.setAlignment(ALIGN_CENTER)
        main_layout.addWidget(title_label)
        
        # 版本信息
        version_label = QLabel("V0.0.1")
        version_label.setFont(QFont("Arial", 10))
        version_label.setAlignment(ALIGN_CENTER)
        version_label.setStyleSheet("color: #666666; margin-top: -5px; margin-bottom: 5px;")  # 提高对比度
        main_layout.addWidget(version_label)
        
        # 问题卡片区域
        problems_label = QLabel("📋 常见问题快速修复")
        problems_label.setFont(QFont("Arial", 15, FONT_WEIGHT_BOLD))
        problems_label.setStyleSheet("color: #1a1a1a; margin-bottom: 8px;")  # 深色文字，提高对比度
        main_layout.addWidget(problems_label)
        
        # 问题卡片网格（延迟创建，避免阻塞启动）
        cards_layout = QGridLayout()
        cards_layout.setSpacing(12)  # 减少卡片间距
        
        # 先添加布局，卡片延迟创建
        main_layout.addLayout(cards_layout)
        
        # 延迟创建卡片，让窗口先显示
        QTimer.singleShot(50, lambda: self._create_problem_cards(cards_layout))
        
        # 工具箱
        tools_label = QLabel("🔧 工具箱")
        tools_label.setFont(QFont("Arial", 15, FONT_WEIGHT_BOLD))
        tools_label.setStyleSheet("color: #1a1a1a; margin-top: 10px; margin-bottom: 8px;")  # 深色文字，提高对比度
        main_layout.addWidget(tools_label)
        
        tools_layout = QHBoxLayout()
        tools_layout.setSpacing(10)
        
        tool_buttons = [
            ("📋 检查Hosts配置", "check_hosts"),
            ("🧹 清除浏览器缓存", "clear_cache"),
            ("🔄 清除DNS缓存", "clear_dns"),
            ("🌐 检查浏览器版本", "check_browser"),
            ("🔍 诊断下载问题", "check_download"),
            ("📊 一键获取系统信息", "collect_info"),
        ]
        
        for text, tool_type in tool_buttons:
            btn = QPushButton(text)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 10px 15px;
                    font-size: 13px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #1890ff;
                    color: white;
                    border-color: #1890ff;
                }
            """)
            btn.setCursor(POINTING_HAND_CURSOR)
            if tool_type == "collect_info":
                btn.clicked.connect(lambda: self.info_collect_requested.emit())
            else:
                btn.clicked.connect(lambda checked, t=tool_type: self.tool_requested.emit(t))
            tools_layout.addWidget(btn)
        
        main_layout.addLayout(tools_layout)
        
        # 状态栏
        status_widget = QWidget()
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(10, 5, 10, 5)
        
        self.status_system = QLabel()
        self.status_permission = QLabel()
        self.status_hosts = QLabel()
        self.status_version = QLabel("版本: V0.0.1")
        self.status_version.setStyleSheet("color: #999; font-size: 11px;")
        
        status_layout.addWidget(self.status_system)
        status_layout.addStretch()
        status_layout.addWidget(self.status_permission)
        status_layout.addStretch()
        status_layout.addWidget(self.status_hosts)
        status_layout.addStretch()
        status_layout.addWidget(self.status_version)
        
        status_widget.setLayout(status_layout)
        status_widget.setStyleSheet("""
            QWidget {
                background-color: #fafafa;
                border-radius: 8px;
                border: 1px solid #e0e0e0;
            }
            QLabel {
                color: #333333;
                font-size: 12px;
                font-weight: 500;
            }
        """)
        
        main_layout.addWidget(status_widget)
        
        central_widget.setLayout(main_layout)
    
    def _create_problem_cards(self, cards_layout: QGridLayout):
        """延迟创建问题卡片（在窗口显示后进行）"""
        problem_types = ['preview', 'js', 'icon', 'download', 'cloud', 'unbind_preview', 'main_site', 'safari_cache']
        row = 0
        col = 0
        for problem_type in problem_types:
            problem_info = PROBLEMS.get(problem_type, {})
            card = ProblemCard(
                problem_type=problem_type,
                title=problem_info.get('title', ''),
                description=problem_info.get('description', '')
            )
            card.fix_clicked.connect(self.on_problem_fix_clicked)
            cards_layout.addWidget(card, row, col)
            
            col += 1
            if col >= 3:
                col = 0
                row += 1
    
    def update_status_quick(self):
        """快速更新状态栏（同步操作，不阻塞）"""
        # 快速设置系统信息（不阻塞）
        system = platform.system()
        system_version = platform.release()
        self.status_system.setText(f"📊 系统: {system} {system_version}")
        
        # 检查权限（快速操作）
        try:
            if system == 'Windows':
                import ctypes
                is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                is_admin = os.geteuid() == 0
            
            if is_admin:
                self.status_permission.setText("权限: ✓ 已获取管理员权限")
                self.status_permission.setStyleSheet("color: #52c41a; font-weight: bold;")
            else:
                self.status_permission.setText("权限: ⚠ 需要管理员权限")
                self.status_permission.setStyleSheet("color: #fa8c16; font-weight: bold;")
        except Exception as e:
            self.status_permission.setText("权限: ? 未知")
            print(f"权限检查失败: {e}")  # 不阻塞，只打印日志
        
        # 先显示占位符，避免空白
        self.status_hosts.setText("已绑定域名: 检查中...")
    
    def update_status_async(self):
        """异步更新状态栏（后台线程执行，不阻塞UI）"""
        # 使用后台线程检查hosts，避免阻塞UI
        # 如果之前的线程还在运行，先清理
        if self.hosts_worker and self.hosts_worker.isRunning():
            self.hosts_worker.quit()
            self.hosts_worker.wait(1000)  # 等待最多1秒
        
        self.hosts_worker = HostsCheckWorker()
        self.hosts_worker.result_ready.connect(self.on_hosts_check_result)
        self.hosts_worker.finished.connect(self.on_hosts_worker_finished)  # 线程完成时清理
        self.hosts_worker.start()
    
    def on_hosts_worker_finished(self):
        """线程完成时的清理"""
        if self.hosts_worker:
            self.hosts_worker.deleteLater()
            self.hosts_worker = None
    
    def on_hosts_check_result(self, count: int):
        """接收hosts检查结果"""
        if count >= 0:
            self.status_hosts.setText(f"已绑定域名: {count}个")
        else:
            self.status_hosts.setText("已绑定域名: ?")
    
    def update_status(self):
        """兼容旧接口（保留向后兼容）"""
        self.update_status_quick()
        self.update_status_async()
    
    def on_problem_fix_clicked(self, problem_type: str):
        """处理问题修复点击"""
        self.problem_fix_requested.emit(problem_type)
    
    def show_message(self, title: str, message: str, icon=ICON_INFORMATION):
        """显示消息框"""
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.exec()
    
    def closeEvent(self, event):
        """窗口关闭事件：确保线程正确清理"""
        # 如果有后台线程在运行，等待其完成
        if self.hosts_worker and self.hosts_worker.isRunning():
            # 请求线程退出
            self.hosts_worker.quit()
            # 等待线程完成（最多等待2秒）
            if not self.hosts_worker.wait(2000):
                # 如果2秒内没有完成，强制终止（不推荐，但避免程序卡死）
                self.hosts_worker.terminate()
                self.hosts_worker.wait(1000)
            # 清理线程对象
            self.hosts_worker.deleteLater()
            self.hosts_worker = None
        
        # 接受关闭事件
        event.accept()


class HostsCheckWorker(QThread):
    """后台线程：检查hosts绑定（不阻塞主线程）"""
    result_ready = pyqtSignal(int)  # 传递绑定数量，-1表示错误
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._stop_requested = False
    
    def stop(self):
        """请求停止线程"""
        self._stop_requested = True
    
    def run(self):
        """在后台线程中执行"""
        try:
            if self._stop_requested:
                return
            
            sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            from hosts.check_hosts import check_hosts
            
            if self._stop_requested:
                return
            
            bindings = check_hosts()
            
            if self._stop_requested:
                return
            
            count = len(bindings)
            self.result_ready.emit(count)
        except Exception as e:
            if not self._stop_requested:
                print(f"hosts检查失败: {e}")  # 不阻塞，只打印日志
                self.result_ready.emit(-1)
