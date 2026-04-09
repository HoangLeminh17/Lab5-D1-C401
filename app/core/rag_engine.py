"""
Module RAG Engine - Sử dụng Google Gemini API
Kết hợp FDA API, Pandas Query, và Google Gemini để sinh ra tư vấn lâm sàng
"""

import logging
import os
from typing import Dict, List, Optional

import google.generativeai as genai
import pandas as pd
from dotenv import load_dotenv

from app.tools.fda import get_full_fda_info, find_alternative_drugs

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables từ file .env
load_dotenv()

# Cấu hình từ env
INVENTORY_PATH = os.getenv("INVENTORY_PATH", "inventory.csv")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def _stream_chunks(text: str, chunk_size: int = 120):
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


def _invoke_fda_tool(brand_name: str) -> Dict:
    """Handle LangChain tool invocation in a plain function flow."""
    try:
        return get_full_fda_info.invoke({"brand_name": brand_name})
    except AttributeError:
        return get_full_fda_info(brand_name)




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
            "recommendation": "...",
            "success": True/False,
            "error_message": "..."
        }
    """
    result = {
        "brand_name": thuoc_het_hang,
        "fda_info": None,
        "alternative_drugs": [],
        "recommendation": "",
        "success": False,
        "error_message": ""
    }
    
    try:
        logger.info(f"\n{'='*60}")
        logger.info(f"🏥 BẮT ĐẦU QUY TRÌNH TƯ VẤN: {thuoc_het_hang}")
        logger.info(f"{'='*60}")
        
        # Ưu tiên key truyền vào, nếu không có thì đọc từ .env
        resolved_api_key = gemini_api_key or GEMINI_API_KEY
        if not resolved_api_key:
            result["error_message"] = "Thiếu GEMINI_API_KEY. Vui lòng cấu hình trong file .env"
            logger.error(result["error_message"])
            return result

        # Cấu hình Google Generative AI
        logger.info("📍 [Bước 1] Cấu hình Google Gemini...")
        genai.configure(api_key=resolved_api_key)
        
        # Bước 2: Tra cứu FDA API
        logger.info("📍 [Bước 2] Tra cứu FDA API...")
        fda_info = _invoke_fda_tool(thuoc_het_hang)
        
        if not fda_info["success"]:
            result["error_message"] = f"Không tìm thấy thông tin thuốc '{thuoc_het_hang}' trên FDA API"
            logger.error(result["error_message"])
            return result
        
        result["fda_info"] = fda_info
        
        # Bước 3: Tìm thuốc thay thế trong kho
        logger.info("📍 [Bước 3] Tìm kiếm thuốc thay thế...")
        active_ingredient = fda_info.get("Hoat_Chat", "Unknown")
        alternative_drugs = find_alternative_drugs(active_ingredient)
        result["alternative_drugs"] = alternative_drugs
        
        if not alternative_drugs:
            logger.warning("⚠️ Không tìm thấy thuốc thay thế có sẵn")
        
        # Bước 4 & 5: Tạo prompt và gọi Gemini
        logger.info("📍 [Bước 4-5] Gọi Google Gemini để sinh tư vấn...")
        
        # Tạo system instruction
        system_instruction = """Bạn là một DƯỢC SĨ LÂM SÀNG CẤP CAO với 20 năm kinh nghiệm.
Nhiệm vụ của bạn là tư vấn các nhân viên quầy thuốc khi cần tìm thuốc thay thế.

Hãy:
1. Phân tích hoạt chất, đường dùng, chỉ định, chống chỉ định của thuốc gốc
2. So sánh với các thuốc thay thế có sẵn trong kho
3. Giải thích lý do lựa chọn từng thuốc
4. Cảnh báo các điểm quan trọng (chống chỉ định, tác dụng phụ) BẰNG TIẾNG VIỆT
5. Format kết quả rõ ràng, dễ đọc, sử dụng Markdown

Luôn ưu tiên an toàn bệnh nhân. Nếu có nghi ngờ, hãy khuyến nghị bệnh nhân tham khảo bác sĩ."""

        model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=system_instruction
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
Hãy tư vấn DỰA TRÊN thông tin trên. Dịch các cảnh báo quan trọng sang tiếng Việt. Format bằng Markdown. Gợi ý thuốc nào tốt nhất và tại sao."""
        
        # Gọi Gemini API
        response = model.generate_content(
            user_message,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )
        
        recommendation_text = response.text
        result["recommendation"] = recommendation_text
        result["success"] = True
        
        logger.info("✅ HOÀN THÀNH QUY TRÌNH TƯ VẤN")
        
        return result
    
    except Exception as e:
        error_msg = f"Lỗi trong quy trình: {str(e)}"
        logger.error(f"❌ {error_msg}")
        result["error_message"] = error_msg
        return result


def get_clinical_recommendation_stream(
    thuoc_het_hang: str,
    gemini_api_key: Optional[str] = None
):
    """
    Stream workflow events for UI while generating the recommendation.
    """
    result = {
        "brand_name": thuoc_het_hang,
        "fda_info": None,
        "alternative_drugs": [],
        "recommendation": "",
        "success": False,
        "error_message": ""
    }

    try:
        yield {"type": "status", "message": "Cau hinh Google Gemini"}
        resolved_api_key = gemini_api_key or GEMINI_API_KEY
        if not resolved_api_key:
            result["error_message"] = "Thieu GEMINI_API_KEY. Vui long cau hinh trong file .env"
            yield {"type": "error", "message": result["error_message"], "result": result}
            return

        genai.configure(api_key=resolved_api_key)

        yield {"type": "status", "message": "Tra cuu FDA API"}
        fda_info = _invoke_fda_tool(thuoc_het_hang)
        if not fda_info.get("success"):
            result["error_message"] = f"Khong tim thay thong tin thuoc '{thuoc_het_hang}' tren FDA API"
            yield {"type": "error", "message": result["error_message"], "result": result}
            return

        result["fda_info"] = fda_info
        yield {"type": "fda_info", "data": fda_info}

        yield {"type": "status", "message": "Tim thuoc thay the trong database"}
        active_ingredient = fda_info.get("Hoat_Chat", "Unknown")
        alternative_drugs = find_alternative_drugs(active_ingredient)
        result["alternative_drugs"] = alternative_drugs
        yield {"type": "alternatives", "data": alternative_drugs}

        system_instruction = """Ban la mot DUOC SI LAM SANG CAP CAO voi 20 nam kinh nghiem.
Nhiem vu cua ban la tu van cac nhan vien quay thuoc khi can tim thuoc thay the.

Hay:
1. Phan tich hoat chat, duong dung, chi dinh, chong chi dinh cua thuoc goc
2. So sanh voi cac thuoc thay the co san trong kho
3. Giai thich ly do lua chon tung thuoc
4. Canh bao cac diem quan trong (chong chi dinh, tac dung phu) BANG TIENG VIET
5. Format ket qua ro rang, de doc, su dung Markdown

Luon uu tien an toan benh nhan. Neu co nghi ngo, hay khuyen nghi benh nhan tham khao bac si."""

        model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=system_instruction
        )

        alternative_drugs_text = ""
        if alternative_drugs:
            alternative_drugs_text = "**DANH SACH THUOC CO SAN TRONG KHO:**\n"
            for i, drug in enumerate(alternative_drugs, 1):
                alternative_drugs_text += f"\n{i}. **{drug['Ten_Thuoc']}**\n"
                alternative_drugs_text += f"   - Ton kho: {drug['Ton_Kho']} hop\n"
        else:
            alternative_drugs_text = "**LUU Y:** Hien khong co thuoc thay the cung hoat chat trong kho."

        fda_summary = f"""**THONG TIN THUOC GOC (Tu FDA Database - Tieng Anh):**

- **Ten thuong mai:** {thuoc_het_hang}
- **Hoat chat:** {fda_info.get('Hoat_Chat', 'N/A')}
- **Duong dung:** {fda_info.get('Duong_Dung', 'N/A')}
- **Chi dinh:** {fda_info.get('Chi_Dinh', 'N/A')[:200]}...
- **Chong chi dinh:** {fda_info.get('Chong_Chi_Dinh', 'N/A')[:200]}...
- **Tac dung phu:** {fda_info.get('Tac_Dung_Phu', 'N/A')[:200]}...

{alternative_drugs_text}"""

        user_message = f"""{fda_summary}
**YEU CAU:**
Hay tu van DUA TREN thong tin tren. Dich cac canh bao quan trong sang tieng Viet. Format bang Markdown. Goi y thuoc nao tot nhat va tai sao."""

        for chunk in _stream_chunks(fda_summary, chunk_size=160):
            yield {"type": "context_chunk", "chunk": chunk}

        response = model.generate_content(
            user_message,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )

        recommendation_text = response.text or ""
        result["recommendation"] = recommendation_text
        result["success"] = True

        for chunk in _stream_chunks(recommendation_text, chunk_size=160):
            yield {"type": "recommendation_chunk", "chunk": chunk}

        yield {"type": "done", "result": result}

    except Exception as e:
        result["error_message"] = f"Loi trong quy trinh: {str(e)}"
        yield {"type": "error", "message": result["error_message"], "result": result}


def get_drug_explanation_for_pharmacist(
    brand_name: str,
    gemini_api_key: Optional[str] = None
) -> Dict:
    """Explain a drug in short, pharmacist-friendly Vietnamese."""
    result = {
        "brand_name": brand_name,
        "fda_info": None,
        "explanation": "",
        "success": False,
        "error_message": ""
    }

    try:
        resolved_api_key = gemini_api_key or GEMINI_API_KEY
        if not resolved_api_key:
            result["error_message"] = "Thieu GEMINI_API_KEY. Vui long cau hinh trong file .env"
            return result

        genai.configure(api_key=resolved_api_key)
        fda_info = _invoke_fda_tool(brand_name)
        if not fda_info.get("success"):
            result["error_message"] = f"Khong tim thay thong tin thuoc '{brand_name}' tren FDA API"
            return result

        result["fda_info"] = fda_info

        system_instruction = """Ban la duoc si. Hay giai thich ngan gon, de hieu, tap trung vao:
1) Hoat chat va tac dung chinh
2) Luu y quan trong
3) Doi tuong can canh bao

Tra loi bang tieng Viet, 5-7 dong, dang Markdown."""

        model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=system_instruction
        )

        user_message = f"""Thong tin FDA (English):
- Ten thuong mai: {brand_name}
- Hoat chat: {fda_info.get('Hoat_Chat', 'N/A')}
- Duong dung: {fda_info.get('Duong_Dung', 'N/A')}
- Chi dinh: {fda_info.get('Chi_Dinh', 'N/A')[:200]}...
- Chong chi dinh: {fda_info.get('Chong_Chi_Dinh', 'N/A')[:200]}...
- Tac dung phu: {fda_info.get('Tac_Dung_Phu', 'N/A')[:200]}...

Hay giai thich de hieu cho duoc si."""

        response = model.generate_content(
            user_message,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )

        result["explanation"] = response.text or ""
        result["success"] = True
        return result

    except Exception as e:
        result["error_message"] = f"Loi trong quy trinh: {str(e)}"
        return result


def get_drug_explanation_for_pharmacist_stream(
    brand_name: str,
    gemini_api_key: Optional[str] = None
):
    """Stream explanation events for a single drug."""
    result = {
        "brand_name": brand_name,
        "fda_info": None,
        "explanation": "",
        "success": False,
        "error_message": ""
    }

    try:
        yield {"type": "status", "message": "Tra cuu FDA API"}
        resolved_api_key = gemini_api_key or GEMINI_API_KEY
        if not resolved_api_key:
            result["error_message"] = "Thieu GEMINI_API_KEY. Vui long cau hinh trong file .env"
            yield {"type": "error", "message": result["error_message"], "result": result}
            return

        genai.configure(api_key=resolved_api_key)
        fda_info = _invoke_fda_tool(brand_name)
        if not fda_info.get("success"):
            result["error_message"] = f"Khong tim thay thong tin thuoc '{brand_name}' tren FDA API"
            yield {"type": "error", "message": result["error_message"], "result": result}
            return

        result["fda_info"] = fda_info
        yield {"type": "fda_info", "data": fda_info}

        system_instruction = """Ban la duoc si. Hay giai thich ngan gon, de hieu, tap trung vao:
1) Hoat chat va tac dung chinh
2) Luu y quan trong
3) Doi tuong can canh bao

Tra loi bang tieng Viet, 5-7 dong, dang Markdown."""

        model = genai.GenerativeModel(
            GEMINI_MODEL,
            system_instruction=system_instruction
        )

        user_message = f"""Thong tin FDA (English):
- Ten thuong mai: {brand_name}
- Hoat chat: {fda_info.get('Hoat_Chat', 'N/A')}
- Duong dung: {fda_info.get('Duong_Dung', 'N/A')}
- Chi dinh: {fda_info.get('Chi_Dinh', 'N/A')[:200]}...
- Chong chi dinh: {fda_info.get('Chong_Chi_Dinh', 'N/A')[:200]}...
- Tac dung phu: {fda_info.get('Tac_Dung_Phu', 'N/A')[:200]}...

Hay giai thich de hieu cho duoc si."""

        response = model.generate_content(
            user_message,
            safety_settings=[
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
        )

        explanation_text = response.text or ""
        result["explanation"] = explanation_text
        result["success"] = True

        for chunk in _stream_chunks(explanation_text, chunk_size=140):
            yield {"type": "explanation_chunk", "chunk": chunk}

        yield {"type": "done", "result": result}

    except Exception as e:
        result["error_message"] = f"Loi trong quy trinh: {str(e)}"
        yield {"type": "error", "message": result["error_message"], "result": result}


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
