import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from langchain_core.tools import Tool, StructuredTool
from agent_tools import check_availability, book_slot_event, BookSlotInput,tell_today_date, get_today_free_slots


load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="models/gemini-2.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.4,
                             convert_system_message_to_human=True)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)



tools = [
    Tool.from_function(
        func=check_availability,
        name="check_availability",
        description="Check if a specific time slot like 'July 3 at 3pm' is available.",
        return_direct=True
    ),
    StructuredTool.from_function(
        func=book_slot_event,
        name="book_slot_event",
        description="Book a calendar event given a title and time.",
        args_schema=BookSlotInput,
        return_direct=True
    ),
    Tool.from_function(
        func=get_today_free_slots,
        name="get_today_free_slots",
        description="Returns a list of available time slots for the given day. Input should be a natural language date like 'today', 'tomorrow', or 'July 3'.",
        return_direct=True
    ),

    StructuredTool.from_function(
        func=tell_today_date,
        name="tell_today_date",
        description="Returns today's date if the user asks 'what is today's date', 'what day is today', etc.",
        return_direct=True
    )

]


prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant that can help users book calendar appointments, check availability, return today's date, and suggest free time slots using tools."),
    ("placeholder", "{chat_history}"),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

agent = create_tool_calling_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True
)


def run_agent(user_query: str) -> str:
    try:
        response = agent_executor.invoke({"input": user_query})
        if isinstance(response, dict) and "output" in response:
            return response["output"]
        else:
            return str(response)
    except Exception as e:
        print(f"Error running agent: {e}")
        return f"Sorry, I encountered an error: {str(e)}"
