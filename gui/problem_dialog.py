#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
问题修复对话框
集成现有修复功能，显示进度
"""

import os
import sys
import platform
from typing import Optional
from gui.qt_api import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QTextEdit,
    QMessageBox,
    QScrollArea,
    QWidget,
    QToolButton,
    QTabWidget,
    QThread,
    pyqtSignal,
    QFont,
    QPixmap,
    ALIGN_CENTER,
    FONT_WEIGHT_BOLD,
    POINTING_HAND_CURSOR,
    TOOLBUTTON_TEXT_ONLY,
    KEEP_ASPECT_RATIO,
    SMOOTH_TRANSFORMATION,
    STD_YES_NO,
    STD_YES,
)

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.image_viewer import ClickableImageLabel

from hosts.bind_hosts import bind_by_problem, PROBLEM_DOMAINS
from hosts.unbind_hosts import unbind_domain
from hosts.get_domain_ip import get_domain_ip, get_domain_ip_with_source
from browser.clear_dns import clear_dns


# 问题图片映射（相对于resources/images目录）
PROBLEM_IMAGES = {
    'preview': ['preview_1.png', 'preview_2.png'],
    'js': ['js.png'],
    'icon': ['icon.png'],
    'download': ['download_1.png', 'download_2.png'],
    'cloud': ['cloud.png'],
    'unbind_preview': ['unbind_preview.jpeg'],
    'main_site': ['download_1.png'],  # 使用下载问题的图片作为示例
    'download_fail': ['download_fail_1.png'],
    'safari_cache': ['safari_cache_1.png', 'safari_cache_2.png'],  # Safari清除缓存示例图
}

# 问题描述映射
PROBLEM_DESCRIPTIONS = {
    'preview': {
        'title': '修复问题: 主站卡片预览图无法显示、加载慢',
        'description': '主站卡片预览图无法显示或加载缓慢，影响用户体验。通常是由于CDN节点访问异常导致的。',
        'solution': '需要绑定域名: preview.qiantucdn.com 到最优IP地址，以加速访问。',
    },
    'js': {
        'title': '修复问题: 下载页面样式乱了',
        'description': '下载页面样式显示异常，页面布局混乱，影响正常使用。',
        'solution': '需要绑定域名: js.qiantucdn.com 以加载正确的样式文件。',
    },
    'icon': {
        'title': '修复问题: 主站样式丢了',
        'description': '主站样式文件无法加载，页面显示异常。',
        'solution': '需要绑定域名: icon.qiantucdn.com 以加载图标和样式资源。',
    },
    'download': {
        'title': '修复问题: 下载页面显示无法访问网站',
        'description': '点击下载素材后，页面显示无法访问网站的错误提示。',
        'solution': '需要绑定域名: dl.58pic.com 到IP地址 47.104.5.133。',
    },
    'cloud': {
        'title': '修复问题: 云设计首页显示无法访问',
        'description': '云设计首页无法正常打开，显示访问错误。',
        'solution': '需要绑定域名: y.58pic.com 到IP地址 118.190.104.146。',
    },
    'unbind_preview': {
        'title': '修复问题: 千图首页面卡片无法加载但显示标签',
        'description': '首页卡片区域显示标签文字，但图片内容无法加载。',
        'solution': '需要解绑 preview.qiantucdn.com 域名。',
    },
    'main_site': {
        'title': '修复问题: 主站打不开',
        'description': '主站（www.58pic.com）或企业版（qiye.58pic.com）无法正常打开，显示无法访问网站的错误提示。',
        'solution': '需要绑定域名: www.58pic.com 和 qiye.58pic.com 到IP地址 47.104.159.75。',
    },
    'download_fail': {
        'title': '修复问题: 下载失败-网络错误、下载中断',
        'description': '素材下载时出现网络错误或下载中断的问题。',
        'solution': '需要绑定下载代理域名: proxy-rar.58pic.com, proxy-vip.58pic.com, proxy-vd.58pic.com',
    },
    'safari_cache': {
        'title': '修复问题: macOS Safari浏览器无法打开页面',
        'description': 'macOS系统使用Safari浏览器时，页面无法正常打开或显示异常。通常是由于浏览器缓存或Cookie数据导致的。',
        'solution': '需要清除Safari浏览器的缓存和数据，然后重启浏览器。',
    },
}

def _get_manual_steps(problem_type: str, system_override: Optional[str] = None) -> str:
    """
    生成“手动操作步骤”说明（根据系统切换）。

    注意：此处面向非技术同事，尽量做到可照抄、可转发给技术同事协助。
    """
    system = system_override or platform.system()

    def _how_to_open_cli_windows() -> str:
        return (
            "【如何打开 Windows 命令行】\n"
            "方法1：打开 CMD\n"
            "  1) 按 Win 键\n"
            "  2) 输入：cmd\n"
            "  3) 回车\n\n"
            "方法2：以管理员身份打开 CMD（推荐）\n"
            "  1) 按 Win 键\n"
            "  2) 输入：cmd\n"
            "  3) 右键“命令提示符” → 以管理员身份运行\n\n"
            "方法3：打开 PowerShell\n"
            "  1) 按 Win + X\n"
            "  2) 选择“终端/Windows PowerShell”\n"
        )

    def _how_to_open_terminal_macos() -> str:
        return (
            "【如何打开 macOS 终端】\n"
            "方法1：Spotlight\n"
            "  1) 按 ⌘ + 空格\n"
            "  2) 输入：终端（Terminal）\n"
            "  3) 回车\n\n"
            "方法2：Finder\n"
            "  应用程序 → 实用工具 → 终端\n"
        )

    def _dynamic_ip_howto(domain: str) -> str:
        return (
            "【先获取最优IP】\n"
            "方法A（推荐，最简单）：\n"
            f"  1) 打开 17ce.com\n  2) 选择 PING 测试\n  3) 输入域名：{domain}\n"
            "  4) 在结果里找“最快/延迟最低”的节点 IP（IPv4）\n\n"
            "方法B（你电脑有 Python 时）：\n"
            f"  在命令行执行：python hosts/get_domain_ip.py {domain}\n"
            "  复制输出的 IPv4 地址\n\n"
            "提示：有时本地 DNS 解析会失败，17ce 的结果更可靠。"
        )

    # 每个问题对应的“你要改什么”
    # 固定 IP 的直接写死，动态 IP 的提供“自己获取最优IP”的方法。
    domain_block = ""
    if problem_type == "preview":
        domain_block = (
            _dynamic_ip_howto("preview.qiantucdn.com")
            + "\n\n【要绑定】\n<上一步获取的IP>    preview.qiantucdn.com"
        )
    elif problem_type == "js":
        domain_block = (
            _dynamic_ip_howto("js.qiantucdn.com")
            + "\n\n【要绑定】\n<上一步获取的IP>    js.qiantucdn.com"
        )
    elif problem_type == "icon":
        domain_block = (
            _dynamic_ip_howto("icon.qiantucdn.com")
            + "\n\n【要绑定】\n<上一步获取的IP>    icon.qiantucdn.com"
        )
    elif problem_type == "download":
        domain_block = "【要绑定】\n47.104.5.133    dl.58pic.com"
    elif problem_type == "cloud":
        domain_block = "【要绑定】\n118.190.104.146    y.58pic.com"
    elif problem_type == "main_site":
        domain_block = "【要绑定】\n47.104.159.75    www.58pic.com\n47.104.159.75    qiye.58pic.com"
    elif problem_type == "download_fail":
        domain_block = (
            "【先获取最优IP（不需要技术同事）】\n"
            "建议依次对下面 3 个域名用 17ce.com 做 PING，分别拿到各自的最快 IPv4：\n"
            "  - proxy-rar.58pic.com\n  - proxy-vip.58pic.com\n  - proxy-vd.58pic.com\n\n"
            "（如果你只想先试一个：优先从 proxy-rar.58pic.com 开始）\n\n"
            "【要绑定】\n"
            "<对应域名获取的IP>    proxy-rar.58pic.com\n"
            "<对应域名获取的IP>    proxy-vip.58pic.com\n"
            "<对应域名获取的IP>    proxy-vd.58pic.com"
        )
    elif problem_type == "unbind_preview":
        domain_block = "【要解绑】\n从 hosts 文件中删除包含 preview.qiantucdn.com 的那一行（或在行首加 # 注释掉）。"
    else:
        domain_block = "（此问题类型暂无手动步骤）"

    common_after = (
        "\n\n【改完必须做】\n"
        "1) 清 DNS 缓存（让修改立即生效）\n"
        "2) 刷新页面（建议强制刷新）或完全退出浏览器重开\n"
        "3) 仍不生效：清浏览器缓存或重启电脑"
    )

    if system == "Windows":
        return (
            "手动操作步骤（Windows）\n\n"
            + _how_to_open_cli_windows()
            + "\n\n"
            "【1】找到 hosts 文件\n"
            "路径：C:\\Windows\\System32\\drivers\\etc\\hosts\n\n"
            "【2】用管理员权限编辑（推荐记事本）\n"
            "开始菜单搜索“记事本” → 右键 → 以管理员身份运行\n"
            "记事本：文件 → 打开 → 右下角文件类型选“所有文件(*.*)” → 打开 hosts\n\n"
            "【3】先备份\n"
            "把 hosts 另存一份，例如：hosts.backup\n\n"
            "【4】按本问题追加/删除内容\n"
            f"{domain_block}\n\n"
            "【5】保存\n"
            "Ctrl+S\n\n"
            "【6】清 DNS 缓存（管理员 CMD）\n"
            "ipconfig /flushdns"
            + common_after
        )

    if system == "Darwin":
        return (
            "手动操作步骤（macOS）\n\n"
            + _how_to_open_terminal_macos()
            + "\n\n"
            "【1】hosts 文件路径\n"
            "/etc/hosts\n\n"
            "【2】先备份（推荐）\n"
            "sudo cp /etc/hosts /etc/hosts.backup\n\n"
            "【3】用管理员权限编辑（nano 示例）\n"
            "sudo nano /etc/hosts\n\n"
            "【4】按本问题追加/删除内容\n"
            f"{domain_block}\n\n"
            "【5】保存并退出（nano）\n"
            "Ctrl+O 保存 → 回车确认 → Ctrl+X 退出\n\n"
            "【6】清 DNS 缓存\n"
            "sudo dscacheutil -flushcache\n"
            "sudo killall -HUP mDNSResponder"
            + common_after
        )

    # Linux/其他系统：给一个通用版
    return (
        "手动操作步骤（通用/Linux）\n\n"
        "【1】hosts 文件路径（常见）\n"
        "/etc/hosts\n\n"
        "【2】用管理员权限编辑\n"
        "sudo nano /etc/hosts\n\n"
        "【3】按本问题追加/删除内容\n"
        f"{domain_block}\n\n"
        "【4】清 DNS 缓存\n"
        "不同发行版命令不同，可先重启网络/重启电脑，或联系技术同事协助。"
        + common_after
    )


class FixWorker(QThread):
    """修复工作线程"""
    progress_updated = pyqtSignal(int, str)  # 进度百分比, 状态消息
    finished = pyqtSignal(bool, str)  # 成功, 消息
    
    def __init__(self, problem_type: str, auto_fix: bool = True):
        super().__init__()
        self.problem_type = problem_type
        self.auto_fix = auto_fix
    
    def run(self):
        """执行修复"""
        try:
            if self.problem_type == 'unbind_preview':
                # 解绑操作
                self.progress_updated.emit(25, "正在解绑域名...")
                success = unbind_domain('preview.qiantucdn.com', auto_fix=self.auto_fix)
                if success:
                    self.progress_updated.emit(75, "正在清除DNS缓存...")
                    clear_dns()
                    self.progress_updated.emit(100, "修复完成！")
                    self.finished.emit(True, "已成功解绑 preview.qiantucdn.com")
                else:
                    self.finished.emit(False, "解绑失败")
            elif self.problem_type == 'safari_cache':
                # Safari清除缓存引导（不需要实际执行，只显示引导）
                self.progress_updated.emit(100, "引导教程已显示")
                self.finished.emit(True, "请按照引导教程操作")
            else:
                # 绑定操作
                self.progress_updated.emit(10, "正在获取IP地址...")
                
                # 获取需要绑定的域名
                domains = PROBLEM_DOMAINS.get(self.problem_type, [])
                if not domains:
                    self.finished.emit(False, f"未知的问题类型: {self.problem_type}")
                    return
                
                # 获取IP（对于多个域名，获取第一个域名的IP作为参考显示）
                domain = domains[0]
                ip, source = get_domain_ip_with_source(domain, use_config=True)
                
                if not ip:
                    self.finished.emit(False, f"无法获取 {domain} 的IP地址")
                    return
                
                # 显示IP和来源（对于多域名问题，显示第一个域名的IP信息）
                source_text = ""
                if source == "17ce.com":
                    source_text = f"✓ 已从17ce.com获取最优IP: {ip}"
                    self.progress_updated.emit(30, f"已从17ce.com获取最优IP: {ip}")
                elif source == "配置文件":
                    source_text = f"✓ 已从配置文件获取IP: {ip}"
                    self.progress_updated.emit(30, f"已从配置文件获取IP: {ip}")
                elif source == "ip-api.com":
                    source_text = f"✓ 已从ip-api.com获取IP: {ip}"
                    self.progress_updated.emit(30, f"已从ip-api.com获取IP: {ip}")
                elif source == "ipapi.co":
                    source_text = f"✓ 已从ipapi.co获取IP: {ip}"
                    self.progress_updated.emit(30, f"已从ipapi.co获取IP: {ip}")
                elif source == "Ping测试":
                    source_text = f"✓ 已通过Ping测试获取IP: {ip}"
                    self.progress_updated.emit(30, f"已通过Ping测试获取IP: {ip}")
                else:
                    source_text = f"✓ 已通过DNS查询获取IP: {ip}"
                    self.progress_updated.emit(30, f"已通过DNS查询获取IP: {ip}")
                
                # 通过信号发送IP信息（需要在worker中处理）
                if len(domains) > 1:
                    # 多域名时显示所有域名
                    source_text += f" (将绑定 {len(domains)} 个域名)"
                self.progress_updated.emit(31, f"IP_INFO:{source_text}")
                self.progress_updated.emit(40, "正在备份hosts文件...")
                
                # 执行绑定（bind_by_problem会处理所有域名）
                self.progress_updated.emit(60, "正在修改hosts文件...")
                success = bind_by_problem(self.problem_type, auto_fix=self.auto_fix, use_config=True)
                
                if success:
                    self.progress_updated.emit(80, "正在清除DNS缓存...")
                    clear_dns()
                    self.progress_updated.emit(100, "修复完成！")
                    self.finished.emit(True, f"已成功绑定域名: {', '.join(domains)}")
                else:
                    self.finished.emit(False, "绑定失败")
                    
        except Exception as e:
            error_msg = str(e)
            # 如果是权限相关错误，提供更友好的提示
            if "权限" in error_msg or "permission" in error_msg.lower() or "用户取消" in error_msg:
                self.finished.emit(False, f"修复失败: {error_msg}\n\n提示: 如果取消了密码输入，请重试并输入密码。")
            else:
                self.finished.emit(False, f"修复过程中出错: {error_msg}")


class ProblemDialog(QDialog):
    """问题修复对话框"""
    
    def __init__(self, problem_type: str, parent=None):
        super().__init__(parent)
        self.problem_type = problem_type
        self.worker = None
        self.init_ui()
    
    def init_ui(self):
        """初始化UI"""
        problem_info = PROBLEM_DESCRIPTIONS.get(self.problem_type, {})
        
        self.setWindowTitle(problem_info.get('title', '修复问题'))
        self.setMinimumSize(600, 500)
        self.setMaximumSize(800, 900)
        
        # 创建主滚动区域（整个对话框可滚动）
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: white;
            }
        """)
        
        # 主内容容器
        content_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 问题描述
        desc_label = QLabel("📋 问题描述")
        desc_label.setFont(QFont("Arial", 12, FONT_WEIGHT_BOLD))
        layout.addWidget(desc_label)
        
        desc_text = QTextEdit()
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(80)
        desc_text.setText(problem_info.get('description', ''))
        desc_text.setStyleSheet("background-color: #f5f5f5; border-radius: 6px; padding: 10px;")
        layout.addWidget(desc_text)

        # 手动修复步骤（放在最靠上位置，避免用户看不到）
        if self.problem_type != 'safari_cache':
            manual_toggle_top = QToolButton()
            manual_toggle_top.setCheckable(True)
            manual_toggle_top.setChecked(True)  # 默认展开，确保用户能看到
            manual_toggle_top.setText("🧩 手动修复步骤（不用点“立即修复”也能自己改）")
            manual_toggle_top.setToolButtonStyle(TOOLBUTTON_TEXT_ONLY)
            manual_toggle_top.setCursor(POINTING_HAND_CURSOR)
            manual_toggle_top.setStyleSheet(
                "QToolButton { text-align: left; font-weight: bold; padding: 6px 4px; }"
                "QToolButton:hover { color: #1890ff; }"
            )
            layout.addWidget(manual_toggle_top)

            # Tab：允许切换查看其它系统的文档，默认是当前系统
            manual_tabs = QTabWidget()
            manual_tabs.setStyleSheet(
                "QTabWidget::pane { border: 0; }"
                "QTabBar::tab { padding: 8px 12px; border: 1px solid #e0e0e0; border-bottom: 0; "
                "border-top-left-radius: 8px; border-top-right-radius: 8px; background: #fafafa; }"
                "QTabBar::tab:selected { background: #ffffff; font-weight: bold; }"
            )

            def _make_manual_tab(text: str) -> QWidget:
                w = QWidget()
                v = QVBoxLayout()
                v.setContentsMargins(0, 0, 0, 0)
                te = QTextEdit()
                te.setReadOnly(True)
                te.setMinimumHeight(190)
                te.setMaximumHeight(300)
                te.setText(text)
                te.setStyleSheet("background-color: #f5f5f5; border-radius: 6px; padding: 12px; font-size: 12px;")
                v.addWidget(te)
                w.setLayout(v)
                # 便于 toggle 时统一隐藏
                w._manual_textedit = te  # type: ignore[attr-defined]
                return w

            win_tab = _make_manual_tab(_get_manual_steps(self.problem_type, system_override="Windows"))
            mac_tab = _make_manual_tab(_get_manual_steps(self.problem_type, system_override="Darwin"))
            linux_tab = _make_manual_tab(_get_manual_steps(self.problem_type, system_override="Linux"))

            manual_tabs.addTab(win_tab, "Windows")
            manual_tabs.addTab(mac_tab, "macOS")
            manual_tabs.addTab(linux_tab, "通用/Linux")

            current_system = platform.system()
            if current_system == "Windows":
                manual_tabs.setCurrentIndex(0)
            elif current_system == "Darwin":
                manual_tabs.setCurrentIndex(1)
            else:
                manual_tabs.setCurrentIndex(2)

            layout.addWidget(manual_tabs)

            def _toggle_manual_top(checked: bool):
                manual_tabs.setVisible(checked)
                manual_toggle_top.setText(
                    "🧩 手动修复步骤（不用点“立即修复”也能自己改）" if checked else "🧩 手动修复步骤（点我展开）"
                )

            manual_toggle_top.toggled.connect(_toggle_manual_top)
            _toggle_manual_top(True)
        
        # 问题示例图片（显示缩略图，点击可放大）
        images = PROBLEM_IMAGES.get(self.problem_type, [])
        if images and self.problem_type != 'safari_cache':  # Safari问题在引导教程中显示图片
            image_label = QLabel("🖼️ 问题示例（点击图片可放大查看）")
            image_label.setFont(QFont("Arial", 12, FONT_WEIGHT_BOLD))
            layout.addWidget(image_label)
            
            # 图片容器（不使用滚动，直接显示缩略图）
            images_widget = QWidget()
            images_layout = QVBoxLayout()
            images_layout.setSpacing(10)
            images_layout.setContentsMargins(0, 0, 0, 0)
            
            # 获取资源目录路径（支持打包后的路径）
            if getattr(sys, 'frozen', False):
                # 打包后的路径
                base_dir = sys._MEIPASS
            else:
                # 开发环境路径
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            images_dir = os.path.join(base_dir, 'resources', 'images')
            
            for img_file in images:
                img_path = os.path.join(images_dir, img_file)
                if os.path.exists(img_path):
                    original_pixmap = QPixmap(img_path)
                    if not original_pixmap.isNull():
                        # 创建缩略图（宽度200px）
                        thumbnail_pixmap = original_pixmap.scaled(
                            200, int(200 * original_pixmap.height() / original_pixmap.width()),
                            KEEP_ASPECT_RATIO,
                            SMOOTH_TRANSFORMATION
                        )
                        
                        # 使用可点击的图片标签
                        img_label = ClickableImageLabel(original_pixmap, thumbnail_pixmap)
                        images_layout.addWidget(img_label, alignment=ALIGN_CENTER)
            
            images_widget.setLayout(images_layout)
            layout.addWidget(images_widget)
        
        # 如果是Safari缓存问题，显示引导教程和图片
        if self.problem_type == 'safari_cache':
            # Safari清除缓存引导教程
            guide_label = QLabel("📖 操作步骤")
            guide_label.setFont(QFont("Arial", 12, FONT_WEIGHT_BOLD))
            layout.addWidget(guide_label)
            
            guide_text = QTextEdit()
            guide_text.setReadOnly(True)
            guide_text.setMaximumHeight(200)
            guide_text.setText(
                "清除 Safari 缓存与数据\n\n"
                "步骤 1: 打开 Safari 浏览器\n"
                "  在顶部菜单栏点击「Safari」\n\n"
                "步骤 2: 打开设置\n"
                "  点击「设置」（或按快捷键 ⌘,）\n\n"
                "步骤 3: 进入隐私设置\n"
                "  在设置窗口中，点击「隐私」标签页\n\n"
                "步骤 4: 管理网站数据\n"
                "  点击「管理网站数据...」按钮\n\n"
                "步骤 5: 搜索并移除58pic.com数据\n"
                "  • 在搜索框中输入: 58pic.com\n"
                "  • 找到 58pic.com 的条目（显示：缓存、Cookie 和本地储存空间）\n"
                "  • 点击「移除」按钮\n\n"
                "步骤 6: 完成并重启Safari\n"
                "  • 点击「完成」按钮关闭设置窗口\n"
                "  • 完全退出并重新打开 Safari 浏览器\n\n"
                "💡 提示: 如果问题仍然存在，可以点击「全部移除」清除所有网站数据"
            )
            guide_text.setStyleSheet("background-color: #f5f5f5; border-radius: 6px; padding: 15px; font-size: 13px;")
            layout.addWidget(guide_text)
            
            # Safari操作示例图片（显示缩略图，点击可放大）
            safari_images = PROBLEM_IMAGES.get('safari_cache', [])
            if safari_images:
                image_label = QLabel("🖼️ 操作示例（点击图片可放大查看）")
                image_label.setFont(QFont("Arial", 12, FONT_WEIGHT_BOLD))
                layout.addWidget(image_label)
                
                images_widget = QWidget()
                images_layout = QVBoxLayout()
                images_layout.setSpacing(10)
                images_layout.setContentsMargins(0, 0, 0, 0)
                
                # 获取资源目录路径（支持打包后的路径）
                if getattr(sys, 'frozen', False):
                    base_dir = sys._MEIPASS
                else:
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                images_dir = os.path.join(base_dir, 'resources', 'images')
                
                for img_file in safari_images:
                    img_path = os.path.join(images_dir, img_file)
                    if os.path.exists(img_path):
                        original_pixmap = QPixmap(img_path)
                        if not original_pixmap.isNull():
                            # 创建缩略图（宽度200px）
                            thumbnail_pixmap = original_pixmap.scaled(
                                200, int(200 * original_pixmap.height() / original_pixmap.width()),
                                KEEP_ASPECT_RATIO,
                                SMOOTH_TRANSFORMATION
                            )
                            
                            # 使用可点击的图片标签
                            img_label = ClickableImageLabel(original_pixmap, thumbnail_pixmap)
                            images_layout.addWidget(img_label, alignment=ALIGN_CENTER)
                
                images_widget.setLayout(images_layout)
                layout.addWidget(images_widget)
            
            # 重要提示
            warning_label = QLabel("⚠️ 重要提示")
            warning_label.setFont(QFont("Arial", 12, FONT_WEIGHT_BOLD))
            layout.addWidget(warning_label)
            
            warning_text = QTextEdit()
            warning_text.setReadOnly(True)
            warning_text.setMaximumHeight(80)
            warning_text.setText(
                "• 清除缓存后，您可能需要重新登录网站\n"
                "• 建议先关闭所有Safari窗口再进行操作\n"
                "• 操作完成后请重启Safari浏览器"
            )
            warning_text.setStyleSheet("background-color: #fff7e6; border-radius: 6px; padding: 10px;")
            layout.addWidget(warning_text)
        else:
            # 其他问题的正常显示
            # 解决方案
            solution_label = QLabel("🔧 解决方案")
            solution_label.setFont(QFont("Arial", 12, FONT_WEIGHT_BOLD))
            layout.addWidget(solution_label)
            
            solution_text = QTextEdit()
            solution_text.setReadOnly(True)
            solution_text.setMaximumHeight(60)
            solution_text.setText(problem_info.get('solution', ''))
            solution_text.setStyleSheet("background-color: #f5f5f5; border-radius: 6px; padding: 10px;")
            layout.addWidget(solution_text)

            # 进度区域
            progress_label = QLabel("🌐 修复进度")
            progress_label.setFont(QFont("Arial", 12, FONT_WEIGHT_BOLD))
            layout.addWidget(progress_label)
            
            self.progress_bar = QProgressBar()
            self.progress_bar.setMinimum(0)
            self.progress_bar.setMaximum(100)
            self.progress_bar.setValue(0)
            self.progress_bar.setStyleSheet("""
                QProgressBar {
                    border: 2px solid #e0e0e0;
                    border-radius: 8px;
                    text-align: center;
                    height: 25px;
                }
                QProgressBar::chunk {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 #1890ff, stop:1 #52c41a);
                    border-radius: 6px;
                }
            """)
            layout.addWidget(self.progress_bar)
            
            self.status_label = QLabel("等待开始...")
            self.status_label.setStyleSheet("color: #666; padding: 5px;")
            layout.addWidget(self.status_label)
            
            # IP信息显示（动态更新）
            self.ip_info_label = QLabel("")
            self.ip_info_label.setStyleSheet("color: #1890ff; font-weight: bold; padding: 5px;")
            self.ip_info_label.setVisible(False)
            layout.addWidget(self.ip_info_label)
            
            # 重要提示
            warning_label = QLabel("⚠️ 重要提示")
            warning_label.setFont(QFont("Arial", 12, FONT_WEIGHT_BOLD))
            layout.addWidget(warning_label)
            
            warning_text = QTextEdit()
            warning_text.setReadOnly(True)
            warning_text.setMaximumHeight(100)
            warning_text.setText(
                "• 此操作需要管理员权限\n"
                "• 将自动备份当前hosts文件\n"
                "• 修复后需要刷新浏览器才能生效"
            )
            warning_text.setStyleSheet("background-color: #fff7e6; border-radius: 6px; padding: 10px;")
            layout.addWidget(warning_text)
        
        # 设置内容容器的布局（不包含按钮）
        content_widget.setLayout(layout)
        
        # 将内容容器放入滚动区域
        main_scroll.setWidget(content_widget)
        
        # 创建按钮区域（固定在底部，不随内容滚动）
        button_widget = QWidget()
        button_widget.setStyleSheet("""
            QWidget {
                background-color: white;
                border-top: 1px solid #e0e0e0;
            }
        """)
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(20, 15, 20, 15)
        button_layout.setSpacing(10)
        
        if self.problem_type == 'safari_cache':
            # Safari问题只显示关闭按钮
            close_btn = QPushButton("我已了解")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1890ff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #40a9ff;
                }
            """)
            close_btn.clicked.connect(self.accept)
            button_layout.addStretch()
            button_layout.addWidget(close_btn)
        else:
            # 其他问题显示正常按钮
            preview_btn = QPushButton("预览修改")
            preview_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 2px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            preview_btn.clicked.connect(self.on_preview)
            button_layout.addWidget(preview_btn)
            
            self.fix_btn = QPushButton("立即修复")
            self.fix_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1890ff;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px 20px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #40a9ff;
                }
                QPushButton:disabled {
                    background-color: #d9d9d9;
                }
            """)
            self.fix_btn.clicked.connect(self.on_fix)
            button_layout.addWidget(self.fix_btn)
            
            cancel_btn = QPushButton("取消")
            cancel_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 2px solid #e0e0e0;
                    border-radius: 6px;
                    padding: 10px 20px;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
            cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(cancel_btn)
        
        button_widget.setLayout(button_layout)
        
        # 创建主布局（包含滚动区域和固定在底部的按钮）
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.addWidget(main_scroll, 1)  # 滚动区域占据剩余空间
        main_layout.addWidget(button_widget, 0)  # 按钮区域固定在底部，不拉伸
        
        self.setLayout(main_layout)
    
    def on_preview(self):
        """预览修改"""
        QMessageBox.information(
            self,
            "预览模式",
            "预览功能将在后续版本中实现。\n\n"
            "预览将显示将要修改的hosts文件内容。"
        )
    
    def on_fix(self):
        """开始修复"""
        if self.problem_type == 'safari_cache':
            # Safari问题不需要执行修复，直接返回
            return
        
        reply = QMessageBox.question(
            self,
            "确认修复",
            "确定要执行修复操作吗？\n\n"
            "此操作将修改hosts文件，需要管理员权限。",
            STD_YES_NO,
        )
        
        if reply == STD_YES:
            self.fix_btn.setEnabled(False)
            self.fix_btn.setText("修复中...")
            
            # 启动工作线程
            self.worker = FixWorker(self.problem_type, auto_fix=True)
            self.worker.progress_updated.connect(self.on_progress_updated)
            self.worker.finished.connect(self.on_fix_finished)
            self.worker.start()
    
    def on_progress_updated(self, value: int, message: str):
        """更新进度"""
        # 处理特殊消息（IP信息）
        if message.startswith("IP_INFO:"):
            ip_info = message.replace("IP_INFO:", "")
            self.ip_info_label.setText(ip_info)
            self.ip_info_label.setVisible(True)
            return
        
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def on_fix_finished(self, success: bool, message: str):
        """修复完成"""
        self.fix_btn.setEnabled(True)
        self.fix_btn.setText("立即修复")
        
        if success:
            QMessageBox.information(
                self,
                "修复成功",
                f"{message}\n\n"
                "提示: 请刷新浏览器或重启浏览器以使更改生效。"
            )
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "修复失败",
                message
            )
