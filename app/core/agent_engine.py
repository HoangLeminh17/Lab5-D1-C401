import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.tools.fda import get_full_fda_info
from app.tools.interaction_checker import check_interaction_openfda
from langchain.agents import create_agent
from dotenv import load_dotenv
load_dotenv()

system_prompt = """Bạn là một DƯỢC SĨ LÂM SÀNG CẤP CAO với 20 năm kinh nghiệm.
Nhiệm vụ của bạn là tư vấn các nhân viên quầy thuốc khi cần tìm thuốc thay thế.

Hãy:
1. Phân tích hoạt chất, đường dùng, chỉ định, chống chỉ định của thuốc gốc
2. So sánh với các thuốc thay thế có sẵn trong kho
3. Giải thích lý do lựa chọn từng thuốc
4. Cảnh báo các điểm quan trọng (chống chỉ định, tác dụng phụ) BẰNG TIẾNG VIỆT
5. Format kết quả rõ ràng, dễ đọc, sử dụng Markdown

Luôn ưu tiên an toàn bệnh nhân. Nếu có nghi ngờ, hãy khuyến nghị bệnh nhân tham khảo bác sĩ."""
# Danh sách tools cho Agent
tools = [get_full_fda_info, check_interaction_openfda]

# LLM hỗ trợ gọi tool (function calling)
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key = os.getenv("GEMINI_API_KEY")
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