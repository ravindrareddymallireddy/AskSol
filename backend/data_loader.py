import os
import pandas as pd

def load_and_dedupe(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"CSV dataset not found: {path}")
    df = pd.read_csv(path)
    # Normalize column names to lowercase
    df.columns = [c.strip() for c in df.columns]
    # Expect 'question' and 'answer' columns
    if "question" not in [c.lower() for c in df.columns] or "answer" not in [c.lower() for c in df.columns]:
        # try common alternatives
        cols = {c.lower(): c for c in df.columns}
        if "question" in cols and "answer" in cols:
            pass
        else:
            raise ValueError("CSV must contain 'question' and 'answer' columns")
    # ensure using lowercase 'question' and 'answer' keys
    df = df.rename(columns={c: c.lower() for c in df.columns})
    df = df[["question","answer"]].dropna().reset_index(drop=True)
    df = df.drop_duplicates(subset=["question","answer"], keep="first").reset_index(drop=True)
    return df
