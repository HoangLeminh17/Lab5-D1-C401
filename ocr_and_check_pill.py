"""
ocr_and_check_pill.py - Pipeline OCR + Kiểm Tra Tồn Kho Thuốc
---------------------------------------------------------------
Luồng xử lý:
  1. Nhận ảnh hóa đơn thuốc (đơn lẻ hoặc cả thư mục)
  2. Dùng GPT-4o Vision để OCR → trích xuất tên thuốc + liều lượng
  3. So khớp từng thuốc với file inventory.csv (kiểm tra tồn kho)
  4. Xuất kết quả OCR (JSON) và kết quả kiểm tra (JSON)

Sử dụng:
    python ocr_and_check_pill.py                          # scan tất cả ảnh trong INPUT_DIR
    python ocr_and_check_pill.py --input path/to/img.jpg  # scan 1 ảnh cụ thể
    python ocr_and_check_pill.py --input ./invoices --output ./results --inventory ./inventory.csv
"""

import os
import csv
import json
import logging
import argparse
import base64
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

# ──────────────────────────────────────────────
# CẤU HÌNH MẶC ĐỊNH
# ──────────────────────────────────────────────
INPUT_DIR      = Path("./drugs_image")   # Thư mục chứa ảnh hóa đơn đầu vào
OUTPUT_DIR     = Path("./output")        # Thư mục lưu file JSON kết quả OCR
CHECK_DIR      = Path("./check")         # Thư mục lưu file JSON kết quả kiểm kho
INVENTORY_FILE = Path("./inventory.csv") # File CSV tồn kho
SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
GPT_MODEL = "gpt-4o"
# ──────────────────────────────────────────────


# ══════════════════════════════════════════════
# SETUP LOGGING
# ══════════════════════════════════════════════
def setup_logging() -> logging.Logger:
    """
    Cấu hình logging với 2 handler:
      - Console (StreamHandler): hiển thị ra terminal
      - File (FileHandler): ghi vào logs/pipeline_<timestamp>.log
    """
    log_dir = Path("./logs")
    log_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"pipeline_{timestamp}.log"

    logger = logging.getLogger("ocr_pill_pipeline")
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        fmt="%(asctime)s  [%(levelname)-8s]  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Handler cho console
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    # Handler cho file (ghi cả DEBUG)
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    logger.addHandler(ch)
    logger.addHandler(fh)

    logger.info(f"Log file: {log_file.resolve()}")
    return logger


# ══════════════════════════════════════════════
# SYSTEM PROMPT CHO GPT-4o VISION
# ══════════════════════════════════════════════
SYSTEM_PROMPT = """Bạn là chuyên gia OCR hóa đơn thuốc.
Hãy đọc hình ảnh này và trích xuất TẤT CẢ các thuốc xuất hiện trong hóa đơn.
Với mỗi thuốc, hãy tách riêng: tên thuốc và liều lượng (mg, ml, mcg, g, IU, %).
KHÔNG trả về số lượng mua, đơn giá, hoạt chất, hay thông tin nào khác.
Kết quả BẮT BUỘC chỉ là một JSON array thuần túy (không có markdown, không có ```json), theo format:
[
  {"ten_thuoc": "<Tên thuốc>", "lieu_luong": "<liều lượng hoặc null>", "full_name": "<Tên đầy đủ>"}
]
Nếu không tìm thấy thuốc nào, trả về: []"""


# ══════════════════════════════════════════════
# BƯỚC 1 — KHỞI TẠO OPENAI CLIENT
# ══════════════════════════════════════════════
def setup_openai(logger: logging.Logger) -> OpenAI:
    """Khởi tạo OpenAI client từ biến môi trường OPENAI_API_KEY."""
    logger.info("BƯỚC 1 — Khởi tạo OpenAI client ...")
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        logger.error("Không tìm thấy OPENAI_API_KEY trong file .env")
        raise EnvironmentError(
            "Không tìm thấy OPENAI_API_KEY. Thêm dòng sau vào .env:\n"
            "OPENAI_API_KEY=sk-..."
        )
    logger.info(f"OpenAI client khởi tạo thành công | model: {GPT_MODEL}")
    return OpenAI(api_key=api_key)


# ══════════════════════════════════════════════
# BƯỚC 2 — TẢI DỮ LIỆU TỒN KHO
# ══════════════════════════════════════════════
def load_inventory(inventory_path: Path, logger: logging.Logger) -> dict[str, str]:
    """
    Đọc file CSV tồn kho, trả về dict {Ten_Thuoc: Ton_Kho}.
    Cột bắt buộc: Ten_Thuoc, Ton_Kho
    """
    logger.info(f"BƯỚC 2 — Tải dữ liệu tồn kho từ: {inventory_path.resolve()}")

    if not inventory_path.exists():
        logger.error(f"Không tìm thấy file inventory: {inventory_path}")
        raise FileNotFoundError(f"Không tìm thấy file inventory: {inventory_path}")

    stock: dict[str, str] = {}
    with open(inventory_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get("Ten_Thuoc", "").strip()
            qty  = row.get("Ton_Kho",   "").strip()
            if name:
                stock[name] = qty

    logger.info(f"Tải thành công {len(stock)} mặt hàng từ inventory.")
    logger.debug(f"Danh sách thuốc trong kho: {list(stock.keys())}")
    return stock


# ══════════════════════════════════════════════
# BƯỚC 3 — OCR ẢNH (gọi GPT-4o Vision)
# ══════════════════════════════════════════════
def image_to_base64(image_path: Path) -> tuple[str, str]:
    """Encode ảnh sang base64, trả về (base64_data, mime_type)."""
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


def extract_drugs_from_image(
    client: OpenAI,
    image_path: Path,
    logger: logging.Logger,
) -> list[dict]:
    """
    Gửi ảnh lên GPT-4o Vision và trích xuất danh sách thuốc + liều lượng.
    Trả về list[dict] với keys: ten_thuoc, lieu_luong, full_name
    """
    logger.info(f"  → Đang gửi ảnh lên GPT-4o Vision: {image_path.name}")
    logger.debug(f"  → Đường dẫn đầy đủ: {image_path.resolve()}")

    b64_data, mime_type = image_to_base64(image_path)
    logger.debug(f"  → Encode base64 thành công | mime_type: {mime_type}")

    try:
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": SYSTEM_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_data}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            max_tokens=1024,
            temperature=0,
        )
        logger.debug("  → Nhận phản hồi từ GPT-4o Vision thành công.")
    except Exception as e:
        logger.error(f"  → Lỗi khi gọi OpenAI API: {e}")
        raise

    raw_text = response.choices[0].message.content.strip()
    logger.debug(f"  → Raw response (300 ký tự đầu): {raw_text[:300]}")

    # Làm sạch nếu GPT bọc markdown ```json ... ```
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_text, flags=re.MULTILINE).strip()

    try:
        drugs = json.loads(cleaned)
        if not isinstance(drugs, list):
            raise ValueError("Kết quả không phải JSON array")
        result = []
        for item in drugs:
            result.append({
                "ten_thuoc": str(item.get("ten_thuoc", "")).strip() or None,
                "lieu_luong": item.get("lieu_luong") or None,
                "full_name":  str(item.get("full_name", "")).strip() or None,
            })
        logger.info(f"  → OCR thành công: tìm được {len(result)} thuốc.")
        return result
    except json.JSONDecodeError as e:
        logger.error(f"  → Không parse được JSON từ GPT: {e}")
        logger.error(f"  → Raw response: {raw_text[:300]}")
        return []


def ocr_image(
    client: OpenAI,
    image_path: Path,
    output_dir: Path,
    logger: logging.Logger,
) -> tuple[Path, list[dict]]:
    """OCR 1 ảnh và lưu kết quả JSON vào output_dir."""
    logger.info(f"BƯỚC 3 — OCR ảnh: {image_path.name}")
    drugs = extract_drugs_from_image(client, image_path, logger)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{image_path.stem}_{timestamp}.json"
    output_path = output_dir / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(drugs, f, ensure_ascii=False, indent=2)

    logger.info(f"  → Đã lưu kết quả OCR: {output_path.name}")
    for d in drugs:
        tag = f"[{d['lieu_luong']}]" if d.get("lieu_luong") else "[không có liều lượng]"
        logger.info(f"     • {d['ten_thuoc']} {tag}")

    return output_path, drugs


# ══════════════════════════════════════════════
# BƯỚC 4 — KIỂM TRA TỒN KHO
# ══════════════════════════════════════════════
def check_inventory(
    drugs: list[dict],
    stock: dict[str, str],
    ocr_json_path: Path,
    check_dir: Path,
    logger: logging.Logger,
) -> Path:
    """
    So khớp từng thuốc trong danh sách OCR với kho inventory.
    Ghi kết quả ra file JSON trong check_dir.
    Trả về đường dẫn file kết quả.
    """
    logger.info("BƯỚC 4 — Kiểm tra tồn kho ...")
    results = []

    for item in drugs:
        full_name = str(item.get("full_name", "")).strip()
        qty = stock.get(full_name)

        if qty is None:
            status = "KHÔNG TÌM THẤY trong kho"
            logger.warning(f"  ✗ {full_name!r} → {status}")
        else:
            qty_int = int(qty) if qty.isdigit() else 0
            if qty_int > 0:
                status = f"CÒN HÀNG — tồn kho: {qty}"
                logger.info(f"  ✓ {full_name!r} → {status}")
            else:
                status = "HẾT HÀNG — tồn kho: 0"
                logger.warning(f"  ⚠ {full_name!r} → {status}")

        results.append({
            "full_name":    full_name,
            "co_trong_db":  qty is not None,
            "ton_kho":      qty if qty is not None else "KHONG_TIM_THAY",
            "trang_thai":   status,
        })

    check_dir.mkdir(parents=True, exist_ok=True)
    out_filename = f"check_{ocr_json_path.stem}.json"
    out_file = check_dir / out_filename

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "source_ocr_file": str(ocr_json_path),
                "timestamp": datetime.now().isoformat(),
                "results": results,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    logger.info(f"  → Đã lưu kết quả kiểm kho: {out_file.resolve()}")
    return out_file


# ══════════════════════════════════════════════
# XỬ LÝ 1 ẢNH ĐƠN LẺ (end-to-end)
# ══════════════════════════════════════════════
def run_pipeline_single(
    client: OpenAI,
    image_path: Path,
    output_dir: Path,
    check_dir: Path,
    stock: dict[str, str],
    logger: logging.Logger,
) -> None:
    """Chạy toàn bộ pipeline OCR → Kiểm kho cho 1 ảnh."""
    logger.info(f"{'─' * 55}")
    logger.info(f"Bắt đầu xử lý ảnh: {image_path.name}")
    logger.info(f"{'─' * 55}")

    # Bước 3: OCR
    ocr_path, drugs = ocr_image(client, image_path, output_dir, logger)

    if not drugs:
        logger.warning("Không tìm được thuốc nào từ ảnh — bỏ qua bước kiểm kho.")
        return

    # Bước 4: Kiểm kho
    check_file = check_inventory(drugs, stock, ocr_path, check_dir, logger)

    logger.info(f"{'═' * 55}")
    logger.info(f"HOÀN TẤT xử lý: {image_path.name}")
    logger.info(f"  OCR  JSON  : {ocr_path.resolve()}")
    logger.info(f"  Check JSON : {check_file.resolve()}")
    logger.info(f"{'═' * 55}")


# ══════════════════════════════════════════════
# XỬ LÝ CẢ THƯ MỤC
# ══════════════════════════════════════════════
def run_pipeline_directory(
    client: OpenAI,
    input_dir: Path,
    output_dir: Path,
    check_dir: Path,
    stock: dict[str, str],
    logger: logging.Logger,
) -> None:
    """Quét toàn bộ ảnh trong thư mục và chạy pipeline cho từng ảnh."""
    images = [p for p in input_dir.iterdir() if p.suffix.lower() in SUPPORTED_FORMATS]

    if not images:
        logger.warning(
            f"Không tìm thấy ảnh nào trong '{input_dir}' "
            f"(hỗ trợ: {', '.join(SUPPORTED_FORMATS)})"
        )
        return

    logger.info(f"Tìm thấy {len(images)} ảnh trong '{input_dir}'")

    for idx, image_path in enumerate(sorted(images), 1):
        logger.info(f"\n[{idx}/{len(images)}] Bắt đầu xử lý: {image_path.name}")
        run_pipeline_single(client, image_path, output_dir, check_dir, stock, logger)

    logger.info(f"\n{'═' * 55}")
    logger.info(f"Pipeline hoàn tất! Đã xử lý {len(images)} ảnh.")
    logger.info(f"  OCR JSON  → {output_dir.resolve()}")
    logger.info(f"  Check JSON → {check_dir.resolve()}")
    logger.info(f"{'═' * 55}")


# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="Pipeline OCR hóa đơn thuốc + kiểm tra tồn kho"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=None,
        help=f"Đường dẫn đến ảnh hoặc thư mục chứa ảnh (mặc định: {INPUT_DIR})",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help=f"Thư mục lưu file JSON kết quả OCR (mặc định: {OUTPUT_DIR})",
    )
    parser.add_argument(
        "--check", "-c",
        type=str,
        default=None,
        help=f"Thư mục lưu file JSON kết quả kiểm kho (mặc định: {CHECK_DIR})",
    )
    parser.add_argument(
        "--inventory", "-inv",
        type=str,
        default=None,
        help=f"Đường dẫn đến file inventory CSV (mặc định: {INVENTORY_FILE})",
    )
    args = parser.parse_args()

    input_path     = Path(args.input)     if args.input     else INPUT_DIR
    output_dir     = Path(args.output)    if args.output    else OUTPUT_DIR
    check_dir      = Path(args.check)     if args.check     else CHECK_DIR
    inventory_path = Path(args.inventory) if args.inventory else INVENTORY_FILE

    load_dotenv()

    # ── Setup logging
    logger = setup_logging()
    logger.info("=" * 55)
    logger.info("  OCR + Kiểm Tra Tồn Kho Thuốc — Pipeline")
    logger.info("=" * 55)
    logger.info(f"Input       : {input_path}")
    logger.info(f"Output OCR  : {output_dir}")
    logger.info(f"Output Check: {check_dir}")
    logger.info(f"Inventory   : {inventory_path}")

    # ── Bước 1: Khởi tạo OpenAI
    try:
        client = setup_openai(logger)
    except EnvironmentError as e:
        logger.critical(str(e))
        return

    # ── Bước 2: Tải tồn kho
    try:
        stock = load_inventory(inventory_path, logger)
    except FileNotFoundError as e:
        logger.critical(str(e))
        return

    # ── Bước 3 + 4: OCR & Kiểm kho
    if input_path.is_file():
        if input_path.suffix.lower() not in SUPPORTED_FORMATS:
            logger.error(f"Định dạng ảnh không hỗ trợ: {input_path.suffix}")
            return
        run_pipeline_single(client, input_path, output_dir, check_dir, stock, logger)

    elif input_path.is_dir():
        run_pipeline_directory(client, input_path, output_dir, check_dir, stock, logger)

    else:
        logger.error(f"Không tìm thấy đường dẫn: '{input_path}'")
        logger.error(f"Hãy tạo thư mục '{INPUT_DIR}' và đặt ảnh vào đó,")
        logger.error(f"hoặc dùng: python ocr_and_check_pill.py --input path/to/image.jpg")


if __name__ == "__main__":
    main()
