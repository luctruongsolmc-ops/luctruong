@echo off
title Cloudflare Tunnel - Auto Reply
echo [%date% %time%] Khoi dong Cloudflare Tunnel...
echo.
echo ============================================================
echo  COPY URL HTTPS ben duoi roi cap nhat vao Facebook Webhook!
echo ============================================================
echo.
C:\Users\LUC\cloudflared.exe tunnel --url http://localhost:5000
