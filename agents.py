import re
import os
import sqlite3
import autogen
from autogen import AssistantAgent

from dotenv import load_dotenv

load_dotenv()
config_list_gemini = autogen.config_list_from_json("model_config.json")

DB_DIR = "data/databases"
MAX_RETRIES = 3

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
        "Suggest which tables, filters, joins and columns are needed." 
        "Give clear names of tables and columns that can be used by another agent."
        "Plan should include Schema:\n Allowed Tables: <Tables> and Allowed Columns: <Columns>."
        "Make a short but detailed plan with all the correct context. "
        "Do not generate SQL. Only make a plan and pass to NL2SQL."
    )
)

def run_sql_safely(db_id: str, sql: str) -> tuple[bool, str]:
    db_path = os.path.join(DB_DIR, db_id, f"{db_id}.sqlite")
    if not os.path.exists(db_path):
        return False, f"Database not found: {db_path}"
    
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")  # optional safety
            conn.execute(sql)
        return True, ""
    except Exception as e:
        return False, str(e)

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

    # Step 3: Critic loop with retry if SQL invalid
    attempts = 0
    while attempts < MAX_RETRIES:
        critic_prompt = f"{full_prompt}\n\nGenerated SQL:\n{sql}"
        if attempts > 0:
            critic_prompt += f"\n\nPrevious SQL failed with error:\n{sql_error}"

        critic_reply = critic.generate_reply(messages=[{"role": "user", "content": critic_prompt}])
        final = critic_reply["content"]

        sql_only = re.sub(r"FINAL\s*", "", final)
        sql_only = re.sub(r"```sql\s*|\s*```", "", sql_only).strip()

        # Step 4: Try executing
        success, sql_error = run_sql_safely(db_id, sql_only)
        if success:
            break  # Valid SQL
        else:
            attempts += 1
            sql = sql_only  # Retry with improved version

    # Logging
    with open("agent_log3.txt", "a", encoding="utf-8") as log_file:
        log_file.write("=====================\n")
        log_file.write(f"Question: {question}\n db_id: {db_id}\n")
        log_file.write(f"Planner: {plan}\n")
        log_file.write(f"Final SQL (attempt {attempts}): {sql}\n")
        if not success:
            log_file.write(f"Final Error: {sql_error}\n")

    if success:
        return sql_only
    else:
        raise ValueError(f"Failed to generate valid SQL after {MAX_RETRIES} retries. Last error: {sql_error}")