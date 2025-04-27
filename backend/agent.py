import mysql.connector
from langchain_community.llms import Ollama
from langchain.agents import initialize_agent, AgentExecutor, AgentType
from langchain_core.tools import Tool
import concurrent.futures
import constants

# MySQL Connection Setup
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=constants.PASSWORD,   
    database=constants.STUDENT_DATABASE    
)

# SQL Tool Functions

def create_table(query):
    try:
        cursor = conn.cursor() 
        cursor.execute(query)
        conn.commit()
        cursor.close()         
        return "Table created successfully!"
    except Exception as e:
        return f"Create table error: {str(e)}"


def modify_student(query):
    try:
        if query.strip().lower().startswith(("insert", "update", "delete", "alter", "drop")):
            cursor = conn.cursor()
            cursor.execute(query)
            conn.commit()
            cursor.close()
            return "Modification successful!"
        else:
            return "This tool only accepts INSERT, UPDATE, DROP, ALTER or DELETE queries."
    except Exception as e:
        return f"Modify error: {str(e)}"


def select_student(query):
    try:
        cursor = conn.cursor()
        cursor.execute(query)
        rows = cursor.fetchall()
        cursor.close()
        if not rows:
            return "No matching records found."
        return str(rows)
    except Exception as e:
        return f"Select error: {str(e)}"

def fallback_tool_handler(context):
    return (
        f"The system couldn't match your request to a specific tool or query.\n\n"
        f"Here's what the model returned:\n\n{context}\n\n"
        "If this looks like a valid response to you, please proceed. "
        "Otherwise, try rephrasing your request more clearly."
    )



# Define Tools

create_table_tool = Tool(
    name="CreateTableTool",
    func=create_table,
    description="Use to create new tables using SQL CREATE TABLE."
)

modify_tool = Tool(
    name="ModifyTool",
    func=modify_student,
    description="Use to insert, update, or delete student records or table using SQL INSERT, UPDATE, DROP, ALTER or DELETE queries."
)


select_tool = Tool(
    name="SelectTool",
    func=select_student,
    description="Use to query student data using SQL SELECT."
)

final_answer = Tool(
    name="Final Answer",
    func=fallback_tool_handler,
    description=(
        "Use this when the LLM provides a final answer without calling any tool, or "
        "when the request is unclear, incomplete, or doesn't translate into a SQL operation."
    )
)

tools = [
    create_table_tool,
    modify_tool,        
    select_tool,
    final_answer  
]

# LLM and Agent Setup
llm = Ollama(model="mistral")
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    handle_parsing_errors=True,
    verbose=True,
    agent_kwargs={
    "prefix": (
        "You are an intelligent AI assistant that manages a university student database using MySQL.\n\n"
        "You have access to four tools:\n"
        "• CreateTableTool — for creating tables.\n"
        "• ModifyTool — for INSERT, UPDATE, DELETE, DROP, or ALTER queries.\n"
        "• SelectTool — for SELECT queries to read data.\n"
        "• Final Answer — use when:\n"
        "   - The LLM already gives a natural final answer.\n"
        "   - The user's request is unclear or not actionable.\n\n"
        "Always call a tool. If you use Final Answer, return its result as the final response without further reasoning."
    )
}
)

agent_executor = AgentExecutor.from_agent_and_tools(
    agent=agent.agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    return_intermediate_steps=True,
    max_iterations=10,
)

# Test by command line
def run_agent_with_timeout(user_input, timeout=60):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(agent_executor.run, user_input)
        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            return f"Agent took too long to respond (over {timeout} seconds)."
        except Exception as e:
            return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    print("AI Agent Student DB Manager is ready!")
    while True:
        user_input = input("\nNhập yêu cầu của bạn: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = run_agent_with_timeout(user_input)
        print(response)
