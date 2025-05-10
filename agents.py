import re
import os
import autogen
from autogen import AssistantAgent

from dotenv import load_dotenv

load_dotenv()
config_list_gemini = autogen.config_list_from_json("model_config.json")

# Define the agents

nl2sql = AssistantAgent(
    name="NL2SQL",
    llm_config = {"config_list" : config_list_gemini},
    system_message=(
        "You generate SQL queries based on the question, plan, schema and evidence. "
        "Use only allowed table names and columns mentioned in schema. "
        "Do not invent new table names or columns. "
        "Do not execute the SQL, only generate the SQL query."
        "Do not add any extra words or explanations — only return the pure SQL query."
    )
)

critic = AssistantAgent(
    name="Critic",
    llm_config = {"config_list" : config_list_gemini},
    system_message=(
        "You check the generated SQL query for correctness."
        "If the query is correct, return it as-is."
        "If the query is incorrect, return the corrected SQL query."
        "Do not add any extra words or explanations — only return the pure SQL query."
        "Do not execute the SQL. Only generate or fix SQL queries."
    )
)

planner = AssistantAgent(
    name="Planner",
    llm_config = {"config_list" : config_list_gemini},
    system_message=(
        "You plan how to solve the question using SQL. "
        "Suggest which tables, filters, joins and columns are needed. Give clear names of tables and columns that can be used by another agent."
        "Make a short plan. "
        "Do not generate SQL. Only make a plan and pass to NL2SQL."
    )
)

def solve(question: str, schema: str, db_id: str, evidence: str = "") -> str:
    full_prompt = f"Question: {question}\nDB_ID: {db_id}"
    if evidence:
        full_prompt += f"\nEvidence: {evidence}"

    # Step 1: Planner → plans
    planner_prompt = f"{full_prompt}\nSchema:{schema}"
    planner_reply = planner.generate_reply(messages=[{"role": "user", "content": planner_prompt}])
    plan = planner_reply["content"]

    # Step 2: NL2SQL → generates SQL
    nl2sql_prompt = f"{full_prompt}\n\nPlanner's Plan:\n{plan}"
    nl2sql_reply = nl2sql.generate_reply(messages=[{"role": "user", "content": nl2sql_prompt}])
    sql = nl2sql_reply["content"]

    # Step 3: Critic → checks and responds FINAL <SQL>
    critic_prompt = f"{full_prompt}\n\nGenerated SQL:\n{sql}"
    critic_reply = critic.generate_reply(messages=[{"role": "user", "content": critic_prompt}])
    final = critic_reply["content"]

    # Optional: logging
    with open("agent_log2.txt", "a", encoding="utf-8") as log_file:
        log_file.write("=====================\n")
        log_file.write(f"Question: {question}\n db_id: {db_id}\n")
        log_file.write(f"Planner: {plan}\n")
        log_file.write(f"NL2SQL: {sql}\n")
        log_file.write(f"Critic: {final}\n")

    # Extract the SQL query from the Critic's response
    if final:
        sql_only = re.sub(r"```sql\s*|\s*```", "", final).strip()
        return sql_only

    raise ValueError("No FINAL SQL found in Critic output.")
