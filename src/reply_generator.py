"""
Reply Generator
Tạo tin nhắn phản hồi dựa trên intent, knowledge base sản phẩm đồ nam, và nhận diện 63 tỉnh thành
"""

import os
import json
import random
import re
import unicodedata
from typing import Optional, Tuple


def remove_accents(input_str: str) -> str:
    """Chuyển chuỗi tiếng Việt có dấu thành không dấu"""
    if not input_str:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd_form if not unicodedata.combining(c)]).replace('đ', 'd').replace('Đ', 'D')


class ReplyGenerator:
    """Tạo phản hồi cá nhân hóa dựa trên template + knowledge base sản phẩm đồ nam + nhận diện tỉnh thành"""

    # ── TEMPLATES THEO INTENT ──────────────────────────────────────────────

    TEMPLATES = {

        "GREETING": [
            "Chào {name}! 😊 Shop {shop_name} đây ạ, em có thể hỗ trợ anh/chị chọn mẫu áo quần nam nào ạ?",
            "Xin chào {name}! 👋 Em là trợ lý tự động của {shop_name}. Bên em đang có đầy đủ các mẫu áo thun, sơ mi, polo, quần jeans, kaki, short nam... Anh/chị cần tư vấn mẫu nào ạ?",
            "Chào {name} ạ! 🌟 Anh/chị đang quan tâm đến mẫu đồ nam nào bên em (áo thun, sơ mi, quần jeans, áo khoác...)? Em tư vấn size và mẫu ngay nha!"
        ],

        "PRICE_INQUIRY": [
            "Dạ chào {name}! Các sản phẩm thời trang nam bên em có mức giá từ {price_range} ạ 😊. Anh/chị đang quan tâm đến áo hay quần loại nào để em báo giá chi tiết từng mẫu nhé!",
            "Chào {name}! Đồ nam bên em giá cực ưu đãi từ {price_range} (áo thun từ 99k, polo từ 179k, sơ mi từ 189k, quần jeans từ 299k...). Anh/chị ưng mẫu nào em gửi bảng giá chi tiết ngay ạ 🎉",
            "Dạ {name} ơi! Giá sản phẩm bên em từ {price_range} ạ. Toàn bộ là hàng chuẩn form nam, đủ size S đến XXL. Anh/chị cần em hỗ trợ mẫu nào ạ? 😊"
        ],

        "SHIPPING_INQUIRY": [
            "Dạ chào {name}! Bảng phí ship và thời gian giao hàng bên em như sau ạ 🚚:\n"
            "• **Nội thành Hà Nội**: 0đ (Freeship) – Hỏa tốc nhận trong 2h 🚀\n"
            "• **Miền Bắc**: 30.000đ – Nhận hàng từ 3 - 5 ngày\n"
            "• **Miền Trung**: 40.000đ – Nhận hàng từ 4 - 6 ngày\n"
            "• **Miền Nam**: 50.000đ – Nhận hàng từ 5 - 7 ngày\n"
            "Anh/chị đang ở tỉnh/thành nào để em báo phí ship và thời gian giao hàng chính xác nhất ạ? 😊"
        ],

        "PRODUCT_INFO": [
            "Dạ chào {name}! Shop {shop_name} có đầy đủ 100+ mẫu thời trang nam: Áo thun, Sơ mi, Polo, Áo khoác, Hoodie, Quần Jeans, Kaki, Tây, Short, Đồ thể thao và Mặc nhà. Full size từ S đến XXL (50kg - 90kg). Anh/chị cần tư vấn mẫu hay size nào ạ? 📦",
            "Chào {name} ạ! 😊 Bên em có đủ size từ S, M, L, XL đến XXL cho người từ 50kg - 90kg, chất vải co giãn thoáng mát, chuẩn form nam. Anh/chị cho em xin chiều cao + cân nặng để em chọn size chuẩn nhất cho mình nhé!",
        ],

        "ORDER_STATUS": [
            "Dạ chào {name}! Anh/chị cho em xin SĐT đặt hàng hoặc mã đơn để em kiểm tra hành trình đơn hàng ngay nhé! 🔍\n\nHoặc anh/chị có thể tra cứu tại: {tracking_link}",
            "Chào {name}! Em kiểm tra đơn hàng cho mình ngay ạ. Anh/chị cho em biết SĐT đặt hàng hoặc mã đơn nhé, em check và báo lại ngay ạ 😊"
        ],

        "COMPLAINT": [
            "Dạ {name} ơi! Em thực sự xin lỗi vì trải nghiệm không như ý này ạ 😔\n\nĐể hỗ trợ mình nhanh nhất, anh/chị cho em xin thông tin đơn hàng và ảnh/video lỗi của sản phẩm. Shop cam kết đổi mới hoặc hoàn tiền 100% miễn phí ngay ạ! ✅",
            "Ôi {name} ơi, em thành thật xin lỗi về sự cố này! 🙏\n\nShop {shop_name} luôn cam kết bảo hành sản phẩm. Anh/chị gửi ảnh/video sản phẩm qua đây, em báo bộ phận hỗ trợ đổi hàng tận nhà ngay trong 24h ạ!"
        ],

        "REFUND": [
            "Dạ chào {name}! Shop có chính sách đổi trả trong vòng {return_days} ngày đối với mọi sản phẩm ạ 😔. Anh/chị cho em xin SĐT/mã đơn và lý do cần đổi (đổi size hay đổi mẫu) để em tạo đơn đổi trả cho mình ngay nhé! ✅",
        ],

        "BOOKING": [
            "Dạ {name} ơi! Anh/chị muốn được tư vấn kỹ hơn về mẫu mã và size số đồ nam, em sẵn sàng hỗ trợ ngay 📅\n\nAnh/chị có thể để lại Chiều cao + Cân nặng hoặc SĐT, nhân viên shop sẽ gọi điện/nhắn tin tư vấn trực tiếp cho mình ngay ạ 😊",
        ],

        "HUMAN_HANDOVER": [
            "Dạ em đang kết nối {name} với nhân viên tư vấn của {shop_name} ngay ạ! 👨‍💼\nNhân viên sẽ vào hỗ trợ trực tiếp cho mình trong giây lát, anh/chị đợi em một chút nhé! 😊\n\n🔔 [CẦN XỬ LÝ NGAY - ĐÃ BÀN GIAO CHO QUẢN TRỊ VIÊN TRỰC PAGE]"
        ],

        "BOT_RESUME": [
            "Dạ em là trợ lý tự động của {shop_name} đã quay lại sẵn sàng hỗ trợ {name} ạ! 🌟 Anh/chị cần em hỗ trợ xem mẫu đồ nam hay tư vấn size số nào ạ?"
        ],

        "UNKNOWN": [
            "Dạ chào {name}! Em đã nhận được tin nhắn của anh/chị rồi ạ 😊\n\nAnh/chị đang cần tìm mẫu áo, quần nam hay cần tư vấn size số gì ạ? Hoặc anh/chị có thể liên hệ trực tiếp hotline {hotline} để được hỗ trợ nhanh nhất ạ!",
            "Chào {name}! Cảm ơn anh/chị đã liên hệ {shop_name} 🌟\n\nAnh/chị cần hỗ trợ chọn mẫu đồ nam hay tư vấn size số ạ? Em sẵn sàng hỗ trợ ngay!",
        ]
    }

    # Bảng giá theo danh mục đồ nam
    CATEGORY_INFO = {
        "áo thun": {"name": "Áo thun nam", "price": "99.000đ - 169.000đ", "count": 10},
        "áo sơ mi": {"name": "Áo sơ mi nam", "price": "189.000đ - 239.000đ", "count": 9},
        "sơ mi": {"name": "Áo sơ mi nam", "price": "189.000đ - 239.000đ", "count": 9},
        "áo polo": {"name": "Áo polo nam", "price": "179.000đ - 239.000đ", "count": 9},
        "polo": {"name": "Áo polo nam", "price": "179.000đ - 239.000đ", "count": 9},
        "áo khoác": {"name": "Áo khoác nam", "price": "339.000đ - 459.000đ", "count": 9},
        "khoác": {"name": "Áo khoác nam", "price": "339.000đ - 459.000đ", "count": 9},
        "hoodie": {"name": "Hoodie & Sweatshirt nam", "price": "279.000đ - 339.000đ", "count": 9},
        "sweatshirt": {"name": "Hoodie & Sweatshirt nam", "price": "279.000đ - 339.000đ", "count": 9},
        "quần jeans": {"name": "Quần jeans nam", "price": "299.000đ - 359.000đ", "count": 9},
        "quần jean": {"name": "Quần jeans nam", "price": "299.000đ - 359.000đ", "count": 9},
        "jeans": {"name": "Quần jeans nam", "price": "299.000đ - 359.000đ", "count": 9},
        "quần kaki": {"name": "Quần kaki nam", "price": "259.000đ - 309.000đ", "count": 9},
        "kaki": {"name": "Quần kaki nam", "price": "259.000đ - 309.000đ", "count": 9},
        "quần short": {"name": "Quần short nam", "price": "159.000đ - 239.000đ", "count": 9},
        "short": {"name": "Quần short nam", "price": "159.000đ - 239.000đ", "count": 9},
        "quần đùi": {"name": "Quần short nam", "price": "159.000đ - 239.000đ", "count": 9},
        "quần tây": {"name": "Quần tây nam", "price": "309.000đ - 369.000đ", "count": 9},
        "quần âu": {"name": "Quần tây nam", "price": "309.000đ - 369.000đ", "count": 9},
        "đồ thể thao": {"name": "Đồ thể thao nam", "price": "179.000đ - 269.000đ", "count": 9},
        "thể thao": {"name": "Đồ thể thao nam", "price": "179.000đ - 269.000đ", "count": 9},
        "đồ mặc nhà": {"name": "Đồ mặc nhà nam", "price": "99.000đ - 249.000đ", "count": 9},
        "mặc nhà": {"name": "Đồ mặc nhà nam", "price": "99.000đ - 249.000đ", "count": 9},
        "ngủ": {"name": "Đồ mặc nhà nam", "price": "99.000đ - 249.000đ", "count": 9},
    }

    # ── BẢNG TỪ ĐIỂN 63 TỈNH THÀNH THEO MIỀN ──────────────────────────────
    PROVINCE_REGIONS = {
        # 1. HÀ NỘI
        "nội thành hà nội": {"province": "Nội thành Hà Nội", "region": "Hà Nội", "fee": "0đ (Miễn phí ship)", "time": "Hỏa tốc nhận trong 2h", "is_hanoi": True},
        "hà nội": {"province": "Hà Nội", "region": "Hà Nội", "fee": "0đ (Freeship hỏa tốc 2h nội thành) hoặc 30.000đ (ngoại thành)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "hn": {"province": "Hà Nội", "region": "Hà Nội", "fee": "0đ (Freeship hỏa tốc 2h)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "hà đông": {"province": "Hà Đông (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "cầu giấy": {"province": "Cầu Giấy (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "đống đa": {"province": "Đống Đa (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "thanh xuân": {"province": "Thanh Xuân (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "hoàn kiếm": {"province": "Hoàn Kiếm (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "ba đình": {"province": "Ba Đình (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "hai bà trưng": {"province": "Hai Bà Trưng (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "hoàng mai": {"province": "Hoàng Mai (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "long biên": {"province": "Long Biên (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "tây hồ": {"province": "Tây Hồ (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "nam từ liêm": {"province": "Nam Từ Liêm (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},
        "bắc từ liêm": {"province": "Bắc Từ Liêm (Hà Nội)", "region": "Hà Nội", "fee": "0đ (Freeship)", "time": "Hỏa tốc trong 2h", "is_hanoi": True},

        # 2. MIỀN BẮC (30.000đ - 3 đến 5 ngày)
        "hải phòng": {"province": "Hải Phòng", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "quảng ninh": {"province": "Quảng Ninh", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "bắc ninh": {"province": "Bắc Ninh", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "hải dương": {"province": "Hải Dương", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "hưng yên": {"province": "Hưng Yên", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "nam định": {"province": "Nam Định", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "thái bình": {"province": "Thái Bình", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "ninh bình": {"province": "Ninh Bình", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "hà nam": {"province": "Hà Nam", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "vĩnh phúc": {"province": "Vĩnh Phúc", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "phú thọ": {"province": "Phú Thọ", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "bắc giang": {"province": "Bắc Giang", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "thái nguyên": {"province": "Thái Nguyên", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "lạng sơn": {"province": "Lạng Sơn", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "cao bằng": {"province": "Cao Bằng", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "hà giang": {"province": "Hà Giang", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "tuyên quang": {"province": "Tuyên Quang", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "bắc kạn": {"province": "Bắc Kạn", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "bac kan": {"province": "Bắc Kạn", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "lào cai": {"province": "Lào Cai", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "yên bái": {"province": "Yên Bái", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "sơn la": {"province": "Sơn La", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "hòa bình": {"province": "Hòa Bình", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "điện biên": {"province": "Điện Biên", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},
        "lai châu": {"province": "Lai Châu", "region": "Miền Bắc", "fee": "30.000đ", "time": "3 - 5 ngày"},

        # 3. MIỀN TRUNG & TÂY NGUYÊN (40.000đ - 4 đến 6 ngày)
        "thanh hóa": {"province": "Thanh Hóa", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "nghệ an": {"province": "Nghệ An", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "hà tĩnh": {"province": "Hà Tĩnh", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "quảng bình": {"province": "Quảng Bình", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "quảng trị": {"province": "Quảng Trị", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "thừa thiên huế": {"province": "Thừa Thiên Huế", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "huế": {"province": "Thừa Thiên Huế", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "đà nẵng": {"province": "Đà Nẵng", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "quảng nam": {"province": "Quảng Nam", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "quảng ngãi": {"province": "Quảng Ngãi", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "bình định": {"province": "Bình Định", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "quy nhơn": {"province": "Bình Định (Quy Nhơn)", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "phú yên": {"province": "Phú Yên", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "khánh hòa": {"province": "Khánh Hòa", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "nha trang": {"province": "Khánh Hòa (Nha Trang)", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "ninh thuận": {"province": "Ninh Thuận", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "phan rang": {"province": "Ninh Thuận (Phan Rang)", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "bình thuận": {"province": "Bình Thuận", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "phan thiết": {"province": "Bình Thuận (Phan Thiết)", "region": "Miền Trung", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "kon tum": {"province": "Kon Tum", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "gia lai": {"province": "Gia Lai", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "pleiku": {"province": "Gia Lai (Pleiku)", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "đắk lắk": {"province": "Đắk Lắk", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "dak lak": {"province": "Đắk Lắk", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "buôn ma thuột": {"province": "Đắk Lắk (Buôn Ma Thuột)", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "bmt": {"province": "Đắk Lắk (Buôn Ma Thuột)", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "đắk nông": {"province": "Đắk Nông", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "dak nong": {"province": "Đắk Nông", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "lâm đồng": {"province": "Lâm Đồng", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},
        "đà lạt": {"province": "Lâm Đồng (Đà Lạt)", "region": "Miền Trung (Tây Nguyên)", "fee": "40.000đ", "time": "4 - 6 ngày"},

        # 4. MIỀN NAM (50.000đ - 5 đến 7 ngày)
        "hồ chí minh": {"province": "TP. Hồ Chí Minh", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "tp hcm": {"province": "TP. Hồ Chí Minh", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "tphcm": {"province": "TP. Hồ Chí Minh", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "sài gòn": {"province": "TP. Hồ Chí Minh (Sài Gòn)", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "sg": {"province": "TP. Hồ Chí Minh", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "bà rịa": {"province": "Bà Rịa - Vũng Tàu", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "vũng tàu": {"province": "Bà Rịa - Vũng Tàu", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "bình dương": {"province": "Bình Dương", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "bình phước": {"province": "Bình Phước", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "đồng nai": {"province": "Đồng Nai", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "biên hòa": {"province": "Đồng Nai (Biên Hòa)", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "tây ninh": {"province": "Tây Ninh", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "long an": {"province": "Long An", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "tiền giang": {"province": "Tiền Giang", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "mỹ tho": {"province": "Tiền Giang (Mỹ Tho)", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "bến tre": {"province": "Bến Tre", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "trà vinh": {"province": "Trà Vinh", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "vĩnh long": {"province": "Vĩnh Long", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "đồng tháp": {"province": "Đồng Tháp", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "cao lãnh": {"province": "Đồng Tháp (Cao Lãnh)", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "an giang": {"province": "An Giang", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "long xuyên": {"province": "An Giang (Long Xuyên)", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "châu đốc": {"province": "An Giang (Châu Đốc)", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "kiên giang": {"province": "Kiên Giang", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "rạch giá": {"province": "Kiên Giang (Rạch Giá)", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "phú quốc": {"province": "Kiên Giang (Phú Quốc)", "region": "Miền Nam", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "cần thơ": {"province": "Cần Thơ", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "hậu giang": {"province": "Hậu Giang", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "vị thanh": {"province": "Hậu Giang (Vị Thanh)", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "sóc trăng": {"province": "Sóc Trăng", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "bạc liêu": {"province": "Bạc Liêu", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
        "cà mau": {"province": "Cà Mau", "region": "Miền Nam (Tây Nam Bộ)", "fee": "50.000đ", "time": "5 - 7 ngày"},
    }

    # ── PLATFORM-SPECIFIC ADJUSTMENTS ─────────────────────────────────────

    PLATFORM_STYLE = {
        "messenger": {
            "emoji_level": "high",
            "max_length": 640,
            "formal": False,
        },
        "zalo": {
            "emoji_level": "medium",
            "max_length": 1000,
            "formal": True,
        },
        "tiktok": {
            "emoji_level": "high",
            "max_length": 250,
            "formal": False,
        }
    }

    def __init__(self):
        self.config = self._load_config()
        self.products = self._load_products()
        # Sắp xếp các từ khóa tỉnh thành theo độ dài giảm dần để ưu tiên match từ dài trước
        self._sorted_provinces = sorted(
            self.PROVINCE_REGIONS.keys(), 
            key=lambda k: len(k), 
            reverse=True
        )

    def _load_config(self) -> dict:
        """Đọc config từ file hoặc dùng default"""
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.json')
        defaults = {
            "shop_name": "Shop đồ Nam",
            "hotline": "0832 717 850",
            "price_range": "99.000đ - 459.000đ",
            "price_link": "link bảng giá",
            "tracking_link": "link tra cứu",
            "return_days": "7",
            "working_hours": "8:00 - 21:00 (T2-CN)"
        }
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    defaults.update(user_config)
            except Exception:
                pass
        return defaults

    def _load_products(self) -> list:
        """Đọc danh sách sản phẩm từ products.json"""
        json_path = os.path.join(os.path.dirname(__file__), '..', 'knowledge-base', 'products.json')
        if os.path.exists(json_path):
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _find_category_match(self, message: str) -> Optional[dict]:
        """Kiểm tra xem tin nhắn có nhắc đến danh mục sản phẩm cụ thể nào không"""
        msg_lower = message.lower()
        for kw, info in self.CATEGORY_INFO.items():
            if kw in msg_lower:
                return info
        return None

    def _detect_province(self, message: str) -> Optional[dict]:
        """
        Nhận diện tỉnh thành / quận huyện trong tin nhắn (hỗ trợ cả có dấu và không dấu).
        """
        msg_lower = message.lower()
        msg_no_accents = remove_accents(msg_lower)

        for p_key in self._sorted_provinces:
            p_no_accents = remove_accents(p_key)
            # Dùng regex word boundary để match chính xác
            pattern_accented = r'(?i)(?<!\w)' + re.escape(p_key) + r'(?!\w)'
            pattern_no_accents = r'(?i)(?<!\w)' + re.escape(p_no_accents) + r'(?!\w)'

            if re.search(pattern_accented, msg_lower) or re.search(pattern_no_accents, msg_no_accents):
                return self.PROVINCE_REGIONS[p_key]
        
        return None

    def _build_shipping_response(self, name: str, message: str) -> str:
        """
        Tạo phản hồi chính xác theo tỉnh thành khách hàng cung cấp.
        """
        detected = self._detect_province(message)
        msg_lower = message.lower()

        # Trường hợp 1: Nhận diện được tỉnh thành cụ thể
        if detected:
            prov_name = detected["province"]
            region_name = detected["region"]
            fee = detected["fee"]
            time_est = detected["time"]

            if detected.get("is_hanoi"):
                return (
                    f"Dạ chào {name}! Khu vực **{prov_name}** bên em áp dụng chính sách **{fee}** và có hỗ trợ **{time_est}** ạ! 🚀\n\n"
                    f"📋 Phí ship các khu vực khác để mình tham khảo:\n"
                    f"• Miền Bắc: 30.000đ (3 - 5 ngày)\n"
                    f"• Miền Trung: 40.000đ (4 - 6 ngày)\n"
                    f"• Miền Nam: 50.000đ (5 - 7 ngày)\n"
                    f"Anh/chị cho em xin địa chỉ cụ thể + SĐT để em lên đơn gửi hỏa tốc ngay cho mình nhé! 😊"
                )
            else:
                return (
                    f"Dạ chào {name}! Khu vực **{prov_name}** thuộc **{region_name}** bên em có:\n"
                    f"• **Phí ship**: **{fee}**\n"
                    f"• **Thời gian nhận hàng dự kiến**: **{time_est}** 🚚\n\n"
                    f"📋 Chính sách giao hàng:\n"
                    f"• Nội thành Hà Nội: Freeship hỏa tốc trong 2h\n"
                    f"• Miền Bắc: 30.000đ (3 - 5 ngày) | Miền Trung: 40.000đ (4 - 6 ngày) | Miền Nam: 50.000đ (5 - 7 ngày)\n\n"
                    f"Anh/chị đang quan tâm đến mẫu nào ạ? Cho em xin thông tin để em hỗ trợ tư vấn size và lên đơn ship cho mình nha! 😊"
                )

        # Trường hợp 2: Khách hỏi theo vùng miền chung (miền bắc, miền trung, miền nam)
        if "miền bắc" in msg_lower or "mien bac" in msg_lower or "phía bắc" in msg_lower or "phia bac" in msg_lower:
            return (
                f"Dạ chào {name}! Khu vực **Miền Bắc** phí ship là **30.000đ**, thời gian nhận hàng dự kiến từ **3 - 5 ngày** ạ 🚚 (Riêng nội thành Hà Nội Freeship hỏa tốc trong 2h 🚀).\n\n"
                f"📋 Các khu vực khác:\n"
                f"• Miền Trung: 40.000đ (4 - 6 ngày)\n"
                f"• Miền Nam: 50.000đ (5 - 7 ngày)\n"
                f"Anh/chị đang ở tỉnh nào phía Bắc để em hỗ trợ lên đơn nhanh nhất cho mình nhé! 😊"
            )
        elif "miền trung" in msg_lower or "mien trung" in msg_lower:
            return (
                f"Dạ chào {name}! Khu vực **Miền Trung & Tây Nguyên** phí ship là **40.000đ**, thời gian nhận hàng dự kiến từ **4 - 6 ngày** ạ 🚚.\n\n"
                f"📋 Các khu vực khác:\n"
                f"• Nội thành Hà Nội: 0đ (Freeship hỏa tốc 2h)\n"
                f"• Miền Bắc: 30.000đ (3 - 5 ngày)\n"
                f"• Miền Nam: 50.000đ (5 - 7 ngày)\n"
                f"Anh/chị đang ở tỉnh nào miền Trung để em hỗ trợ kiểm tra đơn và thời gian giao hàng nhé! 😊"
            )
        elif "miền nam" in msg_lower or "mien nam" in msg_lower or "phía nam" in msg_lower or "phia nam" in msg_lower or "miền tây" in msg_lower or "mien tay" in msg_lower:
            return (
                f"Dạ chào {name}! Khu vực **Miền Nam & Tây Nam Bộ** phí ship là **50.000đ**, thời gian nhận hàng dự kiến từ **5 - 7 ngày** ạ 🚚.\n\n"
                f"📋 Các khu vực khác:\n"
                f"• Nội thành Hà Nội: 0đ (Freeship hỏa tốc 2h)\n"
                f"• Miền Bắc: 30.000đ (3 - 5 ngày)\n"
                f"• Miền Trung: 40.000đ (4 - 6 ngày)\n"
                f"Anh/chị đang ở tỉnh/thành nào phía Nam để em hỗ trợ tư vấn mẫu và lên đơn ship cho mình nha! 😊"
            )

        # Trường hợp 3: Bảng tổng quát khi hỏi chung
        return (
            f"Dạ chào {name}! Bảng phí ship và thời gian giao hàng dự kiến bên em theo từng khu vực như sau ạ 🚚:\n"
            f"• **Nội thành Hà Nội**: **0đ (Freeship)** – Hỏa tốc nhận trong **2h** 🚀\n"
            f"• **Miền Bắc**: **30.000đ** – Nhận hàng từ **3 - 5 ngày**\n"
            f"• **Miền Trung & Tây Nguyên**: **40.000đ** – Nhận hàng từ **4 - 6 ngày**\n"
            f"• **Miền Nam & Tây Nam Bộ**: **50.000đ** – Nhận hàng từ **5 - 7 ngày**\n"
            f"Anh/chị đang ở tỉnh/thành nào để em báo chi tiết giá ship và ngày nhận hàng cho mình nhé! 😊"
        )

    def generate(
        self,
        message: str,
        intent: dict,
        platform: str = "messenger",
        username: Optional[str] = None,
        **kwargs
    ) -> dict:
        """
        Tạo phản hồi hoàn chỉnh
        """
        intent_type = intent.get("type", "UNKNOWN")
        platform_style = self.PLATFORM_STYLE.get(platform, self.PLATFORM_STYLE["messenger"])
        
        name = username or "anh/chị"
        msg_lower = message.lower()

        # Kiểm tra nhận diện tỉnh thành trong câu
        detected_prov = self._detect_province(message)

        # 1. Nếu hỏi phí ship HOẶC trong câu có nhắc đến tỉnh thành kèm ý định giao hàng/mua hàng
        if intent_type == "SHIPPING_INQUIRY" or (detected_prov and ("ship" in msg_lower or "giao" in msg_lower or "nhận" in msg_lower or "nhan" in msg_lower or "mấy ngày" in msg_lower or "bao lâu" in msg_lower or "bao gia" in msg_lower or "giá" in msg_lower or "phi" in msg_lower or "o " in msg_lower or "ở " in msg_lower)):
            reply = self._build_shipping_response(name, message)
        
        # 2. Xử lý hỏi giá theo danh mục
        elif intent_type == "PRICE_INQUIRY":
            cat_match = self._find_category_match(message)
            if cat_match:
                reply = (
                    f"Dạ chào {name}! Mẫu {cat_match['name']} bên em có mức giá từ {cat_match['price']} ạ 😊.\n"
                    f"Tất cả đều full size S - XXL (50kg - 90kg), chuẩn form dáng nam. Anh/chị cho em xin chiều cao + cân nặng để em gửi các mẫu đẹp nhất nha!"
                )
            else:
                templates = self.TEMPLATES.get("PRICE_INQUIRY", self.TEMPLATES["UNKNOWN"])
                template = random.choice(templates)
                reply = template.format(
                    name=name,
                    shop_name=self.config.get("shop_name", "Shop đồ Nam"),
                    hotline=self.config.get("hotline", "0832 717 850"),
                    price_range=self.config.get("price_range", "99.000đ - 459.000đ"),
                    price_link=self.config.get("price_link", ""),
                    tracking_link=self.config.get("tracking_link", ""),
                    return_days=self.config.get("return_days", "7"),
                )
        
        # 3. Xử lý hỏi về size
        elif "size" in msg_lower or "cân nặng" in msg_lower or "chiều cao" in msg_lower or "kg" in msg_lower:
            reply = (
                f"Dạ chào {name}! Bên em có đủ 5 size từ S đến XXL cho nam (50kg - 90kg+):\n"
                f"• Size S: 50-58kg (1m60-1m65)\n"
                f"• Size M: 59-66kg (1m65-1m70)\n"
                f"• Size L: 67-74kg (1m70-1m75)\n"
                f"• Size XL: 75-82kg (1m75-1m80)\n"
                f"• Size XXL: 83-90kg+ (1m80-1m88)\n"
                f"Anh/chị cho em xin chiều cao, cân nặng để em chọn size vừa vặn nhất cho mình nhé! 😊"
            )
        
        # 4. Các intent khác theo template
        else:
            templates = self.TEMPLATES.get(intent_type, self.TEMPLATES["UNKNOWN"])
            template = random.choice(templates)
            
            reply = template.format(
                name=name,
                shop_name=self.config.get("shop_name", "Shop đồ Nam"),
                hotline=self.config.get("hotline", "0832 717 850"),
                price_range=self.config.get("price_range", "99.000đ - 459.000đ"),
                price_link=self.config.get("price_link", ""),
                tracking_link=self.config.get("tracking_link", ""),
                return_days=self.config.get("return_days", "7"),
            )

        # Cắt ngắn nếu vượt giới hạn platform
        max_len = platform_style["max_length"]
        if len(reply) > max_len:
            reply = reply[:max_len - 3] + "..."

        needs_escalate = (
            (intent_type in ["COMPLAINT", "REFUND"] and intent.get("confidence", 0) > 0.7) or
            intent_type == "HUMAN_HANDOVER"
        )
        escalate_reason = (
            "[CẦN XỬ LÝ NGAY] Khách yêu cầu chat với người bán / nhân viên"
            if intent_type == "HUMAN_HANDOVER"
            else (f"Cần xử lý thủ công: {intent_type}" if needs_escalate else None)
        )

        return {
            "platform": platform,
            "intent": intent_type,
            "priority": self._get_priority(intent_type),
            "reply": reply,
            "escalate": needs_escalate,
            "escalate_reason": escalate_reason,
            "tags": self._get_tags(intent_type, message, detected_prov)
        }

    def _get_priority(self, intent_type: str) -> str:
        priority_map = {
            "HUMAN_HANDOVER": "URGENT",
            "COMPLAINT": "URGENT",
            "REFUND": "URGENT",
            "SHIPPING_INQUIRY": "HIGH",
            "ORDER_STATUS": "HIGH",
            "PRICE_INQUIRY": "HIGH",
            "BOOKING": "HIGH",
            "PRODUCT_INFO": "MEDIUM",
            "GREETING": "LOW",
            "BOT_RESUME": "LOW",
            "UNKNOWN": "MEDIUM"
        }
        return priority_map.get(intent_type, "MEDIUM")

    def _get_tags(self, intent_type: str, message: str, detected_prov: Optional[dict] = None) -> list:
        tags = [intent_type.lower()]
        msg_lower = message.lower()
        if detected_prov:
            tags.append(f"tỉnh: {detected_prov['province']}")
            tags.append(f"vùng: {detected_prov['region']}")
        if "giá" in msg_lower or "gia" in msg_lower:
            tags.append("hỏi giá")
        if "ship" in msg_lower or "giao hàng" in msg_lower or "giao hang" in msg_lower:
            tags.append("phí ship & giao hàng")
        if "lỗi" in msg_lower or "hỏng" in msg_lower:
            tags.append("sản phẩm lỗi")
        if "size" in msg_lower:
            tags.append("tư vấn size")
        for cat in ["áo thun", "sơ mi", "polo", "jeans", "kaki", "short", "khoác", "hoodie"]:
            if cat in msg_lower:
                tags.append(cat)
        return tags
