#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI应用测试脚本
用于验证基本功能是否正常
"""

import os
import sys

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入"""
    print("测试模块导入...")
    
    try:
        from gui import qt_api
        from gui.qt_api import QApplication

        print(f"✓ Qt 后端: {'PyQt5' if qt_api.USE_PYQT5 else 'PyQt6'}")
        assert QApplication is not None
    except ImportError as e:
        print(f"✗ Qt 导入失败: {e}")
        return False
    
    try:
        from gui.main_window import MainWindow
        print("✓ MainWindow导入成功")
    except ImportError as e:
        print(f"✗ MainWindow导入失败: {e}")
        return False
    
    try:
        from gui.problem_dialog import ProblemDialog
        print("✓ ProblemDialog导入成功")
    except ImportError as e:
        print(f"✗ ProblemDialog导入失败: {e}")
        return False
    
    try:
        from gui.info_dialog import InfoDialog
        print("✓ InfoDialog导入成功")
    except ImportError as e:
        print(f"✗ InfoDialog导入失败: {e}")
        return False
    
    try:
        from gui.hosts_viewer import HostsViewer
        print("✓ HostsViewer导入成功")
    except ImportError as e:
        print(f"✗ HostsViewer导入失败: {e}")
        return False
    
    try:
        from utils.system_info import SystemInfoCollector
        print("✓ SystemInfoCollector导入成功")
    except ImportError as e:
        print(f"✗ SystemInfoCollector导入失败: {e}")
        return False
    
    return True


def test_system_info():
    """测试系统信息收集"""
    print("\n测试系统信息收集...")
    
    try:
        from utils.system_info import SystemInfoCollector
        collector = SystemInfoCollector()
        
        # 测试各个收集函数
        sys_info = collector.get_system_info()
        print(f"✓ 系统信息: {sys_info.get('os', 'N/A')} {sys_info.get('version', 'N/A')}")
        
        browser_info = collector.get_browser_info()
        print(f"✓ 浏览器信息: {len(browser_info)} 个浏览器")
        
        network_info = collector.get_network_info()
        print(f"✓ 网络信息: 本机IP {network_info.get('local_ip', 'N/A')}")
        
        dns_info = collector.get_dns_info()
        print(f"✓ DNS信息: {len(dns_info.get('servers', []))} 个DNS服务器")
        
        hosts_info = collector.get_hosts_info()
        print(f"✓ Hosts信息: {hosts_info.get('binding_count', 0)} 个绑定")
        
        perm_info = collector.check_permissions()
        print(f"✓ 权限信息: 管理员权限 {'✓' if perm_info.get('admin') else '✗'}")
        
        return True
    except Exception as e:
        print(f"✗ 系统信息收集失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_tool_modules():
    """测试工具模块"""
    print("\n测试工具模块...")
    
    try:
        from hosts.check_hosts import check_hosts
        bindings = check_hosts()
        print(f"✓ Hosts检查: {len(bindings)} 个绑定")
    except Exception as e:
        print(f"✗ Hosts检查失败: {e}")
        return False
    
    try:
        from browser.clear_dns import clear_dns
        print("✓ DNS清除模块导入成功")
    except Exception as e:
        print(f"✗ DNS清除模块导入失败: {e}")
        return False
    
    return True


def main():
    """主测试函数"""
    print("=" * 60)
    print("千图网问题解决工具 - GUI测试")
    print("=" * 60)
    
    all_passed = True
    
    # 测试导入
    if not test_imports():
        all_passed = False
    
    # 测试系统信息
    if not test_system_info():
        all_passed = False
    
    # 测试工具模块
    if not test_tool_modules():
        all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✓ 所有测试通过！")
        print("\n可以运行应用: python gui/main.py")
    else:
        print("✗ 部分测试失败，请检查错误信息")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
