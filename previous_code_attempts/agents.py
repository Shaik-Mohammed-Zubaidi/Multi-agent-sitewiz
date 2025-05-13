import asyncio
import pathlib, sqlite3
from inspect import signature
from autogen_agentchat.ui import Console
from autogen_core.tools import FunctionTool          # NEW
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams  import RoundRobinGroupChat
from autogen_agentchat.messages import TextMessage
from autogen_ext.models.openai import OpenAIChatCompletionClient
import os
from dotenv import load_dotenv
load_dotenv()

# ---------- model clients ----------
gpt4o = OpenAIChatCompletionClient(model="gpt-4o-mini")
gpt35 = OpenAIChatCompletionClient(model="gpt-3.5-turbo")

# ---------- SQL function ----------
BASE_DB_PATH = pathlib.Path("bird_sql_mini/llm/mini_dev_data/data_minidev/MINIDEV/dev_databases")

def run_sql(db_id: str, query: str) -> dict:
    """Execute SQL against <db_id>.sqlite and return {'rows': [...]} or {'error': ...}."""
    db_path = BASE_DB_PATH / db_id / f"{db_id}.sqlite"
    print("========================")
    print("========================")
    print(f"DB Path: {db_path}", type(db_path))
    print("========================")
    print("========================")
    if not db_path.exists():
        return {"rows": None, "error": f"Database {db_path} does not exist."}
    
    try:
        with sqlite3.connect(db_path) as conn:
            rows = conn.execute(query).fetchall()
        return {"rows": rows, "error": None}
    except Exception as e:
        return {"rows": None, "error": str(e)}

sql_tool = FunctionTool(                             # REPLACES PythonTool
    run_sql,
    name="run_sql",
    description="Execute SQL query on given database and return result or error.",
)

# ---------- agents ----------
nl2sql = AssistantAgent(
    "NL2SQL",
    model_client=gpt4o,
    tools=[sql_tool],        # could also be tools=[run_sql] – autowraps to FunctionTool
    system_message=(
        "You generate SQL queries. Use only columns/tables present in schema. "
        "Call run_sql tool to execute queries."
    ),
)

critic = AssistantAgent(
    "Critic",
    model_client=gpt4o,
    system_message=(
        "You check SQL results. If error or empty rows, suggest fix SQL. "
        "If correct, respond with 'FINAL <SQL>' to finish."
    ),
)

planner = AssistantAgent(
    "Planner",
    model_client=gpt35,
    system_message="Coordinate the conversation and stop when Critic says FINAL.",
)

# ---------- solve ----------
async def solve(question: str, schema: str, db_id: str) -> str:
    chat = RoundRobinGroupChat(
        [planner, nl2sql, critic],
        max_turns=3,
    )
    result = await Console(chat.run_stream(task=f"{question}\n\nSchema:\n{schema}\nDB_ID:{db_id}"))
    print("Result:", result)
    print("Result final:", result.messages[-1].content)
    return result.messages[-1].content
    # for msg in reversed(result.messages):
    #     print(f"Message: {msg}")
    #     if msg.role == "assistant" and msg.content.startswith("FINAL"):
    #         return msg.content.removeprefix("FINAL").strip()
    return "FAILED"
