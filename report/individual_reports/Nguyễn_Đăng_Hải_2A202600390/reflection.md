# Individual reflection — Nguyễn Đăng Hải (2A202600390)

## 1. Role
Tôi đảm nhiệm vai trò Product Owner (PO): chốt scope bài toán, định nghĩa user flow, thống nhất acceptance criteria với team, và dựng khung hệ thống để các module có thể ghép được với nhau.

Trọng tâm phần tôi phụ trách là cơ chế tìm kiếm thuốc thay thế theo hoạt chất từ dữ liệu nội bộ, sau khi lấy được thông tin chuẩn hóa từ OpenFDA/RxNorm.

## 2. Đóng góp cụ thể
- Chốt bài toán theo hướng augmentation: AI hỗ trợ dược sĩ ra quyết định, không tự động chốt đơn.
- Thiết kế user flow chính: nhập thuốc hết hàng -> chuẩn hóa tên thuốc -> lấy thông tin FDA -> tìm thuốc thay thế còn hàng -> hiển thị cảnh báo/an toàn -> dược sĩ duyệt hoặc từ chối.
- Định nghĩa acceptance criteria cho vòng demo:
  - trả được hoạt chất và cảnh báo chính (nếu có dữ liệu),
  - gợi ý thuốc thay thế có tồn kho > 0,
  - phản hồi UI rõ ràng khi thiếu dữ liệu,
  - có vòng feedback Duyệt/Từ chối.
- Xây dựng logic cốt lõi cho tìm thuốc thay thế:
  - ưu tiên match chính xác theo `Hoat_Chat`,
  - fallback match theo chuỗi chứa hoạt chất,
  - lọc `Ton_Kho > 0`,
  - trả về danh sách thuốc có thể tư vấn ngay tại quầy.
- Thống nhất cách xử lý rủi ro sản phẩm: luôn hiển thị cảnh báo rằng dữ liệu thiếu/404 không đồng nghĩa an toàn.

## 3. SPEC mạnh/yếu
### Điểm mạnh
- SPEC bám rất sát pain point thực tế của quầy thuốc: tốc độ + an toàn + tồn kho nội bộ.
- Canvas có phân tách rõ Value / Trust / Feasibility, giúp team không sa đà vào feature không cần thiết.
- Failure modes đi đúng bản chất domain dược: sai mapping tên thuốc, thiếu dữ liệu FDA, và false sense of safety khi không tìm thấy tương tác.

### Điểm còn yếu
- Một số metric ban đầu thiên về kỹ thuật (precision/recall) hơn là vận hành lâm sàng.
- ROI ở bản đầu còn ước lượng khá thô, chưa tách rõ chi phí cố định và chi phí biến đổi theo số lượt dùng.
- Tài liệu và code có lúc lệch phiên bản (ví dụ module `rag_engine`), ảnh hưởng khả năng onboard nhanh.

## 4. Đóng góp ngoài phạm vi chính
- Review và làm rõ lại luồng UX với các trạng thái lỗi: không tìm thấy thuốc, timeout API, thiếu dữ liệu cảnh báo.
- Phối hợp với thành viên phụ trách data để chuẩn hóa cột inventory (`Ten_Thuoc`, `Hoat_Chat`, `Ton_Kho`) nhằm giảm lỗi ghép module.
- Góp ý phần README/Spec để nhấn mạnh quyết định cuối cùng vẫn thuộc về dược sĩ hoặc bác sĩ.

## 5. Điều học được
Vai trò PO trong AI product không chỉ là viết tính năng, mà là giữ ranh giới giữa “có thể làm” và “nên làm”.

Tôi học được rằng với domain y tế/dược:
- UX phải thể hiện mức độ chắc chắn của hệ thống,
- dữ liệu thiếu phải nói rõ là thiếu,
- và metric tốt nhất không phải lúc nào cũng là số đẹp nhất, mà là metric giúp giảm rủi ro thực tế cho người dùng.

Ngoài ra, thiết kế data flow sớm (normalize -> retrieve -> match inventory -> explain -> feedback) giúp team code nhanh hơn và ít xung đột interface hơn.

## 6. Nếu làm lại
- Tôi sẽ khóa interface contract giữa các module ngay từ ngày đầu (đầu vào/đầu ra, key bắt buộc) để giảm lệch giữa docs và implementation.
- Tôi sẽ bổ sung bộ test case nghiệp vụ sớm hơn cho các tình huống khó:
  - tên thuốc gõ sai,
  - thuốc đa hoạt chất,
  - trường hợp OpenFDA thiếu dữ liệu,
  - đơn nhiều thuốc có tương tác.
- Tôi sẽ đưa KPI vận hành vào demo sớm (time-to-answer, acceptance rate, correction rate) thay vì chờ cuối vòng.

## 7. AI giúp gì / AI sai gì
- **AI giúp:** tăng tốc brainstorm failure modes, gợi ý nhanh các tình huống edge cases, và hỗ trợ soạn thảo/tinh chỉnh SPEC theo cấu trúc rõ ràng.
- **AI sai/mislead:** có xu hướng đề xuất mở rộng scope quá sớm (thêm tính năng ngoài mục tiêu hackathon) hoặc trả lời quá tự tin khi dữ liệu thiếu.

Bài học tôi rút ra: AI rất hiệu quả để tăng tốc product thinking, nhưng PO phải luôn giữ kỷ luật scope, kiểm chứng với code thực tế, và ưu tiên an toàn người dùng trong mọi quyết định.