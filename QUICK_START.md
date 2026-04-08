# ⚡ Quick Start Guide

Bắt đầu trong 5 phút!

## 1️⃣ Cài Đặt (1 phút)

```bash
# Tạo virtual environment
python -m venv venv
venv\Scripts\activate

# Cài package
pip install -r requirements.txt
```

## 2️⃣ Cấu Hình Google Gemini API (2 phút)

### Bước 1: Lấy API Key

Truy cập: https://makersuite.google.com/app/apikey

1. Đăng nhập bằng tài khoản Google
2. Click "Create API key"
3. Copy API Key (thường bắt đầu với `AIzaSy...`)

### Bước 2: Cập nhật file `.env`

Mở file `.env` trong thư mục dự án và điền API key:

```env
GEMINI_API_KEY=AIzaSyD...  # Dán API key vừa lấy
GEMINI_MODEL=gemini-2.5-flash
```

**Lưu ý:** Không để _key này public trên GitHub!

## 3️⃣ Chạy Ứng Dụng (1 phút)

```bash
streamlit run app.py
```

Trình duyệt tự động mở: http://localhost:8501

## 4️⃣ Test (1 phút)

```
1. App Streamlit mở lên
2. Nhập tên thuốc: "Advil" (hoặc thuốc khác trong CSV)
3. Click "🔎 Tìm kiếm"
5. Chờ hệ thống xử lý:
   - Tra cứu FDA API
   - Tìm thuốc thay thế
   - Gọi Gemini để tư vấn
6. Xem kết quả + Nút [Duyệt Bán] / [Từ Chối]
```

---

## 🎮 Cách Sử Dụng Hệ Thống

### Luồng hoạt động:

```
┌─────────────────────────┐
│ Đọc GEMINI_API_KEY từ .env │
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│ Nhập tên thuốc hết hàng │ (vd: "Advil")
└────────────┬────────────┘
             │
┌────────────▼────────────┐
│ Click "🔎 Tìm kiếm"     │
└────────────┬────────────┘
      ⏳ Xử lý đang chạy
             │
   ┌────────┴────────┐
   │                 │
  1️⃣ FDA API    2️⃣ Tìm kho
   │                 │
   └────────┬────────┘
            │
   3️⃣ Gọi Gemini
            │
┌───────────▼────────────┐
│ Hiển thị kết quả       │
│ - Hoạt chất            │
│ - Chống chỉ định       │
│ - Thuốc thay thế       │
│ - Tư vấn Gemini        │
└─────────────────────────┘
       ✅ / ❌ Phản hồi
```

---

## ❓ Gặp Lỗi?

| Lỗi | Giải pháp |
|-----|----------|
| `No module named 'streamlit'` | `pip install -r requirements.txt` |
| `Invalid API key` | Kiểm tra `GEMINI_API_KEY` trong file `.env` |
| `Connection timeout` | Kiểm tra internet / FDA API status |
| `File not found: inventory.csv` | Đảm bảo file ở cùng thư mục với app.py |
| `module 'google.generativeai' not found` | `pip install google-generativeai` |

## 📚 Tiếp Theo

- Đọc [README.md](README.md) cho chi tiết đầy đủ
- Explore các module: `fda_api.py`, `rag_engine.py`, `app.py`
- Tùy chỉnh `inventory.csv` với dữ liệu thực tế
- Test `test_modules.py` để kiểm tra setup

---

**Happy coding! 🚀**
