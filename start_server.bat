@echo off
title Auto Reply System - Thoi Trang Hoa
cd /d "c:\Users\LUC\.gemini\antigravity\scratch\auto-reply-system"
echo [%date% %time%] Khoi dong Auto Reply System... >> logs\startup.log
python auto_start.py >> logs\startup.log 2>&1
