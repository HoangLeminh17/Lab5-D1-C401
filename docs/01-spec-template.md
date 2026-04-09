# SPEC — AI Product Hackathon

**Nhóm:** D1-C401
**Track:** ☐ VinFast · ☐ Vinmec · ☐ VinUni-VinSchool · ☐ XanhSM · ☑ Open
**Problem statement (1 câu):** Dược sĩ quầy thuốc cần tìm nhanh thuốc thay thế, chuẩn hóa tên thuốc và kiểm tra tương tác trong toa; chatbot AI dùng OpenFDA + RxNorm + tồn kho nội bộ để gợi ý còn hàng, cảnh báo rủi ro và rút ngắn thời gian tư vấn.

---

## 1. AI Product Canvas

|   | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| **Câu hỏi** | User nào? Pain gì? AI giải gì? | Khi AI sai thì sao? User sửa bằng cách nào? | Cost/latency bao nhiêu? Risk chính? |
| **Trả lời** | Dược sĩ quầy thuốc và nhân viên tư vấn thường phải tra cứu thủ công tên thuốc, hoạt chất, tồn kho và cảnh báo an toàn. Hệ thống này nhận tên thuốc bị hết hàng, tự chuẩn hóa tên bằng API khác, tra OpenFDA lấy hoạt chất/chỉ định/chống chỉ định/tác dụng phụ, rồi đối chiếu với inventory nội bộ để gợi ý thuốc thay thế còn hàng. Vì dữ liệu nội bộ của nhà thuốc có tồn kho và tên thương mại thật, kết quả thực dụng hơn một chatbot tổng quát như ChatGPT. | Nếu AI sai, dược sĩ vẫn là người quyết định cuối. UI luôn hiển thị nguồn FDA, cảnh báo rõ ràng, cho phép duyệt/từ chối/tư vấn khác, và coi “không tìm thấy dữ liệu” là trạng thái cần kiểm tra chứ không phải an toàn. Với đơn nhiều thuốc, hệ thống kiểm tra tương tác theo từng cặp và chỉ dùng để hỗ trợ ra quyết định, không tự chốt bán. | Mỗi lượt có thể cần 2-4 lần gọi API (OpenFDA, RxNorm, Gemini) + đọc CSV nội bộ. Mục tiêu latency end-to-end là dưới 5 giây. Rủi ro chính là timeout API, dữ liệu FDA thiếu hoặc không đồng nhất, và map sai brand/generic name khi người dùng gõ thiếu/thừa chữ. |

**Automation hay augmentation?** ☑ Automation · ☑ Augmentation
Justify: Augmentation là chính. AI đưa ra gợi ý và cảnh báo, nhưng dược sĩ vẫn duyệt/từ chối trước khi quyết định cuối. Một phần workflow có thể tự động hóa ở mức tra cứu và lọc thuốc thay thế, nhưng không được tự động chốt tư vấn an toàn.

**Learning signal:**

1. User correction đi vào đâu? Ghi nhận trạng thái duyệt/từ chối, trường hợp người dùng đổi thuốc/nhập lại tên, và các case không có kết quả để cập nhật mapping tên thuốc, inventory, và prompt/rule xử lý.
2. Product thu signal gì để biết tốt lên hay tệ đi? Tỷ lệ duyệt bán, tỷ lệ từ chối, tỷ lệ người dùng phải sửa lại tên thuốc, tỷ lệ query không ra kết quả, thời gian đến khi ra quyết định, và số case cảnh báo tương tác được xác nhận.
3. Data thuộc loại nào? ☑ User-specific · ☑ Domain-specific · ☑ Real-time · ☑ Human-judgment · ☐ Khác: ___
   Có marginal value không? Có, rất cao. Model tổng quát không biết tồn kho nhà thuốc, tên thương mại nội bộ, hay ngữ cảnh bán thuốc thực tế nên dữ liệu nội bộ mang giá trị tăng thêm rõ rệt.

---

## 2. User Stories — 4 paths

Mỗi feature chính = 1 bảng. AI trả lời xong → chuyện gì xảy ra?

### Feature: Tìm thuốc thay thế theo hoạt chất

**Trigger:** Dược sĩ nhập tên thuốc hết hàng hoặc thuốc khách hỏi → AI chuẩn hóa tên → tra OpenFDA → lấy hoạt chất → tìm các thuốc còn hàng trong inventory nội bộ → hiển thị danh sách thay thế.

| Path | Câu hỏi thiết kế | Mô tả |
|------|-------------------|-------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | AI trả về hoạt chất, thông tin FDA, và danh sách thuốc thay thế còn hàng. Dược sĩ xem được tên thuốc, hoạt chất và số lượng tồn kho, rồi dùng ngay để tư vấn bán. |
| Low-confidence — AI không chắc | System báo "không chắc" bằng cách nào? User quyết thế nào? | Nếu tên thuốc bị gõ sai, brand/generic mơ hồ, hoặc OpenFDA không có record rõ ràng, hệ thống hiển thị tên đã chuẩn hóa và yêu cầu dược sĩ xác nhận trước khi dùng kết quả. |
| Failure — AI sai | User biết AI sai bằng cách nào? Recover ra sao? | Nếu AI map nhầm hoạt chất hoặc không thấy tồn kho đúng, dược sĩ sẽ thấy danh sách thay thế không khớp với thuốc thực tế. UI phải cho phép thử lại với tên khác hoặc chuyển sang kiểm tra thủ công. |
| Correction — user sửa | User sửa bằng cách nào? Data đó đi vào đâu? | Dược sĩ nhập lại tên đúng, chọn “Tư vấn khác”, hoặc từ chối gợi ý. Các phản hồi này đi vào log phản hồi để cập nhật synonym, whitelist brand name, và rule normalize. |

### Feature: Giải thích nhanh một thuốc thay thế

**Trigger:** Dược sĩ bấm nút “Không rõ thuốc này? Giải thích thêm” trên thẻ thuốc thay thế.

| Path | Câu hỏi thiết kế | Mô tả |
|------|-------------------|-------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | AI trả lời ngắn gọn bằng tiếng Việt: thuốc là gì, dùng khi nào, đường dùng, cảnh báo quan trọng và tác dụng phụ. Dược sĩ đọc nhanh rồi quyết định có dùng thuốc này hay không. |
| Low-confidence — AI không chắc | System báo "không chắc" bằng cách nào? User quyết thế nào? | Nếu dữ liệu FDA thiếu, hệ thống nói rõ phần nào không đủ dữ liệu thay vì tự bịa. Dược sĩ có thể bỏ qua hoặc chọn thuốc thay thế khác. |
| Failure — AI sai | User biết AI sai bằng cách nào? Recover ra sao? | Nếu giải thích quá chung chung, lệch với thuốc đang cầm hoặc quá dài, user có thể thấy ngay qua thẻ thuốc và quay lại danh sách thay thế. |
| Correction — user sửa | User sửa bằng cách nào? Data đó đi vào đâu? | Khi dược sĩ bỏ qua hoặc yêu cầu giải thích lại, hệ thống có thể tinh chỉnh prompt rút gọn hơn và ưu tiên cảnh báo quan trọng. |

### Feature: Kiểm tra tương tác thuốc trong toa

**Trigger:** Dược sĩ nhập một danh sách thuốc trong đơn hoặc hệ thống nhận được nhiều thuốc cần kiểm tra → tạo các cặp thuốc → gọi OpenFDA drug label để tìm drug_interactions.

| Path | Câu hỏi thiết kế | Mô tả |
|------|-------------------|-------|
| Happy — AI đúng, tự tin | User thấy gì? Flow kết thúc ra sao? | Hệ thống trả về các cặp có tương tác và đoạn cảnh báo trích từ FDA label. Dược sĩ dùng cảnh báo đó để đổi thuốc hoặc hỏi bác sĩ. |
| Low-confidence — AI không chắc | System báo "không chắc" bằng cách nào? User quyết thế nào? | Nếu chỉ có 1 thuốc, tên chưa chuẩn hóa, hoặc OpenFDA không có record, hệ thống báo cần thêm dữ liệu và không suy ra an toàn. |
| Failure — AI sai | User biết AI sai bằng cách nào? Recover ra sao? | Nguy cơ lớn nhất là OpenFDA không ghi tương tác dù thực tế có tương tác. Khi đó user chỉ nhìn thấy “không có dữ liệu”, nên UI phải nhấn mạnh rằng thiếu dữ liệu không đồng nghĩa an toàn. |
| Correction — user sửa | User sửa bằng cách nào? Data đó đi vào đâu? | Nếu dược sĩ phát hiện combo cần lưu ý nhưng hệ thống chưa báo, case đó nên được đưa vào danh sách review thủ công để bổ sung rule an toàn nội bộ. |

---

## 3. Eval metrics + threshold

**Optimize precision hay recall?** ☑ Precision · ☐ Recall
Tại sao? Bài toán thuốc ưu tiên an toàn hơn độ phủ. Sai sót kiểu gợi ý nhầm hoặc bỏ sót cảnh báo có thể gây hại cho bệnh nhân, nên cần precision cao và chấp nhận recall thấp hơn một chút để dược sĩ có thể kiểm tra thủ công.
Nếu sai ngược lại thì chuyện gì xảy ra? Nếu chỉ tối ưu recall mà precision thấp, hệ thống sẽ trả quá nhiều gợi ý hoặc cảnh báo nhiễu, làm dược sĩ mất niềm tin và bỏ dùng. Nếu ngược lại precision cao nhưng recall thấp, hệ thống có thể bỏ sót một phần kết quả nhưng vẫn an toàn hơn vì có fallback thủ công.

| Metric | Threshold | Red flag (dừng khi) |
|--------|-----------|---------------------|
| Precision của thuốc thay thế đúng hoạt chất trên bộ test nội bộ | ≥92% | <85% trong 1 tuần |
| Recall cảnh báo tương tác thuốc nguy hiểm trên bộ case curated | ≥95% | Bất kỳ critical miss nào trong bộ kiểm thử |
| P95 latency end-to-end cho một lượt tư vấn | ≤5 giây | >8 giây hoặc timeout API lặp lại >5% |

---

## 4. Top 3 failure modes

Liệt kê cách product có thể fail — không phải list features.
"Failure mode nào user KHÔNG BIẾT bị sai? Đó là cái nguy hiểm nhất."

| # | Trigger | Hậu quả | Mitigation |
|---|---------|---------|------------|
| 1 | Tên thuốc bị gõ thiếu/thừa chữ, brand name không chuẩn hoặc nhiều tên thương mại trùng nhau | AI map sai sang hoạt chất khác, dẫn tới gợi ý thay thế sai | Dùng RxNorm approximate term để chuẩn hóa, hiển thị tên đã normalize cho dược sĩ xác nhận, và cho phép retry ngay trên UI |
| 2 | OpenFDA không có record đầy đủ, field bị thiếu hoặc label quá dài/inconsistent | AI có thể trả lời quá tự tin hoặc làm user hiểu nhầm rằng thuốc “an toàn” | Khi thiếu dữ liệu phải hiển thị rõ “không đủ dữ liệu”, trích nguồn FDA, và không coi 404 là an toàn |
| 3 | Tương tác thuốc không được ghi trong drug label dù ngoài thực tế vẫn có rủi ro | Hệ thống bỏ sót cảnh báo quan trọng, nguy cơ cao nhất vì user không biết mình bị sai | Dùng kết quả như hỗ trợ, không tự động chốt; với đơn nhiều thuốc và nhóm nguy cơ cao phải yêu cầu manual review |

---

## 5. ROI 3 kịch bản

|   | Conservative | Realistic | Optimistic |
|---|-------------|-----------|------------|
| **Assumption** | 50 lượt/ngày, 40% chấp nhận gợi ý, mỗi lượt tiết kiệm 2 phút | 200 lượt/ngày, 70% chấp nhận, mỗi lượt tiết kiệm 4 phút | 500 lượt/ngày, 85% chấp nhận, mỗi lượt tiết kiệm 5 phút |
| **Cost** | ~$3/ngày cho API + vận hành nhẹ | ~$10/ngày | ~$25/ngày |
| **Benefit** | Tiết kiệm khoảng 40 phút công tư vấn/ngày và giảm sai sót tra cứu thủ công | Tiết kiệm khoảng 9 giờ công/ngày, tăng tốc độ phục vụ quầy | Tiết kiệm hơn 30 giờ công/ngày, giảm đáng kể thời gian chờ và tăng throughput |
| **Net** | Dương nhẹ, phù hợp pilot nhỏ | Dương rõ rệt, đủ lý do mở rộng | Dương mạnh, có thể trở thành workflow mặc định |

**Kill criteria:** Dừng hoặc quay lại workflow thủ công nếu có bất kỳ critical interaction miss nào trong validation, nếu precision thuốc thay thế xuống dưới ngưỡng trong 2 tuần liên tiếp, hoặc nếu chi phí API/lỗi mạng làm P95 latency vượt 8 giây kéo dài.

---

## 6. Mini AI spec (1 trang)

Hệ thống này là một chatbot hỗ trợ dược sĩ quầy thuốc khi cần tìm thuốc thay thế hoặc kiểm tra an toàn đơn thuốc. User nhập tên thuốc bị hết hàng, hệ thống tự chuẩn hóa tên bằng API RxNorm-like để xử lý typo thiếu/thừa chữ, sau đó tra OpenFDA để lấy hoạt chất, đường dùng, chỉ định, chống chỉ định và tác dụng phụ. Từ hoạt chất đó, hệ thống đối chiếu với inventory nội bộ của nhà thuốc để gợi ý các thuốc còn hàng có cùng hoạt chất, rồi dùng Gemini để trình bày kết quả ngắn gọn bằng tiếng Việt cho dược sĩ.

Đây là bài toán augmentation hơn là automation. AI không tự chốt đơn hay tự thay thế thuốc; nó chỉ đưa ra gợi ý có nguồn và cảnh báo, còn dược sĩ là người quyết định cuối cùng. Vì dữ liệu nội bộ biết tên thương mại, tồn kho và ngữ cảnh bán hàng thực tế, hệ thống có giá trị cao hơn một chatbot tổng quát như ChatGPT cho cùng bài toán.

Chất lượng cần ưu tiên precision, đặc biệt ở hai chỗ: map đúng hoạt chất/tên thuốc và không bỏ sót cảnh báo tương tác nguy hiểm. Khi dữ liệu thiếu hoặc không chắc, hệ thống phải nói rõ là chưa đủ dữ liệu thay vì suy đoán. Learning loop đến từ phản hồi duyệt/từ chối, case sửa tên thuốc, case không ra kết quả, và các case tương tác được phát hiện thủ công để cập nhật inventory, synonym map, prompt và rule an toàn.
