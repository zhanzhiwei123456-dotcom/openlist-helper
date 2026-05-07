@echo off
chcp 65001 >nul
title OpenList Helper 卸载

set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%.venv

echo ========================================
echo   OpenList Helper - 卸载
echo ========================================
echo.

echo [1/3] 取消开机自启动...
if exist "%VENV_DIR%\Scripts\python.exe" (
    "%VENV_DIR%\Scripts\python.exe" -c "import sys; sys.path.insert(0, r'%SCRIPT_DIR%'); from openlist_helper import AutoStartManager; AutoStartManager.disable_auto_start(); print('开机自启动已取消')"
) else (
    python -c "from openlist_helper import AutoStartManager; AutoStartManager.disable_auto_start(); print('开机自启动已取消')"
)

echo.
echo [2/3] 清理快捷方式...
if exist "%SCRIPT_DIR%OpenList Helper.lnk" (
    del "%SCRIPT_DIR%OpenList Helper.lnk"
    echo 快捷方式已删除
)

echo.
echo [3/3] 清理虚拟环境...
if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
    echo 虚拟环境已删除
)

echo.
echo ========================================
echo   卸载完成！
echo ========================================
echo.
echo 注意: 程序文件未删除，如需彻底删除请手动删除整个文件夹
echo.
pause
