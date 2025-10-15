#!/bin/bash

echo "开始打包 TTS_Tool..."

# 清理之前的构建文件
rm -rf dist build

echo "使用 PyInstaller 自动检测 spec 文件打包..."
pyinstaller --clean --noconfirm "TTS_Tool_auto.spec"

if [ $? -eq 0 ]; then
    echo "打包成功！可执行文件位于 dist 目录"
    echo "正在测试可执行文件..."
    cd dist
    ./TTS_Tool
else
    echo "打包失败！"
    exit 1
fi
