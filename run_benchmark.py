import json, pathlib
from agents import solve

# Load the mini_dev_sqlite.json
MINI_DEV_PATH = pathlib.Path("bird_sql_mini/llm/mini_dev_data/data_minidev/MINIDEV/mini_dev_sqlite.json")
data = json.loads(MINI_DEV_PATH.read_text())

preds = []

for row in data:
    question = row["question"]
    schema = row["schema"]
    db_id = row["db_id"]

    print(f"Processing: {question[:80]}...")
    
    sql = solve(question, schema, db_id)

    preds.append({"id": row["id"], "query": sql})

# Save predictions
out_path = pathlib.Path("pred.json")
out_path.write_text(json.dumps(preds, indent=2))
print("Finished. Wrote predictions to", out_path)

# To evaluate
# python bird_sql_mini/eval.py --predict-file pred.json
