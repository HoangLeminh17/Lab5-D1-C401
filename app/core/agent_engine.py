# agents/pharmacist_agent.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from app.tools.fda import get_full_fda_info
from app.tools.interaction_checker import find_inventory_tool

system_prompt = ""

# Danh sách tools cho Agent
tools = [get_full_fda_info, find_inventory_tool]

# LLM hỗ trợ gọi tool (function calling)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")


# Tạo Agent: Tự động quyết định gọi tool nào khi cần
agent_executor = create_react_agent(
    model = llm,
    prompt= system_prompt,
    tools = tools
)