#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用入口
启动应用，处理权限检查
"""

import os
import sys
import platform

from gui.qt_api import (
    QApplication,
    QMessageBox,
    QTimer,
    QIcon,
    ICON_WARNING,
    ICON_INFORMATION,
    STD_YES_NO,
    STD_YES,
)

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.main_window import MainWindow
from gui.problem_dialog import ProblemDialog
from gui.info_dialog import InfoDialog
from gui.hosts_viewer import HostsViewer

# 注意：工具箱功能模块改为延迟导入，只在需要时加载
# 这样可以加快启动速度


def check_permissions():
    """检查权限"""
    system = platform.system()
    
    if system == 'Windows':
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            is_admin = False
    else:
        is_admin = os.geteuid() == 0
    
    return is_admin


def show_permission_warning(app):
    """显示权限警告"""
    system = platform.system()
    
    if system == 'Windows':
        message = (
            "需要管理员权限才能修改hosts文件。\n\n"
            "请右键点击程序，选择\"以管理员身份运行\"。"
        )
    else:
        message = (
            "需要管理员权限才能修改hosts文件。\n\n"
            "请使用 sudo 运行此程序：\n"
            "sudo python gui/main.py"
        )
    
    msg = QMessageBox()
    msg.setIcon(ICON_WARNING)
    msg.setWindowTitle("权限提示")
    msg.setText(message)
    msg.setInformativeText(
        "注意：某些功能（如查看信息、检查配置）不需要管理员权限。\n"
        "但修复问题和修改hosts文件需要管理员权限。"
    )
    msg.exec()


def handle_tool_request(tool_type: str, main_window: MainWindow):
    """处理工具请求"""
    try:
        if tool_type == 'check_hosts':
            dialog = HostsViewer(main_window)
            dialog.exec()
        
        elif tool_type == 'clear_cache':
            # 延迟导入，只在需要时加载
            from browser.clear_cache import clear_all_browsers
            
            reply = QMessageBox.question(
                main_window,
                "确认清除",
                "清除浏览器缓存前请先关闭浏览器！\n\n确定要继续吗？",
                STD_YES_NO,
            )
            if reply == STD_YES:
                try:
                    clear_all_browsers(auto_fix=True)
                    QMessageBox.information(
                        main_window,
                        "成功",
                        "浏览器缓存已清除\n\n请重新打开浏览器。"
                    )
                except Exception as e:
                    QMessageBox.warning(main_window, "错误", f"清除失败: {str(e)}")
        
        elif tool_type == 'clear_dns':
            # 延迟导入，只在需要时加载
            from browser.clear_dns import clear_dns
            
            try:
                clear_dns()
                QMessageBox.information(
                    main_window,
                    "成功",
                    "DNS缓存已清除\n\n请刷新浏览器。"
                )
            except Exception as e:
                QMessageBox.warning(main_window, "错误", f"清除失败: {str(e)}")
        
        elif tool_type == 'check_browser':
            dialog = QMessageBox(main_window)
            dialog.setWindowTitle("浏览器版本检查")
            dialog.setIcon(ICON_INFORMATION)
            
            try:
                from browser.check_browser import check_all_browsers
                browsers = check_all_browsers()
                
                message = "浏览器版本信息：\n\n"
                for browser_name, info in browsers.items():
                    if info.get('installed'):
                        status = "✓ 兼容" if info.get('compatible') else "⚠ 需要升级"
                        message += f"{browser_name}: {info.get('version', 'N/A')} - {status}\n"
                    else:
                        message += f"{browser_name}: 未安装\n"
                
                dialog.setText(message)
                dialog.exec()
            except Exception as e:
                QMessageBox.warning(main_window, "错误", f"检查失败: {str(e)}")
        
        elif tool_type == 'check_download':
            # 延迟导入，只在需要时加载（虽然这里没有直接使用，但保持一致性）
            # from download.check_download import diagnose_download_issue
            
            QMessageBox.information(
                main_window,
                "诊断下载问题",
                "下载问题诊断功能\n\n"
                "请检查：\n"
                "1. 是否使用第三方下载工具（如迅雷）\n"
                "2. 浏览器是否开启云加速下载\n"
                "3. 网络连接是否正常\n\n"
                "建议使用浏览器自带下载功能。"
            )
        
    except Exception as e:
        QMessageBox.warning(main_window, "错误", f"操作失败: {str(e)}")


def main():
    """主函数"""
    # 创建应用
    app = QApplication(sys.argv)
    app.setApplicationName("千图网问题解决工具")
    app.setOrganizationName("千图网")
    
    # 设置应用图标（窗口/任务栏/Dock）
    try:
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_path = os.path.join(base_dir, 'resources', 'app_icon.png')
        if os.path.exists(icon_path):
            app.setWindowIcon(QIcon(icon_path))
    except Exception:
        # 图标设置失败不影响启动
        pass
    
    # 设置样式
    app.setStyle('Fusion')
    
    # 创建主窗口（先创建，再加载样式表，避免阻塞）
    main_window = MainWindow()
    
    # 延迟加载样式表，让窗口先显示
    def load_stylesheet():
        try:
            stylesheet_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'resources', 'styles.qss'
            )
            if os.path.exists(stylesheet_path):
                # 使用更快的读取方式
                with open(stylesheet_path, 'r', encoding='utf-8', errors='ignore') as f:
                    stylesheet = f.read()
                    app.setStyleSheet(stylesheet)
        except Exception as e:
            print(f"加载样式表失败: {e}")
    
    # 延迟加载样式表（窗口显示后）
    QTimer.singleShot(100, load_stylesheet)
    
    # 连接信号
    def on_problem_fix(problem_type: str):
        """处理问题修复请求"""
        dialog = ProblemDialog(problem_type, main_window)
        dialog.exec()
        # 修复后刷新状态
        main_window.update_status()
    
    def on_tool_request(tool_type: str):
        """处理工具请求"""
        handle_tool_request(tool_type, main_window)
    
    def on_info_collect():
        """处理信息收集请求"""
        dialog = InfoDialog(main_window)
        dialog.exec()
    
    main_window.problem_fix_requested.connect(on_problem_fix)
    main_window.tool_requested.connect(on_tool_request)
    main_window.info_collect_requested.connect(on_info_collect)
    
    # 立即显示主窗口（此时UI可能还在初始化，但窗口框架已显示）
    main_window.show()
    
    # 处理事件循环，确保窗口能立即显示
    app.processEvents()
    
    # 运行应用
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
