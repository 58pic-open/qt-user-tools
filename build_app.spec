# -*- mode: python ; coding: utf-8 -*-
"""
macOS App Bundle 打包配置
生成 .app 格式的应用包
"""

import os

block_cipher = None

a = Analysis(
    ['gui/main.py'],
    pathex=[os.path.dirname(os.path.abspath(SPEC))],
    binaries=[],
    datas=[
        ('gui/resources', 'gui/resources'),
        ('config', 'config'),
        ('resources/app_icon.png', 'resources'),
        ('resources/images', 'resources/images'),  # 添加问题示例图片
    ],
    hiddenimports=[
        'hosts',
        'hosts.bind_hosts',
        'hosts.unbind_hosts',
        'hosts.check_hosts',
        'hosts.get_domain_ip',
        'browser',
        'browser.clear_cache',
        'browser.clear_dns',
        'browser.check_browser',
        'download',
        'download.check_download',
        'utils',
        'utils.system_info',
        'utils.elevate_permission',
        'gui.image_viewer',
        'bs4',
        'bs4.builder',
        'bs4.builder._htmlparser',
        'bs4.builder._lxml',
        'bs4.element',
        'bs4.formatter',
        'lxml',
        'lxml.etree',
        'lxml.html',
        'requests',
        'netifaces',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 避免在仅安装 PyQt6 的机器上误打入 PyQt5（若本机同时装了两者）
    excludes=[
        "PyQt5",
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "PyQt5.sip",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    [],
    name='千图网问题解决工具',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以指定 .icns 图标文件路径
    exclude_binaries=True,
)

# onedir 模式：避免 onefile 每次启动解包导致的“每次都慢”
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='千图网问题解决工具',
)

# 创建 macOS App Bundle
app = BUNDLE(
    coll,
    name='千图网问题解决工具.app',
    icon='resources/app_icon.icns',
    bundle_identifier='com.qiantu.troubleshooter',
    version='0.0.1',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '0.0.1',
        'CFBundleVersion': '0.0.1',
        'NSHumanReadableCopyright': 'Copyright © 2024 千图网',
        # Qt6 / PyQt6 官方 macOS 二进制通常以 Big Sur 为最低系统；写 10.13 会在旧系统上出现“要求版本”与无法启动的矛盾提示
        'LSMinimumSystemVersion': '11.0',
    },
)
