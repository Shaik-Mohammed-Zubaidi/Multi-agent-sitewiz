import os
import csv

def get_schema(database_dir: str, encoding: str) -> str:
    """
    Read schema directly from 'database_description/*.csv' and return formatted schema string.
    """
    desc_dir = os.path.join(database_dir, "database_description")
    if not os.path.exists(desc_dir):
        raise FileNotFoundError(f"No database_description folder in {database_dir}")

    schema_lines = []
    table_names = []
    tables_data = []

    # Read all tables
    for filename in os.listdir(desc_dir):
        if filename.endswith(".csv"):
            table_name = filename[:-4]
            table_names.append(table_name)


            print(f"Reading {filename}...")

            columns = []
            with open(os.path.join(desc_dir, filename), newline='', encoding=encoding) as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    print(row)
                    column_name = row.get("original_column_name") or ""
                    data_type = row.get("data_format", "").strip()
                    description = row.get("column_description", "").strip()

                    if not column_name:
                        raise ValueError(f"Missing original_column_name in {filename} at row {row}")

                    columns.append({
                        "name": column_name,
                        "type": data_type,
                        "description": description
                    })
            # print(f"Table: {table_name}, Columns: {len(columns)}")
            tables_data.append({
                "table_name": table_name,
                "columns": columns
            })

    # Build schema string
    schema_lines.append(f"Allowed Tables: {', '.join(table_names)}\n")

    for table in tables_data:
        schema_lines.append(f"Table: {table['table_name']}")
        col_lines = []
        for col in table["columns"]:
            col_str = col["name"]
            if col["type"]:
                col_str += f" ({col['type']})"
            if col["description"]:
                col_str += f": {col['description']}"
            col_lines.append(col_str)
        if col_lines:
            schema_lines.append("Columns: " + ", ".join(col_lines))
        schema_lines.append("")

    return "\n".join(schema_lines).strip()

# if __name__ == "__main__":
#     # Example usage
#     db_dir = "./data/databases/debit_card_specializing"  # Replace with your database directory
#     schema = get_schema(db_dir)
#     print(schema)