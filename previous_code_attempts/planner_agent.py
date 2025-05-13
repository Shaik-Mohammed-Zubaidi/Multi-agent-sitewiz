from openai import OpenAI
import os

# Configure OpenAI API key (expects an environment variable for security)
api_key = os.getenv("OPENAI_API_KEY", "")

def plan_query(question: str, evidence: str = "") -> str:
    """
    Uses an LLM (Planner agent) to create a step-by-step plan for the given question.
    The plan outlines which tables/columns or operations are needed, without giving the final SQL.
    """
    system_prompt = (
        "You are a Planner agent that helps break down a user's database query question into a plan. "
        "Analyze the question and outline an approach to find the answer using SQL. "
        "Include which tables and columns to use, any necessary joins or filters, and the general strategy. "
        "Do NOT write the final SQL query. End your plan with an indication to proceed to the NL2SQL agent."
    )
    user_prompt = f"Question: {question}"
    if evidence:
        user_prompt += f"\nEvidence: {evidence}"
    
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    plan_text = response.choices[0].message.content.strip()
    return plan_text

if __name__ == "__main__":
    # Example usage
    question = "What is the ratio of customers who pay in EUR against customers who pay in CZK?"
    evidence = "ratio of customers who pay in EUR against customers who pay in CZK = count(Currency = 'EUR') / count(Currency = 'CZK')."
    plan = plan_query(question, evidence)
    print("Generated Plan:", plan)