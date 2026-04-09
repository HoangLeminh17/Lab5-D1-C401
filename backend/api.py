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
    from app.core.agent_engine import run_clinical_agent_with_context
except ImportError:
    def run_clinical_agent_with_context(brand_name, fda_info, alternative_drugs):
        return f"AI Agent khong kha dung cho: {brand_name}"

try:
    from api_fda import get_active_ingredients
except ImportError:
    def get_active_ingredients(brand_name):
        return ["Unknown"]

app = Flask(__name__)
CORS(app)


def _load_inventory():
    """Tim va load inventory.csv theo thu tu uu tien."""
    import os
    candidates = [
        os.getenv("INVENTORY_PATH", ""),
        "inventory.csv",
        "../inventory.csv",
        str(Path(__file__).resolve().parents[1] / "inventory.csv"),
        str(Path(__file__).resolve().parents[1] / "app" / "data" / "inventory.csv"),
    ]
    for path in candidates:
        if path and Path(path).exists():
            return pd.read_csv(path)
    raise FileNotFoundError("Khong tim thay inventory.csv")


def _find_alternatives(brand_name: str, active_ing_list: list) -> list:
    """Tim thuoc thay the trong inventory co cung hoat chat va con ton kho."""
    try:
        inventory = _load_inventory()
    except Exception as e:
        app.logger.warning(f"Load inventory that bai: {e}")
        return []

    alternative_drugs = []
    for _, row in inventory.iterrows():
        ten_thuoc = str(row.get("brand_name", ""))
        hoat_chat = str(row.get("generic_name", ""))
        ton_kho = row.get("stock_quantity", 0)

        if pd.isna(ton_kho):
            ton_kho = 0

        if ten_thuoc.strip().lower() == brand_name.lower():
            continue  # Bo qua chinh no

        is_match = any(
            ai.lower() in hoat_chat.lower() or hoat_chat.lower() in ai.lower()
            for ai in active_ing_list
            if ai and len(ai) > 2
        )

        if is_match and int(ton_kho) > 0:
            alternative_drugs.append({
                "Ten_Thuoc": ten_thuoc,
                "Hoat_Chat": hoat_chat,
                "Ton_Kho": int(ton_kho),
            })

    return alternative_drugs


@app.route("/recommend", methods=["POST"])
def recommend():
    try:
        data = request.json
        brand_name = data.get("brand_name", "")
        if not brand_name:
            return jsonify({"success": False, "error_message": "brand_name is empty"}), 400

        # ── Buoc 1: Lay hoat chat qua FDA API ──────────────────────────────────
        active_ing_list = get_active_ingredients(brand_name)
        hoat_chat_str = ", ".join(active_ing_list)

        fda_info = {
            "Hoat_Chat": hoat_chat_str,
            "Duong_Dung": "N/A",
            "Chi_Dinh": "N/A",
            "Chong_Chi_Dinh": "N/A",
            "Tac_Dung_Phu": "N/A",
            "success": True,
        }

        # ── Buoc 2: Tim thuoc thay the trong kho ──────────────────────────────
        alternative_drugs = _find_alternatives(brand_name, active_ing_list)

        # ── Buoc 3: Goi AI voi du lieu da co san (chi 1 LLM call) ─────────────
        # Truyen fda_info + alternative_drugs vao agent -> agent chi can synthesis,
        # khong can goi tools -> giam tu 3-5 Gemini calls xuong con 1 call.
        recommendation_text = run_clinical_agent_with_context(
            brand_name=brand_name,
            fda_info=fda_info,
            alternative_drugs=alternative_drugs,
        )

        # ── Buoc 4: Tra ket qua ────────────────────────────────────────────────
        payload = {
            "brand_name": brand_name,
            "fda_info": fda_info,
            "alternative_drugs": alternative_drugs,
            "recommendation": recommendation_text,
            "success": True,
            "error_message": "",
        }

        return jsonify(payload)

    except Exception as e:
        return jsonify({"success": False, "error_message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
