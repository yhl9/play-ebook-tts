@echo off
REM 启动程序并抑制libpng警告
set QT_LOGGING_RULES="*=false"
set QT_SCALE_FACTOR=1
python main.py
