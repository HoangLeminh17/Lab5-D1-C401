from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import pandas as pd
from pathlib import Path

# Add project root to sys.path so we can import from app
project_root = str(Path(__file__).resolve().parents[1])
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Try to import agent_engine. If not found, create a placeholder.
try:
    from app.core.agent_engine import run_clinical_agent
except ImportError:
    def run_clinical_agent(query):
        return f"AI Agent consultation for: {query}\n(Note: Agent engine not fully connected)"

try:
    from api_fda import get_active_ingredients
except ImportError:
    def get_active_ingredients(brand_name):
        return ["Unknown"]

app = Flask(__name__)
CORS(app)

@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.json
        brand_name = data.get("brand_name", "")
        if not brand_name:
            return jsonify({"success": False, "error_message": "brand_name is empty"}), 400
            
        # 1. Provide AI clinical recommendation
        # Prompt the agent assuming it replies with clinical advice regarding alternatives
        agent_query = f"Tôi đang tìm kiếm thông tin lâm sàng và gợi ý thay thế khi thuốc '{brand_name}' bị hết hàng. Hãy tư vấn."
        recommendation_text = run_clinical_agent(agent_query)
        
        # 2. Get active ingredients (mock FDA response for basic JSON compliance)
        # Next.js will use this or its own fallback. If Next.js receives success=True, it uses this data.
        # But wait, Next.js can calculate fda_info and alternative_drugs internally if we don't return them here?
        # Actually Next.js expects a FULL response if success: true!
        
        # Let's search inventory for alternative_drugs
        try:
            import os
            inventory_path = os.getenv("INVENTORY_PATH", "app/data/inventory.csv")
            if not os.path.exists(inventory_path):
                inventory_path = "../inventory.csv" if os.path.exists("../inventory.csv") else "inventory.csv"
            inventory = pd.read_csv(inventory_path)
            # Convert values manually for simplicity
            alternative_drugs = []
            active_ing_list = get_active_ingredients(brand_name)
            
            if inventory is not None and not inventory.empty:
                for idx, row in inventory.iterrows():
                    ten_thuoc = str(row.get('brand_name', ''))
                    hoat_chat = str(row.get('generic_name', ''))
                    ton_kho = row.get('stock_quantity', 0)
                    
                    if pd.isna(ton_kho):
                        ton_kho = 0
                    
                    if ten_thuoc.strip().lower() != brand_name.lower():
                        # Just a naive match if we couldn't properly fetch active_ing
                        is_match = False
                        for ai in active_ing_list:
                            if ai.lower() in hoat_chat.lower() or hoat_chat.lower() in ai.lower():
                                is_match = True
                        if is_match and int(ton_kho) > 0:
                            alternative_drugs.append({
                                "Ten_Thuoc": ten_thuoc,
                                "Hoat_Chat": hoat_chat,
                                "Ton_Kho": int(ton_kho)
                            })
        except Exception as e:
            alternative_drugs = []
            print(f"Error reading inventory: {e}")

        # Basic fda info
        fda_info = {
            "Hoat_Chat": ", ".join(get_active_ingredients(brand_name)),
            "Duong_Dung": "N/A",
            "Chi_Dinh": "N/A",
            "Chong_Chi_Dinh": "N/A",
            "Tac_Dung_Phu": "N/A",
            "success": True
        }

        # Build final payload
        payload = {
            "brand_name": brand_name,
            "fda_info": fda_info,
            "alternative_drugs": alternative_drugs,
            "recommendation": recommendation_text,
            "success": True,
            "error_message": ""
        }
        
        return jsonify(payload)

    except Exception as e:
        return jsonify({"success": False, "error_message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
