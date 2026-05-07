"""
AList/OpenList Helper - 主入口程序
自动识别 alist.exe 或 openlist.exe，提供开机自启动、系统托盘、进程管理等功能
"""

import sys
import logging
import argparse
import threading
from pathlib import Path

# 获取程序目录（兼容 PyInstaller 打包）
if getattr(sys, 'frozen', False):
    APP_DIR = Path(sys.executable).parent.resolve()
    _MEIPASS = Path(sys._MEIPASS)
else:
    APP_DIR = Path(__file__).parent.resolve()
    _MEIPASS = APP_DIR

# 确保 sys.path 包含两个关键目录
for p in [str(APP_DIR), str(_MEIPASS)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from openlist_helper import AListManager, AutoStartManager, load_config, save_config


def get_resource_path(filename):
    """获取资源文件路径（兼容 PyInstaller 打包）"""
    user_path = APP_DIR / filename
    if user_path.exists():
        return user_path
    packed_path = _MEIPASS / filename
    if packed_path.exists():
        return packed_path
    return user_path


def create_default_icon():
    """创建默认图标文件"""
    icon_path = APP_DIR / "icon.ico"
    if icon_path.exists():
        return

    # 尝试从内嵌资源复制
    packed_icon = _MEIPASS / "icon.ico"
    if packed_icon.exists():
        import shutil
        try:
            shutil.copy2(str(packed_icon), str(icon_path))
            return
        except Exception:
            pass

    try:
        from PIL import Image, ImageDraw, ImageFont

        size = 256
        image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        dc = ImageDraw.Draw(image)

        margin = 16
        dc.rounded_rectangle(
            [margin, margin, size - margin, size - margin],
            radius=40,
            fill=(52, 119, 235, 240),
            outline=(30, 80, 180, 255),
            width=4,
        )

        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 72)
        except Exception:
            font = ImageFont.load_default()

        text = "AL"
        bbox = dc.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x = (size - text_w) / 2
        y = (size - text_h) / 2 - 4
        dc.text((x, y), text, fill=(255, 255, 255, 255), font=font)

        image.save(str(icon_path), format="ICO",
                   sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    except ImportError:
        pass
    except Exception:
        pass


def main():
    # 设置错误日志（打包后便于排查问题）
    log_file = APP_DIR / "openlist_helper.log"
    try:
        logging.basicConfig(
            filename=str(log_file),
            level=logging.DEBUG,
            format='%(asctime)s %(levelname)s %(message)s',
            encoding='utf-8',
        )
        logging.info(f"程序启动, APP_DIR={APP_DIR}, _MEIPASS={_MEIPASS}")
        logging.info(f"sys.frozen={getattr(sys, 'frozen', False)}")
    except Exception:
        pass

    parser = argparse.ArgumentParser(description="AList/OpenList Helper - 开机自启动管理")
    parser.add_argument("--silent", action="store_true", help="静默启动（最小化到托盘）")
    parser.add_argument("--settings", action="store_true", help="直接打开设置窗口")
    args = parser.parse_args()

    # 加载配置
    config = load_config()

    # 创建图标（根据程序名称动态生成）
    # 需要先初始化管理器才能知道程序名
    # create_default_icon 在打包后不太需要，tray_icon 会动态生成
    # create_default_icon()

    # 初始化管理器（自动识别 alist 或 openlist）
    program_manager = AListManager(config)
    auto_start_manager = AutoStartManager()

    prog_name = program_manager.program_name
    print(f"检测到程序: {prog_name} ({program_manager.program_path})")

    logging.info(f"检测到程序: {prog_name} ({program_manager.program_path})")
    logging.info(f"program_path exists: {program_manager.program_path.exists()}")

    # 如果配置了开机自启动，同步注册表
    if config.get("auto_start") and not auto_start_manager.is_auto_start_enabled():
        auto_start_manager.enable_auto_start()

    # 静默启动模式 - 只启动托盘
    silent = args.silent or config.get("silent_start", True)

    if not silent or args.settings:
        # 非静默模式或显式请求设置 - 启动 GUI
        def run_gui():
            from gui_settings import SettingsWindow
            settings = SettingsWindow(config, program_manager, auto_start_manager)
            settings.show()

        if not silent:
            gui_thread = threading.Thread(target=run_gui, daemon=True)
            gui_thread.start()

    # 运行系统托盘
    try:
        from tray_icon import run_tray
        logging.info("tray_icon 导入成功，启动托盘...")
        run_tray(program_manager, auto_start_manager, config)
    except ImportError as e:
        print(f"错误: 缺少依赖库 - {e}")
        print("请运行: pip install pystray Pillow")
        logging.error(f"缺少依赖库: {e}")
        logging.error(f"sys.path: {sys.path}")
        print(f"\n降级模式: 仅启动 {prog_name}，无托盘图标")
        if config.get("auto_start_program", True):
            program_manager.start()
            print(f"{prog_name} 已启动（无托盘模式）")
            try:
                while True:
                    import time
                    time.sleep(1)
            except KeyboardInterrupt:
                program_manager.stop()
                print(f"{prog_name} 已停止")
    except Exception as e:
        print(f"托盘启动异常: {e}")
        logging.exception("托盘启动异常")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
