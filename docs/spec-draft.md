# SPEC draft — NhomD1-C401

## Track: Vinmec

## Problem statement
Tại quầy thuốc/bộ phận tư vấn, dược sĩ thường gặp tình huống thuốc mà khách yêu cầu đã hết hàng.
Hiện tại nhân sự phải tra cứu thủ công theo hoạt chất và hướng dẫn sử dụng, mất 3-10 phút mỗi ca,
dễ bỏ sót chống chỉ định hoặc tác dụng phụ quan trọng. Hệ thống AI có thể tự động tra cứu OpenFDA,
đối chiếu tồn kho nội bộ, gợi ý thuốc thay thế có giải thích rõ ràng và kiểm chứng việc kết hợp các loại thuốc trong cùng 1 đơn để rút ngắn thời gian tư vấn.

## Canvas draft

| | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| Trả lời | Đối tượng chính: dược sĩ quầy và nhân viên tư vấn. Pain: tìm thuốc thay thế thủ công, mất thời gian, dễ sai sót khi cảnh báo. Giải pháp: chatbot nhập tên thuốc hết hàng -> trả hoạt chất, chỉ định/chống chỉ định, danh sách thay thế còn hàng, và khuyến nghị bằng tiếng Việt. | Nếu AI gợi ý sai có thể ảnh hưởng an toàn người bệnh. Bắt buộc hiển thị cảnh báo rõ ràng + giữ quyền quyết định cuối cho dược sĩ (nút duyệt/từ chối). Có phương án fallback: chuyển tư vấn thủ công khi confidence thấp hoặc dữ liệu FDA thiếu. | Khả thi cao: stack hiện tại đã chạy được (Python + Streamlit + OpenFDA + Gemini + CSV). Chi phí API theo lượt thấp, thời gian phản hồi mục tiêu < 5 giây/lượt. Rủi ro chính: dữ liệu FDA không đồng nhất, mô tả hoạt chất dạng chuỗi dài, và tên thuốc thương mại đa biến thể. |

**Auto hay aug?** Augmentation - AI đóng vai trò trợ lý dược sĩ, không tự động chốt đơn. Dược sĩ là người ra quyết định cuối cùng.

**Learning signal:**
- Dược sĩ bấm Duyệt Bán hay Từ Chối sau mỗi gợi ý.
- Tên thuốc thay thế được chọn cuối cùng so với top gợi ý.
- Các case không tìm được thuốc thay thế để cập nhật inventory/prompt.

## Hướng đi chính
- Prototype hiện tại:
	- Module 1: `fda_api.py` lấy 5 trường FDA (`Hoat_Chat`, `Duong_Dung`, `Chi_Dinh`, `Chong_Chi_Dinh`, `Tac_Dung_Phu`).
	- Module 2: `rag_engine.py` load `inventory.csv`, tìm thuốc còn hàng cùng hoạt chất, gọi Gemini để sinh tư vấn.
	- Module 3: `app.py` Streamlit UI để nhập thuốc, xem cảnh báo, duyệt/từ chối, lưu history ngắn hạn.
- Eval mục tiêu phiên bản đầu:
	- Top-3 alternative coverage >= 80% trên tập test nội bộ.
	- Tỷ lệ có cảnh báo chống chỉ định/tác dụng phụ trong output >= 95%.
	- P95 latency end-to-end < 5 giây/lượt (không tính mạng bất thường).
- Main failure modes:
	- FDA trả hoạt chất dạng chuỗi nhiều thành phần làm match inventory kém chính xác.
	- Thuốc generic/brand name mapping chưa đầy đủ.
	- Prompt LLM trả lời dài, thiếu cấu trúc hoặc không nhấn mạnh cảnh báo nguy cơ cao.

## Phân công (7 thành viên)
- Đăng Hải: Product owner, chốt scope bài toán, user flow và acceptance criteria.
- Hưng: Data owner cho `inventory.csv`, chuẩn hóa tên thuốc/hoạt chất và kịch bản hết hàng.
- Ngọc: Phụ trách `fda_api.py`, xử lý parse dữ liệu OpenFDA và fallback khi field thiếu.
- Hậu: Phụ trách `rag_engine.py`, logic tìm thuốc thay thế, prompt và orchestration Gemini.
- Kiên: Phụ trách `app.py`, UX Streamlit, luồng feedback Duyệt/Từ chối và hiển thị cảnh báo.
- Hoàng: Thiết kế bộ eval, đo top-k accuracy, latency, warning coverage, tổng hợp báo cáo test.
- Xuân Hải: Phụ trách quản lý `.env`, dependency, chạy regression test và release demo, viết ARCHITECTURE.md và README.md.
