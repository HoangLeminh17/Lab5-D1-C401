import requests
from langchain.tools import tool

def get_rxcui(drug_name):
    """Lấy mã rxcui từ tên thuốc thông qua RxNav API"""
    url = f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={drug_name}"
    response = requests.get(url).json()
    try:
        return response['idGroup']['rxnormId'][0]
    except:
        return None

@tool
def check_interaction_rxnav(drug_list):
    """Kiểm tra tương tác của một danh sách thuốc"""
    # 1. Chuyển đổi tên thuốc sang mã rxcui
    rxcuis = [get_rxcui(name) for name in drug_list]
    rxcuis = [c for c in rxcuis if c is not None]

    if len(rxcuis) < 2:
        return "Không đủ thuốc để kiểm tra tương tác."

    # 2. Gọi API tương tác
    rxcui_str = "+".join(rxcuis)
    url = f"https://rxnav.nlm.nih.gov/REST/interaction/list.json?rxcuis={rxcui_str}"
    data = requests.get(url).json()

    return data
