import faiss
from sentence_transformers import SentenceTransformer
from old.schema_loader import load_schema
import numpy as np

class SchemaRetriever:
    def __init__(self, schema_entries):
        self.entries = schema_entries
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.index = faiss.IndexFlatL2(384)

        texts = [entry["text"] for entry in self.entries]
        self.embeddings = self.model.encode(texts, show_progress_bar=False)

        self.index.add(np.array(self.embeddings))

    def retrieve(self, query, top_k=10):
        query_emb = self.model.encode([query])
        D, I = self.index.search(np.array(query_emb), top_k)
        results = []
        for idx in I[0]:
            results.append(self.entries[idx])
        return results

    def build_schema_text(self, retrieved_entries):
        schema_lines = []

        table_to_cols = {}
        for entry in retrieved_entries:
            table_to_cols.setdefault(entry["table"], []).append(entry)

        for table, cols in table_to_cols.items():
            schema_lines.append(f"Table: {table}")
            col_lines = []
            for col in cols:
                col_text = col["column"]
                if col["description"]:
                    col_text += f": {col['description']}"
                col_lines.append(col_text)
            schema_lines.append("Columns: " + ", ".join(col_lines))
            schema_lines.append("")

        return "\n".join(schema_lines).strip()

# if __name__ == "__main__":
#     # Example usage
#     schema_entries = load_schema("./data/databases/debit_card_specializing", encoding="utf-8-sig")
#     retriever = SchemaRetriever(schema_entries)

#     query = "What is the name of the customer?"
#     retrieved_entries = retriever.retrieve(query, top_k=5)
#     schema_text = retriever.build_schema_text(retrieved_entries)

#     print("Retrieved Schema:")
#     print(schema_text)