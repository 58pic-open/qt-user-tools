#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限提升工具
类似SwitchHosts!，在需要时提示用户输入密码获取权限
"""

import os
import sys
import json
import base64
import platform
import subprocess
import tempfile
import shutil
import secrets
from typing import Tuple


def _windows_ps_encoded_command(script: str) -> str:
    """PowerShell -EncodedCommand 需要 UTF-16LE 的 Base64。"""
    return base64.b64encode(script.encode("utf-16le")).decode("ascii")


def _windows_run_elevated_powershell(inner_ps: str, timeout: int = 180) -> Tuple[bool, str]:
    """
    在管理员 PowerShell 中执行 inner_ps，并等待结束。
    不使用 sys.executable：PyInstaller 打包后 exe 再运行会拉起第二个 GUI，且 ShellExecuteW 不等待会导致临时脚本被删失败。
    """
    enc_inner = _windows_ps_encoded_command(inner_ps.strip() + "\r\n")
    outer_ps = (
        "$ErrorActionPreference='Stop';"
        f"$p=Start-Process -FilePath powershell.exe -Verb RunAs -PassThru -Wait "
        f"-ArgumentList @('-NoProfile','-NonInteractive','-WindowStyle','Hidden','-EncodedCommand','{enc_inner}');"
        "if ($null -eq $p) { exit 1 };"
        "exit $p.ExitCode"
    )
    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        r = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-WindowStyle",
                "Hidden",
                "-Command",
                outer_ps,
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=creationflags,
        )
        if r.returncode == 0:
            return True, ""
        msg = (r.stderr or "").strip() or (r.stdout or "").strip() or f"exit {r.returncode}"
        return False, msg
    except subprocess.TimeoutExpired:
        return False, "等待 UAC / 管理员操作超时（请确认已点「是」）"
    except Exception as e:
        return False, str(e)


def check_permission() -> bool:
    """检查当前是否有管理员权限"""
    system = platform.system()
    
    if system == 'Windows':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except:
            return False
    else:
        # macOS/Linux
        return os.geteuid() == 0


def elevate_copy_file(src_path: str, dst_path: str) -> Tuple[bool, str]:
    """
    使用提升的权限复制文件
    
    Args:
        src_path: 源文件路径
        dst_path: 目标文件路径
        
    Returns:
        (成功标志, 错误消息)
    """
    system = platform.system()
    
    if system == 'Windows':
        return _elevate_copy_windows(src_path, dst_path)
    else:
        return _elevate_copy_unix(src_path, dst_path)


def _elevate_copy_windows(src_path: str, dst_path: str) -> Tuple[bool, str]:
    """Windows：管理员 PowerShell 复制（避免用 exe 跑 .py 导致多窗口 / 未等待）。"""
    try:
        import ctypes

        if ctypes.windll.shell32.IsUserAnAdmin():
            shutil.copy2(src_path, dst_path)
            return True, ""

        s_lit = json.dumps(os.path.normpath(src_path), ensure_ascii=False)
        d_lit = json.dumps(os.path.normpath(dst_path), ensure_ascii=False)
        inner = (
            f"Copy-Item -LiteralPath {s_lit} -Destination {d_lit} -Force;"
            "if (-not (Test-Path -LiteralPath {0})) {{ exit 1 }}; exit 0".format(d_lit)
        )
        return _windows_run_elevated_powershell(inner)
    except Exception as e:
        return False, f"Windows权限提升失败: {str(e)}"


def _elevate_copy_unix(src_path: str, dst_path: str) -> Tuple[bool, str]:
    """macOS/Linux系统：使用sudo和osascript提示输入密码"""
    try:
        if platform.system() == 'Darwin':  # macOS
            # 转义路径中的特殊字符
            src_quoted = src_path.replace("'", "'\\''")
            dst_quoted = dst_path.replace("'", "'\\''")
            
            # 使用正确的 AppleScript 语法
            # 使用 with administrator privileges 会自动提示输入密码
            script = f'''
do shell script "cp '{src_quoted}' '{dst_quoted}'" with administrator privileges
'''
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, ""
            else:
                error_msg = result.stderr.strip()
                if "User canceled" in error_msg or "用户取消" in error_msg or "canceled" in error_msg.lower():
                    return False, "用户取消了密码输入"
                else:
                    return False, f"权限提升失败: {error_msg}"
        else:
            # Linux
            result = subprocess.run(
                ['sudo', 'cp', src_path, dst_path],
                input='',
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, ""
            else:
                return False, f"权限提升失败: {result.stderr.strip()}"
                
    except subprocess.TimeoutExpired:
        return False, "操作超时，请重试"
    except Exception as e:
        return False, f"权限提升失败: {str(e)}"


def elevate_write_file(file_path: str, content: str) -> Tuple[bool, str]:
    """
    使用提升的权限写入文件（类似SwitchHosts!）
    
    Args:
        file_path: 要写入的文件路径
        content: 文件内容（字符串）
        
    Returns:
        (成功标志, 错误消息)
    """
    system = platform.system()
    
    if system == 'Windows':
        return _elevate_write_windows(file_path, content)
    else:
        # macOS/Linux
        return _elevate_write_unix(file_path, content)


def _elevate_write_windows(file_path: str, content: str) -> Tuple[bool, str]:
    """Windows：先写入用户可写临时文件，再由管理员 PowerShell 覆盖系统 hosts（无命令行长度问题）。"""
    try:
        import ctypes

        if ctypes.windll.shell32.IsUserAnAdmin():
            with open(file_path, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)
            return True, ""

        tmp = os.path.join(
            tempfile.gettempdir(),
            f"qiantu_hosts_payload_{secrets.token_hex(8)}.tmp",
        )
        try:
            with open(tmp, "w", encoding="utf-8", newline="\n") as f:
                f.write(content)

            src_lit = json.dumps(os.path.normpath(tmp), ensure_ascii=False)
            dst_lit = json.dumps(os.path.normpath(file_path), ensure_ascii=False)
            inner = (
                f"$t = [System.IO.File]::ReadAllText({src_lit}, [System.Text.UTF8Encoding]::new($false));"
                f"[System.IO.File]::WriteAllText({dst_lit}, $t, [System.Text.UTF8Encoding]::new($false));"
                f"Remove-Item -LiteralPath {src_lit} -Force -ErrorAction SilentlyContinue;"
                f"exit 0"
            )
            ok, err = _windows_run_elevated_powershell(inner)
            return ok, err
        finally:
            try:
                if os.path.isfile(tmp):
                    os.unlink(tmp)
            except OSError:
                pass
    except Exception as e:
        return False, f"Windows权限提升失败: {str(e)}"


def _elevate_write_unix(file_path: str, content: str) -> Tuple[bool, str]:
    """macOS/Linux系统：使用sudo和osascript提示输入密码"""
    try:
        # 创建临时文件保存内容
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8')
        temp_file.write(content)
        temp_file.close()
        
        # 使用osascript（macOS）或sudo（Linux）来复制文件
        if platform.system() == 'Darwin':  # macOS
            # 转义路径中的特殊字符
            temp_file_quoted = temp_file.name.replace("'", "'\\''")
            file_path_quoted = file_path.replace("'", "'\\''")
            
            # 使用正确的 AppleScript 语法
            # 使用 with administrator privileges 会自动提示输入密码
            script = f'''
do shell script "cp '{temp_file_quoted}' '{file_path_quoted}'" with administrator privileges
'''
            
            # 执行AppleScript
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 清理临时文件
            cleanup_success = False
            try:
                os.unlink(temp_file.name)
                cleanup_success = True
            except:
                pass
            
            if result.returncode == 0:
                return True, ""
            else:
                error_msg = result.stderr.strip()
                if "User canceled" in error_msg or "用户取消" in error_msg or "canceled" in error_msg.lower():
                    return False, "用户取消了密码输入"
                else:
                    return False, f"权限提升失败: {error_msg}"
        else:
            # Linux系统：使用sudo
            result = subprocess.run(
                ['sudo', 'cp', temp_file.name, file_path],
                input='',  # 密码通过终端输入
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # 清理临时文件
            try:
                os.unlink(temp_file.name)
            except:
                pass
            
            if result.returncode == 0:
                return True, ""
            else:
                return False, f"权限提升失败: {result.stderr.strip()}"
                
    except subprocess.TimeoutExpired:
        return False, "操作超时，请重试"
    except Exception as e:
        # 清理临时文件
        try:
            os.unlink(temp_file.name)
        except:
            pass
        return False, f"权限提升失败: {str(e)}"


def elevate_execute_command(command: list) -> Tuple[bool, str, str]:
    """
    使用提升的权限执行命令
    
    Args:
        command: 命令列表（如 ['cp', 'src', 'dst']）
        
    Returns:
        (成功标志, 标准输出, 错误输出)
    """
    system = platform.system()
    
    if system == 'Windows':
        # Windows: 使用ShellExecuteW
        try:
            import ctypes
            if ctypes.windll.shell32.IsUserAnAdmin():
                # 已有权限，直接执行
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True
                )
                return result.returncode == 0, result.stdout, result.stderr
            else:
                # 需要提升权限（Windows下比较复杂，这里简化处理）
                return False, "", "需要管理员权限，请以管理员身份运行"
        except Exception as e:
            return False, "", str(e)
    else:
        # macOS/Linux: 使用sudo
        if platform.system() == 'Darwin':  # macOS
            # 使用osascript获取密码
            cmd_str = ' '.join(f"'{arg}'" for arg in command)
            script = f'''
tell application "System Events"
    set password to text returned of (display dialog "需要管理员权限" & return & return & "请输入您的密码：" default answer "" with hidden answer buttons {{"Cancel", "OK"}} default button "OK" with icon caution)
end tell
do shell script "{cmd_str}" password password with administrator privileges
'''
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True, result.stdout, ""
            else:
                error_msg = result.stderr.strip()
                if "User canceled" in error_msg:
                    return False, "", "用户取消了密码输入"
                else:
                    return False, "", error_msg
        else:
            # Linux
            result = subprocess.run(
                ['sudo'] + command,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.returncode == 0, result.stdout, result.stderr
