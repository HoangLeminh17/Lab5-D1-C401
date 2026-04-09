# 💊 Pharmacist Assistant - RAG Chatbot powered by Google Gemini

Một hệ thống chatbot thông minh giúp dược sĩ gợi ý thuốc thay thế khi dụng cụ bị hết hàng, sử dụng Google Gemini 2.5 Flash API.

## 🎯 Tính Năng

- **Tra cứu OpenFDA API**: Lấy hoạt chất, đường dùng, chỉ định, chống chỉ định, tác dụng phụ
- **Tìm kiếm kho**: Query CSV để tìm thuốc thay thế có sẵn
- **Tư vấn thông minh**: Sử dụng Google Gemini 2.5 Flash để sinh tư vấn lâm sàng chuyên sâu
- **Dịch Tiếng Việt**: Tự động dịch các cảnh báo quan trọng sang tiếng Việt
- **Giao diện Streamlit**: Dễ sử dụng, hiệu ứng visuạl
- **Feedback System**: Duyệt/Từ chối tư vấn để cải thiện hệ thống

## 📋 Yêu Cầu Hệ Thống

- Python 3.8+
- pip
- Internet connection (để gọi FDA API và Google Gemini API)

## 🚀 Cài Đặt

### 1. Clone/Download Project

```bash
cd Drug
```

### 2. Tạo Virtual Environment (Optional nhưng được khuyến nghị)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# MacOS/Linux
source venv/bin/activate
```

### 3. Cài Đặt Dependencies

```bash
pip install -r requirements.txt
```

### 4. Cấu Hình API Keys

Edit file `.env` với thông tin API của bạn:

```env
# Lấy API key từ: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=AIzaSyD...
GEMINI_MODEL=gemini-2.5-flash
```

**Lưu ý**: 
- Truy cập vào https://makersuite.google.com/app/apikey để tạo và lấy API key
- FDA API không cần API key (public)
- Không commit file `.env` (đã thêm vào `.gitignore`)

## 📂 Cấu Trúc Dự Án

```
Drug/
├── fda_api.py           # Module FDA API Integration
├── rag_engine.py        # Module RAG Engine
├── app.py               # Giao diện Streamlit
├── inventory.csv        # Mock Data (Kho thuốc)
├── requirements.txt     # Python Dependencies
├── .env                 # Environment Configuration
└── README.md            # Tài liệu này
```

## 🛠️ Cách Sử Dụng

### Chạy ứng dụng Streamlit:

```bash
python -m streamlit run main.py
```

Ứng dụng sẽ mở tại: `http://localhost:8501`

### Luồng Nghiệp Vụ:

1. **Cấu hình `.env` & nhập tên thuốc**: Khai báo `GEMINI_API_KEY` trong file `.env`, sau đó nhập tên thuốc bị hết hàng (vd: "Advil")
2. **FDA API**: Hệ thống gọi API để lấy hoạt chất, chỉ định, chống chỉ định, tác dụng phụ
3. **Tìm Kho**: Tìm các thuốc có cùng hoạt chất và `Ton_Kho > 0`
4. **Tư Vấn Gemini**: Gọi Google Gemini 2.5 Flash với system instruction dạng Dược sĩ lâm sàng. Dịch cảnh báo sang Tiếng Việt
5. **Feedback**: Dược sĩ chọn [✅ Duyệt Bán] hoặc [❌ Từ Chối]

## 📚 Chi Tiết Các Module

### 1. `fda_api.py` - Tra cứu OpenFDA

```python
from fda_api import get_full_fda_info

# Lấy thông tin chi tiết
fda_info = get_full_fda_info("Advil")

# Kết quả:
# {
#     "Hoat_Chat": "ibuprofen",
#     "Duong_Dung": "Oral",
#     "Chi_Dinh": "For temporary relief of...",
#     "Chong_Chi_Dinh": "Do not use if...",
#     "Tac_Dung_Phu": "May cause...",
#     "success": True
# }
```

**Tính năng:**
- ✅ Lấy 5 thông tin chi tiết (Hoạt chất, Đường dùng, Chỉ định, Chống chỉ định, Tác dụng phụ)
- ✅ Xử lý timeout API (10s)
- ✅ Try/except toàn diện
- ✅ Logging chi tiết

### 2. `rag_engine.py` - RAG Engine với Google Gemini

```python
from rag_engine import get_clinical_recommendation

# Lấy tư vấn hoàn chỉnh (tự đọc GEMINI_API_KEY từ .env)
result = get_clinical_recommendation("Advil")

# Kết quả:
# {
#     "brand_name": "Advil",
#     "fda_info": {...},
#     "alternative_drugs": [...],
#     "recommendation": "...",
#     "success": True,
#     "error_message": ""
# }
```

**Luồng 5 bước:**
1. Cấu hình Google Gemini API
2. Gọi `get_full_fda_info()` để lấy thông tin FDA
3. Tìm thuốc thay thế từ `inventory.csv`
4. Tạo prompt với system instruction dạng Dược sĩ lâm sàng
5. Gọi Gemini API với dịch sang Tiếng Việt

**Đặc điểm:**
- 🎯 Sử dụng `gemini-2.5-flash` (nhanh chóng và chính xác)
- 🇻🇳 Tự động dịch cảnh báo quan trọng sang Tiếng Việt
- 📋 Format Markdown cho dễ đọc
- ⚠️ Ưu tiên an toàn bệnh nhân

### 3. `main.py` - Streamlit UI

**Các thành phần:**
- 🔐 Đọc Google Gemini API Key từ file `.env`
- 🔍 Form tìm kiếm thuốc
- 📊 Hiển thị thông tin FDA chi tiết (Hoạt chất, Đường dùng, Chỉ định, Chống chỉ định, Tác dụng phụ)
- 💊 Danh sách thuốc thay thế có sẵn trong kho
- 📋 Tư vấn lâm sàng từ Google Gemini (với Tiếng Việt)
- ✅ Nút [✅ Duyệt Bán] / ❌ [Từ Chối]
- 📜 Lịch sử tư vấn

## 🔧 Cấu Hình Nâng Cao

### Tạo API Key từ Google Cloud Console

Nếu bạn muốn quản lý quyền hạn cao hơn:

1. Truy cập: https://console.cloud.google.com
2. Tạo project mới
3. Bật API: Google Generative AI API
4. Tạo Service Account key
5. Sử dụng trong code

### Test Module Riêng Lẻ

```bash
# Test fda_api.py
python fda_api.py

# Test rag_engine.py (đọc API key từ .env)
python rag_engine.py
```

## 📝 Inventory CSV Format

```csv
Ten_Thuoc,Hoat_Chat,Ton_Kho
Advil,ibuprofen,0
Ibuprofen 200mg,ibuprofen,120
Paracetamol,paracetamol,0
Tylenol,paracetamol,200
...
```

**Lưu ý:**
- Header phải là: `Ten_Thuoc, Hoat_Chat, Ton_Kho`
- `Ton_Kho > 0` = Drug có sẵn
- `Ton_Kho = 0` = Drug hết hàng (sẽ bỏ qua)

## 🐛 Troubleshooting

### "Timeout khi gọi FDA API"

```
FDA API chậm hoặc không kết nối. Kiểm tra:
- Kết nối internet
- FDA API status: https://api.fda.gov
- Thử lại sau vài giây
```

### "Google Gemini API Error: Invalid API key"

```
Kiểm tra:
1. API key lấy từ https://makersuite.google.com/app/apikey?
2. API key không bị revoke?
3. API key còn hạn sử dụng?
4. Tài khoản Google đã kích hoạt API?
```

### "File not found: inventory.csv"

```
Đảm bảo:
1. inventory.csv nằm cùng thư mục với app.py
2. Hoặc set INVENTORY_PATH trong .env
```

### "Gemini API returns safety error"

```
Điều này có thể xảy ra nếu prompt bị xem là không an toàn.
Giải pháp: Hệ thống đã setup safety_settings=BLOCK_NONE.
Nếu vẫn lỗi, thử test với prompt khác hoặc kiểm tra quota API.
```

### "Module 'google.generativeai' not found"

```
Cần cài đặt:
pip install google-generativeai
```

## 🔐 Security Notes

- ⚠️ **Không commit file `.env` có API key** - thêm vào `.gitignore`
- ⚠️ Google Gemini API key là sensitive - không share công khai
- ⚠️ FDA API là public (không cần key)
- ⚠️ Sử dụng HTTPS khi triển khai trên production
- ⚠️ Hạn chế rate limit khi gọi gemin API để tránh chi phí cao

## 📈 Cải Thiện Tương Lai

- [ ] Vector DB (Pinecone, Weaviate) thay CSV
- [ ] Multi-language support
- [ ] Advanced filtering (giá, nhà sản xuất, ...)
- [ ] Analytics dashboard
- [ ] Database integration thay CSV

## 📞 Support

Liên hệ: [Your Contact]

## 📄 License

MIT License

---

**Made with ❤️ for Pharmacists** | Powered by OpenFDA + Google Gemini 2.5 Flash
