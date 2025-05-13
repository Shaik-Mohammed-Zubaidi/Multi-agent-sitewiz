import os
import csv

def load_schema(database_dir: str, encoding: str = "utf-8-sig"):
    desc_dir = os.path.join(database_dir, "database_description")
    if not os.path.exists(desc_dir):
        raise FileNotFoundError(f"No database_description folder in {database_dir}")

    schema_entries = []
    table_names = []

    for filename in os.listdir(desc_dir):
        if filename.endswith(".csv"):
            table_name = filename[:-4]

            with open(os.path.join(desc_dir, filename), newline='', encoding=encoding) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    column_name = row.get("original_column_name") or ""
                    description = row.get("column_description", "").strip()

                    if not column_name:
                        raise ValueError(f"Missing original_column_name in {filename}, row={row}")

                    entry_text = f"Table: {table_name}, Column: {column_name}, Description: {description}"
                    schema_entries.append({
                        "table": table_name,
                        "column": column_name,
                        "description": description,
                        "text": entry_text
                    })
                    if table_name not in table_names:
                        table_names.append(table_name)

    return {
        "schema_entries": schema_entries,
        "table_names": table_names,
    }
