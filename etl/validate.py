"""
Validate workout and skill data before loading to database.
"""

from typing import List, Tuple
import pandas as pd


VALID_EXERCISE_TYPES = {"strength", "skill", "accessory", "mobility"}
VALID_WEIGHT_UNITS = {
    "lbs", "kg", "bodyweight", "band", "plates", "",
    # Standard bands
    "red_band", "blue_band", "green_band", "orange_band", "black_band",
    # Sized bands (s=small, l=large)
    "s-red band", "l-red band", "s-blue band", "l-blue band",
    "s-green band", "l-green band", "s-orange band", "l-orange band",
    "s-black band", "l-black band",
}


def validate_workouts(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate the workout DataFrame.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required columns
    required = ["date", "exercise", "exercise_type", "sets_manual", "reps_manual", "weight", "weight_unit"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")
        return False, errors
    
    # Check for missing dates
    missing_dates = df["date"].isna().sum()
    if missing_dates > 0:
        errors.append(f"{missing_dates} rows have missing dates")
    
    # Check exercise_type values
    invalid_types = df[~df["exercise_type"].isin(VALID_EXERCISE_TYPES | {""})]["exercise_type"].unique()
    if len(invalid_types) > 0:
        errors.append(f"Invalid exercise_type values: {list(invalid_types)}")
    
    # Check weight_unit values
    invalid_units = df[~df["weight_unit"].isin(VALID_WEIGHT_UNITS)]["weight_unit"].unique()
    if len(invalid_units) > 0:
        errors.append(f"Invalid weight_unit values: {list(invalid_units)}")
    
    # Check for negative values
    for col in ["sets_manual", "reps_manual", "weight"]:
        negative = (df[col] < 0).sum()
        if negative > 0:
            errors.append(f"{negative} rows have negative {col}")
    
    # Warn about incomplete data (not errors, just warnings)
    missing_sets = df["sets_manual"].isna().sum()
    missing_reps = df["reps_manual"].isna().sum()
    missing_type = (df["exercise_type"] == "").sum()
    
    if missing_sets > 0 or missing_reps > 0:
        print(f"Warning: {missing_sets} rows missing sets_manual, {missing_reps} missing reps_manual")
    if missing_type > 0:
        print(f"Warning: {missing_type} rows have no exercise_type assigned")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def validate_skills(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate the skill_progress DataFrame.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    if len(df) == 0:
        print("Warning: skill_progress is empty (no data to validate)")
        return True, errors
    
    # Check required columns
    required = ["date", "skill", "progression", "achieved"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")
        return False, errors
    
    # Check for missing dates
    missing_dates = df["date"].isna().sum()
    if missing_dates > 0:
        errors.append(f"{missing_dates} skill rows have missing dates")
    
    # Check achieved values (should be boolean after cleaning)
    invalid_achieved = df["achieved"].isna().sum()
    if invalid_achieved > 0:
        errors.append(f"{invalid_achieved} skill rows have invalid 'achieved' values (not Yes/No)")
    
    # Check for negative hold_seconds
    if "hold_seconds" in df.columns:
        negative = (df["hold_seconds"] < 0).sum()
        if negative > 0:
            errors.append(f"{negative} skill rows have negative hold_seconds")
    
    is_valid = len(errors) == 0
    return is_valid, errors


def run_all_validations(workouts: pd.DataFrame, skills: pd.DataFrame) -> bool:
    """Run all validations and print results."""
    print("=" * 50)
    print("VALIDATION REPORT")
    print("=" * 50)
    
    print("\n--- Workout Validation ---")
    w_valid, w_errors = validate_workouts(workouts)
    if w_valid:
        print("✓ Workouts passed validation")
    else:
        print("✗ Workout validation failed:")
        for e in w_errors:
            print(f"  - {e}")
    
    print("\n--- Skill Progress Validation ---")
    s_valid, s_errors = validate_skills(skills)
    if s_valid:
        print("✓ Skills passed validation")
    else:
        print("✗ Skill validation failed:")
        for e in s_errors:
            print(f"  - {e}")
    
    print("\n" + "=" * 50)
    all_valid = w_valid and s_valid
    print(f"Overall: {'✓ PASSED' if all_valid else '✗ FAILED'}")
    print("=" * 50)
    
    return all_valid


if __name__ == "__main__":
    from pathlib import Path
    from read_and_clean_excel import load_workouts, load_skills
    
    excel_path = Path(__file__).parent.parent / "data_samples" / "workout_entry_template.xlsx"
    
    workouts = load_workouts(excel_path)
    skills = load_skills(excel_path)
    
    run_all_validations(workouts, skills)

