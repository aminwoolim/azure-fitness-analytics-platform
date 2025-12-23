"""
ML Pipeline for Skill Progress Prediction

Steps 5-6: Train models to understand what training factors
correlate with skill progress (Planche, Back Lever, etc.)
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import timedelta
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
warnings.filterwarnings('ignore')


def load_data(db_path: str, features_path: str):
    """Load skill progress from DB and weekly features from CSV."""
    # Load skills from database
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as conn:
        skills = pd.read_sql("SELECT * FROM skill_progress", conn)
    skills["date"] = pd.to_datetime(skills["date"])
    
    # Load weekly features
    features = pd.read_csv(features_path)
    features["week_start"] = pd.to_datetime(features["week_start"])
    
    return skills, features


def create_training_dataset(skills: pd.DataFrame, features: pd.DataFrame, 
                            lookback_weeks: int = 4) -> pd.DataFrame:
    """
    Create training dataset by aligning skill check-ins with 
    preceding weekly training features.
    
    For each skill measurement, we look at the training from the 
    previous N weeks to understand what led to that result.
    """
    records = []
    
    for _, skill_row in skills.iterrows():
        skill_date = skill_row["date"]
        
        # Get features from the preceding weeks
        mask = (features["week_start"] < skill_date) & \
               (features["week_start"] >= skill_date - timedelta(weeks=lookback_weeks))
        
        preceding_features = features[mask]
        
        if len(preceding_features) == 0:
            continue
        
        # Aggregate the preceding weeks' features
        agg_features = {}
        
        # Sum up training volume
        for col in preceding_features.columns:
            if col == "week_start":
                continue
            if col.startswith("total_") or col.startswith("sessions_") or col.startswith("exercises_"):
                agg_features[f"sum_{col}"] = preceding_features[col].sum()
            elif col.startswith("pct_"):
                # Average the percentages
                agg_features[f"avg_{col}"] = preceding_features[col].mean()
        
        # Add skill info as target
        agg_features["skill"] = skill_row["skill"]
        agg_features["progression"] = skill_row["progression"]
        agg_features["hold_seconds"] = skill_row["hold_seconds"]
        agg_features["check_date"] = skill_date
        agg_features["weeks_of_data"] = len(preceding_features)
        
        records.append(agg_features)
    
    return pd.DataFrame(records)


def prepare_features_and_target(df: pd.DataFrame, target_skill: str = None):
    """Prepare feature matrix X and target y."""
    
    # Filter by skill if specified
    if target_skill:
        df = df[df["skill"] == target_skill].copy()
    
    if len(df) < 3:
        print(f"Warning: Only {len(df)} samples for {target_skill or 'all skills'}")
    
    # Select feature columns (exclude metadata)
    feature_cols = [c for c in df.columns if c.startswith("sum_") or c.startswith("avg_")]
    
    X = df[feature_cols].fillna(0)
    y = df["hold_seconds"].values
    
    return X, y, df


def train_and_evaluate(X: pd.DataFrame, y: np.ndarray, skill_name: str):
    """Train models and evaluate using Leave-One-Out cross-validation."""
    
    print(f"\n{'='*60}")
    print(f"TRAINING MODELS FOR: {skill_name}")
    print(f"{'='*60}")
    print(f"Samples: {len(y)}")
    print(f"Features: {len(X.columns)}")
    
    if len(y) < 3:
        print("⚠️  Not enough data to train reliably. Need at least 3 samples.")
        return None, None
    
    # Scale features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Models to try
    models = {
        "Linear Regression": LinearRegression(),
        "Ridge Regression": Ridge(alpha=1.0),
        "Random Forest": RandomForestRegressor(n_estimators=50, max_depth=3, random_state=42)
    }
    
    results = {}
    
    for name, model in models.items():
        # Use Leave-One-Out CV for small datasets
        loo = LeaveOneOut()
        
        y_pred = []
        y_true = []
        
        for train_idx, test_idx in loo.split(X_scaled):
            X_train, X_test = X_scaled[train_idx], X_scaled[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]
            
            model.fit(X_train, y_train)
            pred = model.predict(X_test)[0]
            
            y_pred.append(pred)
            y_true.append(y_test[0])
        
        mae = mean_absolute_error(y_true, y_pred)
        
        # Calculate correlation between predicted and actual
        if np.std(y_pred) > 0 and np.std(y_true) > 0:
            corr = np.corrcoef(y_true, y_pred)[0, 1]
        else:
            corr = 0
        
        results[name] = {
            "mae": mae,
            "correlation": corr,
            "predictions": y_pred,
            "actual": y_true
        }
        
        print(f"\n{name}:")
        print(f"  MAE: {mae:.2f} seconds")
        print(f"  Correlation: {corr:.2f}")
    
    # Train final model on all data for feature importance
    best_model_name = min(results.keys(), key=lambda k: results[k]["mae"])
    print(f"\nBest model: {best_model_name}")
    
    # Fit Linear Regression for interpretability
    lr = LinearRegression()
    lr.fit(X_scaled, y)
    
    # Fit Random Forest for feature importance
    rf = RandomForestRegressor(n_estimators=100, max_depth=3, random_state=42)
    rf.fit(X_scaled, y)
    
    return lr, rf, scaler, X.columns.tolist(), results


def analyze_feature_importance(lr_model, rf_model, feature_names: list, skill_name: str):
    """Analyze and display feature importance from both models."""
    
    print(f"\n{'='*60}")
    print(f"FEATURE IMPORTANCE FOR: {skill_name}")
    print(f"{'='*60}")
    
    # Linear Regression coefficients
    lr_importance = pd.DataFrame({
        "feature": feature_names,
        "coefficient": lr_model.coef_
    }).sort_values("coefficient", key=abs, ascending=False)
    
    print("\n--- Linear Regression Coefficients ---")
    print("(Positive = helps hold duration, Negative = hurts)")
    for _, row in lr_importance.head(10).iterrows():
        direction = "+" if row["coefficient"] > 0 else ""
        print(f"  {row['feature']:40} {direction}{row['coefficient']:.3f}")
    
    # Random Forest importance
    rf_importance = pd.DataFrame({
        "feature": feature_names,
        "importance": rf_model.feature_importances_
    }).sort_values("importance", ascending=False)
    
    print("\n--- Random Forest Feature Importance ---")
    print("(Higher = more predictive)")
    for _, row in rf_importance.head(10).iterrows():
        print(f"  {row['feature']:40} {row['importance']:.3f}")
    
    return lr_importance, rf_importance


def generate_recommendations(lr_importance: pd.DataFrame, rf_importance: pd.DataFrame, 
                            skill_name: str, current_mix: dict):
    """Generate actionable training recommendations."""
    
    print(f"\n{'='*60}")
    print(f"RECOMMENDATIONS FOR: {skill_name}")
    print(f"{'='*60}")
    
    # Find top positive and negative factors
    top_positive = lr_importance[lr_importance["coefficient"] > 0].head(3)
    top_negative = lr_importance[lr_importance["coefficient"] < 0].head(3)
    
    print("\n📈 Training factors that HELP progress:")
    for _, row in top_positive.iterrows():
        feature = row["feature"].replace("sum_", "").replace("avg_", "").replace("_", " ")
        print(f"  • Increase: {feature}")
    
    print("\n📉 Training factors that may HURT progress:")
    for _, row in top_negative.iterrows():
        feature = row["feature"].replace("sum_", "").replace("avg_", "").replace("_", " ")
        print(f"  • Consider reducing: {feature}")
    
    # Specific recommendations based on current training mix
    print("\n💡 Based on your current training:")
    
    if current_mix.get("pct_work_skill", 0) < 5:
        print("  ⚠️  Your skill work is only {:.1f}% of training".format(
            current_mix.get("pct_work_skill", 0)))
        print("     → Try dedicating 15-20% of training to skill-specific work")
    
    if current_mix.get("pct_work_mobility", 0) < 5:
        print("  ⚠️  Mobility work is very low ({:.1f}%)".format(
            current_mix.get("pct_work_mobility", 0)))
        print("     → Mobility may help with skill positions (planche lean, etc.)")
    
    if current_mix.get("pct_work_strength", 0) > 80:
        print("  ℹ️  Strength dominates at {:.1f}%".format(
            current_mix.get("pct_work_strength", 0)))
        print("     → Consider rebalancing some strength volume to skill practice")


def plot_results(results: dict, skill_name: str, output_dir: Path):
    """Plot model predictions vs actual values."""
    
    fig, axes = plt.subplots(1, len(results), figsize=(5*len(results), 5))
    if len(results) == 1:
        axes = [axes]
    
    for ax, (model_name, result) in zip(axes, results.items()):
        actual = result["actual"]
        predicted = result["predictions"]
        
        ax.scatter(actual, predicted, s=100, alpha=0.7, c='#3498db')
        
        # Perfect prediction line
        min_val = min(min(actual), min(predicted))
        max_val = max(max(actual), max(predicted))
        ax.plot([min_val, max_val], [min_val, max_val], 'r--', alpha=0.5, label='Perfect prediction')
        
        ax.set_xlabel("Actual Hold (seconds)")
        ax.set_ylabel("Predicted Hold (seconds)")
        ax.set_title(f"{model_name}\nMAE: {result['mae']:.1f}s, Corr: {result['correlation']:.2f}")
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.suptitle(f"Model Performance: {skill_name}", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    plot_path = output_dir / f"model_performance_{skill_name.lower().replace(' ', '_')}.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved plot to {plot_path}")
    plt.show()


def plot_feature_importance(lr_importance: pd.DataFrame, rf_importance: pd.DataFrame,
                           skill_name: str, output_dir: Path):
    """Plot feature importance comparison."""
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Linear Regression coefficients
    ax1 = axes[0]
    top_lr = lr_importance.head(10)
    colors = ['#2ecc71' if x > 0 else '#e74c3c' for x in top_lr["coefficient"]]
    ax1.barh(range(len(top_lr)), top_lr["coefficient"], color=colors)
    ax1.set_yticks(range(len(top_lr)))
    ax1.set_yticklabels([f.replace("sum_", "").replace("avg_", "")[:30] for f in top_lr["feature"]])
    ax1.set_xlabel("Coefficient (+ helps, - hurts)")
    ax1.set_title("Linear Regression Coefficients")
    ax1.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
    ax1.invert_yaxis()
    
    # Random Forest importance
    ax2 = axes[1]
    top_rf = rf_importance.head(10)
    ax2.barh(range(len(top_rf)), top_rf["importance"], color='#3498db')
    ax2.set_yticks(range(len(top_rf)))
    ax2.set_yticklabels([f.replace("sum_", "").replace("avg_", "")[:30] for f in top_rf["feature"]])
    ax2.set_xlabel("Importance Score")
    ax2.set_title("Random Forest Feature Importance")
    ax2.invert_yaxis()
    
    plt.suptitle(f"What Predicts {skill_name} Progress?", fontsize=14, fontweight='bold')
    plt.tight_layout()
    
    plot_path = output_dir / f"feature_importance_{skill_name.lower().replace(' ', '_')}.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved plot to {plot_path}")
    plt.show()


if __name__ == "__main__":
    # Setup paths
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data_samples" / "fitness.db"
    features_path = project_root / "data_samples" / "weekly_features.csv"
    output_dir = project_root / "data_samples"
    
    print("=" * 60)
    print("SKILL PROGRESS ML PIPELINE")
    print("=" * 60)
    
    # Load data
    print("\n=== Loading Data ===")
    skills, features = load_data(db_path, features_path)
    print(f"Loaded {len(skills)} skill check-ins, {len(features)} weekly feature rows")
    
    # Get current training mix for recommendations
    current_mix = {
        "pct_work_strength": features["pct_work_strength"].mean(),
        "pct_work_skill": features["pct_work_skill"].mean(),
        "pct_work_accessory": features["pct_work_accessory"].mean(),
        "pct_work_mobility": features["pct_work_mobility"].mean(),
    }
    
    # Create training dataset
    print("\n=== Creating Training Dataset ===")
    train_df = create_training_dataset(skills, features, lookback_weeks=4)
    print(f"Created {len(train_df)} training samples")
    print(f"Skills: {train_df['skill'].unique()}")
    
    # Train models for each skill
    for skill_name in train_df["skill"].unique():
        X, y, df = prepare_features_and_target(train_df, target_skill=skill_name)
        
        if len(y) >= 3:
            result = train_and_evaluate(X, y, skill_name)
            
            if result[0] is not None:
                lr_model, rf_model, scaler, feature_names, results = result
                
                # Analyze feature importance
                lr_imp, rf_imp = analyze_feature_importance(lr_model, rf_model, 
                                                            feature_names, skill_name)
                
                # Generate recommendations
                generate_recommendations(lr_imp, rf_imp, skill_name, current_mix)
                
                # Plot results
                plot_results(results, skill_name, output_dir)
                plot_feature_importance(lr_imp, rf_imp, skill_name, output_dir)
    
    # Also train on all skills combined
    print("\n" + "=" * 60)
    print("COMBINED MODEL (ALL SKILLS)")
    print("=" * 60)
    
    X_all, y_all, df_all = prepare_features_and_target(train_df, target_skill=None)
    
    if len(y_all) >= 3:
        result = train_and_evaluate(X_all, y_all, "All Skills Combined")
        
        if result[0] is not None:
            lr_model, rf_model, scaler, feature_names, results = result
            lr_imp, rf_imp = analyze_feature_importance(lr_model, rf_model, 
                                                        feature_names, "All Skills")
            generate_recommendations(lr_imp, rf_imp, "All Skills", current_mix)
            plot_feature_importance(lr_imp, rf_imp, "All Skills", output_dir)
    
    print("\n" + "=" * 60)
    print("✅ ML PIPELINE COMPLETE")
    print("=" * 60)
    print("\nFiles generated:")
    print(f"  • {output_dir}/model_performance_*.png")
    print(f"  • {output_dir}/feature_importance_*.png")

