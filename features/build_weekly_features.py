"""
Build weekly aggregate features from workout data.
Creates ML-ready feature tables and visualizations of training patterns.
"""

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def load_from_db(db_path: str = "data_samples/fitness.db"):
    """Load workout and skill data from SQLite database."""
    engine = create_engine(f"sqlite:///{db_path}")
    
    with engine.connect() as conn:
        workouts = pd.read_sql("SELECT * FROM workout_log", conn)
        skills = pd.read_sql("SELECT * FROM skill_progress", conn)
    
    # Convert dates
    workouts["date"] = pd.to_datetime(workouts["date"])
    skills["date"] = pd.to_datetime(skills["date"])
    
    return workouts, skills


def to_week_start(dates: pd.Series) -> pd.Series:
    """Convert dates to week start (Monday)."""
    return pd.to_datetime(dates).dt.to_period("W").apply(lambda r: r.start_time)


def build_weekly_features(workouts: pd.DataFrame) -> pd.DataFrame:
    """
    Build weekly aggregate features from workout data.
    
    Features per week:
    - sessions: number of unique workout days
    - total_sets: sum of sets
    - total_reps: sum of reps
    - total_work: sets × reps × weight (volume estimate)
    
    Pivoted by exercise_type (strength, skill, accessory, mobility)
    """
    w = workouts.copy()
    w["week_start"] = to_week_start(w["date"])
    
    # Fill missing exercise_type with 'unknown'
    w["exercise_type"] = w["exercise_type"].fillna("unknown").replace("", "unknown")
    
    # Simple work estimate: sets × reps × weight
    # For bodyweight, use weight=1 so we still count volume
    w["weight_for_calc"] = w["weight"].fillna(0)
    w.loc[w["weight_for_calc"] == 0, "weight_for_calc"] = 1  # Bodyweight = 1
    
    w["work_est"] = (
        w["sets_manual"].fillna(0) * 
        w["reps_manual"].fillna(0) * 
        w["weight_for_calc"]
    )
    
    # Aggregate by week and exercise_type
    agg = (
        w.groupby(["week_start", "exercise_type"], as_index=False)
        .agg(
            sessions=("date", "nunique"),
            total_sets=("sets_manual", "sum"),
            total_reps=("reps_manual", "sum"),
            total_work=("work_est", "sum"),
            exercises=("exercise", "nunique"),
        )
    )
    
    # Pivot exercise_type to columns
    features = {}
    for metric in ["sessions", "total_sets", "total_reps", "total_work", "exercises"]:
        pivot = agg.pivot(index="week_start", columns="exercise_type", values=metric)
        pivot.columns = [f"{metric}_{col}" for col in pivot.columns]
        features[metric] = pivot
    
    # Combine all pivoted features
    feat_df = pd.concat(features.values(), axis=1).reset_index()
    feat_df = feat_df.fillna(0)
    
    # Add total columns across all types
    set_cols = [c for c in feat_df.columns if c.startswith("total_sets_")]
    rep_cols = [c for c in feat_df.columns if c.startswith("total_reps_")]
    work_cols = [c for c in feat_df.columns if c.startswith("total_work_")]
    
    feat_df["total_sets_all"] = feat_df[set_cols].sum(axis=1)
    feat_df["total_reps_all"] = feat_df[rep_cols].sum(axis=1)
    feat_df["total_work_all"] = feat_df[work_cols].sum(axis=1)
    
    # Calculate percentages
    for exercise_type in ["strength", "skill", "accessory", "mobility"]:
        col = f"total_work_{exercise_type}"
        if col in feat_df.columns:
            feat_df[f"pct_work_{exercise_type}"] = (
                feat_df[col] / feat_df["total_work_all"].replace(0, 1) * 100
            ).round(1)
    
    return feat_df


def build_skill_timeline(skills: pd.DataFrame) -> pd.DataFrame:
    """Build a timeline of skill progress."""
    s = skills.copy()
    s["week_start"] = to_week_start(s["date"])
    
    # Pivot to show each skill's progress
    timeline = s.pivot_table(
        index="week_start",
        columns=["skill", "progression"],
        values="hold_seconds",
        aggfunc="max"
    )
    
    return timeline


def plot_weekly_volume(feat_df: pd.DataFrame, output_dir: Path):
    """Plot weekly training volume by exercise type."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Weekly Training Analysis", fontsize=14, fontweight="bold")
    
    weeks = feat_df["week_start"]
    
    # Plot 1: Total sets by type (stacked)
    ax1 = axes[0, 0]
    types = ["strength", "skill", "accessory", "mobility"]
    colors = ["#e74c3c", "#9b59b6", "#3498db", "#2ecc71"]
    
    bottom = np.zeros(len(feat_df))
    for exercise_type, color in zip(types, colors):
        col = f"total_sets_{exercise_type}"
        if col in feat_df.columns:
            values = feat_df[col].values
            ax1.bar(weeks, values, bottom=bottom, label=exercise_type.title(), color=color, alpha=0.8)
            bottom += values
    
    ax1.set_title("Weekly Sets by Exercise Type")
    ax1.set_ylabel("Total Sets")
    ax1.legend(loc="upper left")
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax1.tick_params(axis="x", rotation=45)
    
    # Plot 2: Work volume trend
    ax2 = axes[0, 1]
    ax2.plot(weeks, feat_df["total_work_all"], marker="o", linewidth=2, color="#2c3e50")
    ax2.fill_between(weeks, feat_df["total_work_all"], alpha=0.3, color="#3498db")
    ax2.set_title("Total Work Volume Over Time")
    ax2.set_ylabel("Work (sets × reps × weight)")
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax2.tick_params(axis="x", rotation=45)
    
    # Plot 3: Training mix percentages
    ax3 = axes[1, 0]
    for exercise_type, color in zip(types, colors):
        col = f"pct_work_{exercise_type}"
        if col in feat_df.columns:
            ax3.plot(weeks, feat_df[col], marker="o", label=exercise_type.title(), 
                    color=color, linewidth=2)
    
    ax3.set_title("Training Mix (% of Total Work)")
    ax3.set_ylabel("Percentage")
    ax3.set_ylim(0, 100)
    ax3.legend(loc="upper right")
    ax3.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax3.tick_params(axis="x", rotation=45)
    
    # Plot 4: Sessions per week
    ax4 = axes[1, 1]
    session_cols = [c for c in feat_df.columns if c.startswith("sessions_") and c != "sessions_unknown"]
    if session_cols:
        total_sessions = feat_df[session_cols].sum(axis=1)
        ax4.bar(weeks, total_sessions, color="#1abc9c", alpha=0.8)
        ax4.axhline(y=total_sessions.mean(), color="#e74c3c", linestyle="--", 
                   label=f"Avg: {total_sessions.mean():.1f}")
    ax4.set_title("Training Sessions per Week")
    ax4.set_ylabel("Sessions")
    ax4.legend()
    ax4.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax4.tick_params(axis="x", rotation=45)
    
    plt.tight_layout()
    
    # Save plot
    plot_path = output_dir / "weekly_training_analysis.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved plot to {plot_path}")
    
    plt.show()


def plot_skill_progress(skills: pd.DataFrame, output_dir: Path):
    """Plot skill progress over time."""
    if len(skills) == 0:
        print("No skill data to plot")
        return
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Get unique skill+progression combinations
    skills["skill_prog"] = skills["skill"] + " - " + skills["progression"]
    
    colors = {"Planche": "#9b59b6", "Back Lever": "#e74c3c", "Front Lever": "#3498db"}
    markers = {"Tuck Planche": "o", "Tuck Back Lever": "s", "Tuck Front Lever": "^"}
    
    for skill in skills["skill"].unique():
        skill_data = skills[skills["skill"] == skill].sort_values("date")
        color = colors.get(skill, "#2c3e50")
        
        ax.plot(skill_data["date"], skill_data["hold_seconds"], 
               marker="o", linewidth=2, label=skill, color=color, markersize=8)
        
        # Add progression labels
        for _, row in skill_data.iterrows():
            ax.annotate(f'{row["hold_seconds"]}s', 
                       (row["date"], row["hold_seconds"]),
                       textcoords="offset points", xytext=(0, 10),
                       ha="center", fontsize=9)
    
    ax.set_title("Skill Progress Over Time", fontsize=14, fontweight="bold")
    ax.set_xlabel("Date")
    ax.set_ylabel("Hold Duration (seconds)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.tick_params(axis="x", rotation=45)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    plot_path = output_dir / "skill_progress.png"
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    print(f"✓ Saved plot to {plot_path}")
    
    plt.show()


def print_summary(feat_df: pd.DataFrame, skills: pd.DataFrame):
    """Print a summary of the training data."""
    print("\n" + "=" * 60)
    print("WEEKLY TRAINING SUMMARY")
    print("=" * 60)
    
    print(f"\nDate range: {feat_df['week_start'].min().date()} to {feat_df['week_start'].max().date()}")
    print(f"Total weeks: {len(feat_df)}")
    
    print("\n--- Average Weekly Volume ---")
    print(f"Total sets/week:  {feat_df['total_sets_all'].mean():.0f}")
    print(f"Total reps/week:  {feat_df['total_reps_all'].mean():.0f}")
    print(f"Total work/week:  {feat_df['total_work_all'].mean():.0f}")
    
    print("\n--- Training Mix (% of total work) ---")
    for exercise_type in ["strength", "skill", "accessory", "mobility"]:
        col = f"pct_work_{exercise_type}"
        if col in feat_df.columns:
            print(f"  {exercise_type.title():12}: {feat_df[col].mean():.1f}%")
    
    if len(skills) > 0:
        print("\n--- Skill Progress ---")
        for skill in skills["skill"].unique():
            skill_data = skills[skills["skill"] == skill].sort_values("date")
            first = skill_data.iloc[0]
            last = skill_data.iloc[-1]
            print(f"  {skill}: {first['hold_seconds']:.0f}s → {last['hold_seconds']:.0f}s "
                  f"(+{last['hold_seconds'] - first['hold_seconds']:.0f}s)")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # Setup paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data_samples" / "fitness.db"
    output_dir = project_root / "data_samples"
    
    print("=== Loading Data from Database ===")
    workouts, skills = load_from_db(db_path)
    print(f"Loaded {len(workouts)} workout rows, {len(skills)} skill rows")
    
    print("\n=== Building Weekly Features ===")
    feat_df = build_weekly_features(workouts)
    print(f"Created {len(feat_df)} weekly feature rows")
    print(f"Features: {list(feat_df.columns)}")
    
    # Save features
    features_path = output_dir / "weekly_features.csv"
    feat_df.to_csv(features_path, index=False)
    print(f"✓ Saved features to {features_path}")
    
    # Print summary
    print_summary(feat_df, skills)
    
    # Generate visualizations
    print("\n=== Generating Visualizations ===")
    plot_weekly_volume(feat_df, output_dir)
    plot_skill_progress(skills, output_dir)
    
    print("\n✅ Step 4 Complete — Weekly features built!")

