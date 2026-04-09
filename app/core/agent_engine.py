# agents/pharmacist_agent.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent
from app.tools.pharmacist_tools import get_fda_info_tool, find_inventory_tool

# Danh sách tools cho Agent
tools = [get_fda_info_tool, find_inventory_tool]

# LLM hỗ trợ gọi tool (function calling)
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# Tạo Agent: Tự động quyết định gọi tool nào khi cần
agent_executor = create_react_agent(llm, tools)