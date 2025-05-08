import re
import os
from autogen_agentchat.ui import Console
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv

load_dotenv()

gpt4 = OpenAIChatCompletionClient(model="gpt-4o-mini")
gpt35 = OpenAIChatCompletionClient(model="gpt-3.5-turbo")

# Define the agents

nl2sql = AssistantAgent(
    "NL2SQL",
    model_client=gpt4,
    system_message=(
        "You generate SQL queries based on the question, plan, schema and evidence. "
        "Use only allowed table names and columns mentioned in schema. "
        "Do not invent new table names or columns. "
        "Do not execute the SQL, only generate the SQL query."
    )
)

critic = AssistantAgent(
    "Critic",
    model_client=gpt4,
    system_message=(
        "You check the generated SQL query for correctness."
        "If the query is correct, return it as-is."
        "If the query is incorrect, return the corrected SQL query."
        "Do not add any extra words or explanations — only return the pure SQL query."
        "Do not execute the SQL. Only generate or fix SQL queries."
    )
)

planner = AssistantAgent(
    "Planner",
    model_client=gpt4,
    system_message=(
        "You plan how to solve the question using SQL. "
        "Suggest which tables, filters, joins and columns are needed. "
        "Make a short plan. "
        "Do not generate SQL. Only make a plan and pass to NL2SQL."
    )
)

# Solve function using GroupChat

async def solve(question: str, schema: str, db_id: str, evidence: str = "") -> str:
    chat = RoundRobinGroupChat(
        [planner, nl2sql, critic],
        max_turns=3,
    )

    full_prompt = f"Question: {question}\nSchema:\n{schema}\nDB_ID: {db_id}"
    if evidence:
        full_prompt += f"\nEvidence: {evidence}"

    result = await Console(chat.run_stream(task=full_prompt))
    with open("agent_log.txt", "a", encoding="utf-8") as log_file:
        log_file.write("=====================\n")
        log_file.write(f"Question: {question}\n db_id: {db_id}\n")
        for msg in result.messages:
            log_file.write(str(msg) + "\n")


    # print("Result:", result)
    # print("Result final:", result.messages[-1].content)
    # return result.messages[-1].content
    for msg in reversed(result.messages):
        if msg.source == "Critic":
            msg_content = msg.content.strip()
            cleaned = re.sub(r"```sql\s*|\s*```", "", msg_content).strip()
            return cleaned

    return "FAILED"
