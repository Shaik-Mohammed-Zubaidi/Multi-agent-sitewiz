import json
import asyncio
import os
from schema_extractor import get_schema
from agents import solve
from schema_loader import load_schema
from schema_index import SchemaRetriever

DATA_FILE = "data/mini_dev_sqlite.json"
DB_DIR = "data/databases"
OUTPUT_FILE = "predictions.json"
RESULTS_DIR = "results"

os.makedirs(RESULTS_DIR, exist_ok=True)

def load_dataset(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_predictions(preds, out_path):
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(preds, f, indent=2)

def save_individual_result(idx, db_id, result_data):
    file_path = os.path.join(RESULTS_DIR, f"{idx}_{db_id}.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(result_data, f, indent=2)

def append_to_predictions(output_line):
    predictions = {}

    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            predictions = json.load(f)

    # Ensure keys are string indices
    next_key = str(len(predictions))
    print(f"Appending to predictions with key: {next_key} type: {type(next_key)}")
    predictions[next_key] = output_line

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(predictions, f, indent=2)

async def process_all():
    data = load_dataset(DATA_FILE)
    predictions = []
    table_names = {}
    retriever_cache = {}


    for idx, example in enumerate(data, start=1):
        db_id = example["db_id"]
        question = example["question"]
        evidence = example.get("evidence", "")

        print(f"Processing {db_id}...")
        print(idx,"index")
        if db_id not in retriever_cache:
            try:
                schema = get_schema(os.path.join(DB_DIR, db_id), encoding="utf-8-sig")
            except Exception as e:
                print("Exception occured: changed encoding to cp1252")
                print(e)
                schema = get_schema(os.path.join(DB_DIR, db_id), encoding="cp1252")
            retriever_cache[db_id] = schema
        
        schema = retriever_cache[db_id]

        # retriever = retriever_cache[db_id]["retriever"]
        # table_names[db_id] = retriever_cache[db_id]["table_names"]
        
        # retrieved_entries = retriever.retrieve(question, top_k=10)
        # schema_text = retriever.build_schema_text(retrieved_entries)
        # allowed_tables = ", ".join(table_names[db_id])
        # schema = f"Allowed Tables: {allowed_tables}\n\n{schema_text}"

        if schema == "":
            raise ValueError(f"Schema is empty for {db_id}")
        print(f"[{idx}/{len(data)}] {db_id}: {question[:80]}")

        try:
            sql = solve(question, schema, db_id, evidence)
        except Exception as e:
            print("ERROR:", e)
            raise e

        # Final SQL cleaning
        sql = sql.replace(f"{db_id}.", "").strip()

        sql_entry = f"{sql}\t----- bird -----\t{db_id}"
        save_individual_result(idx, db_id, {
            "question": question,
            "schema": schema,
            "evidence": evidence,
            "sql": sql_entry
        })
        predictions.append(sql_entry)
        append_to_predictions(sql_entry)
        # if idx == 2:
        #     break
    print("cached dbs", len(retriever_cache))
    print("cached dbs keys", retriever_cache.keys())
    print("table names", table_names)

if __name__ == "__main__":
    asyncio.run(process_all())
