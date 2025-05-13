from openai import OpenAI
import os

api_key = os.getenv("OPENAI_API_KEY", "")

def generate_sql(question: str, schema: str, plan: str = "", evidence: str = "") -> str:
    """
    Uses an LLM (NL2SQL agent) to generate a SQL query for the question, given the schema and plan.
    Returns the SQL query as a string.
    """
    system_prompt = (
        "You are an NL2SQL Agent, an expert at writing SQL queries for a SQLite database. "
        "You will be given a database schema, a question, and a plan. "
        "Follow the plan and use the schema to ensure all table and column names are correct. "
        "Do not include any explanation, only return the SQL query."
    )
    # Compose the user prompt with all provided context
    user_prompt_parts = []
    if schema:
        user_prompt_parts.append("Database Schema:\n" + schema.strip())
    user_prompt_parts.append("Question: " + question)
    if plan:
        user_prompt_parts.append("Plan: " + plan)
    if evidence:
        user_prompt_parts.append("Evidence: " + evidence)
    user_prompt_parts.append("Now write the final SQL query.")
    user_prompt = "\n".join(user_prompt_parts)

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    sql_query = response.choices[0].message.content.strip()
    # Remove any code block formatting if present
    if sql_query.startswith("```"):
        # Sometimes the model might format the query as a code block
        sql_query = sql_query.strip("```").strip()
        # If the model included a language like ```sql, remove that too
        if sql_query.lower().startswith("sql"):
            sql_query = sql_query[3:].strip()
    # Ensure the DB name is not included (just a safety check to fix known issue)
    # (The prompt already guides this, but we enforce: replace occurrences of DB ID in the query if any)
    # For example, if the question is for db 'foo_bar', remove "foo_bar." from the query.
    # (Assume db ids have no special regex chars)
    # Note: Only do this if it's a standalone word followed by a dot (to avoid accidental replacement in values).
    db_id_placeholder = ""  # We don't know db_id here; this check is done in main with actual db_id if needed.
    if db_id_placeholder:
        sql_query = sql_query.replace(f"{db_id_placeholder}.", "")
    return sql_query
