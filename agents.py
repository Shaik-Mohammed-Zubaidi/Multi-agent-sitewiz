import re
import os
import json
import sqlite3
import autogen
from autogen import AssistantAgent
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
config_list_gemini = autogen.config_list_from_json("model_config.json")
MAX_RETRIES = 3

# --- Agent Definitions ---

selector = AssistantAgent(
    name="Selector",
    llm_config={"config_list": config_list_gemini},
    system_message=(
        """
        As an experienced and professional database administrator, your task is to analyze a user question
        and a database schema to provide relevant information. The database schema consists of table
        descriptions, each containing multiple column descriptions. Your goal is to identify the relevant
        tables and columns based on the user question and evidence provided.
        [Instruction]
        1. Discard any table schema that is not related to the user question and evidence.
        2. Sort the columns in each relevant table in descending order of relevance and keep the top 6
        columns.
        3. Ensure that at least 3 tables are included in the final output JSON.
        4. The output should be in JSON format.
        [Requirements]
        1. If a table has less than or equal to 10 columns, mark it as "keep_all".
        2. If a table is completely irrelevant to the user question and evidence, mark it as "drop_all".
        3. Prioritize the columns in each relevant table based on their relevance.
        Here is a typical example:
        ==========
        [DB_ID] banking_system
        [Schema]
        # Table: account
        [
        (account_id, the id of the account. Value examples: [11382, 11362, 2, 1, 2367].),
        (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].),
        (frequency, frequency of the acount. Value examples: [’POPLATEK MESICNE’, ’POPLATEK
        TYDNE’, ’POPLATEK PO OBRATU’].),
        (date, the creation date of the account. Value examples: [’1997-12-29’, ’1997-12-28’].)
        ]
        # Table: client
        [
        (client_id, the unique number. Value examples: [13998, 13971, 2, 1, 2839].),
        (gender, gender. Value examples: [’M’, ’F’]. And F:female . M:male ),
        (birth_date, birth date. Value examples: [’1987-09-27’, ’1986-08-13’].), (district_id, location
        of branch. Value examples: [77, 76, 2, 1, 39].)
        ]
        # Table: loan
        [
        (loan_id, the id number identifying the loan data. Value examples: [4959, 4960, 4961].),
        (account_id, the id number identifying the account. Value examples: [10, 80, 55, 43].),
        (date, the date when the loan is approved. Value examples: [’1998-07-12’, ’1998-04-19’].),
        (amount, the id number identifying the loan data. Value examples: [1567, 7877, 9988].),
        (duration, the id number identifying the loan data. Value examples: [60, 48, 24, 12, 36].),
        (payments, the id number identifying the loan data. Value examples: [3456, 8972, 9845].),
        (status, the id number identifying the loan data. Value examples: [’C’, ’A’, ’D’, ’B’].)
        ]
        # Table: district
        [
        (district_id, location of branch. Value examples: [77, 76].),
        (A2, area in square kilometers. Value examples: [50.5, 48.9].),
        (A4, number of inhabitants. Value examples: [95907, 95616].),
        (A5, number of households. Value examples: [35678, 34892].),
        (A6, literacy rate. Value examples: [95.6, 92.3, 89.7].),
        (A7, number of entrepreneurs. Value examples: [1234, 1456].),
        (A8, number of cities. Value examples: [5, 4].),
        (A9, number of schools. Value examples: [15, 12, 10].),
        (A10, number of hospitals. Value examples: [8, 6, 4].),
        (A11, average salary. Value examples: [12541, 11277].),
        (A12, poverty rate. Value examples: [12.4, 9.8].),
        (A13, unemployment rate. Value examples: [8.2, 7.9].),
        (A15, number of crimes. Value examples: [256, 189].)
        ]
        [Foreign keys]
        client.‘district_id‘ = district.‘district_id‘
        [Question]
        What is the gender of the youngest client who opened account in the lowest average salary branch?
        [Evidence]
        Later birthdate refers to younger age; A11 refers to average salary
        [Answer]
        ”’json
        {
        "account": "keep_all",
        "client": "keep_all",
        "loan": "drop_all",
        "district": ["district_id", "A11", "A2", "A4", "A6", "A7"]
        }
        ”’
        Question Solved.
        ==========
        """
    )
)

decomposer = AssistantAgent(
    name="Decomposer",
    llm_config={"config_list": config_list_gemini},
    system_message=(
        """
        Given a [Database schema] description, a knowledge [Evidence] and the [Question], you need to
        use valid SQLite and understand the database and knowledge, and then decompose the question
        into subquestions for text-to-SQL generation.
        When generating SQL, we should always consider constraints:
        [Constraints]
        - In ‘SELECT <column>‘, just select needed columns in the [Question] without any unnecessary
        column or value
        - In ‘FROM <table>‘ or ‘JOIN <table>‘, do not include unnecessary table
        - If use max or min func, ‘JOIN <table>‘ FIRST, THEN use ‘SELECT MAX(<column>)‘ or
        ‘SELECT MIN(<column>)‘
        - If [Value examples] of <column> has ’None’ or None, use ‘JOIN <table>‘ or ‘WHERE <column>
        is NOT NULL‘ is better
        - If use ‘ORDER BY <column> ASC|DESC‘, add ‘GROUP BY <column>‘ before to select distinct
        values
        ==========
        [Database schema]
        # Table: frpm
        [
        (CDSCode, CDSCode. Value examples: [’01100170109835’, ’01100170112607’].),
        (Charter School (Y/N), Charter School (Y/N). Value examples: [1, 0, None]. And 0: N;. 1: Y),
        (Enrollment (Ages 5-17), Enrollment (Ages 5-17). Value examples: [5271.0, 4734.0].),
        (Free Meal Count (Ages 5-17), Free Meal Count (Ages 5-17). Value examples: [3864.0, 2637.0].
        And eligible free rate = Free Meal Count / Enrollment)
        ]
        # Table: satscores
        [
        (cds, California Department Schools. Value examples: [’10101080000000’,
        ’10101080109991’].),
        (sname, school name. Value examples: [’None’, ’Middle College High’, ’John F. Kennedy
        High’, ’Independence High’, ’Foothill High’].),
        (NumTstTakr, Number of Test Takers in this school. Value examples: [24305, 4942, 1, 0, 280].
        And number of test takers in each school),
        (AvgScrMath, average scores in Math. Value examples: [699, 698, 289, None, 492]. And
        average scores in Math), (NumGE1500, Number of Test Takers Whose Total SAT Scores Are
        Greater or Equal to 1500. Value examples: [5837, 2125, 0, None, 191]. And Number of Test Takers
        Whose Total SAT Scores Are Greater or Equal to 1500. . commonsense evidence:. . Excellence
        Rate = NumGE1500 / NumTstTakr)
        ]
        [Foreign keys]
        frpm.‘CDSCode‘ = satscores.‘cds‘
        [Question]
        List school names of charter schools with an SAT excellence rate over the average.
        [Evidence]
        Charter schools refers to ‘Charter School (Y/N)‘ = 1 in the table frpm; Excellence rate =
        NumGE1500 / NumTstTakr
        Decompose the question into sub questions, considering [Constraints], and generate the SQL after
        thinking step by step:
        Sub question 1: Get the average value of SAT excellence rate of charter schools.
        SQL
        ”’ sql
        SELECT AVG(CAST(T2.‘NumGE1500‘ AS REAL) / T2.‘NumTstTakr‘)
        FROM frpm AS T1
        INNER JOIN satscores AS T2
        ON T1.‘CDSCode‘ = T2.‘cds‘
        WHERE T1.‘Charter School (Y/N)‘ = 1
        ”’
        Sub question 2: List out school names of charter schools with an SAT excellence rate over the
        average.
        SQL
        ”’ sql
        SELECT T2.‘sname‘
        FROM frpm AS T1
        INNER JOIN satscores AS T2
        ON T1.‘CDSCode‘ = T2.‘cds‘
        WHERE T2.‘sname‘ IS NOT NULL
        AND T1.‘Charter School (Y/N)‘ = 1
        AND CAST(T2.‘NumGE1500‘ AS REAL) / T2.‘NumTstTakr‘ > (
        SELECT AVG(CAST(T4.‘NumGE1500‘ AS REAL) / T4.‘NumTstTakr‘)
        FROM frpm AS T3
        INNER JOIN satscores AS T4
        ON T3.‘CDSCode‘ = T4.‘cds‘
        WHERE T3.‘Charter School (Y/N)‘ = 1
        )
        ”’
        Question Solved.
        ==========
        [Database schema]
        # Table: account
        [
        (account_id, the id of the account. Value examples: [11382, 11362, 2, 1, 2367].),
        (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].),
        (frequency, frequency of the acount. Value examples: [’POPLATEK MESICNE’, ’POPLATEK
        TYDNE’, ’POPLATEK PO OBRATU’].),
        (date, the creation date of the account. Value examples: [’1997-12-29’, ’1997-12-28’].)
        ]
        # Table: client
        [
        (client_id, the unique number. Value examples: [13998, 13971, 2, 1, 2839].),
        (gender, gender. Value examples: [’M’, ’F’]. And F:female . M:male ),
        (birth_date, birth date. Value examples: [’1987-09-27’, ’1986-08-13’].),
        (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].)
        ]
        # Table: district
        [
        (district_id, location of branch. Value examples: [77, 76, 2, 1, 39].),
        (A4, number of inhabitants . Value examples: [’95907’, ’95616’, ’94812’].),
        (A11, average salary. Value examples: [12541, 11277, 8114].) ]
        [Foreign keys]
        account.‘district_id‘ = district.‘district_id‘
        client.‘district_id‘ = district.‘district_id‘
        [Question]
        What is the gender of the youngest client who opened account in the lowest average salary branch?
        [Evidence]
        Later birthdate refers to younger age; A11 refers to average salary
        Decompose the question into sub questions, considering [Constraints], and generate the SQL after
        thinking step by step:
        Sub question 1: What is the district_id of the branch with the lowest average salary?
        SQL
        ”’ sql
        SELECT ‘district_id‘
        FROM district
        ORDER BY ‘A11‘ ASC
        LIMIT 1
        ”’
        Sub question 2: What is the youngest client who opened account in the lowest average
        salary branch?
        SQL
        ”’ sql
        SELECT T1.‘client_id‘
        FROM client AS T1
        INNER JOIN district AS T2
        ON T1.‘district_id‘ = T2.‘district_id‘
        ORDER BY T2.‘A11‘ ASC, T1.‘birth_date‘ DESC
        LIMIT 1
        ”’
        Sub question 3: What is the gender of the youngest client who opened account in the lowest
        average salary branch?
        SQL
        ”’ sql
        SELECT T1.‘gender‘
        FROM client AS T1
        INNER JOIN district AS T2
        ON T1.‘district_id‘ = T2.‘district_id‘
        ORDER BY T2.‘A11‘ ASC, T1.‘birth_date‘ DESC
        LIMIT 1
        ”’
        Question Solved.
        ==========
        
        """
    )
)

refiner = AssistantAgent(
    name="Refiner",
    llm_config={"config_list": config_list_gemini},
    system_message=(
        """
        [Instruction]
        When executing SQL below, some errors occurred, please fix up SQL based on query and database
        info. Solve the task step by step if you need to. Using SQL format in the code block, and indicate
        script type in the code block. When you find an answer, verify the answer carefully. Include
        verifiable evidence in your response if possible. Always output only the final SQL.
        [Constraints]
        - In ‘SELECT <column>‘, just select needed columns in the [Question] without any unnecessary
        column or value
        - In ‘FROM <table>‘ or ‘JOIN <table>‘, do not include unnecessary table
        - If use max or min func, ‘JOIN <table>‘ FIRST, THEN use ‘SELECT MAX(<column>)‘ or
        ‘SELECT MIN(<column>)‘
        - If [Value examples] of <column> has ’None’ or None, use ‘JOIN <table>‘ or ‘WHERE <column>
        is NOT NULL‘ is better
        - If use ‘ORDER BY <column> ASC|DESC‘, add ‘GROUP BY <column>‘ before to select distinct
        values
        
        """
    )
)

# --- Utility Functions ---

def run_sql_safely(db_dir: str,db_id: str, sql: str) -> tuple[bool, str, str]:
    db_path = os.path.join(db_dir, db_id, f"{db_id}.sqlite")
    if not os.path.exists(db_path):
        return False, f"Database not found: {db_path}", "FileNotFoundError"
    try:
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute(sql)
        return True, "", ""
    except Exception as e:
        return False, str(e), e.__class__.__name__

def get_foreign_keys(db_id: str, data_dir: str) -> str:
    fk_file_path = f"{data_dir}/dev_tables.json"
    try:
        with open(fk_file_path, "r", encoding="utf-8") as f:
            fk_data = json.load(f)
        table_info = fk_data.get(db_id, {})
        fks = table_info.get("foreign_keys", [])
        lines = [f"{fk[0]}.{fk[1]} = {fk[2]}.{fk[3]}" for fk in fks]
        return "\n".join(lines)
    except Exception as e:
        return ""

# --- Main solve() Function ---

def solve(db_dir: str, data_dir: str, question: str, schema: str, db_id: str, evidence: str = "") -> str:
    fk_str = get_foreign_keys(db_id, data_dir)
    full_prompt = f"Question: {question}\nDB_ID: {db_id}"

    if evidence:
        full_prompt += f"\nEvidence: {evidence}"
    if fk_str:
        full_prompt += f"\nForeign keys: {fk_str}"


    # Step 1: Selector
    selector_prompt = f"""
        Here is a new example, please start answering:
        [DB_ID] {db_id}
        [Schema]
        {schema}
        [Foreign keys]
        {fk_str}
        [Question]
        {question}
        [Evidence]
        {evidence}
        [Answer]
    """
    print("size of prompt:", len(selector_prompt))
    selector_reply = selector.generate_reply(messages=[{"role": "user", "content": selector_prompt}])
    selections = selector_reply["content"]

    # Step 2: Decomposer
    decomposer_prompt = f"""
        [Database schema]
        {selections}
        [Foreign keys]
        {fk_str}
        [Question]
        {question}
        [Evidence]
        {evidence}
        Decompose the question into sub questions, considering [Constraints], and generate the SQL after
        thinking step by step
    """
    print("size of prompt:", len(decomposer_prompt))
    decomposer_reply = decomposer.generate_reply(messages=[{"role": "user", "content": decomposer_prompt}])
    sql = decomposer_reply["content"]
    # print("After decomposer SQL:", sql)
    sql_only = re.sub(r"```sql\s*|\s*```", "", sql).strip()

    # Step 3: Initial Execution
    success, sql_error, exception_class = run_sql_safely(db_dir, db_id, sql_only)

    # Step 4: Retry loop using Refiner if needed
    attempts = 0
    while not success and attempts < MAX_RETRIES:

        refiner_prompt = f"""
            [Query]
            {question}
            [Evidence]
            {evidence}
            [Database info]
            {schema}
            [Foreign keys]
            {fk_str}
            [old SQL]
            ”’ sql
            {sql}
            ”’
            [SQLite error]
            {sql_error}
            [Exception class]
            {exception_class}
            Now please fixup old SQL and generate new SQL again.
            [correct SQL]
        """
        
        print("size of prompt:", len(refiner_prompt))
        refiner_reply = refiner.generate_reply(messages=[{"role": "user", "content": refiner_prompt}])
        final = refiner_reply["content"]

        sql_only = re.sub(r"FINAL\s*", "", final)
        sql_only = re.sub(r"```sql\s*|\s*```", "", sql_only).strip()

        success, sql_error, exception_class = run_sql_safely(db_dir, db_id, sql_only)
        # print(f"After refiner SQL at attempt {attempts}:", sql_only)
        attempts += 1
    # print("After refiner SQL:", sql_only)
    # Final SQL cleaning
    # --- Logging ---
    with open("agent_log3.txt", "a", encoding="utf-8") as log_file:
        log_file.write("=====================\n")
        log_file.write(f"Question: {question}\n db_id: {db_id}\n")
        log_file.write(f"Selector: {selections}\n")
        log_file.write(f"Final SQL (attempt {attempts}): {sql_only}\n")
        if not success:
            log_file.write(f"Final Error: {sql_error}\n")

    if success:
        return sql_only
    else:
        raise ValueError(f"Failed to generate valid SQL after {MAX_RETRIES} retries. Last error: {sql_error}")
