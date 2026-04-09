# 💊 Pharmacist Assistant

<p>
  <b>AI-powered decision support for pharmacists</b><br/>
  Find safe alternatives, normalize misspelled drug names, and check potential interaction risks.
</p>

<p>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white" />
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-UI-FF4B4B?logo=streamlit&logoColor=white" />
  <img alt="LangChain" src="https://img.shields.io/badge/LangChain-Agent-1B5E20" />
  <img alt="Gemini" src="https://img.shields.io/badge/Gemini-2.5%20Flash-1A73E8" />
  <img alt="OpenFDA" src="https://img.shields.io/badge/OpenFDA-Label%20API-0B7285" />
  <img alt="RxNorm" src="https://img.shields.io/badge/RxNorm-Approximate%20Term-6A1B9A" />
</p>

---

## ✨ Highlights

- 🔎 Query OpenFDA for core clinical fields
- 🧠 Normalize drug names via RxNorm (handles approximate spelling)
- 🏥 Match alternatives against internal inventory (CSV)
- ⚠️ Check pairwise interaction warnings from OpenFDA labels
- 💬 Generate concise Vietnamese recommendation text using Gemini
- ✅ Record pharmacist feedback (approve/reject) in UI session history

> <span style="color:#b45309;"><b>Clinical safety note:</b></span> This system supports decisions. It does not replace licensed pharmacist or physician judgment.

---

## 🧭 What The System Does

For an out-of-stock medicine request, the pipeline can:

1. Normalize the input drug name (brand/generic/typo handling)
2. Pull FDA label information:
   - active ingredient
   - route
   - indications
   - contraindications
   - adverse reactions
3. Find in-stock alternatives from internal inventory data
4. Produce concise clinical recommendation text for pharmacy staff
5. Optionally check interaction alerts for multi-drug combinations

---

## 🚨 Current Repository Gap

<div style="border-left: 4px solid #dc2626; padding: 10px 14px; background: #fff5f5;">
  <b style="color:#b91c1c;">Important:</b>
  <span style="color:#7f1d1d;"> app/main.py imports app/core/rag_engine.py, but this file is currently missing in this repository snapshot.</span>
</div>

Practical impact:
- ✅ Tools and agent engine exist and can run
- ⚠️ Streamlit UI path depends on the missing rag_engine module
- ⚠️ Some tests/docs still reference older rag_engine locations

---

## 🗂️ Project Structure

```text
Lab5-D1-C401/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py
│   │   └── agent_engine.py
│   ├── tools/
│   │   ├── check_name_drug.py
│   │   ├── fda.py
│   │   └── interaction_checker.py
│   └── data/
│       └── inventory.csv
├── docs/
│   └── README.md
├── tests/
│   ├── test_modules.py
│   ├── test_modules_for_dev.py
│   └── test.py
└── requirements.txt
```

---

## 🧩 Core Modules

### app/tools/check_name_drug.py

<div style="border-left: 4px solid #2563eb; padding: 8px 12px; background: #eff6ff;">
  <b style="color:#1d4ed8;">Role:</b> Normalize user drug input to US-standard naming via RxNorm APIs.
</div>

- Main function: get_us_standard_name
- Uses approximateTerm + properties endpoints
- Returns lowercase standardized name when possible

### app/tools/fda.py

<div style="border-left: 4px solid #0f766e; padding: 8px 12px; background: #f0fdfa;">
  <b style="color:#0f766e;">Role:</b> Fetch FDA label data and map alternatives from inventory.
</div>

- Main function: get_full_fda_info
- Helper functions:
  - resolve_inventory_path
  - load_inventory
  - find_alternative_drugs
- Returned fields:
  - Hoat_Chat
  - Duong_Dung
  - Chi_Dinh
  - Chong_Chi_Dinh
  - Tac_Dung_Phu

### app/tools/interaction_checker.py

<div style="border-left: 4px solid #9333ea; padding: 8px 12px; background: #faf5ff;">
  <b style="color:#7e22ce;">Role:</b> Run pairwise interaction lookup using OpenFDA label interaction text.
</div>

- Main function: check_interaction_openfda
- Builds combinations from input list
- Checks both directions A→B and B→A

### app/core/config.py

<div style="border-left: 4px solid #c2410c; padding: 8px 12px; background: #fff7ed;">
  <b style="color:#9a3412;">Role:</b> Prompt templates, safety settings, and environment-driven config.
</div>

- CLINICAL_SYSTEM_PROMPT
- CLINICAL_CONCISE_RESPONSE_RULES
- DRUG_EXPLANATION_RULES
- GEMINI_SAFETY_SETTINGS
- get_core_config

### app/core/agent_engine.py

<div style="border-left: 4px solid #15803d; padding: 8px 12px; background: #f0fdf4;">
  <b style="color:#166534;">Role:</b> LangChain tool-calling agent powered by Gemini.
</div>

- Creates a tool-enabled clinical assistant
- Registered tools:
  - get_full_fda_info
  - check_interaction_openfda
  - get_us_standard_name
- Main entry: run_clinical_agent

### app/main.py

<div style="border-left: 4px solid #be123c; padding: 8px 12px; background: #fff1f2;">
  <b style="color:#9f1239;">Role:</b> Streamlit interface for pharmacists (search, recommendation, explanation, feedback).
</div>

- UI features:
  - Search input for out-of-stock medicine
  - FDA details panel
  - Alternatives panel
  - Recommendation panel
  - Explain-this-drug button
  - Approve/Reject feedback buttons

---

## ⚙️ Requirements

- Python 3.10+
- pip
- Internet access for Gemini, OpenFDA, RxNorm

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## 🔐 Environment Variables

Create .env (or copy from .env.example):

```env
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash
INVENTORY_PATH=app/data/inventory.csv
```

> <span style="color:#065f46;"><b>Cost note:</b></span> OpenFDA and RxNorm are free/public. Main variable cost is Gemini inference.

---

## ▶️ Run

### Option A: Agent CLI (works now)

```bash
python app/core/agent_engine.py
```

Example prompt:
- Suggest alternatives for Advil and check interactions with aspirin.

### Option B: Streamlit UI (requires rag_engine)

```bash
streamlit run app/main.py
```

This path needs app/core/rag_engine.py to be restored/implemented.

---

## 🧪 Test Scripts

```bash
python tests/test_modules.py
python tests/test_modules_for_dev.py
python tests/test.py
```

Some tests still include legacy import references. Update paths if needed before running in this snapshot.

---

## 🗃️ Inventory Format

```csv
Ten_Thuoc,Hoat_Chat,Ton_Kho
```

- Ten_Thuoc: display/commercial name
- Hoat_Chat: active ingredient
- Ton_Kho: stock amount (0 = out of stock)

---

## 🛡️ Safety & Limitations

- OpenFDA data can be incomplete/inconsistent
- No match does not mean no risk
- Interaction search is label-text based, not a complete interaction DB
- Clinical outputs must be verified by licensed professionals

---

## 🚀 Suggested Next Steps

- Rebuild app/core/rag_engine.py for full UI pipeline
- Add confidence signaling for uncertain mapping results
- Add curated high-risk interaction regression set
- Add structured evaluation and analytics dashboard
- Move inventory from CSV to database-backed storage

---

## 📄 License

MIT License
