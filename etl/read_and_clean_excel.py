"""
Read and clean workout data from the Excel workbook.
"""

import pandas as pd
from pathlib import Path

WORKOUT_SHEET = "workout_entry_template"
SKILL_SHEET = "skill_progress"


def load_workouts(path: str) -> pd.DataFrame:
    """Load and clean the workout_entry_template sheet."""
    df = pd.read_excel(path, sheet_name=WORKOUT_SHEET)
    
    # Normalize date
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    
    # Normalize strings
    df["exercise"] = df["exercise"].astype(str).str.strip()
    df["exercise_type"] = df["exercise_type"].astype(str).str.strip().str.lower()
    df["weight_unit"] = df["weight_unit"].astype(str).str.strip().str.lower()
    
    # Clean up 'nan' strings from astype(str)
    df["exercise"] = df["exercise"].replace("nan", "")
    df["exercise_type"] = df["exercise_type"].replace("nan", "")
    df["weight_unit"] = df["weight_unit"].replace("nan", "")
    
    # Numeric cleanup
    for col in ["sets_manual", "reps_manual", "weight"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    # Flag bodyweight exercises
    df["is_bodyweight"] = df["weight_unit"].eq("bodyweight")
    
    # Drop rows with no exercise name
    df = df[df["exercise"].str.len() > 0]
    
    return df


def load_skills(path: str) -> pd.DataFrame:
    """Load and clean the skill_progress sheet."""
    try:
        df = pd.read_excel(path, sheet_name=SKILL_SHEET)
    except ValueError:
        # Sheet doesn't exist yet
        print(f"Warning: '{SKILL_SHEET}' sheet not found in workbook")
        return pd.DataFrame(columns=["date", "skill", "progression", "achieved", "hold_seconds", "notes"])
    
    # Normalize date
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date
    
    # Normalize strings
    df["skill"] = df["skill"].astype(str).str.strip()
    df["progression"] = df["progression"].astype(str).str.strip()
    
    # Clean up 'nan' strings
    df["skill"] = df["skill"].replace("nan", "")
    df["progression"] = df["progression"].replace("nan", "")
    
    # Normalize achieved -> boolean
    df["achieved"] = (
        df["achieved"].astype(str).str.strip().str.lower()
        .map({
            "yes": True, "y": True, "true": True, "1": True,
            "no": False, "n": False, "false": False, "0": False,
            "nan": None, "": None
        })
    )
    
    df["hold_seconds"] = pd.to_numeric(df["hold_seconds"], errors="coerce")
    
    return df


if __name__ == "__main__":
    # Test loading
    excel_path = Path(__file__).parent.parent / "data_samples" / "workout_entry_template.xlsx"
    
    print("=== Loading Workouts ===")
    workouts = load_workouts(excel_path)
    print(f"Loaded {len(workouts)} workout rows")
    print(f"Date range: {workouts['date'].min()} to {workouts['date'].max()}")
    print(f"Exercise types: {workouts['exercise_type'].unique()}")
    print(workouts.head(10))
    
    print("\n=== Loading Skills ===")
    skills = load_skills(excel_path)
    print(f"Loaded {len(skills)} skill rows")
    if len(skills) > 0:
        print(skills.head(10))

