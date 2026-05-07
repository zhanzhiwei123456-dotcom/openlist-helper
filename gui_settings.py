"""
AList/OpenList Helper - GUI 设置界面
使用 tkinter 实现图形化设置界面
兼容 alist 和 openlist（两者命令行接口一致）
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path


class SettingsWindow:
    """设置窗口"""

    def __init__(self, config, program_manager, auto_start_manager):
        self.config = config
        self.manager = program_manager
        self.auto_start = auto_start_manager
        self.root = None

    def show(self):
        """显示设置窗口"""
        if self.root is not None:
            try:
                self.root.lift()
                self.root.focus_force()
                return
            except Exception:
                pass

        self.root = tk.Tk()
        self.root.title("AList/OpenList Helper 设置")
        self.root.geometry("520x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f0f0")

        # 居中显示
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - 520) // 2
        y = (self.root.winfo_screenheight() - 600) // 2
        self.root.geometry(f"+{x}+{y}")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()

    def _build_ui(self):
        """构建界面"""
        from openlist_helper import save_config

        prog_name = self.manager.program_name

        # 标题区域
        title_frame = tk.Frame(self.root, bg="#2E75B6", height=60)
        title_frame.pack(fill="x")
        title_frame.pack_propagate(False)
        tk.Label(
            title_frame, text=f"⚙ {prog_name} Helper 设置",
            font=("Microsoft YaHei UI", 16, "bold"),
            bg="#2E75B6", fg="white"
        ).pack(pady=12)

        # 内容区域
        content = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=10)
        content.pack(fill="both", expand=True)

        # === 状态区域 ===
        status_frame = tk.LabelFrame(content, text=" 运行状态 ", font=("Microsoft YaHei UI", 10, "bold"),
                                      bg="#f0f0f0", padx=10, pady=8)
        status_frame.pack(fill="x", pady=(0, 10))

        self.status_var = tk.StringVar(value="检测中...")
        self._update_status()
        tk.Label(status_frame, textvariable=self.status_var, font=("Microsoft YaHei UI", 10),
                 bg="#f0f0f0").pack(anchor="w")

        btn_frame = tk.Frame(status_frame, bg="#f0f0f0")
        btn_frame.pack(fill="x", pady=(5, 0))

        self.start_btn = tk.Button(btn_frame, text="▶ 启动", width=10, command=self._on_start,
                                    bg="#4CAF50", fg="white", font=("Microsoft YaHei UI", 9))
        self.start_btn.pack(side="left", padx=(0, 5))

        self.stop_btn = tk.Button(btn_frame, text="⏹ 停止", width=10, command=self._on_stop,
                                   bg="#f44336", fg="white", font=("Microsoft YaHei UI", 9))
        self.stop_btn.pack(side="left", padx=(0, 5))

        self.restart_btn = tk.Button(btn_frame, text="🔄 重启", width=10, command=self._on_restart,
                                      bg="#FF9800", fg="white", font=("Microsoft YaHei UI", 9))
        self.restart_btn.pack(side="left")

        tk.Button(btn_frame, text="🌐 打开 Web", width=10, command=self._open_web,
                  bg="#2196F3", fg="white", font=("Microsoft YaHei UI", 9)).pack(side="right")

        # === 路径设置 ===
        path_frame = tk.LabelFrame(content, text=" 程序路径 ", font=("Microsoft YaHei UI", 10, "bold"),
                                    bg="#f0f0f0", padx=10, pady=8)
        path_frame.pack(fill="x", pady=(0, 10))

        path_row = tk.Frame(path_frame, bg="#f0f0f0")
        path_row.pack(fill="x")

        self.path_var = tk.StringVar(value=self.config["program_path"])
        tk.Entry(path_row, textvariable=self.path_var, font=("Consolas", 9), width=38).pack(
            side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(path_row, text="浏览...", command=self._browse_path,
                  font=("Microsoft YaHei UI", 9)).pack(side="right")

        tk.Label(path_frame, text="支持 alist.exe 或 openlist.exe", font=("Microsoft YaHei UI", 8),
                 bg="#f0f0f0", fg="gray").pack(anchor="w", pady=(4, 0))

        # === 启动参数 ===
        args_frame = tk.LabelFrame(content, text=" 启动参数 ", font=("Microsoft YaHei UI", 10, "bold"),
                                    bg="#f0f0f0", padx=10, pady=8)
        args_frame.pack(fill="x", pady=(0, 10))

        self.args_var = tk.StringVar(value=self.config.get("program_args", "server"))
        tk.Entry(args_frame, textvariable=self.args_var, font=("Consolas", 9)).pack(fill="x")
        tk.Label(args_frame, text="alist/openlist 通用: server (前台) | start (守护进程模式)", font=("Microsoft YaHei UI", 8),
                 bg="#f0f0f0", fg="gray").pack(anchor="w")

        # === 开关设置 ===
        toggle_frame = tk.LabelFrame(content, text=" 功能设置 ", font=("Microsoft YaHei UI", 10, "bold"),
                                      bg="#f0f0f0", padx=10, pady=8)
        toggle_frame.pack(fill="x", pady=(0, 10))

        self.auto_start_var = tk.BooleanVar(value=self.auto_start.is_auto_start_enabled())
        tk.Checkbutton(toggle_frame, text="开机自启动（注册到 Windows 启动项）",
                       variable=self.auto_start_var, font=("Microsoft YaHei UI", 10),
                       bg="#f0f0f0").pack(anchor="w", pady=2)

        self.auto_start_prog_var = tk.BooleanVar(value=self.config.get("auto_start_program", True))
        tk.Checkbutton(toggle_frame, text=f"程序启动时自动运行 {prog_name}",
                       variable=self.auto_start_prog_var, font=("Microsoft YaHei UI", 10),
                       bg="#f0f0f0").pack(anchor="w", pady=2)

        self.auto_restart_var = tk.BooleanVar(value=self.config.get("auto_restart", True))
        tk.Checkbutton(toggle_frame, text=f"{prog_name} 退出后自动重启",
                       variable=self.auto_restart_var, font=("Microsoft YaHei UI", 10),
                       bg="#f0f0f0").pack(anchor="w", pady=2)

        self.silent_var = tk.BooleanVar(value=self.config.get("silent_start", True))
        tk.Checkbutton(toggle_frame, text="静默启动（不显示控制台窗口）",
                       variable=self.silent_var, font=("Microsoft YaHei UI", 10),
                       bg="#f0f0f0").pack(anchor="w", pady=2)

        self.minimized_var = tk.BooleanVar(value=self.config.get("start_minimized", True))
        tk.Checkbutton(toggle_frame, text="启动时最小化到托盘",
                       variable=self.minimized_var, font=("Microsoft YaHei UI", 10),
                       bg="#f0f0f0").pack(anchor="w", pady=2)

        # === 底部按钮 ===
        bottom_frame = tk.Frame(self.root, bg="#f0f0f0", padx=20, pady=10)
        bottom_frame.pack(fill="x")

        tk.Button(bottom_frame, text="保存设置", width=15, command=self._save,
                  bg="#2E75B6", fg="white", font=("Microsoft YaHei UI", 10, "bold")).pack(side="left")
        tk.Button(bottom_frame, text="关闭", width=10, command=self._on_close,
                  font=("Microsoft YaHei UI", 10)).pack(side="right")

    def _update_status(self):
        """更新运行状态显示"""
        prog_name = self.manager.program_name
        if self.manager.is_running:
            self.status_var.set(f"● {prog_name} 正在运行")
        else:
            self.status_var.set(f"○ {prog_name} 已停止")

        if self.root:
            self.root.after(2000, self._update_status)

    def _on_start(self):
        if self.manager.start():
            self._update_status()
        else:
            messagebox.showerror("错误", f"启动 {self.manager.program_name} 失败，请检查路径是否正确")

    def _on_stop(self):
        self.manager.stop()
        self._update_status()

    def _on_restart(self):
        self.manager.restart()
        self._update_status()

    def _open_web(self):
        import webbrowser
        webbrowser.open("http://localhost:5244")

    def _browse_path(self):
        path = filedialog.askopenfilename(
            title="选择 AList 或 OpenList 可执行文件",
            filetypes=[
                ("AList/OpenList", "*.exe"),
                ("所有文件", "*.*")
            ],
            initialdir=str(Path(self.path_var.get()).parent) if Path(self.path_var.get()).exists() else str(Path.home())
        )
        if path:
            self.path_var.set(path)

    def _save(self):
        """保存设置"""
        from openlist_helper import save_config

        # 更新配置
        self.config["program_path"] = self.path_var.get()
        self.config["program_args"] = self.args_var.get()
        self.config["auto_start_program"] = self.auto_start_prog_var.get()
        self.config["auto_restart"] = self.auto_restart_var.get()
        self.config["silent_start"] = self.silent_var.get()
        self.config["start_minimized"] = self.minimized_var.get()

        save_config(self.config)

        # 更新注册表自启动
        if self.auto_start_var.get():
            self.auto_start.enable_auto_start()
        else:
            self.auto_start.disable_auto_start()

        messagebox.showinfo("成功", "设置已保存")

    def _on_close(self):
        self.root.destroy()
        self.root = None
