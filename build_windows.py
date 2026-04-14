#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows EXE 打包脚本
使用 PyInstaller 打包为 Windows 可执行文件
"""

import os
import sys
import shutil
from pathlib import Path

# 版本信息
VERSION = "0.0.1"
APP_NAME = "千图网问题解决工具"
APP_NAME_EN = "QiantuTroubleshooter"

def _force_utf8_console() -> None:
    """
    Windows CI/某些终端默认编码可能是 cp1252 / gbk，直接 print 中文会触发 UnicodeEncodeError。
    这里尽量把 stdout/stderr 切到 UTF-8，避免脚本在 CI 里崩溃。
    """
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def get_output_name(platform, format_type):
    """生成平台特定的文件名"""
    if platform == "windows":
        if format_type == "exe":
            return f"{APP_NAME_EN}_v{VERSION}_Windows-x64.exe"
        elif format_type == "zip":
            return f"{APP_NAME_EN}_v{VERSION}_Windows-x64.zip"
    return None

def main():
    _force_utf8_console()
    print("=" * 50)
    print("Windows EXE 打包脚本")
    print("=" * 50)
    print()
    
    # 检查 PyInstaller
    try:
        import PyInstaller
    except ImportError:
        print("✗ 未安装 PyInstaller")
        print("正在安装 PyInstaller...")
        os.system("pip install pyinstaller")
        import PyInstaller
    
    print("✓ PyInstaller 已安装")
    
    # 检查依赖
    print("\n检查依赖...")
    try:
        import PyQt6
        import bs4
        import requests
    except ImportError:
        print("⚠ 缺少依赖，正在安装...")
        os.system("pip install -r requirements.txt")
    
    print("✓ 依赖检查完成")
    
    # 创建 Windows spec 文件
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
# Windows 打包配置

import os

block_cipher = None

a = Analysis(
    ['gui/main.py'],
    pathex=[os.path.dirname(os.path.abspath(SPEC))],
    binaries=[],
    datas=[
        ('gui/resources', 'gui/resources'),
        ('config', 'config'),
        ('resources/images', 'resources/images'),
    ],
    hiddenimports=[
        'hosts', 'hosts.bind_hosts', 'hosts.unbind_hosts', 'hosts.check_hosts', 'hosts.get_domain_ip',
        'browser', 'browser.clear_cache', 'browser.clear_dns', 'browser.check_browser',
        'download', 'download.check_download',
        'utils', 'utils.system_info', 'utils.elevate_permission',
        'gui.image_viewer',
        'bs4', 'bs4.builder', 'bs4.builder._htmlparser', 'bs4.builder._lxml', 'bs4.element', 'bs4.formatter',
        'beautifulsoup4', 'lxml', 'lxml.etree', 'lxml.html',
        'requests', 'netifaces',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    spec_file = "build_windows_temp.spec"
    with open(spec_file, "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("\n开始打包...")
    
    # 运行 PyInstaller
    dist_dir = "dist/windows"
    build_dir = "build/windows"
    
    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)
    
    # 使用 subprocess 而不是 os.system 以获得更好的错误处理
    import subprocess
    cmd = ['pyinstaller', spec_file, 
           '--workpath', build_dir,
           '--distpath', dist_dir,
           '--clean', '--noconfirm']
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        # 打印输出以便调试
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        result_code = 0
    except subprocess.CalledProcessError as e:
        print(f"\n✗ PyInstaller 执行失败 (退出码: {e.returncode})")
        if e.stdout:
            print(f"标准输出:\n{e.stdout}")
        if e.stderr:
            print(f"错误输出:\n{e.stderr}")
        result_code = e.returncode
    except FileNotFoundError:
        print("\n✗ PyInstaller not found. Please install it with: pip install pyinstaller")
        result_code = 1
    
    # 清理临时文件
    if os.path.exists(spec_file):
        os.remove(spec_file)
    
    if result_code != 0:
        print("\n✗ 打包失败")
        sys.exit(1)
    
    # 重命名文件
    old_exe = os.path.join(dist_dir, f"{APP_NAME}.exe")
    new_exe_name = get_output_name("windows", "exe")
    new_exe = os.path.join(dist_dir, new_exe_name)
    
    if os.path.exists(old_exe):
        if os.path.exists(new_exe):
            os.remove(new_exe)
        os.rename(old_exe, new_exe)
        print(f"\n✓ EXE 已重命名: {new_exe}")
        
        # 创建 ZIP 压缩包
        import zipfile
        zip_name = get_output_name("windows", "zip")
        zip_path = os.path.join(dist_dir, zip_name)
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(new_exe, os.path.basename(new_exe))
            print(f"✓ ZIP 创建成功: {zip_path}")
        except Exception as e:
            print(f"⚠ ZIP 创建失败: {e}")
            zip_path = None
    else:
        print(f"\n⚠ 未找到生成的 EXE 文件: {old_exe}")
    
    print("\n" + "=" * 50)
    print("打包完成！")
    print("=" * 50)
    print(f"\n输出目录: {dist_dir}")
    
    # 检查并显示 EXE 文件
    if 'new_exe' in locals() and os.path.exists(new_exe):
        size = os.path.getsize(new_exe) / (1024 * 1024)
        print(f"EXE 文件: {new_exe_name} ({size:.1f} MB)")
    
    # 检查并显示 ZIP 文件
    if 'zip_path' in locals() and zip_path and os.path.exists(zip_path):
        size = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"ZIP 文件: {zip_name} ({size:.1f} MB)")

if __name__ == "__main__":
    main()
