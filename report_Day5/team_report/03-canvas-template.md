# AI Product Canvas — template
Nhóm D1-C401
Điền Canvas cho product AI của nhóm. Mỗi ô có câu hỏi guide — trả lời trực tiếp, xóa phần in nghiêng khi điền.

---

## Canvas

|   | Value | Trust | Feasibility |
|---|-------|-------|-------------|
| **Câu hỏi guide** | User nào? Pain gì? AI giải quyết gì mà cách hiện tại không giải được? | Khi AI sai thì user bị ảnh hưởng thế nào? User biết AI sai bằng cách nào? User sửa bằng cách nào? | Cost bao nhiêu/request? Latency bao lâu? Risk chính là gì? |
| **Trả lời** |**User:** Hành khách của Vietnam Airlines (đặt vé, tra cứu chuyến bay, hành lý, thủ tục)<br><br>**Pain:**<br>- Khó tìm thông tin nhanh trên website (nhiều bước)<br>- Không rõ quy định hành lý / chuyến bay<br>- Không biết xử lý khi có vấn đề (delay, đổi vé)<br><br>**AI giải quyết:**<br>- Chatbot NEO trả lời trực tiếp câu hỏi<br>- Hỗ trợ đa kênh (web, Facebook, Zalo)<br>- Có thể hướng dẫn đặt vé, đưa link trực tiếp<br>- Cho phép upload ảnh (vé, hành lý) để hỏi<br>- Escalate sang nhân viên khi cần<br><br>-> Giảm friction so với việc tự tìm trên web | **Nếu AI sai:**<br>- User có thể hiểu sai quy định hành lý / chuyến bay<br>- Có thể dẫn đến mất tiền hoặc lỡ chuyến<br><br>**User phát hiện sai khi:**<br>- So sánh với website chính thức<br>- Ra sân bay và bị từ chối hành lý<br>- AI trả lời không nhất quán<br><br>**User sửa bằng cách:**<br>- Hỏi lại chatbot (clarify)<br>- Liên hệ CSKH / nhân viên thật<br>- Kiểm tra lại trên web chính thức<br><br>**Mitigation:**<br>- Khi confidence thấp -> hỏi lại user<br>- Khi query phức tạp -> chuyển human<br>- Show nguồn (link chính thức) | **Cost:**<br>- LLM call ~ vài cent/request<br>- Có thể tăng nếu dùng multimodal (ảnh)<br><br>**Latency:**<br>- 1–5s/response (LLM + backend)<br><br>**Risk chính:**<br>- Hallucination (trả lời sai quy định)<br>- Không hiểu context (ảnh, câu hỏi mơ hồ)<br>- Không cover hết edge case (hành lý đặc biệt)<br>- Multimodal chưa đủ tốt -> trả lời sai từ ảnh |

---

---

## Automation hay augmentation?

Augmentation — AI gợi ý, user quyết định cuối cùng

**Justify:** ___

- Khi AI sai, hậu quả khá lớn (liên quan chuyến bay, tiền bạc)  
- User vẫn cần verify hoặc quyết định cuối  
- Có escalation sang nhân viên -> không fully automate  


---

## Learning signal

| # | Câu hỏi | Trả lời |
|---|---------|---------|
| 1 | User correction đi vào đâu? | - Log hội thoại chatbot<br>- Các lần user hỏi lại / sửa câu trả lời<br>- Case bị escalate sang nhân viên |
| 2 | Product thu signal gì để biết tốt lên hay tệ đi? | - Tỷ lệ resolve không cần human<br>- Tỷ lệ user hỏi lại cùng 1 câu<br>- Feedback user (thumb up/down)<br>- Thời gian xử lý trung bình |
| 3 | Data thuộc loại nào? | Domain-specific; Real-time; Human-judgment; User-specific |

**Có marginal value không?** (Model đã biết cái này chưa? Ai khác cũng thu được data này không?)

- Có, vì data nội bộ (quy định hãng bay, case thực tế) không public hoàn toàn  
- Log hội thoại giúp model hiểu đúng context user Việt  
- Các edge case mang tính đặc thù domain  
---
## Sketch As-is / To-be

### As-is
- User hỏi mơ hồ (ví dụ: hành lý xách tay)  
- AI hỏi lại chuyến bay -> gây friction  
- AI thiếu context -> trả lời chưa đúng  

-> Gãy ở: thiếu context + hỏi vòng  

### To-be
- AI hiểu intent ngay từ câu đầu  
- Cho phép upload ảnh + hiểu luôn  
- Chủ động suy luận context (nội địa/quốc tế)  

-> Giảm số bước hỏi lại, tăng tốc trả lời

## Cách dùng

1. Điền Value trước — chưa rõ pain thì chưa điền Trust/Feasibility
2. Trust: trả lời 4 câu UX (đúng -> sai -> không chắc -> user sửa)
3. Feasibility: ước lượng cost, không cần chính xác — order of magnitude đủ
4. Learning signal: nghĩ về vòng lặp dài hạn, không chỉ demo ngày mai
5. Đánh [?] cho chỗ chưa biết — Canvas là hypothesis, không phải đáp án

---

*AI Product Canvas — Ngày 5 — VinUni A20 — AI Thực Chiến · 2026*
