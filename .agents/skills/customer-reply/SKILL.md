---
name: customer-reply
description: >
  Skill chuyên xử lý, phân loại và soạn thảo phản hồi tin nhắn
  khách hàng trên Messenger, Zalo, TikTok. Kích hoạt khi cần
  phân tích ý định khách hàng và tạo phản hồi phù hợp.
---

# Skill: Customer Reply Automation

## Quy trình xử lý tin nhắn (LUÔN theo đúng thứ tự)

### Bước 1: Phân tích & Phân loại

Đọc tin nhắn và xác định intent chính:

| Intent | Từ khóa nhận biết | Ưu tiên |
|--------|-------------------|---------|
| `PRICE_INQUIRY` | giá, bao nhiêu, chi phí, phí, mua, order | HIGH |
| `PRODUCT_INFO` | tính năng, có không, dùng được không, như thế nào | MEDIUM |
| `ORDER_STATUS` | đơn hàng, ship, giao, chờ, khi nào đến | HIGH |
| `COMPLAINT` | lỗi, hỏng, không hoạt động, tệ, thất vọng, trả lại | URGENT |
| `REFUND` | hoàn tiền, đổi trả, trả hàng, refund | URGENT |
| `GREETING` | xin chào, hi, hello, cho hỏi, ơi | LOW |
| `BOOKING` | đặt lịch, book, hẹn, demo, tư vấn | HIGH |
| `UNKNOWN` | không xác định được | MEDIUM |

### Bước 2: Chọn template

Đọc file template tương ứng trong `templates/` folder.
Luôn đọc `knowledge-base/` để bổ sung thông tin chính xác.

### Bước 3: Cá nhân hóa phản hồi

- Thay thế [TÊN KHÁCH] nếu có thông tin
- Thêm chi tiết cụ thể liên quan đến vấn đề của khách
- Điều chỉnh tone phù hợp platform (Messenger = emoji nhiều hơn, Zalo = formal hơn, TikTok = trẻ trung)

### Bước 4: Kiểm tra trước khi output

Checklist:
- [ ] Có xác nhận đã nhận yêu cầu chưa?
- [ ] Có thông tin chính xác từ knowledge-base không?
- [ ] Có CTA rõ ràng ở cuối không?
- [ ] Độ dài phù hợp (Messenger: <200 ký tự, Zalo: <300, TikTok comment: <150)?
- [ ] Có cần escalate không?

### Bước 5: Format output

Luôn output theo JSON format sau:
```json
{
  "platform": "messenger|zalo|tiktok",
  "intent": "PRICE_INQUIRY|...",
  "priority": "LOW|MEDIUM|HIGH|URGENT",
  "reply": "Nội dung trả lời...",
  "follow_up": "Câu hỏi follow-up nếu cần...",
  "escalate": false,
  "escalate_reason": null,
  "tags": ["giá", "tư vấn"]
}
```
