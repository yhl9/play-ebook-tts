@echo off
echo 开始打包 TTS_Tool...

REM 清理之前的构建文件
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

echo 选择打包方式：
echo 1. 完整版本（包含 Piper TTS，可能有 DLL 问题）
echo 2. 稳定版本（不包含 Piper TTS，推荐）
set /p choice="请选择 (1 或 2): "

if "%choice%"=="1" (
    echo 使用完整版本打包...
    pyinstaller --clean --noconfirm "TTS_Tool_auto.spec"
) else (
    echo 使用稳定版本打包...
    pyinstaller --clean --noconfirm "TTS_Tool_no_piper.spec"
)

if %ERRORLEVEL% EQU 0 (
    echo 打包成功！可执行文件位于 dist 目录
    echo 正在测试可执行文件...
    cd dist
    TTS_Tool.exe
) else (
    echo 打包失败！
    pause
)
