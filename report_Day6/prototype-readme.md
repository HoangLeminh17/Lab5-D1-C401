# Prototype — AI hỗ trợ/gợi ý dược sĩ tìm thuốc tương tự có cùng hoạt chất

## Mô tả
Dược sĩ nhập tên một loại thuốc, hệ thống sẽ đưa ra một vài gợi ý về những loại thuốc tương tự có cùng hoạt chất, cùng với các option mô tả chi tiết các loại thuốc đã gợi ý đó nếu dược sĩ cần.

## Level: Working prototype
- UI build bằng Antigravity 
- 1 flow chính chạy thật với Gemini API: nhập tên thuốc đã hết hàng → nhận lại gợi ý các loại thuốc tương tự có hoạt chất tương đương.


## Links
- Prototype: https://github.com/HoangLeminh17/Lab5-D1-C401

## Tools
- UI: Antigravity
- AI: Antigravity
- Prompt: system prompt + few-shot examples cho 10 triệu chứng phổ biến

## Phân công
| Thành viên | Phần | Output |
|-----------|------|--------|
| Đăng Hải | Define scope, design user flow, build logic drug | User flow, acceptance criteria, replacement logic |
| Tuấn Hưng | Backend + Data Engineer | ./app/data |
| Trung Hậu | Eval metrics + ROI + demo slides | spec/spec-final.md phần 3, 5, demo/slides.pdf |
| Bảo Ngọc | UI prototype + demo script | prototype/, demo/demo-script.md |
| Minh Hoàng | UI prototype + demo script | prototype/, demo/demo-script.md |
| Xuân Hải | UI prototype + demo script | prototype/, demo/demo-script.md |
| Minh Kiên | OCR tool, viết doc | tools/ocr_and_check_pill.py |
