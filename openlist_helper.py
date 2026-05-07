"""
AList/OpenList Helper - 开机自启动管理程序
类似 alisthelper，为 alist.exe / openlist.exe 提供开机自启动、系统托盘、进程管理等功能
兼容 alist v3 和 openlist（两者命令行接口一致：server/start/stop/restart）
"""

import sys
import json
import subprocess
import threading
import time
from pathlib import Path

# 配置文件路径（兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent.resolve()
else:
    APP_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = APP_DIR / "config.json"
ICON_FILE = APP_DIR / "icon.ico"

def _detect_default_program_path():
    """自动检测默认程序路径（优先查找 EXE 同目录下的 alist.exe 或 openlist.exe）"""
    if getattr(sys, 'frozen', False):
        search_dir = Path(sys.executable).parent.resolve()
    else:
        search_dir = Path(__file__).parent.resolve()

    # 搜索同目录
    for name in ("alist.exe", "openlist.exe"):
        if (search_dir / name).exists():
            return str(search_dir / name)

    # 搜索上级目录（开发模式下源码在子目录）
    parent = search_dir.parent
    for name in ("alist.exe", "openlist.exe"):
        if (parent / name).exists():
            return str(parent / name)

    # 默认值（可能不存在，用户需在设置中配置）
    return str(search_dir / "alist.exe")


# 默认配置
DEFAULT_CONFIG = {
    "program_path": _detect_default_program_path(),
    "auto_start": True,           # 开机自启动
    "silent_start": True,         # 静默启动（最小化到托盘）
    "start_minimized": True,      # 启动时最小化
    "program_args": "server",     # 启动参数 (server 子命令，alist/openlist 通用)
    "auto_start_program": True,   # 程序启动时自动运行 alist/openlist
    "check_interval": 10,         # 进程检测间隔（秒）
    "auto_restart": True,         # alist/openlist 退出后自动重启
}

# 兼容旧配置（openlist_path → program_path）
_CONFIG_MIGRATION = {
    "openlist_path": "program_path",
    "openlist_args": "program_args",
    "auto_start_openlist": "auto_start_program",
}


def load_config():
    """加载配置文件"""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            # 迁移旧配置键名
            for old_key, new_key in _CONFIG_MIGRATION.items():
                if old_key in config and new_key not in config:
                    config[new_key] = config.pop(old_key)
            # 补充缺失的配置项
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
            return config
        except Exception:
            return DEFAULT_CONFIG.copy()
    return DEFAULT_CONFIG.copy()


def save_config(config):
    """保存配置文件"""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def get_program_name(exe_path):
    """根据可执行文件路径判断程序名称（alist / openlist）"""
    name = Path(exe_path).name.lower()
    if "alist" in name and "open" not in name:
        return "AList"
    elif "openlist" in name:
        return "OpenList"
    return "AList/OpenList"


class AListManager:
    """AList/OpenList 进程管理器（兼容两者，命令行接口一致）"""

    def __init__(self, config):
        self.config = config
        self.process = None
        self._running = False
        self._monitor_thread = None
        self._restart_count = 0
        self._last_restart_time = 0

    @property
    def program_path(self):
        return Path(self.config["program_path"])

    @property
    def program_name(self):
        return get_program_name(self.config["program_path"])

    @property
    def exe_name(self):
        return self.program_path.name.lower()

    @property
    def is_running(self):
        """检查 alist/openlist 是否正在运行（包括子进程和守护进程）"""
        # 先检查直接启动的子进程
        if self.process is not None and self.process.poll() is None:
            return True
        # 通过进程名检查守护进程模式
        try:
            result = subprocess.run(
                ["tasklist", "/FI", f"IMAGENAME eq {self.exe_name}"],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )
            return self.exe_name in result.stdout.lower()
        except Exception:
            # 查询超时或失败时，如果子进程存活则认为运行中
            return self.process is not None and self.process.poll() is None

    def start(self):
        """启动 alist/openlist 进程"""
        if self.is_running:
            # 如果是本程序启动的进程还在，直接返回
            if self.process is not None and self.process.poll() is None:
                return False
            # 否则是残留进程（之前的进程已丢失），先清理再启动
            try:
                subprocess.run(
                    ["taskkill", "/F", "/IM", self.exe_name],
                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5,
                )
                time.sleep(1)
            except Exception:
                pass

        exe_path = self.program_path
        if not exe_path.exists():
            print(f"错误: 程序路径不存在 - {exe_path}")
            return False

        # 安全检查：只允许执行 alist.exe 或 openlist.exe
        exe_name_lower = exe_path.name.lower()
        if exe_name_lower not in ("alist.exe", "openlist.exe"):
            print(f"错误: 不允许执行 {exe_path.name}，仅支持 alist.exe 或 openlist.exe")
            return False

        # alist/openlist 都使用 server 子命令启动服务
        args = self.config.get("program_args", "server").strip()
        cmd = [str(exe_path)]
        if args:
            # 安全过滤：只允许已知的安全子命令和参数
            safe_args = self._filter_safe_args(args)
            cmd.extend(safe_args)

        try:
            # CREATE_NO_WINDOW = 0x08000000, 隐藏控制台窗口
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 0  # SW_HIDE

            self.process = subprocess.Popen(
                cmd,
                cwd=str(exe_path.parent),
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._running = True
            self._start_monitor()
            return True
        except Exception as e:
            print(f"启动 {self.program_name} 失败: {e}")
            return False

    def stop(self):
        """停止 alist/openlist 进程"""
        self._running = False

        # 先通过 stop 命令优雅停止（alist/openlist 都支持）
        try:
            exe_path = self.program_path
            if exe_path.exists():
                subprocess.run(
                    [str(exe_path), "stop"],
                    cwd=str(exe_path.parent),
                    capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
                    timeout=5,
                )
        except Exception:
            pass

        # 再尝试直接终止子进程
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception:
                pass
        self.process = None

        # 最终确保：用 taskkill 强制杀死所有同名进程（处理子进程残留）
        try:
            subprocess.run(
                ["taskkill", "/F", "/IM", self.exe_name],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW,
                timeout=5,
            )
        except Exception:
            pass

    def restart(self):
        """重启 alist/openlist 进程"""
        self.stop()
        time.sleep(1)
        return self.start()

    @staticmethod
    def _filter_safe_args(args_str):
        """过滤启动参数，只允许已知的安全子命令和标志

        alist/openlist 支持的子命令: server, start, stop, restart, version, admin
        允许的标志: --data, --force-bin-dir, --no-prefix, -d 等
        禁止: 含有 |、;、&、$、`、>、< 等shell注入字符的参数
        """
        SAFE_SUBCOMMANDS = {
            "server", "start", "stop", "restart", "version", "admin",
            "help", "completion",
        }
        result = []
        parts = args_str.split()
        for part in parts:
            # 阻止 shell 注入字符
            if any(c in part for c in '|;&$`><\n\r'):
                print(f"警告: 启动参数包含不安全字符，已忽略: {part}")
                continue
            # 第一个参数必须是已知子命令
            if not result and part.lstrip("-") not in SAFE_SUBCOMMANDS and not part.startswith("-"):
                print(f"警告: 未知的子命令，已忽略: {part}")
                continue
            result.append(part)
        return result

    def _start_monitor(self):
        """启动进程监控线程"""
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._monitor_thread.start()

    def _monitor(self):
        """监控进程，如果退出则自动重启"""
        while self._running:
            if self.process and self.process.poll() is not None:
                # 进程已退出
                if self.config.get("auto_restart") and self._running:
                    # 防止重启风暴：60秒内最多重启3次
                    now = time.time()
                    if now - self._last_restart_time > 60:
                        self._restart_count = 0
                    self._restart_count += 1
                    self._last_restart_time = now

                    if self._restart_count > 3:
                        try:
                            from tray_icon import show_notification
                            show_notification(
                                f"{self.program_name} 重启失败",
                                f"{self.program_name} 短时间内多次崩溃，已停止自动重启，请检查配置"
                            )
                        except Exception:
                            pass
                        self._running = False
                        break

                    time.sleep(2)
                    if self._running:
                        self.start()
                        # 通知托盘（安全方式，避免循环导入）
                        try:
                            from tray_icon import show_notification
                            show_notification(f"{self.program_name} 已自动重启", "检测到进程退出，已自动重新启动")
                        except Exception:
                            pass
            time.sleep(self.config.get("check_interval", 10))


# 向后兼容的别名
OpenListManager = AListManager


class AutoStartManager:
    """Windows 开机自启动管理"""

    # 注册表路径
    REG_PATH = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
    REG_NAME = "AListOpenListHelper"

    @staticmethod
    def is_auto_start_enabled():
        """检查开机自启动是否已启用"""
        try:
            result = subprocess.run(
                ["reg", "query", AutoStartManager.REG_PATH, "/v", AutoStartManager.REG_NAME],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.returncode == 0
        except Exception:
            return False

    @staticmethod
    def enable_auto_start():
        """启用开机自启动"""
        try:
            if getattr(sys, 'frozen', False):
                # PyInstaller 打包后的 EXE
                exe_path = Path(sys.executable).resolve()
                cmd_path = f'"{exe_path}" --silent'
            else:
                # Python 脚本模式
                main_script = APP_DIR / "main.py"
                python_exe = sys.executable
                pythonw_exe = Path(python_exe).parent / "pythonw.exe"
                if pythonw_exe.exists():
                    cmd_path = f'"{pythonw_exe}" "{main_script}" --silent'
                else:
                    cmd_path = f'"{python_exe}" "{main_script}" --silent'

            subprocess.run(
                ["reg", "add", AutoStartManager.REG_PATH, "/v", AutoStartManager.REG_NAME,
                 "/t", "REG_SZ", "/d", cmd_path, "/f"],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except Exception as e:
            print(f"启用开机自启动失败: {e}")
            return False

    @staticmethod
    def disable_auto_start():
        """禁用开机自启动"""
        try:
            subprocess.run(
                ["reg", "delete", AutoStartManager.REG_PATH, "/v", AutoStartManager.REG_NAME, "/f"],
                capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            return True
        except Exception as e:
            print(f"禁用开机自启动失败: {e}")
            return False


if __name__ == "__main__":
    config = load_config()
    manager = AListManager(config)
    print(f"程序路径: {manager.program_path}")
    print(f"程序名称: {manager.program_name}")
    print(f"自启动状态: {AutoStartManager.is_auto_start_enabled()}")
