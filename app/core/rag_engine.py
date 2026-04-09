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

from app.tools.fda import get_full_fda_info

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables từ file .env
load_dotenv()

# Cấu hình từ env
INVENTORY_PATH = os.getenv("INVENTORY_PATH", "inventory.csv")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def load_inventory() -> pd.DataFrame:
    """
    Load file inventory.csv vào DataFrame
    
    Returns:
        pd.DataFrame: DataFrame với các cột Ten_Thuoc, Hoat_Chat, Ton_Kho
    """
    try:
        df = pd.read_csv(INVENTORY_PATH)
        logger.info(f"✅ Load inventory thành công: {len(df)} dòng")
        return df
    except FileNotFoundError:
        logger.error(f"❌ Không tìm thấy file: {INVENTORY_PATH}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Lỗi load inventory: {str(e)}")
        return pd.DataFrame()


def find_alternative_drugs(active_ingredient: str) -> List[Dict]:
    """
    Tìm các thuốc thay thế có cùng hoạt chất và còn tồn kho > 0
    
    Args:
        active_ingredient (str): Hoạt chất chính (vd: "ibuprofen")
    
    Returns:
        List[Dict]: Danh sách thuốc thay thế
    """
    try:
        df = load_inventory()
        
        if df.empty:
            logger.warning("⚠️ Inventory trống!")
            return []
        
        active_ingredient_text = str(active_ingredient).lower().strip()

        # Tìm thuốc có cùng hoạt chất và còn tồn kho > 0.
        # Ưu tiên match chính xác, sau đó fallback match theo "chuỗi chứa hoạt chất"
        exact_match_df = df[
            (df["Hoat_Chat"].str.lower() == active_ingredient_text) &
            (df["Ton_Kho"] > 0)
        ]

        if not exact_match_df.empty:
            alternative_drugs = exact_match_df.to_dict("records")
        else:
            contains_match_df = df[
                (df["Ton_Kho"] > 0) &
                (df["Hoat_Chat"].str.lower().apply(lambda ing: str(ing) in active_ingredient_text))
            ]
            alternative_drugs = contains_match_df.to_dict("records")
        
        logger.info(f"🔎 Tìm thấy {len(alternative_drugs)} thuốc thay thế")
        
        return alternative_drugs
    
    except Exception as e:
        logger.error(f"❌ Lỗi tìm kiếm thuốc thay thế: {str(e)}")
        return []


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
        fda_info = get_full_fda_info(thuoc_het_hang)
        
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
