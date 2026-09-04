@echo off
chcp 65001 >nul
echo ======================================================
echo    TỰ ĐỘNG CẬP NHẬT SẢN PHẨM & ĐẨY LÊN CLOUD (RENDER)
echo ======================================================
echo.

echo [1/3] Đang đọc dữ liệu sản phẩm và tạo Knowledge Base...
python sanphamupdated/generate_kb.py
if %ERRORLEVEL% NEQ 0 (
    echo [LỖI] Không thể tạo dữ liệu sản phẩm. Vui lòng kiểm tra lại file Excel!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Đang lưu thay đổi vào Git...
C:\Users\LUC\mingit\cmd\git.exe add .
C:\Users\LUC\mingit\cmd\git.exe commit -m "Update products data: %date% %time%"

echo.
echo [3/3] Đang đẩy lên GitHub để Render tự động Deploy...
C:\Users\LUC\mingit\cmd\git.exe push origin main
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================
    echo  🎉 CẬP NHẬT THÀNH CÔNG!
    echo  Render đang tự động cập nhật sản phẩm mới lên Bot Cloud!
    echo ======================================================
) else (
    echo.
    echo [LỖI] Đẩy code lên GitHub thất bại. Kiểm tra kết nối mạng!
)

echo.
pause
