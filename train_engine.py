#  ___________________________________________________________________________
# |                                                                           |
# |  PROJECT: InstaGuard Enterprise                                           |
# |  AUTHOR:  Pronoy Das                                                      |
# |  LICENSE: MIT                                                             |
# |___________________________________________________________________________|

import os
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding
)

MODEL_NAME = "distilbert-base-multilingual-cased"
DATA_PATH = "data/training_data.csv"
OUTPUT_DIR = "./engine/model_v1"

def train():
    print("🚀 Initializing InstaGuard Training Pipeline (RTX 4060)")

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError("❌ data/training_data.csv not found. Run ingest_data.py first.")

    df = pd.read_csv(DATA_PATH)
    df = df[["text", "label"]].dropna()

    print(f"📚 Loaded {len(df)} curse-only Hinglish samples")

    # Split (no stratify needed — all labels = 1)
    train_df, val_df = train_test_split(df, test_size=0.1, random_state=42)

    tokenizer = DistilBertTokenizerFast.from_pretrained(MODEL_NAME)

    def tokenize(batch):
        return tokenizer(
            batch["text"],
            truncation=True,
            padding=True,
            max_length=32
        )

    train_ds = Dataset.from_pandas(train_df).map(tokenize, batched=True, remove_columns=["text"])
    val_ds = Dataset.from_pandas(val_df).map(tokenize, batched=True, remove_columns=["text"])

    train_ds = train_ds.rename_column("label", "labels")
    val_ds = val_ds.rename_column("label", "labels")

    train_ds.set_format("torch")
    val_ds.set_format("torch")

    model = DistilBertForSequenceClassification.from_pretrained(
        MODEL_NAME,
        num_labels=2
    ).to("cuda")

    print(f"⚡ Using GPU: {torch.cuda.get_device_name(0)}")

    args = TrainingArguments(
        output_dir="./checkpoints",
        learning_rate=2e-5,
        per_device_train_batch_size=32,
        per_device_eval_batch_size=32,
        num_train_epochs=3,
        weight_decay=0.01,
        fp16=True,
        logging_steps=50,
        save_strategy="no",
        report_to="none"
    )

    data_collator = DataCollatorWithPadding(tokenizer)

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=data_collator
    )

    print("🔥 Training Started...")
    trainer.train()

    print(f"💾 Saving model to {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)

    print("✅ ENGINE READY")

if __name__ == "__main__":
    train()
