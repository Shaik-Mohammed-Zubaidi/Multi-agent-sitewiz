---

# 🧠 Multi-Agent NL2SQL System

This project implements a multi-agent system for converting natural language questions into SQL queries, evaluated on the [BIRD-SQL Mini-Dev](https://github.com/bird-bench/mini_dev) benchmark. It uses **Gemini Flash 2.0** and includes automatic SQL validation + retry mechanisms inspired by the BIRD paper.

---

## 📦 Setup Instructions

### 1. Clone the repositories

```bash
git clone https://github.com/Shaik-Mohammed-Zubaidi/Multi-agent-sitewiz
git clone https://github.com/bird-bench/mini_dev bird_sql_mini
```

---

### 2. Download the Dataset

You can download the dataset from:

* Google Drive: [minidev.zip](https://drive.google.com/file/d/1UJyA6I6pTmmhYpwdn8iT9QKrcJqSQAcX/view?usp=sharing)
* Alibaba: [minidev.zip](https://bird-bench.oss-cn-beijing.aliyuncs.com/minidev.zip)

Extract the zip and place it inside the `data/` directory as `data/databases/`.

---

### 3. Get Gemini Flash 2.0 API Key

* Search **“Gemini Flash 2.0 API key”** on Google and click the first link.
* Sign in with your Google account and create an API key.
* Save the key in a `model_config.json` file in the project root:

```json
[
  {
    "model": "gemini-1.5-flash",
    "base_url": "https://generativelanguage.googleapis.com/v1beta/models",
    "api_key": "YOUR_API_KEY",
    "api_type": "google"
  }
]
```

---

### 4. Create and Activate Virtual Environment

For **Mac/Linux**:

```bash
python3 -m venv venv
source venv/bin/activate
```

For **Windows**:

```cmd
python -m venv venv
venv\Scripts\activate
```

---

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🚀 Running the Project

```bash
python main.py
```

If you're using a **free Gemini API key**, you might hit the quota after every \~100 queries.
To continue generation, update `main.py`:

### Modify `main.py` if query fails at index 99:

* Line 45:

  ```python
  data = load_dataset(DATA_FILE)[99:]  # restart from 100th question
  ```
* Line 51:

  ```python
  for idx, example in enumerate(data, start=100):
  ```

Then re-run the script. The final predictions will be stored in `predictions.json`.

---

## 🧪 Evaluating Accuracy

1. Move `predictions.json` to the BIRD repo under:

   ```
   bird_sql_mini/evaluation/
   ```

2. Edit `run_evaluation.sh`:

   * Set `predicted_sql_path=predictions.json`
   * Update `output_log_path` if needed

3. Make it executable and run:

```bash
cd bird_sql_mini/evaluation
chmod +x run_evaluation.sh
./run_evaluation.sh
```

This will calculate your final execution accuracy.

---

## 📁 Project Structure

```
.
├── main.py                # Core pipeline
├── agents.py              # Multi-agent system logic (Selector, Decomposer, Refiner)
├── model_config.json      # Gemini Flash API config
├── data/                  # Place for your downloaded BIRD dataset
├── logs/                  # Logs from all agent calls (selector, decomposer, refiner)
├── evaled_results/        # Evaluation logs from previous runs
├── previous_code_attempts/ # Older version of my system (52% accuracy baseline)
└── predictions.json       # Final output file
```

---

## 📊 Accuracy Results

| Subset    | Accuracy  |
| --------- | --------- |
| First 97  | 65.98%    |
| First 202 | 64.36%    |
| First 298 | 65.44%    |
| First 411 | 62.53%    |
| All 500   | **58.2%** |

The last 100 queries are particularly difficult, as seen in the drop in performance.

---

## 📝 Notes

* My earlier architecture (with Planner, NL2SQL, Critic) is archived in `previous_code_attempts/`. It achieved \~52% accuracy using smaller, simpler prompts.
* All logs of model behavior and thought processes are in the `logs/` folder.
* Evaluation outputs from prior experiments are in `evaled_results/`.

---
