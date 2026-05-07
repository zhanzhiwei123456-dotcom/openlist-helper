@echo off
chcp 65001 >nul
title OpenList Helper 安装

echo ========================================
echo   OpenList Helper - 安装
echo ========================================
echo.

set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%.venv

:: [1/4] 创建虚拟环境
echo [1/4] 创建虚拟环境...
if not exist "%VENV_DIR%\Scripts\python.exe" (
    python -m venv "%VENV_DIR%"
    echo 虚拟环境已创建
) else (
    echo 虚拟环境已存在，跳过
)

:: [2/4] 安装依赖包
echo.
echo [2/4] 安装依赖包...
"%VENV_DIR%\Scripts\pip.exe" install pystray Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple

:: [3/4] 创建快捷方式
echo.
echo [3/4] 创建快捷方式...
set VBS_FILE=%TEMP%\create_shortcut_olh.vbs

echo Set oWS = WScript.CreateObject("WScript.Shell") > "%VBS_FILE%"
echo sLinkFile = "%SCRIPT_DIR%OpenList Helper.lnk" >> "%VBS_FILE%"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%VBS_FILE%"
echo oLink.TargetPath = "%VENV_DIR%\Scripts\pythonw.exe" >> "%VBS_FILE%"
echo oLink.Arguments = """%SCRIPT_DIR%main.py"" --silent" >> "%VBS_FILE%"
echo oLink.WorkingDirectory = "%SCRIPT_DIR%" >> "%VBS_FILE%"
echo oLink.Description = "OpenList Helper - 开机自启动管理" >> "%VBS_FILE%"
echo oLink.IconLocation = "%SCRIPT_DIR%icon.ico,0" >> "%VBS_FILE%"
echo oLink.Save >> "%VBS_FILE%"

cscript //nologo "%VBS_FILE%"
del "%VBS_FILE%"
echo 快捷方式已创建

:: [4/4] 注册开机自启动
echo.
echo [4/4] 注册开机自启动...
"%VENV_DIR%\Scripts\python.exe" -c "import sys; sys.path.insert(0, r'%SCRIPT_DIR%'); from openlist_helper import AutoStartManager; AutoStartManager.enable_auto_start(); print('开机自启动已注册')"

echo.
echo ========================================
echo   安装完成！
echo ========================================
echo.
echo 使用方法:
echo   双击 "OpenList Helper.lnk" 启动程序
echo   或运行: python main.py --silent
echo.
echo 打开设置界面:
echo   运行: python main.py --settings
echo.
pause
