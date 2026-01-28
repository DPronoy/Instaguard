# ingest_data.py
import pandas as pd
import os

RAW_FILE = "raw_data/hinglish.csv"
OUTPUT_FILE = "data/training_data.csv"

os.makedirs("data", exist_ok=True)

print("⚙️ Loading Hinglish Curse Dataset...")

df = pd.read_csv(RAW_FILE)

# Normalize column names
df.columns = df.columns.str.strip().str.lower()

# Auto-detect text column
text_col = None
for col in df.columns:
    if col in ["text", "word", "phrase", "abuse", "curse"]:
        text_col = col
        break

if text_col is None:
    raise Exception(f"No valid text column found. Columns: {list(df.columns)}")

df = df[[text_col]].rename(columns={text_col: "text"})
df["label"] = 1  # ALL ARE CURSES

# Clean text
df["text"] = df["text"].astype(str).str.lower().str.strip()
df = df.drop_duplicates().dropna()

df.to_csv(OUTPUT_FILE, index=False)

print(f"✅ Saved {len(df)} curse-only samples to {OUTPUT_FILE}")
