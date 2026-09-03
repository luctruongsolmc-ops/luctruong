# -*- coding: utf-8 -*-
import pandas as pd
import json
import os

xlsx_path = r'c:\Users\LUC\.gemini\antigravity\scratch\auto-reply-system\sanphamupdated\Danh_sach_100_san_pham_do_nam_full_size.xlsx'
df = pd.read_excel(xlsx_path, sheet_name='Danh sách sản phẩm')
summary_df = pd.read_excel(xlsx_path, sheet_name='Tổng hợp danh mục')

# 1. Tạo file JSON chi tiết cho hệ thống
unique_prods = []
grouped = df.groupby(['Mã SP', 'Danh mục', 'Tên sản phẩm', 'Đơn giá (VNĐ)'])
for (sp_id, cat, name, price), group in grouped:
    sizes = group['Size'].unique().tolist()
    colors = group['Màu sắc'].unique().tolist()
    unique_prods.append({
        'id': sp_id,
        'category': cat,
        'name': name,
        'price': int(price),
        'sizes': sizes,
        'colors': colors
    })

json_path = r'c:\Users\LUC\.gemini\antigravity\scratch\auto-reply-system\knowledge-base\products.json'
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump(unique_prods, f, ensure_ascii=False, indent=2)

# 2. Tạo Markdown Knowledge Base hoàn chỉnh
md_lines = []
md_lines.append("# Knowledge Base – Shop đồ Nam\n")
md_lines.append("## Thông tin shop\n")
md_lines.append("- **Tên shop**: Shop đồ Nam")
md_lines.append("- **Ngành hàng**: Thời trang nam (Áo thun, sơ mi, polo, khoác, hoodie, quần jeans, kaki, tây, short, đồ thể thao, đồ mặc nhà)")
md_lines.append("- **Hotline**: 0832 717 850")
md_lines.append("- **Giờ làm việc**: 8:00 - 21:00 (T2 - CN)")
md_lines.append("- **Khoảng giá chung**: 99.000đ - 459.000đ")
md_lines.append("- **Size**: S, M, L, XL, XXL (Full size cho mọi vóc dáng từ 50kg - 90kg)")
md_lines.append("- **Chính sách đổi trả**: 7 ngày kể từ ngày nhận hàng\n")

md_lines.append("## Bảng tổng hợp danh mục sản phẩm\n")
md_lines.append("| Danh mục | Số mẫu SP | Khoảng giá | Size | Màu sắc chủ đạo |")
md_lines.append("|---|---|---|---|---|")

cat_grouped = {}
for item in unique_prods:
    cat = item['category']
    if cat not in cat_grouped:
        cat_grouped[cat] = []
    cat_grouped[cat].append(item)

for _, row in summary_df.iterrows():
    cat = row['Danh mục']
    count = int(row['Số_sản_phẩm'])
    min_p = f"{int(row['Giá_thấp_nhất']):,}đ"
    max_p = f"{int(row['Giá_cao_nhất']):,}đ"
    md_lines.append(f"| **{cat}** | {count} mẫu | {min_p} - {max_p} | S, M, L, XL, XXL | Đen, Trắng, Xám, Navy, Be, Nâu... |")

md_lines.append("\n## Chi tiết 100 sản phẩm theo từng danh mục\n")

for cat, items in sorted(cat_grouped.items()):
    md_lines.append(f"### {cat} ({len(items)} mẫu)\n")
    md_lines.append("| Mã SP | Tên sản phẩm | Đơn giá | Size | Màu sắc |")
    md_lines.append("|---|---|---|---|---|")
    for it in sorted(items, key=lambda x: x['id']):
        colors_str = ", ".join(it['colors'])
        sizes_str = ", ".join(it['sizes'])
        price_str = f"{it['price']:,}đ"
        md_lines.append(f"| {it['id']} | **{it['name']}** | {price_str} | {sizes_str} | {colors_str} |")
    md_lines.append("")

md_lines.append("## Hướng dẫn chọn Size đồ nam\n")
md_lines.append("| Size | Chiều cao (cm) | Cân nặng (kg) | Vòng ngực (cm) | Vòng bụng (cm) |")
md_lines.append("|---|---|---|---|---|")
md_lines.append("| **S** | 160 - 165 | 50 - 58 kg | 86 - 90 | 72 - 76 |")
md_lines.append("| **M** | 165 - 170 | 59 - 66 kg | 91 - 95 | 77 - 81 |")
md_lines.append("| **L** | 170 - 175 | 67 - 74 kg | 96 - 100 | 82 - 86 |")
md_lines.append("| **XL** | 175 - 180 | 75 - 82 kg | 101 - 106 | 87 - 92 |")
md_lines.append("| **XXL** | 180 - 188 | 83 - 90+ kg | 107 - 112 | 93 - 98 |")
md_lines.append("\n> 💡 *Khách hàng phân vân giữa 2 size hoặc thích mặc thoải mái/oversize nên tăng lên 1 size.*\n")

md_lines.append("## Chính sách bán hàng & Đổi trả\n")
md_lines.append("- **Thời gian đổi trả**: Trong vòng 7 ngày kể từ khi nhận hàng.")
md_lines.append("- **Điều kiện đổi trả**: Sản phẩm còn nguyên tem mác, chưa qua giặt tẩy/sử dụng.")
md_lines.append("- **Lỗi từ shop (sai mẫu, lỗi đường may, rách)**: Đổi trả 100% miễn phí, shop chịu toàn bộ phí ship.")
md_lines.append("- **Đổi size/màu theo nhu cầu khách**: Hỗ trợ đổi size tận nhà, khách hỗ trợ phí ship 1 chiều (25.000đ - 30.000đ).")
md_lines.append("- **Giảm giá tối đa**: Không vượt quá 15% khi chưa có sự đồng ý của quản lý.\n")

md_lines.append("## Giao hàng & Thời gian vận chuyển\n")
md_lines.append("| Khu vực | Phí ship | Thời gian giao hàng | Ghi chú |")
md_lines.append("|---|---|---|---|")
md_lines.append("| **Nội thành Hà Nội** | **0đ (Freeship)** | **Hỏa tốc trong 2h** | Áp dụng tất cả các quận nội thành |")
md_lines.append("| **Miền Bắc** | **30.000đ** | **3 - 5 ngày** | Các tỉnh thành phía Bắc |")
md_lines.append("| **Miền Trung** | **40.000đ** | **4 - 6 ngày** | Các tỉnh thành miền Trung |")
md_lines.append("| **Miền Nam** | **50.000đ** | **5 - 7 ngày** | TP.HCM và các tỉnh miền Nam/Tây Nam Bộ |")
md_lines.append("\n- **Hình thức thanh toán**: COD (nhận hàng kiểm tra thanh toán), Chuyển khoản ngân hàng, Ví điện tử (Momo/ZaloPay/VNPay).")
md_lines.append("- **Quy cách đóng gói**: Đóng hộp chỉn chu, bảo mật thông tin đơn hàng.\n")

kb_path = r'c:\Users\LUC\.gemini\antigravity\scratch\auto-reply-system\knowledge-base\products.md'
with open(kb_path, 'w', encoding='utf-8') as f:
    f.write("\n".join(md_lines))

print("Created products.json & products.md successfully!")
