"""
Module RAG Engine - Sử dụng Google Gemini API
Kết hợp FDA API, Pandas Query, và Google Gemini để sinh ra tư vấn lâm sàng
"""

import logging
import re
from typing import Dict, Iterator, Optional

import google.generativeai as genai

from app.core.config import (
    CLINICAL_SYSTEM_PROMPT,
    CLINICAL_CONCISE_RESPONSE_RULES,
    DRUG_EXPLANATION_RULES,
    GEMINI_SAFETY_SETTINGS,
    get_core_config,
)
from app.tools.fda import get_full_fda_info, find_alternative_drugs

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CORE_CONFIG = get_core_config()


def _normalize_brand_name(brand_name: str) -> str:
    """Chuẩn hóa tên thuốc để tăng tỉ lệ match OpenFDA (vd bỏ liều lượng)."""
    cleaned = re.sub(r"\b\d+(?:\.\d+)?\s*(mg|g|mcg|ml)\b", "", brand_name, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or brand_name


def _keep_short_recommendation(text: str, max_lines: int = 6, max_chars: int = 800) -> str:
    """Giới hạn độ dài output để phù hợp yêu cầu tư vấn ngắn gọn."""
    if not text:
        return ""

    lines = [ln.rstrip() for ln in text.splitlines() if ln.strip()]
    short_text = "\n".join(lines[:max_lines])
    if len(short_text) > max_chars:
        short_text = short_text[:max_chars].rstrip() + "..."
    return short_text


def _build_context_text_for_stream(
    thuoc_het_hang: str,
    fda_info: Dict,
    alternative_drugs: list,
) -> str:
    """Tạo phần context ngắn để hiển thị theo dạng stream trên UI."""
    lines = [
        f"Thuốc gốc: {thuoc_het_hang}",
        f"Hoạt chất: {fda_info.get('Hoat_Chat', 'N/A')}",
        f"Đường dùng: {fda_info.get('Duong_Dung', 'N/A')}",
        f"Số thuốc thay thế trong kho: {len(alternative_drugs)}",
    ]

    if alternative_drugs:
        top_names = [d.get("Ten_Thuoc", "N/A") for d in alternative_drugs[:5]]
        lines.append("Top thuốc có sẵn: " + ", ".join(top_names))

    return "\n".join(lines)




def get_clinical_recommendation(
    thuoc_het_hang: str,
    gemini_api_key: Optional[str] = None
) -> Dict:
    """
    Hàm chính: Lấy tư vấn lâm sàng về thuốc thay thế
    
    Luồng:
    1. Cấu hình Google Gemini API
    2. Gọi FDA API để lấy thông tin chi tiết
    3. Tìm thuốc thay thế trong kho
    4. Tạo prompt system instruction dạng dược sĩ lâm sàng
    5. Gọi Gemini để sinh tư vấn (với dịch sang tiếng Việt)
    6. Trả về markdown format
    
    Args:
        thuoc_het_hang (str): Tên thuốc bị hết hàng (vd: "Advil")
        gemini_api_key (Optional[str]): API key truyền vào trực tiếp.
            Nếu None, sẽ tự đọc từ biến môi trường GEMINI_API_KEY
    
    Returns:
        Dict: {
            "brand_name": "Advil",
            "fda_info": {...},
            "alternative_drugs": [...],
            "context_for_stream": "...",
            "recommendation": "...",
            "success": True/False,
            "error_message": "..."
        }
    """
    result = {
        "brand_name": thuoc_het_hang,
        "fda_info": None,
        "alternative_drugs": [],
        "context_for_stream": "",
        "recommendation": "",
        "success": False,
        "error_message": ""
    }
    
    try:
        for event in get_clinical_recommendation_stream(thuoc_het_hang, gemini_api_key):
            event_type = event.get("type")
            if event_type == "done":
                return event["result"]
            if event_type == "error":
                return event.get("result", result)

        return result

    except Exception as e:
        error_msg = f"Lỗi trong quy trình: {str(e)}"
        logger.error(f"❌ {error_msg}")
        result["error_message"] = error_msg
        return result


def get_clinical_recommendation_stream(
    thuoc_het_hang: str,
    gemini_api_key: Optional[str] = None,
) -> Iterator[Dict]:
    """Streaming pipeline: trả event dần theo từng bước xử lý."""
    result = {
        "brand_name": thuoc_het_hang,
        "fda_info": None,
        "alternative_drugs": [],
        "context_for_stream": "",
        "recommendation": "",
        "success": False,
        "error_message": "",
    }

    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"🏥 BẮT ĐẦU QUY TRÌNH TƯ VẤN: {thuoc_het_hang}")
        logger.info(f"{'='*60}")
        yield {"type": "status", "message": f"Bắt đầu tư vấn cho {thuoc_het_hang}"}
        
        # Ưu tiên key truyền vào, nếu không có thì đọc từ .env
        resolved_api_key = gemini_api_key or CORE_CONFIG.gemini_api_key
        if not resolved_api_key:
            result["error_message"] = "Thiếu GEMINI_API_KEY. Vui lòng cấu hình trong file .env"
            logger.error(result["error_message"])
            yield {"type": "error", "message": result["error_message"], "result": result}
            return

        # Cấu hình Google Generative AI
        logger.info("📍 [Bước 1] Cấu hình Google Gemini...")
        yield {"type": "status", "message": "Đang cấu hình Google Gemini"}
        genai.configure(api_key=resolved_api_key)
        
        # Bước 2: Tra cứu FDA API
        logger.info("📍 [Bước 2] Tra cứu FDA API...")
        yield {"type": "status", "message": "Đang tra cứu OpenFDA"}
        fda_info = get_full_fda_info.invoke({"brand_name": thuoc_het_hang})
        
        if not fda_info["success"]:
            result["error_message"] = f"Không tìm thấy thông tin thuốc '{thuoc_het_hang}' trên FDA API"
            logger.error(result["error_message"])
            yield {"type": "error", "message": result["error_message"], "result": result}
            return
        
        result["fda_info"] = fda_info
        yield {"type": "fda_info", "data": fda_info}
        
        # Bước 3: Tìm thuốc thay thế trong kho
        logger.info("📍 [Bước 3] Tìm kiếm thuốc thay thế...")
        yield {"type": "status", "message": "Đang tìm thuốc thay thế trong kho"}
        active_ingredient = fda_info.get("Hoat_Chat", "Unknown")
        alternative_drugs = find_alternative_drugs(active_ingredient)
        result["alternative_drugs"] = alternative_drugs
        yield {"type": "alternatives", "data": alternative_drugs}
        result["context_for_stream"] = _build_context_text_for_stream(
            thuoc_het_hang,
            fda_info,
            alternative_drugs,
        )

        for line in result["context_for_stream"].splitlines():
            yield {"type": "context_chunk", "chunk": line + "\n"}
        
        if not alternative_drugs:
            logger.warning("⚠️ Không tìm thấy thuốc thay thế có sẵn")
        
        # Bước 4 & 5: Tạo prompt và gọi Gemini
        logger.info("📍 [Bước 4-5] Gọi Google Gemini để sinh tư vấn...")
        yield {"type": "status", "message": "Gemini đang tạo tư vấn lâm sàng"}
        
        model = genai.GenerativeModel(
            CORE_CONFIG.gemini_model,
            system_instruction=CLINICAL_SYSTEM_PROMPT
        )
        
        # Chuẩn bị nội dung tư vấn
        alternative_drugs_text = ""
        if alternative_drugs:
            alternative_drugs_text = "**DANH SÁCH THUỐC CÓ SẴN TRONG KHO:**\n"
            for i, drug in enumerate(alternative_drugs, 1):
                alternative_drugs_text += f"\n{i}. **{drug['Ten_Thuoc']}**\n"
                alternative_drugs_text += f"   - Tồn kho: {drug['Ton_Kho']} hộp\n"
        else:
            alternative_drugs_text = "**LƯU Ý:** Hiện không có thuốc thay thế cùng hoạt chất trong kho."
        
        # Dịch FDA info sang dễ hiểu
        fda_summary = f"""**THÔNG TIN THUỐC GỐC (Từ FDA Database - Tiếng Anh):**

- **Tên thương mại:** {thuoc_het_hang}
- **Hoạt chất:** {fda_info.get('Hoat_Chat', 'N/A')}
- **Đường dùng:** {fda_info.get('Duong_Dung', 'N/A')}
- **Chỉ định:** {fda_info.get('Chi_Dinh', 'N/A')[:200]}...
- **Chống chỉ định:** {fda_info.get('Chong_Chi_Dinh', 'N/A')[:200]}...
- **Tác dụng phụ:** {fda_info.get('Tac_Dung_Phu', 'N/A')[:200]}...

{alternative_drugs_text}"""
        
        # Tạo user message
        user_message = f"""{fda_summary}
**YÊU CẦU:**
    Hãy tư vấn DỰA TRÊN thông tin trên. Dịch các cảnh báo quan trọng sang tiếng Việt.

    {CLINICAL_CONCISE_RESPONSE_RULES}
    """
        
        # Gọi Gemini API theo stream
        response_stream = model.generate_content(
            user_message,
            safety_settings=GEMINI_SAFETY_SETTINGS,
            stream=True,
        )

        streamed_text = ""
        max_stream_chars = 1500
        for chunk in response_stream:
            chunk_text = getattr(chunk, "text", "") or ""
            if not chunk_text:
                continue

            remain = max_stream_chars - len(streamed_text)
            if remain <= 0:
                break

            safe_chunk = chunk_text[:remain]
            streamed_text += safe_chunk
            yield {"type": "recommendation_chunk", "chunk": safe_chunk}

        recommendation_text = _keep_short_recommendation(streamed_text)
        result["recommendation"] = recommendation_text
        result["success"] = True
        
        logger.info("✅ HOÀN THÀNH QUY TRÌNH TƯ VẤN")
        yield {"type": "done", "result": result}
        return
    
    except Exception as e:
        error_msg = f"Lỗi trong quy trình: {str(e)}"
        logger.error(f"❌ {error_msg}")
        result["error_message"] = error_msg
        yield {"type": "error", "message": error_msg, "result": result}
        return


def get_drug_explanation_for_pharmacist(
    drug_name: str,
    gemini_api_key: Optional[str] = None,
) -> Dict:
    """Giải thích nhanh 1 thuốc khi dược sĩ bấm xem chi tiết."""
    result = {
        "drug_name": drug_name,
        "fda_info": None,
        "explanation": "",
        "success": False,
        "error_message": "",
    }

    try:
        for event in get_drug_explanation_for_pharmacist_stream(drug_name, gemini_api_key):
            event_type = event.get("type")
            if event_type == "done":
                return event["result"]
            if event_type == "error":
                return event.get("result", result)

        return result

    except Exception as e:
        result["error_message"] = f"Lỗi giải thích thuốc: {str(e)}"
        return result


def get_drug_explanation_for_pharmacist_stream(
    drug_name: str,
    gemini_api_key: Optional[str] = None,
) -> Iterator[Dict]:
    """Streaming giải thích 1 thuốc cho dược sĩ khi bấm xem chi tiết."""
    result = {
        "drug_name": drug_name,
        "fda_info": None,
        "explanation": "",
        "success": False,
        "error_message": "",
    }

    try:
        resolved_api_key = gemini_api_key or CORE_CONFIG.gemini_api_key
        if not resolved_api_key:
            result["error_message"] = "Thiếu GEMINI_API_KEY. Vui lòng cấu hình trong file .env"
            yield {"type": "error", "message": result["error_message"], "result": result}
            return

        genai.configure(api_key=resolved_api_key)
        yield {"type": "status", "message": f"Đang tra cứu FDA cho {drug_name}"}

        fda_info = get_full_fda_info.invoke({"brand_name": drug_name})

        if not fda_info.get("success"):
            normalized_name = _normalize_brand_name(drug_name)
            if normalized_name.lower() != drug_name.lower():
                yield {"type": "status", "message": f"Thử lại với tên chuẩn hóa: {normalized_name}"}
                fda_info = get_full_fda_info.invoke({"brand_name": normalized_name})

        result["fda_info"] = fda_info
        if not fda_info.get("success"):
            result["error_message"] = f"Không tìm thấy thông tin FDA cho '{drug_name}'"
            yield {"type": "error", "message": result["error_message"], "result": result}
            return

        yield {"type": "fda_info", "data": fda_info}
        yield {"type": "status", "message": "Gemini đang tổng hợp giải thích thuốc"}

        model = genai.GenerativeModel(
            CORE_CONFIG.gemini_model,
            system_instruction=CLINICAL_SYSTEM_PROMPT,
        )

        prompt = f"""{DRUG_EXPLANATION_RULES}

Thông tin FDA hiện có cho thuốc {drug_name}:
- Hoạt chất: {fda_info.get('Hoat_Chat', 'N/A')}
- Đường dùng: {fda_info.get('Duong_Dung', 'N/A')}
- Chỉ định: {fda_info.get('Chi_Dinh', 'N/A')[:350]}
- Chống chỉ định: {fda_info.get('Chong_Chi_Dinh', 'N/A')[:350]}
- Tác dụng phụ: {fda_info.get('Tac_Dung_Phu', 'N/A')[:350]}
"""

        response_stream = model.generate_content(
            prompt,
            safety_settings=GEMINI_SAFETY_SETTINGS,
            stream=True,
        )

        explanation_text = ""
        max_stream_chars = 1400
        for chunk in response_stream:
            chunk_text = getattr(chunk, "text", "") or ""
            if not chunk_text:
                continue

            remain = max_stream_chars - len(explanation_text)
            if remain <= 0:
                break

            safe_chunk = chunk_text[:remain]
            explanation_text += safe_chunk
            yield {"type": "explanation_chunk", "chunk": safe_chunk}

        result["explanation"] = explanation_text
        result["success"] = True
        yield {"type": "done", "result": result}
        return

    except Exception as e:
        result["error_message"] = f"Lỗi giải thích thuốc: {str(e)}"
        yield {"type": "error", "message": result["error_message"], "result": result}
        return


if __name__ == "__main__":
    # Test đọc key từ .env
    result = get_clinical_recommendation("Advil")
    
    print("\n" + "="*60)
    print("KẾT QUẢ:")
    print("="*60)
    print(f"Success: {result['success']}")
    if result['success']:
        print(f"\nThông tin FDA:")
        for key, value in result['fda_info'].items():
            if key != 'success':
                print(f"  {key}: {value[:100] if isinstance(value, str) else value}...")
        
        print(f"\nThuốc thay thế tìm thấy: {len(result['alternative_drugs'])}")
        print(f"\nTư vấn LLM:\n{result['recommendation']}")
    else:
        print(f"Error: {result['error_message']}")
