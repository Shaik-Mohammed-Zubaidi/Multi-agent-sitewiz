import json, pathlib
import asyncio
from old.agents import solve

# Load the mini_dev_sqlite.json
MINI_DEV_PATH = pathlib.Path("bird_sql_mini/llm/mini_dev_data/data_minidev/MINIDEV/mini_dev_sqlite.json")
data = json.loads(MINI_DEV_PATH.read_text())

preds = []

for row in data:
    question = row["question"]
    db_id = row["db_id"]
    print(f"DB ID: {db_id}, Question: {question}")
    
    # schema is NOT included, so use db_id as hint (Optional: extract schema from DB if needed, but for now leave blank)
    schema = f"Database ID is {db_id}. Use only the columns/tables from this database."

    print(f"Processing (ID={row['question_id']}): {question[:80]}...")

    sql = asyncio.run(solve(question, schema, db_id))
    print(f"Generated SQL: {sql}, index={row['question_id']}")
    preds.append({
        "id": row["question_id"],   # ID field expected by eval.py
        "query": sql                # Generated SQL
    })

# Save predictions
out_path = pathlib.Path("pred.json")
out_path.write_text(json.dumps(preds, indent=2))
print("Finished. Wrote predictions to", out_path)

# To evaluate
# python bird_sql_mini/eval.py --predict-file pred.json
