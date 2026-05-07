"""
AList/OpenList Helper - 系统托盘图标管理
使用 pystray 实现系统托盘图标和右键菜单
兼容 alist 和 openlist（两者命令行接口一致）
"""

import threading
import webbrowser
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None

try:
    import pystray
    from pystray import MenuItem, Menu
except ImportError:
    pystray = None

# 兼容 PyInstaller 打包
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent.resolve()
else:
    APP_DIR = Path(__file__).parent.resolve()
ICON_FILE = APP_DIR / "icon.ico"


def create_icon_image(size=64, program_name="AList"):
    """动态生成托盘图标（如果没有 ico 文件），根据程序名称显示不同文字"""
    if Image is None:
        return None

    width = size
    height = size
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    dc = ImageDraw.Draw(image)

    # 根据程序类型选择不同颜色
    if "OpenList" in program_name:
        bg_color = (235, 119, 52, 240)    # 橙色
        border_color = (180, 80, 30, 255)
        text_content = "OL"
    else:
        bg_color = (52, 119, 235, 240)    # 蓝色
        border_color = (30, 80, 180, 255)
        text_content = "AL"

    # 画一个圆角矩形背景
    margin = 4
    dc.rounded_rectangle(
        [margin, margin, width - margin, height - margin],
        radius=12,
        fill=bg_color,
        outline=border_color,
        width=2,
    )

    # 画文字
    try:
        font_size = size // 3
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size)
        except Exception:
            font = ImageFont.load_default()

    text = text_content
    bbox = dc.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (width - text_w) / 2
    y = (height - text_h) / 2 - 2
    dc.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    return image


def get_icon(program_name="AList"):
    """获取托盘图标"""
    if ICON_FILE.exists():
        try:
            if Image is not None:
                return Image.open(ICON_FILE)
        except Exception:
            pass
    return create_icon_image(program_name=program_name)


_notification_icon = None


def show_notification(title, message):
    """显示气泡通知"""
    global _notification_icon
    if _notification_icon is not None:
        try:
            _notification_icon.notify(message, title)
        except Exception:
            pass


def run_tray(program_manager, auto_start_manager, config, on_quit=None):
    """运行系统托盘图标

    Args:
        program_manager: AListManager 实例（管理 alist 或 openlist）
        auto_start_manager: AutoStartManager 实例
        config: 配置字典
        on_quit: 退出回调
    """
    if pystray is None:
        print("错误: 需要安装 pystray 库 (pip install pystray)")
        return

    from openlist_helper import save_config

    prog_name = program_manager.program_name  # "AList" 或 "OpenList"

    def on_start(icon, item):
        if not program_manager.is_running:
            if program_manager.start():
                show_notification(f"{prog_name} Helper", f"{prog_name} 已启动")
            else:
                show_notification(f"{prog_name} Helper", f"{prog_name} 启动失败")

    def on_stop(icon, item):
        if program_manager.is_running:
            program_manager.stop()
            show_notification(f"{prog_name} Helper", f"{prog_name} 已停止")

    def on_restart(icon, item):
        program_manager.restart()
        show_notification(f"{prog_name} Helper", f"{prog_name} 已重启")

    def on_open_browser(icon, item):
        # AList/OpenList 默认端口为 5244，如果用户修改了端口需手动调整
        webbrowser.open("http://localhost:5244")

    def on_toggle_auto_start(icon, item):
        if auto_start_manager.is_auto_start_enabled():
            auto_start_manager.disable_auto_start()
            config["auto_start"] = False
            show_notification(f"{prog_name} Helper", "开机自启动已关闭")
        else:
            auto_start_manager.enable_auto_start()
            config["auto_start"] = True
            show_notification(f"{prog_name} Helper", "开机自启动已开启")
        save_config(config)

    def on_toggle_auto_restart(icon, item):
        config["auto_restart"] = not config.get("auto_restart", True)
        save_config(config)
        state = "开启" if config["auto_restart"] else "关闭"
        show_notification(f"{prog_name} Helper", f"自动重启已{state}")

    def on_toggle_silent(icon, item):
        config["silent_start"] = not config.get("silent_start", True)
        save_config(config)
        state = "开启" if config["silent_start"] else "关闭"
        show_notification(f"{prog_name} Helper", f"静默启动已{state}")

    def on_quit(icon, item):
        program_manager.stop()
        # 清除通知图标引用
        global _notification_icon
        _notification_icon = None
        icon.stop()
        if on_quit:
            on_quit()

    def get_status_text(icon, item):
        if program_manager.is_running:
            return "● 运行中"
        return "○ 已停止"

    # 构建菜单
    icon_image = get_icon(program_name=prog_name)

    menu = Menu(
        MenuItem(
            lambda item: get_status_text(None, None),
            Menu(
                MenuItem(f"启动 {prog_name}", on_start),
                MenuItem(f"停止 {prog_name}", on_stop),
                MenuItem(f"重启 {prog_name}", on_restart),
            )
        ),
        Menu.SEPARATOR,
        MenuItem("打开 Web 管理页面", on_open_browser),
        Menu.SEPARATOR,
        MenuItem(
            lambda item: "☑ 开机自启动" if auto_start_manager.is_auto_start_enabled() else "☐ 开机自启动",
            on_toggle_auto_start,
        ),
        MenuItem(
            lambda item: "☑ 自动重启" if config.get("auto_restart", True) else "☐ 自动重启",
            on_toggle_auto_restart,
        ),
        MenuItem(
            lambda item: "☑ 静默启动" if config.get("silent_start", True) else "☐ 静默启动",
            on_toggle_silent,
        ),
        Menu.SEPARATOR,
        MenuItem("退出", on_quit),
    )

    tray_title = f"{prog_name} Helper"
    icon = pystray.Icon("AListOpenListHelper", icon_image, tray_title, menu)
    global _notification_icon
    _notification_icon = icon

    # 在托盘图标准备好后自动启动程序
    def delayed_start():
        import time
        time.sleep(1)
        if config.get("auto_start_program", True):
            if not program_manager.is_running:
                program_manager.start()
                if config.get("silent_start", True):
                    show_notification(tray_title, f"{prog_name} 已静默启动")

    threading.Thread(target=delayed_start, daemon=True).start()

    icon.run()
