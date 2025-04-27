from fastapi import FastAPI
from pydantic import BaseModel
import concurrent.futures
import mysql.connector
import datetime
import constants
# --- Import agent ---
from agent import agent_executor

app = FastAPI()

# MySQL connection for logs
log_conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=constants.PASSWORD,
    database=constants.LOG_DATABASE
)
log_cursor = log_conn.cursor()

# Create log table if not exists
log_cursor.execute("""
CREATE TABLE IF NOT EXISTS chat_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_input TEXT,
    agent_response TEXT,
    timestamp DATETIME
)
""")
log_conn.commit()

class QueryRequest(BaseModel):
    question: str

def save_log_to_mysql(user_input, agent_response):
    log_cursor.execute(
        "INSERT INTO chat_logs (user_input, agent_response, timestamp) VALUES (%s, %s, %s)",
        (user_input, agent_response, datetime.datetime.now())
    )
    log_conn.commit()

def save_log_to_file(user_input, agent_response):
    with open("chat_logs.txt", "a", encoding="utf-8") as f:
        f.write(f"User: {user_input}\n")
        f.write(f"Agent: {agent_response}\n")
        f.write(f"Timestamp: {datetime.datetime.now()}\n\n")

@app.post("/ask")
def ask_agent(data: QueryRequest):
    try:
        result = agent_executor.invoke({"input": data.question})
        full_trace = result.get("intermediate_steps", [])
        final_answer = result.get("output", "⚠️ No final answer.")
        return {
            "final_answer": final_answer,
            "trace": [(step[0].log, step[1]) for step in full_trace]
        }
    except Exception as e:
        return {"final_answer": f"⚠️ Error: {str(e)}", "trace": []}


