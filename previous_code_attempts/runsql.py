from old.agents import run_sql

result = run_sql(
    db_id="debit_card_specializing",
    query="SELECT * FROM table_name WHERE column_name = 'value';"
)
print(result)