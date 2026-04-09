"""
ocr_invoice.py - OCR Hóa Đơn Thuốc dùng OpenAI GPT-4o Vision API
--------------------------------------------------------------------
Sử dụng:
    python ocr_invoice.py                          # scan tất cả ảnh trong INPUT_DIR
    python ocr_invoice.py --input path/to/img.jpg  # scan 1 ảnh cụ thể
    python ocr_invoice.py --input ./invoices --output ./results  # custom thư mục

Output: file JSON tại OUTPUT_DIR với cấu trúc:
[
  {"ten_thuoc": "Cefprozil", "lieu_luong": "250mg", "full_name": "Cefprozil 250mg"},
  ...
]
"""

import os
import json
import argparse
import base64
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# ──────────────────────────────────────────────
# CẤU HÌNH - chỉnh tại đây nếu cần
# ──────────────────────────────────────────────
INPUT_DIR  = Path("./drugs_image")  # Thư mục chứa ảnh hóa đơn đầu vào
OUTPUT_DIR = Path("./output")       # Thư mục lưu file JSON kết quả
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

GPT_MODEL = "gpt-4o"  # Model hỗ trợ vision tốt nhất
# ──────────────────────────────────────────────

load_dotenv()

SYSTEM_PROMPT = """Bạn là chuyên gia OCR hóa đơn thuốc.
Hãy đọc hình ảnh này và trích xuất TẤT CẢ các thuốc xuất hiện trong hóa đơn.
Với mỗi thuốc, hãy tách riêng: tên thuốc và liều lượng (mg, ml, mcg, g, IU, %).
KHÔNG trả về số lượng mua, đơn giá, hoạt chất, hay thông tin nào khác.
Kết quả BẮT BUỘC chỉ là một JSON array thuần túy (không có markdown, không có ```json), theo format:
[
  {"ten_thuoc": "<Tên thuốc>", "lieu_luong": "<liều lượng hoặc null>", "full_name": "<Tên đầy đủ>"}
]
Nếu không tìm thấy thuốc nào, trả về: []"""


def setup_openai() -> OpenAI:
    """Khởi tạo OpenAI client."""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise EnvironmentError(
            "   Không tìm thấy OPENAI_API_KEY trong file .env\n"
            "   Thêm dòng sau vào file .env:\n"
            "   OPENAI_API_KEY=sk-..."
        )
    return OpenAI(api_key=api_key)


def image_to_base64(image_path: Path) -> tuple[str, str]:
    """Đọc ảnh và encode base64, trả về (base64_data, mime_type)."""
    ext = image_path.suffix.lower()
    mime_map = {
        ".jpg":  "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png":  "image/png",
        ".webp": "image/webp",
        ".bmp":  "image/bmp",
    }
    mime_type = mime_map.get(ext, "image/jpeg")
    with open(image_path, "rb") as f:
        data = base64.b64encode(f.read()).decode("utf-8")
    return data, mime_type


def extract_drugs_from_image(client: OpenAI, image_path: Path) -> list[dict]:
    """
    Gửi ảnh lên GPT-4o Vision và trích xuất danh sách thuốc + liều lượng.
    Trả về list[dict] với keys: ten_thuoc, lieu_luong, full_name
    """
    print(f"Đang phân tích: {image_path.name} ...")

    b64_data, mime_type = image_to_base64(image_path)

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{b64_data}",
                            "detail": "high",  # high = đọc ảnh chi tiết hơn
                        },
                    },
                ],
            }
        ],
        max_tokens=1024,
        temperature=0,  # deterministic output
    )

    raw_text = response.choices[0].message.content.strip()

    # Làm sạch nếu GPT trả về có bọc markdown ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()

    try:
        drugs = json.loads(cleaned)
        if not isinstance(drugs, list):
            raise ValueError("Kết quả không phải JSON array")
        # Validate + normalize từng item
        result = []
        for item in drugs:
            result.append({
                "ten_thuoc": str(item.get("ten_thuoc", "")).strip() or None,
                "lieu_luong": item.get("lieu_luong") or None,
                "full_name":  str(item.get("full_name", "")).strip() or None,
            })
        return result
    except json.JSONDecodeError as e:
        print(f"Không parse được JSON từ GPT: {e}")
        print(f"Raw response: {raw_text[:300]}")
        return []


def save_json(data: list[dict], output_path: Path) -> None:
    """Lưu danh sách thuốc ra file JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def process_single_image(client: OpenAI, image_path: Path, output_dir: Path) -> tuple[Path, list]:
    """Xử lý 1 ảnh và lưu kết quả JSON."""
    drugs = extract_drugs_from_image(client, image_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{image_path.stem}_{timestamp}.json"
    output_path = output_dir / output_filename

    save_json(drugs, output_path)
    return output_path, drugs


def process_directory(client: OpenAI, input_dir: Path, output_dir: Path) -> None:
    """Quét toàn bộ ảnh trong thư mục và xử lý từng cái."""
    images = [p for p in input_dir.iterdir() if p.suffix.lower() in SUPPORTED_FORMATS]

    if not images:
        print(f"Không tìm thấy ảnh nào trong '{input_dir}' (hỗ trợ: {', '.join(SUPPORTED_FORMATS)})")
        return

    print(f"Tìm thấy {len(images)} ảnh trong '{input_dir}'")
    print(f"Output sẽ lưu vào: '{output_dir.resolve()}'\n")

    total_drugs = 0
    for idx, image_path in enumerate(sorted(images), 1):
        print(f"[{idx}/{len(images)}] {image_path.name}")
        output_path, drugs = process_single_image(client, image_path, output_dir)
        total_drugs += len(drugs)
        print(f" Tìm được {len(drugs)} thuốc → {output_path.name}")
        for d in drugs:
            tag = f"[{d['lieu_luong']}]" if d.get("lieu_luong") else "[không có liều lượng]"
            print(f"     • {d['ten_thuoc']} {tag}")
        print()

    print("─" * 50)
    print(f"Hoàn tất! Đã xử lý {len(images)} ảnh, tổng {total_drugs} thuốc được nhận dạng.")
    print(f"Kết quả JSON lưu tại: {output_dir.resolve()}")


def main():
    parser = argparse.ArgumentParser(
        description="OCR hóa đơn thuốc - trích xuất tên thuốc + liều lượng bằng GPT-4o Vision"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help=f"Đường dẫn đến ảnh hoặc thư mục chứa ảnh (mặc định: {INPUT_DIR})"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help=f"Thư mục lưu file JSON kết quả (mặc định: {OUTPUT_DIR})"
    )
    args = parser.parse_args()

    input_path = Path(args.input)  if args.input  else INPUT_DIR
    output_dir = Path(args.output) if args.output else OUTPUT_DIR

    print("=" * 50)
    print("  OCR Hóa Đơn Thuốc - Powered by GPT-4o Vision")
    print("=" * 50)

    # Khởi tạo OpenAI client
    try:
        client = setup_openai()
        print(f"✅ OpenAI model: {GPT_MODEL}\n")
    except EnvironmentError as e:
        print(e)
        return

    # Xử lý ảnh đơn hoặc cả thư mục
    if input_path.is_file():
        if input_path.suffix.lower() not in SUPPORTED_FORMATS:
            print(f" Định dạng không hỗ trợ: {input_path.suffix}")
            return
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f" Xử lý ảnh đơn: {input_path.name}")
        print(f" Output: '{output_dir.resolve()}'\n")
        output_path, drugs = process_single_image(client, input_path, output_dir)
        print(f" Tìm được {len(drugs)} thuốc → {output_path.name}")
        for d in drugs:
            tag = f"[{d['lieu_luong']}]" if d.get("lieu_luong") else "[không có liều lượng]"
            print(f"     • {d['ten_thuoc']} {tag}")
        print("\n" + "─" * 50)
        print(f" Hoàn tất! Kết quả JSON lưu tại: {output_path.resolve()}")

    elif input_path.is_dir():
        process_directory(client, input_path, output_dir)

    else:
        print(f"   Không tìm thấy đường dẫn: '{input_path}'")
        print(f"   Hãy tạo thư mục '{INPUT_DIR}' và đặt ảnh hóa đơn vào đó,")
        print(f"   hoặc dùng: python ocr_invoice.py --input path/to/image.jpg")


if __name__ == "__main__":
    main()
