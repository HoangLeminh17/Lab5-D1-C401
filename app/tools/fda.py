"""
Module FDA API Integration - Lấy thông tin chi tiết từ OpenFDA
Tra cứu: Hoạt chất, Đường dùng, Chỉ định, Chống chỉ định, Tác dụng phụ
"""
import os
import requests
import logging
from typing import Dict, Optional, List, Any
from langchain.tools import tool
import pandas as pd

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Hằng số
FDA_API_BASE_URL = "https://api.fda.gov/drug/label.json"
API_TIMEOUT = 10  # seconds

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

@tool
def get_full_fda_info(brand_name: str):
    """
    Tra cứu thông tin CHI TIẾT của thuốc từ OpenFDA API.
    
    Args:
        brand_name (str): Tên thương mại của thuốc (vd: "Advil")
    
    Returns:
        Dict với keys: Hoat_Chat, Duong_Dung, Chi_Dinh, Chong_Chi_Dinh, Tac_Dung_Phu
        Ví dụ:
        {
            "Hoat_Chat": "ibuprofen",
            "Duong_Dung": "Oral",
            "Chi_Dinh": "For temporary relief of...",
            "Chong_Chi_Dinh": "Do not use if...",
            "Tac_Dung_Phu": "May cause...",
            "success": True
        }
    """
    result: Dict[str, Any] = {
        "Hoat_Chat": None,
        "Duong_Dung": None,
        "Chi_Dinh": None,
        "Chong_Chi_Dinh": None,
        "Tac_Dung_Phu": None,
        "success": False
    }
    
    try:
        # Chuẩn bị query
        search_query = f'openfda.brand_name:"{brand_name}"'
        params = {
            "search": search_query,
            "limit": 1
        }
        
        logger.info(f"🔍 Tra cứu FDA: {brand_name}")
        
        # Gọi API
        response = requests.get(
            FDA_API_BASE_URL,
            params=params,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Kiểm tra kết quả
        if not data.get("results") or len(data["results"]) == 0:
            logger.warning(f"⚠️ Không tìm thấy: {brand_name} trên FDA")
            return result
        
        drug = data["results"][0]
        
        # 1. Hoạt chất (Active Ingredient)
        # OpenFDA có thể trả về list[str], str, hoặc list[dict] tùy record.
        active_ingredient = drug.get("active_ingredient")
        if active_ingredient:
            if isinstance(active_ingredient, list) and len(active_ingredient) > 0:
                first_item = active_ingredient[0]
                if isinstance(first_item, dict):
                    result["Hoat_Chat"] = first_item.get("name") or first_item.get("value") or "Unknown"
                else:
                    result["Hoat_Chat"] = str(first_item)
            elif isinstance(active_ingredient, str):
                result["Hoat_Chat"] = active_ingredient

        # Fallback từ openfda.substance_name nếu active_ingredient thiếu
        if not result["Hoat_Chat"]:
            openfda = drug.get("openfda", {}) if isinstance(drug.get("openfda", {}), dict) else {}
            substance_name = openfda.get("substance_name")
            if isinstance(substance_name, list) and substance_name:
                result["Hoat_Chat"] = str(substance_name[0])
            elif isinstance(substance_name, str):
                result["Hoat_Chat"] = substance_name
        
        # 2. Đường dùng (Route of Administration)
        route = drug.get("route")
        if isinstance(route, list) and route:
            result["Duong_Dung"] = ", ".join(str(x) for x in route[:3])
        elif isinstance(route, str) and route:
            result["Duong_Dung"] = route

        # Fallback từ openfda.route nếu route thiếu
        if not result["Duong_Dung"]:
            openfda = drug.get("openfda", {}) if isinstance(drug.get("openfda", {}), dict) else {}
            openfda_route = openfda.get("route")
            if isinstance(openfda_route, list) and openfda_route:
                result["Duong_Dung"] = ", ".join(str(x) for x in openfda_route[:3])
            elif isinstance(openfda_route, str) and openfda_route:
                result["Duong_Dung"] = openfda_route
        
        # 3. Chỉ định (Indications and Usage)
        if "indications_and_usage" in drug and drug["indications_and_usage"]:
            usage_text = drug["indications_and_usage"]
            result["Chi_Dinh"] = usage_text[0][:500] if isinstance(usage_text, list) else usage_text[:500]
        
        # 4. Chống chỉ định (Contraindications)
        if "contraindications" in drug and drug["contraindications"]:
            contra_text = drug["contraindications"]
            result["Chong_Chi_Dinh"] = contra_text[0][:500] if isinstance(contra_text, list) else contra_text[:500]
        
        # 5. Tác dụng phụ (Adverse Reactions)
        if "adverse_reactions" in drug and drug["adverse_reactions"]:
            adverse_text = drug["adverse_reactions"]
            result["Tac_Dung_Phu"] = adverse_text[0][:500] if isinstance(adverse_text, list) else adverse_text[:500]
        
        # Thay thế None bằng "Not available"
        for key in result:
            if key != "success" and result[key] is None:
                result[key] = "Not available in FDA database"
        
        result["success"] = True
        logger.info(f"✅ Tìm thấy: {result['Hoat_Chat']}")
        
        return result
    
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout FDA API (>{API_TIMEOUT}s)")
        return result
    except requests.exceptions.ConnectionError:
        logger.error(f"❌ Lỗi kết nối mạng")
        return result
    except requests.exceptions.HTTPError as e:
        logger.error(f"❌ Lỗi HTTP: {str(e)}")
        return result
    except ValueError:
        logger.error(f"❌ Lỗi parse JSON")
        return result
    except Exception as e:
        logger.error(f"❌ Lỗi không xác định: {str(e)}")
        return result

if __name__ == "__main__":
    # Test
    result = get_full_fda_info.invoke({"brand_name": "Advil"})
    print("Success:", result["success"])
    print("Hoat_Chat:", result["Hoat_Chat"])
    print("Duong_Dung:", result["Duong_Dung"])
