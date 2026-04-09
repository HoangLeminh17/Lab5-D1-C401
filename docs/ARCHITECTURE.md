# 🏗️ System Architecture

## Sơ Đồ Kiến Trúc Tổng Quát

```
┌────────────────────────────────────────────────────────┐
│                   Streamlit Frontend                   │
│  (User Input, API Key, Display, Feedback Buttons)      │
└─────────────────────────┬──────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌──────────┐    ┌────────────┐    ┌──────────────┐
   │ fda_api  │    │InventorySV │    │ rag_engine   │
   │  .py     │    │  (CSV)     │    │    .py       │
   └────┬─────┘    └────┬───────┘    └──────┬───────┘
        │                │                   │
        │                │                   │
        ▼                ▼                   ▼
   ┌─────────────────────┐        ┌──────────────────┐
   │   OpenFDA API       │        │ Google Gemini    │
   │ (HTTP GET Request)  │        │ API (REST)       │
   └─────────────────────┘        └──────────────────┘
        (English)                       (Gemini Model)
                                      (Vietnamese Output)
```

---

## Module Breakdown

### 1️⃣ **fda_api.py** - Tra Cứu OpenFDA

```
Input: brand_name (str)
    ↓
[Build Query String]
    search = 'openfda.brand_name:"Advil"'
    ↓
[Send HTTP GET Request to FDA API]
    https://api.fda.gov/drug/label.json?search=...&limit=1
    ↓
[Parse JSON Response]
    Extract fields:
    - active_ingredient[0].name
    - route[]
    - indications_and_usage
    - contraindications
    - adverse_reactions
    ↓
[Build Dictionary]
    {
        "Hoat_Chat": "...",
        "Duong_Dung": "...",
        "Chi_Dinh": "...",
        "Chong_Chi_Dinh": "...",
        "Tac_Dung_Phu": "...",
        "success": True
    }
    ↓
Output: Dict
```

**Error Handling:**
- Timeout (10s)
- Connection Error
- HTTP Error
- JSON Parse Error
- Missing fields (set to "Not available")

---

### 2️⃣ **rag_engine.py** - RAG Engine Chính

```
Input: thuoc_het_hang (str), gemini_api_key (str)
    ↓
[Step 1: Configure Gemini]
    genai.configure(api_key=gemini_api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    ↓
[Step 2: Get FDA Info]
    fda_info = get_full_fda_info(thuoc_het_hang)
    if not success: return error
    ↓
[Step 3: Find Alternative Drugs]
    df = load_inventory()  # Load CSV
    alternatives = df[
        (df["Hoat_Chat"] == active_ingredient) &
        (df["Ton_Kho"] > 0)
    ]
    ↓
[Step 4: Build System Prompt]
    system_instruction = """
    Bạn là dược sĩ lâm sàng...
    """
    ↓
[Step 5: Build User Message]
    user_message = f"""
    {fda_summary}
    {alternative_drugs_text}
    Hãy tư vấn...
    """
    ↓
[Step 6: Call Gemini API]
    response = model.generate_content(
        user_message,
        safety_settings=[...]
    )
    ↓
[Step 7: Return Result]
    {
        "brand_name": "...",
        "fda_info": {...},
        "alternative_drugs": [...],
        "recommendation": "...",
        "success": True
    }
    ↓
Output: Dict
```

**Key Features:**
- System Prompt: Dược sĩ lâm sàng
- Auto Translation: English → Tiếng Việt
- Markdown Format: Pretty output
- Safety Settings: BLOCK_NONE (for medical)

---

### 3️⃣ **app.py** - Streamlit UI

```
Page Load
    ↓
[Display Header]
    Trợ lý Dược sĩ - Powered by Google Gemini
    ↓
[Sidebar]
    Settings + Instructions + Documentation Links
    ↓
[Input Section]
    - Password input: Gemini API Key
    - Text input: Brand name
    - Buttons: Search, Clear
    ↓
[If API Key Missing]
    Show warning + instructions to get API key
    STOP (st.stop())
    ↓
[If Search Button Clicked]
    - Validate input
    - Call get_clinical_recommendation()
    - Show spinner while processing
    - Store result in session_state
    ↓
[Display Results]
    - Metrics (Brand name, Active ingredient, Count)
    - FDA Info (5 fields)
    - Alternative Drugs (List)
    - Gemini Recommendation (Markdown)
    ↓
[Action Buttons]
    ✅ Duyệt Bán
    ❌ Từ Chối  
    🔄 Tư Vấn Khác
    ↓
[Chat History]
    Show last 5 recommendations
    ↓
Page Rendered
```

**Session State Management:**
- `recommendation_result`: Stores current recommendation
- `feedback_submitted`: Track if feedback was given
- `chat_history`: List of past recommendations

---

## Data Flow

### Complete Flow Example

```
User enters "Advil" + clicks search
            ↓
    ┌───────────────────────┐
    │ app.py processes      │
    └────────────┬──────────┘
                 ↓
    ┌───────────────────────┐
    │ rag_engine.py         │
    │ get_clinical_         │
    │ recommendation()      │
    └────┬────────┬────┬────┘
         │        │    │
         ▼        ▼    ▼
    FDA   Pandas  Gemini
    API   CSV     API
    
    ↓ ↓ ↓ (All results collected)
    
    ┌───────────────────────┐
    │ Merge all data        │
    │ Format as markdown    │
    │ Return to app.py      │
    └────────────┬──────────┘
                 ↓
    ┌───────────────────────┐
    │ app.py displays:      │
    │ - FDA info            │
    │ - Alternatives        │
    │ - Recommendation      │
    │ - Action buttons      │
    └───────────────────────┘
                 ↓
    User clicks [Duyệt Bán] or [Từ Chối]
                 ↓
    Feedback stored in chat_history
```

---

## API Integrations

### 1. OpenFDA API

**Endpoint:** `https://api.fda.gov/drug/label.json`

**Query Parameters:**
```
search=openfda.brand_name:"Advil"
limit=1
```

**Response Fields Used:**
```json
{
  "results": [{
    "active_ingredient": [{"name": "ibuprofen"}],
    "route": ["ORAL"],
    "indications_and_usage": "...",
    "contraindications": "...",
    "adverse_reactions": "..."
  }]
}
```

**Error Handling:** See fda_api.py

---

### 2. Google Gemini API

**Endpoint:** Uses `google-generativeai` SDK (wraps REST API)

**Model:** `gemini-2.5-flash`

**Parameters:**
```python
model.generate_content(
    user_message,
    safety_settings=[
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        # ... (other categories set to BLOCK_NONE for medical use)
    ]
)
```

**Output:** Markdown text with Vietnamese translation

---

## File Structure

```
Drug/
├── fda_api.py              # Module 1: FDA API Integration
│   └── get_full_fda_info(brand_name)
│
├── rag_engine.py           # Module 2: RAG Engine
│   ├── load_inventory()
│   ├── find_alternative_drugs(active_ingredient)
│   └── get_clinical_recommendation(brand, api_key)
│
├── app.py                  # Module 3: Streamlit UI
│   ├── display_header()
│   ├── display_api_key_input()
│   ├── display_search_form()
│   ├── display_fda_info()
│   ├── display_recommendation()
│   ├── display_feedback_buttons()
│   └── main()
│
├── inventory.csv           # Data: Mock drug database
│   └── [Ten_Thuoc, Hoat_Chat, Ton_Kho]
│
├── requirements.txt        # Dependencies
├── .env.example            # Configuration template
├── .gitignore              # Git ignore rules
├── README.md               # Full documentation
├── QUICK_START.md          # 5-minute setup guide
├── UPGRADE_NOTES.md        # v1.0 → v2.0 changes
├── ARCHITECTURE.md         # This file
└── test_modules.py         # Testing script
```

---

## Session State Management

Streamlit uses session_state to persist data across reruns:

```python
# Initialize
if "recommendation_result" not in st.session_state:
    st.session_state.recommendation_result = None

# Use
st.session_state.recommendation_result = result

# Access
if st.session_state.recommendation_result:
    # Display result
```

---

## Error Handling Strategy

### Level 1: Input Validation
```python
if not api_key:
    st.stop()
if not brand_name.strip():
    continue
```

### Level 2: API Call Errors
```python
try:
    result = requests.get(..., timeout=10)
except Timeout:
    return {"success": False, "error": "Timeout"}
except ConnectionError:
    return {"success": False, "error": "Connection failed"}
```

### Level 3: Data Processing
```python
if not fda_info["success"]:
    return error_result
if alternatives.empty:
    logger.warning("No alternatives found")
```

### Level 4: User Feedback
```python
if not result["success"]:
    st.error(f"❌ {result['error_message']}")
```

---

## Scalability Considerations

### Current Design (Suitable for 100-1000 users)

1. **CSV Storage**: inventory.csv
2. **API Calls**: No caching (direct calls)
3. **LLM**: Direct Gemini API calls
4. **Deployment**: Single Streamlit server

### Future Improvements (1000+ users)

1. Replace CSV → Vector DB (Pinecone, Weaviate)
2. Add caching layer (Redis)
3. Use async API calls
4. Load balancing + multiple servers
5. Analytics/monitoring

---

## Security Considerations

### Current Implementation

- ✅ API Key as password input (not in .env)
- ✅ timeout on API calls (10s)
- ✅ Input validation

### Future Hardening

- [ ] API Key encryption in storage
- [ ] Rate limiting per API key
- [ ] Audit logging
- [ ] HTTPS only
- [ ] CORS policy
- [ ] Authentication system

---

## Performance Metrics

### Typical Latency

| Component | Time |
|-----------|------|
| FDA API call | 500-1500ms |
| CSV lookup | 10-50ms |
| Gemini API call | 300-800ms |
| **Total** | **~1-3 seconds** |

### Optimization Tips

1. Pre-cache FDA data → Further reduce latency
2. Use Gemini streaming → Show results as they generate
3. Implement caching layer → Reduce redundant calls

---

## Monitoring & Logging

### Current Logging

```python
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("✅ Event success")
logger.error("❌ Event failed")
logger.warning("⚠️ Event warning")
```

### Manual Testing

```bash
# Test FDA API
python fda_api.py

# Test RAG Engine
python rag_engine.py

# Test all modules
python test_modules.py

# Run Streamlit app
streamlit run app.py
```

---

**Architecture Last Updated:** April 2026
