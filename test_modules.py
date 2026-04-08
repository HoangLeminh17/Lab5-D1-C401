"""
Script test các module riêng lẻ
Chạy: python test_modules.py
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

def test_fda_api():
    """Test module FDA API"""
    print("\n" + "="*60)
    print("🧪 TEST MODULE: fda_api.py")
    print("="*60)
    
    try:
        from fda_api import get_full_fda_info
        
        print("✓ Module import thành công")
        
        # Test
        print("\n📍 Đang test get_full_fda_info('Advil')...")
        from requests.exceptions import ConnectionError
        
        try:
            result = get_full_fda_info("Advil")
            print(f"✓ Kết quả:")
            print(f"  - Success: {result.get('success')}")
            print(f"  - Hoạt chất: {result.get('Hoat_Chat', 'N/A')}")
            print(f"  - Đường dùng: {result.get('Duong_Dung', 'N/A')}")
            print(f"  - Chỉ định: {result.get('Chi_Dinh', 'N/A')[:50]}...")
        except ConnectionError:
            print("⚠️ Không thể kết nối FDA API (Internet offline?)")
            print("   Bạn có thể bỏ qua lỗi này nếu internet bị ngắt")
    
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False
    
    return True


def test_rag_engine():
    """Test module RAG Engine"""
    print("\n" + "="*60)
    print("🧪 TEST MODULE: rag_engine.py")
    print("="*60)
    
    try:
        from rag_engine import load_inventory, find_alternative_drugs
        
        print("✓ Module import thành công")
        
        # Test load inventory
        print("\n📍 Đang test load_inventory()...")
        df = load_inventory()
        print(f"✓ Load thành công: {len(df)} dòng")
        print(f"  Columns: {list(df.columns)}")
        
        # Test find alternatives
        print("\n📍 Đang test find_alternative_drugs('ibuprofen')...")
        alternatives = find_alternative_drugs("ibuprofen")
        print(f"✓ Tìm thấy {len(alternatives)} thuốc thay thế")
        if alternatives:
            for drug in alternatives[:2]:
                print(f"  - {drug['Ten_Thuoc']} (Tồn kho: {drug['Ton_Kho']})")
    
    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False
    
    return True


def test_google_generativeai():
    """Test Google Generative AI installation"""
    print("\n" + "="*60)
    print("🧪 TEST: Google Generative AI")
    print("="*60)
    
    try:
        import google.generativeai
        print(f"✓ google-generativeai cài đặt OK")
        print("\n📌 Lưu ý:")
        print("   - Cần API key từ: https://makersuite.google.com/app/apikey")
        print("   - Để test, chạy: python rag_engine.py")
    
    except ImportError:
        print("❌ google-generativeai chưa được cài đặt")
        print("   Chạy: pip install google-generativeai")
        return False
    
    return True


def test_streamlit():
    """Test Streamlit installation"""
    print("\n" + "="*60)
    print("🧪 TEST: Streamlit")
    print("="*60)
    
    try:
        import streamlit
        print(f"✓ Streamlit {streamlit.__version__} cài đặt OK")
        print("\n📌 Để chạy app:")
        print("   streamlit run app.py")
    
    except ImportError:
        print("❌ Streamlit chưa được cài đặt")
        print("   Chạy: pip install -r requirements.txt")
        return False
    
    return True


def test_environment():
    """Test environment variables"""
    print("\n" + "="*60)
    print("🧪 TEST: Environment Variables")
    print("="*60)
    
    gemini_api_key = os.getenv("GEMINI_API_KEY", "not set")
    gemini_model = os.getenv("GEMINI_MODEL", "not set")
    
    print(f"GEMINI_API_KEY: {'✓ Set' if gemini_api_key != 'not set' else '❌ Not set'}")
    print(f"GEMINI_MODEL: {gemini_model}")
    
    if gemini_api_key == "not set":
        print("\n⚠️ GEMINI_API_KEY chưa được cấu hình!")
        print("   1. Mở file .env trong thư mục dự án")
        print("   2. Truy cập: https://makersuite.google.com/app/apikey")
        print("   3. Tạo API key và thêm vào .env")
        return False
    
    return True


def main():
    """Chạy tất cả test"""
    print("\n")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🧪 PHARMACIST ASSISTANT v2.0 - MODULE TEST (GEMINI)    ║")
    print("╚════════════════════════════════════════════════════════════╝")
    
    results = {
        "Environment": test_environment(),
        "FDA API": test_fda_api(),
        "RAG Engine": test_rag_engine(),
        "Google Generative AI": test_google_generativeai(),
        "Streamlit": test_streamlit(),
    }
    
    # Tóm tắt
    print("\n" + "="*60)
    print("📊 KẾT QUẢ TEST")
    print("="*60)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:25} {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "="*60)
    if all_passed:
        print("🎉 TẤT CẢ TEST PASS! Bạn có thể bắt đầu:")
        print("   streamlit run app.py")
    else:
        print("⚠️ Một số test không pass. Kiểm tra lỗi ở trên.")
    print("="*60)


if __name__ == "__main__":
    main()
