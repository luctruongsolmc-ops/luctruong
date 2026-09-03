# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import pandas as pd
import json

xlsx = r'c:\Users\LUC\.gemini\antigravity\scratch\auto-reply-system\sanphamupdated\Danh_sach_100_san_pham_do_nam_full_size.xlsx'

# Doc tat ca sheets
all_sheets = pd.read_excel(xlsx, sheet_name=None)
print("=== SHEETS ===")
for name, df in all_sheets.items():
    print(f"Sheet: {name} | Shape: {df.shape}")
    print("Columns:", df.columns.tolist())
    print(df.head(3).to_string())
    print()

# Xuat toan bo du lieu ra JSON de xu ly
main_df = list(all_sheets.values())[0]
out = r'c:\Users\LUC\.gemini\antigravity\scratch\auto-reply-system\sanphamupdated\products_raw.json'
main_df.to_json(out, orient='records', force_ascii=False, indent=2)
print(f"\nDa xuat ra: {out}")
print(f"Tong so san pham: {len(main_df)}")
