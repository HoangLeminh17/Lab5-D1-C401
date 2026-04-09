import requests
from langchain.tools import tool
from typing import List, Dict, Any

def get_rxcui(drug_name):
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug_name}"
    try:
        response = requests.get(url).json()
        return response['idGroup']['rxnormId'][0]
    except:
        return None


@tool
def check_interaction_rxnav(drug_list: List[str]) -> Dict[str, Any]:
    """Kiểm tra tương tác của một danh sách thuốc"""

    # 🔒 Fix 1: đảm bảo input không None
    if not drug_list:
        return {
            "success": False,
            "message": "Drug list is empty",
            "interactions": []
        }

    # 1. convert sang rxcui
    rxcuis = [get_rxcui(name) for name in drug_list]
    rxcuis = [c for c in rxcuis if c is not None]

    # 🔒 Fix 2: không đủ thuốc
    if len(rxcuis) < 2:
        return {
            "success": False,
            "message": "Không đủ thuốc để kiểm tra tương tác",
            "interactions": []
        }

    # 2. gọi API
    try:
        rxcui_str = "+".join(rxcuis)
        url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={rxcui_str}"
        data = requests.get(url).json()

        return {
            "success": True,
            "message": "OK",
            "interactions": data
        }

    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "interactions": []
        }