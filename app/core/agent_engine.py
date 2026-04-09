import sys
from pathlib import Path

# Hỗ trợ chạy trực tiếp: python app/core/agent_engine.py
if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from langchain_google_genai import ChatGoogleGenerativeAI
from app.tools.fda import get_full_fda_info
from app.tools.interaction_checker import check_interaction_rxnav
from langchain.agents import create_agent
from app.core.config import CLINICAL_SYSTEM_PROMPT, get_core_config

CORE_CONFIG = get_core_config()

system_prompt = CLINICAL_SYSTEM_PROMPT
# Danh sách tools cho Agent
tools = [get_full_fda_info, check_interaction_rxnav]

# LLM hỗ trợ gọi tool (function calling)
llm = ChatGoogleGenerativeAI(
    model=CORE_CONFIG.gemini_model,
    api_key=CORE_CONFIG.gemini_api_key
)

# Tạo Agent: Tự động quyết định gọi tool nào khi cần
agent_executor = create_agent(
    model = llm,
    system_prompt= system_prompt,
    tools = tools
)

def run_clinical_agent(query: str) -> str:
    """Hàm chạy agent để trả lời câu hỏi của người dùng"""
    try:
        inputs = {"messages": [("user", query)]}
        response = agent_executor.invoke(inputs)

        # Trả về tin nhắn cuối cùng từ agent
        return response["messages"][-1].content
    except Exception as e:
        return f"Lỗi khi chạy agent: {str(e)}"

if __name__ == "__main__":
    print("💊 Pharmacist Agent (type 'exit' to quit)\n")

    while True:
        query = input("🧑 Bạn: ")

        if query.lower() in ["exit", "quit"]:
            print("👋 Tạm biệt!")
            break

        answer = run_clinical_agent(query)
        print("🤖 Agent:", answer)