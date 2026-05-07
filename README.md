# AList/OpenList Helper

> 类似 [alisthelper](https://github.com/Xmarmalade/alisthelper) 的 AList / OpenList 开机自启动管理工具
> 自动识别 `alist.exe` 或 `openlist.exe`，无需手动配置

## 功能特性

- ✅ **自动识别** - 自动检测同目录下的 alist.exe 或 openlist.exe
- ✅ **开机自启动** - 注册到 Windows 启动项，开机自动运行
- ✅ **系统托盘** - 最小化到系统托盘，右键菜单操作
- ✅ **静默启动** - 无控制台窗口，后台静默运行
- ✅ **自动重启** - 检测到程序退出后自动重启（含防崩溃风暴保护）
- ✅ **进程管理** - 启动、停止、重启 AList/OpenList
- ✅ **图形化设置** - 可视化配置界面（tkinter）
- ✅ **Web 管理入口** - 一键打开 Web 管理页面
- ✅ **自定义启动参数** - 支持配置启动参数（安全过滤）
- ✅ **气泡通知** - 状态变化时弹出通知
- ✅ **区分显示** - AList 蓝色图标/菜单，OpenList 橙色图标/菜单

## 快速开始

### 1. 安装依赖

```bash
pip install pystray Pillow
```

或运行安装脚本：
```bash
install.bat
```

### 2. 启动程序

**静默模式（推荐日常使用）：**
```bash
python main.py --silent
```

**带设置界面：**
```bash
python main.py --settings
```

**直接运行：**
```bash
python main.py
```

### 3. 开机自启动

运行 `install.bat` 自动注册开机自启动，或手动在设置界面中勾选"开机自启动"。

## 项目结构

```
openlist-helper/
├── main.py              # 主入口程序
├── openlist_helper.py   # 核心逻辑（进程管理、自启动管理、安全过滤）
├── tray_icon.py         # 系统托盘图标（动态区分 AList/OpenList）
├── gui_settings.py      # GUI 设置界面
├── config.json          # 配置文件（自动生成）
├── requirements.txt     # Python 依赖
├── install.bat          # 安装脚本
└── uninstall.bat        # 卸载脚本
```

## 配置说明

`config.json` 配置项（首次运行自动生成）：

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `program_path` | alist/openlist 可执行文件路径（自动检测） | 自动检测 |
| `auto_start` | 开机自启动 | `true` |
| `silent_start` | 静默启动 | `true` |
| `start_minimized` | 启动时最小化 | `true` |
| `program_args` | 启动参数 | `"server"` |
| `auto_start_program` | 程序启动时自动运行 alist/openlist | `true` |
| `check_interval` | 进程检测间隔（秒） | `10` |
| `auto_restart` | 退出后自动重启 | `true` |

## 打包为 EXE

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name="OpenListHelper" main.py
```

## 安全特性

- **进程白名单**：只允许执行 `alist.exe` 或 `openlist.exe`，防止任意命令执行
- **参数过滤**：启动参数经过安全过滤，阻止 shell 注入字符
- **防崩溃风暴**：自动重启限制为 60 秒内最多 3 次，超出后停止并通知
- **优雅退出**：三步停止策略（stop 命令 → terminate → taskkill），确保无残留进程

## 与 alisthelper 对比

| 功能 | alisthelper | AList/OpenList Helper |
|------|:-----------:|:---------------:|
| 开机自启 | ✅ | ✅ |
| 静默启动 | ✅ | ✅ |
| 系统托盘 | ✅ | ✅ |
| 自动重启 | ❌ | ✅ |
| 图形界面 | ✅ (Flutter) | ✅ (tkinter) |
| 自定义参数 | ✅ | ✅ |
| 无需安装 | ❌ | ✅ |
| 自动识别 AList/OpenList | ❌ | ✅ |
| 技术栈 | Dart/Flutter | Python |

## License

MIT
