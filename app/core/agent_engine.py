import sys
import time
import logging
import threading
from collections import deque
from pathlib import Path

# Ho tro chay truc tiep: python app/core/agent_engine.py
if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from langchain_google_genai import ChatGoogleGenerativeAI
from app.tools.fda import get_full_fda_info
from app.tools.interaction_checker import check_interaction_openfda
from langchain.agents import create_agent
from app.core.config import CLINICAL_SYSTEM_PROMPT, get_core_config
from app.tools.check_name_drug import get_us_standard_name

logger = logging.getLogger(__name__)

CORE_CONFIG = get_core_config()

# ── Rate Limiter ────────────────────────────────────────────────────────────────
# gemini-2.5-flash free tier: 5 RPM. Dat nguong 4 de co buffer tranh 429.
_rate_lock = threading.Lock()
_call_timestamps: deque = deque()
_MAX_CALLS_PER_MINUTE = 4


def _acquire_rate_limit() -> bool:
    """
    Tra ve True neu co the goi LLM ngay.
    Tra ve False neu da dat gioi han RPM (khong block, caller tu xu ly fallback).
    """
    now = time.monotonic()
    with _rate_lock:
        # Don timestamp cu hon 60 giay
        while _call_timestamps and now - _call_timestamps[0] > 60:
            _call_timestamps.popleft()
        if len(_call_timestamps) >= _MAX_CALLS_PER_MINUTE:
            return False
        _call_timestamps.append(now)
        return True


# ── LLM & Agent ────────────────────────────────────────────────────────────────
system_prompt = CLINICAL_SYSTEM_PROMPT
tools = [get_full_fda_info, check_interaction_openfda, get_us_standard_name]

llm = ChatGoogleGenerativeAI(
    model=CORE_CONFIG.gemini_model,
    api_key=CORE_CONFIG.gemini_api_key,
)

agent_executor = create_agent(
    model=llm,
    system_prompt=system_prompt,
    tools=tools,
)

# ── Response Cache ───────────────────────────────────────────────────────────────
_response_cache: dict = {}
_MAX_CACHE_ENTRIES = 50


# ── Fallback builder ────────────────────────────────────────────────────────────
def _build_fallback_response(brand_name: str, fda_info: dict, alternative_drugs: list) -> str:
    """
    Tao phan hoi du phong (khong can LLM) khi Gemini bi rate limit.
    Dung du lieu FDA va inventory da co san.
    """
    lines = [f"## Goi y thay the cho **{brand_name}** *(che do tu dong - AI tam thoi khong kha dung)*\n"]

    if fda_info and fda_info.get("success"):
        hoat_chat = fda_info.get("Hoat_Chat", "N/A")
        duong_dung = fda_info.get("Duong_Dung", "N/A")
        lines.append(f"- **Hoat chat:** {hoat_chat}")
        lines.append(f"- **Duong dung:** {duong_dung}")

    if alternative_drugs:
        lines.append(f"\n### Thuoc thay the co san trong kho ({len(alternative_drugs)} san pham):")
        for d in alternative_drugs[:5]:
            ten = d.get("Ten_Thuoc", d.get("brand_name", "N/A"))
            hoat = d.get("Hoat_Chat", d.get("generic_name", "N/A"))
            ton = d.get("Ton_Kho", d.get("stock_quantity", 0))
            lines.append(f"  - **{ten}** — Hoat chat: {hoat} | Ton kho: {ton}")
    else:
        lines.append("\n Khong tim thay thuoc thay the trong kho.")

    lines.append(
        "\n> *AI dang bi gioi han toc do. Vui long thu lai sau 1 phut de nhan tu van lam sang chi tiet.*"
    )
    return "\n".join(lines)


# ── Internal invoke ─────────────────────────────────────────────────────────────
def _invoke_agent(query: str) -> str:
    """Goi agent, parse content, tra ve text. Khong xu ly cache/rate-limit."""
    inputs = {"messages": [("user", query)]}
    response = agent_executor.invoke(inputs)
    content = response["messages"][-1].content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join(parts).strip()
    elif isinstance(content, str):
        return content
    return str(content)


def _is_rate_limit_error(err_str: str) -> bool:
    return "429" in err_str or "RESOURCE_EXHAUSTED" in err_str


def _is_unavailable_error(err_str: str) -> bool:
    return "503" in err_str or "UNAVAILABLE" in err_str


# ── Public API ──────────────────────────────────────────────────────────────────
def run_clinical_agent(query: str) -> str:
    """
    Ham goc: chay agent voi query tu do (agent tu goi tools).
    Co cache + rate limit + fallback khi 429/503.
    """
    cache_key = query.strip().lower()
    if cache_key in _response_cache:
        logger.info("[AGENT][CACHE_HIT] query='%s'", query[:60])
        return _response_cache[cache_key]

    if not _acquire_rate_limit():
        logger.warning("[AGENT][RATE_LIMITED] Dat gioi han %d RPM, tra fallback.", _MAX_CALLS_PER_MINUTE)
        return _build_fallback_response(query[:40], {}, [])

    try:
        result_text = _invoke_agent(query)
        if len(_response_cache) < _MAX_CACHE_ENTRIES:
            _response_cache[cache_key] = result_text
        return result_text

    except Exception as e:
        err_str = str(e)
        if _is_rate_limit_error(err_str):
            logger.warning("[AGENT][429] Rate limit hit: %s", err_str[:120])
            return _build_fallback_response(query[:40], {}, [])
        if _is_unavailable_error(err_str):
            logger.warning("[AGENT][503] Service unavailable: %s", err_str[:120])
            return _build_fallback_response(query[:40], {}, [])
        logger.error("[AGENT][ERROR] %s", err_str)
        return f"Loi khi chay agent: {err_str}"


def run_clinical_agent_with_context(
    brand_name: str,
    fda_info: dict,
    alternative_drugs: list,
) -> str:
    """
    Phien ban toi uu: nhan data FDA + kho da co san, chi can 1 LLM call de synthesis.
    Agent KHONG can goi them tools -> giam so luong Gemini request tu 3-5 xuong con 1.
    """
    cache_key = f"ctx:{brand_name.strip().lower()}"
    if cache_key in _response_cache:
        logger.info("[AGENT][CACHE_HIT] brand='%s'", brand_name)
        return _response_cache[cache_key]

    if not _acquire_rate_limit():
        logger.warning("[AGENT][RATE_LIMITED] brand='%s', tra fallback.", brand_name)
        return _build_fallback_response(brand_name, fda_info, alternative_drugs)

    # Xay dung context day du de LLM chi can tong hop, khong can goi tool nao
    alt_summary_lines = []
    if alternative_drugs:
        for d in alternative_drugs[:8]:
            ten = d.get("Ten_Thuoc", d.get("brand_name", "N/A"))
            hoat = d.get("Hoat_Chat", d.get("generic_name", "N/A"))
            ton = d.get("Ton_Kho", d.get("stock_quantity", 0))
            alt_summary_lines.append(f"  - {ten} (hoat chat: {hoat}, ton kho: {ton})")
        alt_summary = "\n".join(alt_summary_lines)
    else:
        alt_summary = "  - Khong co thuoc thay the trong kho."

    safe = fda_info or {}
    hoat_chat = safe.get("Hoat_Chat", "N/A")
    duong_dung = safe.get("Duong_Dung", "N/A")
    chi_dinh = (safe.get("Chi_Dinh") or "N/A")[:300]
    chong_cd = (safe.get("Chong_Chi_Dinh") or "N/A")[:200]
    tac_dung_phu = (safe.get("Tac_Dung_Phu") or "N/A")[:200]

    context_query = (
        f"Toi can tu van lam sang ngan gon ve thuoc thay the. Thong tin da duoc tra cuu san:\n\n"
        f"Thuoc goc: {brand_name}\n"
        f"Hoat chat: {hoat_chat}\n"
        f"Duong dung: {duong_dung}\n"
        f"Chi dinh: {chi_dinh}\n"
        f"Chong chi dinh: {chong_cd}\n"
        f"Tac dung phu: {tac_dung_phu}\n\n"
        f"Thuoc thay the co san trong kho:\n{alt_summary}\n\n"
        f"Hay tong hop tu van lam sang ngan gon (toi da 5 gach dau dong) ve lua chon thuoc thay the "
        f"phu hop nhat va canh bao quan trong. KHONG can tra cuu them tools vi du lieu da day du."
    )

    try:
        result_text = _invoke_agent(context_query)
        if len(_response_cache) < _MAX_CACHE_ENTRIES:
            _response_cache[cache_key] = result_text
        return result_text

    except Exception as e:
        err_str = str(e)
        if _is_rate_limit_error(err_str):
            logger.warning("[AGENT][429] brand='%s': %s", brand_name, err_str[:120])
        elif _is_unavailable_error(err_str):
            logger.warning("[AGENT][503] brand='%s': %s", brand_name, err_str[:120])
        else:
            logger.error("[AGENT][ERROR] brand='%s': %s", brand_name, err_str)
        return _build_fallback_response(brand_name, fda_info, alternative_drugs)


if __name__ == "__main__":
    print("Pharmacist Agent (type 'exit' to quit)\n")

    while True:
        query = input("Ban: ")
        if query.lower() in ["exit", "quit"]:
            print("Tam biet!")
            break
        answer = run_clinical_agent(query)
        print("Agent:", answer)
