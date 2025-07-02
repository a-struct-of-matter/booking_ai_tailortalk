import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
from agent_tools import check_availability, book_slot_event
from langchain_core.tools import Tool

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

llm = ChatGoogleGenerativeAI(model="models/gemini-1.5-flash", google_api_key=GEMINI_API_KEY, temperature=0.4,
                             convert_system_message_to_human=True)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

tools = [
    Tool.from_function(
        func=check_availability,
        name="check_availability",
        description="Checks if a time slot is available in the calendar",
        return_direct=True
    ),
    Tool.from_function(
        func=book_slot_event,
        name="book_slot_event",
        description="Books an event on the calendar",
        return_direct=True
    )
]

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI assistant that helps users book and check calendar events."),
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
