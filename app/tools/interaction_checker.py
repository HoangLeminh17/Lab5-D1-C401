import requests
import logging
from langchain.tools import tool
from typing import List, Dict, Any
import itertools

logger = logging.getLogger(__name__)


def get_us_standard_name(drug_name: str) -> str:
    """Sử dụng RxNorm API để chuẩn hóa 1 tên thuốc sang tên Mỹ."""
    try:
        search_url = "https://rxnav.nlm.nih.gov/REST/approximateTerm.json"
        search_res = requests.get(search_url, params={"term": drug_name, "maxEntries": 1}).json()

        candidates = search_res.get("approximateGroup", {}).get("candidate", [])
        if not candidates:
            return drug_name.lower()

        rxcui = candidates[0].get("rxcui")
        prop_url = f"https://rxnav.nlm.nih.gov/REST/rxcui/{rxcui}/properties.json"
        prop_res = requests.get(prop_url).json()

        properties = prop_res.get("properties")
        if properties and "name" in properties:
            standard_name = properties["name"].lower()
            logger.info(f"🔄 Đổi tên: {drug_name} -> {standard_name}")
            return standard_name
    except Exception as e:
        logger.warning(f"Lỗi đổi tên cho {drug_name}: {str(e)}")

    return drug_name.lower()


@tool
def check_interaction_openfda(drug_list: List[str]) -> Dict[str, Any]:
    """Kiểm tra tương tác của một toa thuốc (bao nhiêu thuốc cũng được) bằng OpenFDA API"""

    if not drug_list or len(drug_list) < 2:
        return {"success": False, "message": "Cần ít nhất 2 thuốc để kiểm tra tương tác", "interactions": []}

    # 1. Chuyển đổi TOÀN BỘ danh sách sang tên chuẩn Mỹ
    fda_drugs = [get_us_standard_name(drug) for drug in drug_list]

    # Loại bỏ trùng lặp (phòng trường hợp user nhập 2 thuốc giống nhau)
    fda_drugs = list(set(fda_drugs))
    if len(fda_drugs) < 2:
        return {"success": False, "message": "Cần ít nhất 2 thuốc khác biệt nhau để kiểm tra.", "interactions": []}

    # 2. Tạo các cặp thuốc (Combinations) để kiểm tra chéo
    # VD: [A, B, C] -> sẽ tạo ra 3 cặp (A,B), (A,C), (B,C)
    drug_pairs = list(itertools.combinations(fda_drugs, 2))

    all_interactions = []
    summary_messages = []

    # 3. Chạy vòng lặp kiểm tra từng cặp qua OpenFDA
    url = 'https://api.fda.gov/drug/label.json'
    for drug_a, drug_b in drug_pairs:
        # Thử chiều 1: Xem nhãn thuốc A có nhắc đến cảnh báo với thuốc B không
        params_1 = {
            'search': f'(openfda.generic_name:"{drug_a}" OR openfda.brand_name:"{drug_a}") AND drug_interactions:"{drug_b}"',
            'limit': 1
        }

        try:
            res = requests.get(url, params=params_1)

            # Nếu không tìm thấy ở nhãn A (404), ta thử chiều 2: Xem nhãn thuốc B có nhắc đến A không
            if res.status_code == 404:
                params_2 = {
                    'search': f'(openfda.generic_name:"{drug_b}" OR openfda.brand_name:"{drug_b}") AND drug_interactions:"{drug_a}"',
                    'limit': 1
                }
                res = requests.get(url, params=params_2)

            # Phân tích kết quả
            if res.status_code == 200:
                data = res.json()
                interaction_text = data['results'][0].get('drug_interactions', [''])[0]

                all_interactions.append({
                    "pair": f"{drug_a} + {drug_b}",
                    "warning_text": interaction_text
                })
                summary_messages.append(f"⚠️ CÓ TƯƠNG TÁC: {drug_a} và {drug_b}")

            elif res.status_code == 404:
                summary_messages.append(f"✅ AN TOÀN (Không thấy dữ liệu): {drug_a} và {drug_b}")
            else:
                summary_messages.append(f"❓ LỖI TRA CỨU: {drug_a} và {drug_b} (Mã lỗi {res.status_code})")

        except Exception as e:
            summary_messages.append(f"❌ LỖI HỆ THỐNG: {drug_a} và {drug_b} - {str(e)}")

    # 4. Trả về kết quả tổng hợp cho Langchain Agent
    return {
        "success": True,
        "message": "\n".join(summary_messages),
        "interactions": all_interactions
    }