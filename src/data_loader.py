"""
Data loading, schema validation, and dataset preparation module.
Prepares the Bitext customer-support dataset with strict leakage prevention and reproducible splits.
"""

import json
import os
from typing import Dict, List, Optional, Tuple
import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import (
    ALL_INTENTS,
    BITEXT_CATEGORIES,
    BITEXT_CLEANED_PATH,
    BITEXT_RAW_PATH,
    DATA_DIR,
)


def validate_bitext_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """Validates required columns and absence of catastrophic corruption."""
    errors = []
    required_cols = ["instruction", "category", "intent", "response"]
    for col in required_cols:
        if col not in df.columns:
            errors.append(f"Missing required column: {col}")

    if errors:
        return False, errors

    # Check for empty text
    empty_instructions = df["instruction"].isna().sum()
    if empty_instructions > 0:
        errors.append(f"Found {empty_instructions} rows with null instruction")

    # Check for unrecognized intents
    unknown_intents = set(df["intent"].unique()) - set(ALL_INTENTS)
    if unknown_intents:
        errors.append(f"Found unexpected intents not in taxonomy: {unknown_intents}")

    return len(errors) == 0, errors


def load_and_clean_bitext(
    raw_path: str = BITEXT_RAW_PATH,
    save_cleaned: bool = True
) -> pd.DataFrame:
    """
    Loads, deduplicates, and cleans the Bitext customer support dataset.
    Preserves exact instruction text while dropping duplicate prompt rows.
    """
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw Bitext dataset not found at: {raw_path}")

    df = pd.read_csv(raw_path)
    is_valid, errors = validate_bitext_schema(df)
    if not is_valid:
        raise ValueError(f"Bitext dataset schema validation failed: {errors}")

    # Remove duplicates on instruction text to prevent leakage between splits
    initial_len = len(df)
    df_clean = df.drop_duplicates(subset=["instruction"]).copy()
    dedup_len = len(df_clean)

    # Filter to only valid known intents
    df_clean = df_clean[df_clean["intent"].isin(ALL_INTENTS)].copy()

    # Clean whitespace
    df_clean["instruction"] = df_clean["instruction"].astype(str).str.strip()

    if save_cleaned:
        os.makedirs(os.path.dirname(BITEXT_CLEANED_PATH), exist_ok=True)
        df_clean.to_csv(BITEXT_CLEANED_PATH, index=False)

    return df_clean


def get_dataset_splits(
    df: Optional[pd.DataFrame] = None,
    test_size: float = 0.15,
    val_size: float = 0.15,
    random_state: int = 42
) -> Dict[str, pd.DataFrame]:
    """
    Splits the cleaned Bitext dataset into stratified Train, Validation, and Test sets.
    Stratified by intent to guarantee representation across all 27 classes.
    """
    if df is None:
        if os.path.exists(BITEXT_CLEANED_PATH):
            df = pd.read_csv(BITEXT_CLEANED_PATH)
        else:
            df = load_and_clean_bitext()

    # First split: Train + Val vs Test
    train_val_df, test_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df["intent"],
        random_state=random_state
    )

    # Second split: Train vs Val
    adjusted_val_size = val_size / (1.0 - test_size)
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=adjusted_val_size,
        stratify=train_val_df["intent"],
        random_state=random_state
    )

    splits_manifest = {
        "total_records": len(df),
        "train_records": len(train_df),
        "val_records": len(val_df),
        "test_records": len(test_df),
        "num_classes": df["intent"].nunique(),
        "random_seed": random_state
    }

    manifest_path = os.path.join(DATA_DIR, "splits_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(splits_manifest, f, indent=2)

    return {
        "train": train_df,
        "val": val_df,
        "test": test_df
    }


def get_dataset_statistics() -> Dict:
    """Calculates distribution statistics for dashboard display."""
    if not os.path.exists(BITEXT_CLEANED_PATH):
        load_and_clean_bitext()

    df = pd.read_csv(BITEXT_CLEANED_PATH)
    category_counts = df["category"].value_counts().to_dict()
    intent_counts = df["intent"].value_counts().to_dict()

    return {
        "total_examples": len(df),
        "unique_categories": len(category_counts),
        "unique_intents": len(intent_counts),
        "category_distribution": category_counts,
        "intent_distribution": intent_counts,
        "avg_char_length": round(df["instruction"].str.len().mean(), 1),
        "max_char_length": int(df["instruction"].str.len().max()),
        "license": "CDLA-Sharing-1.0",
        "provenance": "Hugging Face / bitext/Bitext-customer-support-llm-chatbot-training-dataset"
    }
