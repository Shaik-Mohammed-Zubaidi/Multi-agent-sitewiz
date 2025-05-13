from openai import OpenAI
import os

api_key = os.getenv("OPENAI_API_KEY", "")

def critique_sql(question: str, schema: str, sql_query: str, evidence: str = "") -> str:
    """
    Uses an LLM (Critic agent) to evaluate the SQL query against the question (and schema).
    Returns "OK" if the SQL is correct, or a corrected SQL query string if it found an issue.
    """
    system_prompt = (
        "You are a Critic agent who checks the correctness of an SQL query for a given question and database schema. "
        "If the SQL correctly answers the question, respond with 'OK'. "
        "If it is incorrect or incomplete, respond with the corrected SQL query that would answer the question. "
        "Do not provide any explanation or additional text, only output 'OK' or the new SQL."
    )
    user_prompt_parts = [f"Question: {question}", f"SQL Query: {sql_query}"]
    if schema:
        user_prompt_parts.append("Database Schema:\n" + schema.strip())
    if evidence:
        user_prompt_parts.append("Evidence: " + evidence)
    user_prompt_parts.append("Is the SQL correct? If not, provide a corrected SQL.")
    user_prompt = "\n".join(user_prompt_parts)
    
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    critique = response.choices[0].message.content.strip()
    # Remove any code block formatting from the critique
    if critique.startswith("```"):
        critique = critique.strip("```").strip()
        if critique.lower().startswith("sql"):
            critique = critique[3:].strip()
    return critique
