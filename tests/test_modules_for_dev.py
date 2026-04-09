"""
Script test các module riêng lẻ có thiểu thư viện gì không(RAG engine, FDA API, Google Generative AI, Streamlit)
Chạy: python test_modules.py
"""

import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment
load_dotenv()

def safe_print(text):
    """Print text after stripping non-ASCII characters."""
    if isinstance(text, str):
        print(text.encode('ascii', 'ignore').decode('ascii'))
    else:
        print(text)

def test_fda_api():
    """Test module FDA API"""
    safe_print("\n" + "="*60)
    safe_print("TEST MODULE: fda_api.py")
    safe_print("="*60)
    
    try:
        from fda_api import get_full_fda_info
        
        safe_print("[OK] Module import thanh cong")
        
        # Test
        safe_print("\n[INFO] Dang test get_full_fda_info('Advil')...")
        from requests.exceptions import ConnectionError
        
        try:
            result = get_full_fda_info("Advil")
            safe_print(f"[OK] Ket qua:")
            safe_print(f"  - Success: {result.get('success')}")
            safe_print(f"  - Hoat chat: {result.get('Hoat_Chat', 'N/A')}")
            safe_print(f"  - Duong dung: {result.get('Duong_Dung', 'N/A')}")
            safe_print(f"  - Chi dinh: {result.get('Chi_Dinh', 'N/A')[:50]}...")
        except ConnectionError:
            safe_print("[WARN] Khong the ket noi FDA API (Internet offline?)")
            safe_print("   Ban co the bo qua loi nay neu internet bi ngat")
    
    except Exception as e:
        safe_print(f"[ERROR] Loi: {str(e)}")
        return False
    
    return True


def test_rag_engine():
    """Test module RAG Engine"""
    safe_print("\n" + "="*60)
    safe_print("TEST MODULE: rag_engine.py")
    safe_print("="*60)
    
    try:
        from rag_engine import load_inventory, find_alternative_drugs
        
        safe_print("[OK] Module import thanh cong")
        
        # Test load inventory
        safe_print("\n[INFO] Dang test load_inventory()...")
        df = load_inventory()
        safe_print(f"[OK] Load thanh cong: {len(df)} dong")
        safe_print(f"  Columns: {list(df.columns)}")
        
        # Test find alternatives
        safe_print("\n[INFO] Dang test find_alternative_drugs('ibuprofen')...")
        alternatives = find_alternative_drugs("ibuprofen")
        safe_print(f"[OK] Tim thay {len(alternatives)} thuoc thay the")
        if alternatives:
            for drug in alternatives[:2]:
                safe_print(f"  - {drug['Ten_Thuoc']} (Ton kho: {drug['Ton_Kho']})")
    
    except Exception as e:
        safe_print(f"[ERROR] Loi: {str(e)}")
        return False
    
    return True


def test_google_generativeai():
    """Test Google Generative AI installation"""
    safe_print("\n" + "="*60)
    safe_print("TEST: Google Generative AI")
    safe_print("="*60)
    
    try:
        import google.generativeai
        safe_print(f"[OK] google-generativeai cai dat OK")
        safe_print("\n[INFO] Luu y:")
        safe_print("   - Can API key tu: https://makersuite.google.com/app/apikey")
        safe_print("   - De test, chay: python rag_engine.py")
    
    except ImportError:
        safe_print("[ERROR] google-generativeai chua duoc cai dat")
        safe_print("   Chay: pip install google-generativeai")
        return False
    
    return True


def test_streamlit():
    """Test Streamlit installation"""
    safe_print("\n" + "="*60)
    safe_print("TEST: Streamlit")
    safe_print("="*60)
    
    try:
        import streamlit
        safe_print(f"[OK] Streamlit {streamlit.__version__} cai dat OK")
        safe_print("\n[INFO] De chay app:")
        safe_print("   streamlit run app.py")
    
    except ImportError:
        safe_print("[ERROR] Streamlit chua duoc cai dat")
        safe_print("   Chay: pip install -r requirements.txt")
        return False
    
    return True


def test_environment():
    """Test environment variables"""
    safe_print("\n" + "="*60)
    safe_print("TEST: Environment Variables")
    safe_print("="*60)
    
    gemini_api_key = os.getenv("GEMINI_API_KEY", "not set")
    gemini_model = os.getenv("GEMINI_MODEL", "not set")
    
    safe_print(f"GEMINI_API_KEY: {'[OK] Set' if gemini_api_key != 'not set' else '[FAIL] Not set'}")
    safe_print(f"GEMINI_MODEL: {gemini_model}")
    
    if gemini_api_key == "not set":
        safe_print("\n[WARN] GEMINI_API_KEY chua duoc cau hinh!")
        safe_print("   1. Mo file .env trong thư muc du an")
        safe_print("   2. Truy cap: https://makersuite.google.com/app/apikey")
        safe_print("   3. Tao API key va them vao .env")
        return False
    
    return True


def main():
    """Chay tat ca test"""
    safe_print("\n")
    safe_print("================================================================")
    safe_print("   PHARMACIST ASSISTANT v2.0 - MODULE TEST (GEMINI)             ")
    safe_print("================================================================")
    
    results = {
        "Environment": test_environment(),
        "FDA API": test_fda_api(),
        "RAG Engine": test_rag_engine(),
        "Google Generative AI": test_google_generativeai(),
        "Streamlit": test_streamlit(),
    }
    
    # Tom tat
    safe_print("\n" + "="*60)
    safe_print("KET QUA TEST")
    safe_print("="*60)
    
    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        safe_print(f"{test_name:25} {status}")
    
    all_passed = all(results.values())
    
    safe_print("\n" + "="*60)
    if all_passed:
        safe_print("TAT CA TEST PASS! Ban co the bat dau:")
        safe_print("   streamlit run app.py")
    else:
        safe_print("[WARN] Mot so test khong pass. Kiem tra loi o tren.")
    safe_print("="*60)


if __name__ == "__main__":
    main()
