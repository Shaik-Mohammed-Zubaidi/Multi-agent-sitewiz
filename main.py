import json
import os
from planner_agent import plan_query
from nl2sql_agent import generate_sql
from critic_agent import critique_sql
from schema_extractor import get_schema

# Paths configuration
DATA_FILE = os.getenv("BIRD_SQLITE_JSON", "data/mini_dev_sqlite.json")
DB_DIR = os.getenv("BIRD_DATABASE_DIR", "data/databases")
OUTPUT_FILE = "predictions.json"
RESULTS_DIR = "results"

os.makedirs(RESULTS_DIR, exist_ok=True)

def load_dataset(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_individual_result(idx, db_id, result_data):
    file_path = os.path.join(RESULTS_DIR, f"{idx}_{db_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)

def append_to_predictions(output_line):
    predictions = []
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            predictions = json.load(f)
    
    predictions.append(output_line)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

def main():
    data = load_dataset(DATA_FILE)
    schema_cache = {}
    total = len(data)

    for idx, example in enumerate(data, start=1):
        db_id = example.get("db_id")
        question = example.get("question")
        evidence = example.get("evidence", "") or ""

        if db_id in schema_cache:
            schema = schema_cache[db_id]
        else:
            db_path = os.path.join(DB_DIR, f"{db_id}.sqlite")
            schema = get_schema(db_path)
            schema_cache[db_id] = schema

        print(f"[{idx}/{total}] Processing question (DB: {db_id})...")

        try:
            plan = plan_query(question, evidence)
        except Exception as e:
            print(f"Planner agent failed: {e}")
            plan = ""

        try:
            sql_query = generate_sql(question, schema, plan, evidence)
        except Exception as e:
            print(f"NL2SQL agent failed: {e}")
            sql_query = ""

        corrected_sql = ""
        try:
            critique = critique_sql(question, schema, sql_query, evidence)
            if critique and critique.upper().strip() != "OK":
                corrected_sql = critique
        except Exception as e:
            print(f"Critic agent failed: {e}")

        final_sql = corrected_sql if corrected_sql else sql_query
        final_sql = final_sql.replace(f"{db_id}.", "")

        output_line = f"{final_sql}\t----- bird -----\t{db_id}"

        # Save individual result
        result_data = {
            "idx": idx,
            "db_id": db_id,
            "question": question,
            "evidence": evidence,
            "plan": plan,
            "sql_query": sql_query,
            "corrected_sql": corrected_sql,
            "final_sql": final_sql
        }
        save_individual_result(idx, db_id, result_data)

        # Append to predictions
        append_to_predictions(output_line)

    print("\nDone. Predictions saved to predictions.json and results/ folder")

if __name__ == "__main__":
    main()
