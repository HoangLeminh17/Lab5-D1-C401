import requests

def get_active_ingredients(brand_name):
    """
    Tra cứu hoạt chất (active ingredients) dựa trên tên thương mại qua OpenFDA API.
    """
    # URL cơ bản cho endpoint drug label của OpenFDA
    url = "https://api.fda.gov/drug/label.json"
    
    # Tham số truy vấn: tìm kiếm theo tên thương mại (openfda.brand_name)
    params = {
        'search': f'openfda.brand_name:"{brand_name}"',
        'limit': 1
    }

    try:
        response = requests.get(url, params=params)
        
        # Kiểm tra nếu request thành công
        if response.status_code == 200:
            data = response.json()
            
            # Trích xuất thông tin hoạt chất từ kết quả đầu tiên
            results = data.get('results', [])
            if results:
                # Lấy danh sách hoạt chất từ trường generic_name hoặc active_ingredient
                # OpenFDA thường để hoạt chất trong openfda.generic_name
                info = results[0].get('openfda', {})
                generic_names = info.get('generic_name', [])
                
                if generic_names:
                    return generic_names
                else:
                    return ["Không tìm thấy hoạt chất cụ thể trong dữ liệu openfda."]
            else:
                return ["Không tìm thấy kết quả nào cho tên thuốc này."]
                
        elif response.status_code == 404:
            return ["Không tìm thấy tên thuốc này trong cơ sở dữ liệu FDA."]
        else:
            return [f"Lỗi API: {response.status_code}"]

    except Exception as e:
        return [f"Đã xảy ra lỗi: {str(e)}"]

# --- Sử dụng thử ---
ten_thuoc = input("Nhập tên thuốc cần tra (v.d: Tylenol, Advil): ")
hoat_chat = get_active_ingredients(ten_thuoc)

print(f"\nKết quả tra cứu cho '{ten_thuoc}':")
for item in hoat_chat:
    print(f"- {item}")