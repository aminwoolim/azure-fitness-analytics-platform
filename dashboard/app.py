"""
Fitness Progress Dashboard
Interactive Streamlit app for tracking workout progress and skill development.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="Fitness Progress Dashboard",
    page_icon="🏋️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling (dark mode compatible)
st.markdown("""
<style>
    /* Fix metric cards for dark mode */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1f2e 0%, #2d3748 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    [data-testid="stMetricLabel"] {
        color: #a0aec0 !important;
        font-size: 0.9rem !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    [data-testid="stMetricDelta"] {
        color: #68d391 !important;
    }
    [data-testid="stMetricDelta"][data-testid-delta="negative"] {
        color: #fc8181 !important;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #e2e8f0 !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #1a1f2e;
    }
    
    /* Progress bars in training mix */
    .progress-bar-bg {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 5px;
        height: 20px;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data():
    """Load data from Azure SQL, local SQLite, or CSV files."""
    import os
    
    # Check for Azure SQL credentials (from secrets or env vars)
    azure_server = None
    if hasattr(st, 'secrets') and 'AZURE_SQL_SERVER' in st.secrets:
        azure_server = st.secrets.get("AZURE_SQL_SERVER")
        azure_db = st.secrets.get("AZURE_SQL_DB", "fitness_db")
        azure_user = st.secrets.get("AZURE_SQL_USER")
        azure_pass = st.secrets.get("AZURE_SQL_PASS")
    elif os.getenv("AZURE_SQL_SERVER"):
        azure_server = os.getenv("AZURE_SQL_SERVER")
        azure_db = os.getenv("AZURE_SQL_DB", "fitness_db")
        azure_user = os.getenv("AZURE_SQL_USER")
        azure_pass = os.getenv("AZURE_SQL_PASS")
    
    # Try Azure SQL first
    if azure_server:
        try:
            from sqlalchemy import create_engine
            from urllib.parse import quote_plus
            
            # URL-encode credentials to handle special characters
            encoded_user = quote_plus(azure_user) if azure_user else ""
            encoded_pass = quote_plus(azure_pass) if azure_pass else ""
            
            conn_str = f"mssql+pyodbc://{encoded_user}:{encoded_pass}@{azure_server}/{azure_db}?driver=ODBC+Driver+18+for+SQL+Server"
            engine = create_engine(conn_str)
            
            workouts = pd.read_sql("SELECT * FROM workout_log", engine)
            skills = pd.read_sql("SELECT * FROM skill_progress", engine)
            workouts["date"] = pd.to_datetime(workouts["date"])
            skills["date"] = pd.to_datetime(skills["date"])
            
            # Build features from workouts
            features = build_features_from_workouts(workouts)
            
            return features, workouts, skills
        except Exception as e:
            st.warning(f"Could not connect to Azure SQL: {e}. Falling back to local files.")
    
    # Fall back to local files
    possible_paths = [
        Path("data_samples"),  # If running from project root
        Path("../data_samples"),  # If running from dashboard folder
        Path(__file__).parent.parent / "data_samples",  # Absolute path
    ]
    
    data_path = None
    for p in possible_paths:
        if (p / "weekly_features.csv").exists():
            data_path = p
            break
    
    if data_path is None:
        st.error("Could not find data files. Please run the pipeline first.")
        return None, None, None
    
    # Load weekly features
    features = pd.read_csv(data_path / "weekly_features.csv")
    features["week_start"] = pd.to_datetime(features["week_start"])
    
    # Load from SQLite if available
    db_path = data_path / "fitness.db"
    if db_path.exists():
        import sqlite3
        conn = sqlite3.connect(db_path)
        workouts = pd.read_sql("SELECT * FROM workout_log", conn)
        skills = pd.read_sql("SELECT * FROM skill_progress", conn)
        workouts["date"] = pd.to_datetime(workouts["date"])
        skills["date"] = pd.to_datetime(skills["date"])
        conn.close()
    else:
        workouts = None
        skills = None
    
    return features, workouts, skills


def build_features_from_workouts(workouts: pd.DataFrame) -> pd.DataFrame:
    """Build weekly features from workout data (used when loading from Azure SQL)."""
    w = workouts.copy()
    w["week_start"] = pd.to_datetime(w["date"]).dt.to_period("W").apply(lambda r: r.start_time)
    
    # Fill missing exercise_type
    w["exercise_type"] = w["exercise_type"].fillna("unknown").replace("", "unknown")
    
    # Work estimate
    w["weight_for_calc"] = w["weight"].fillna(0)
    w.loc[w["weight_for_calc"] == 0, "weight_for_calc"] = 1
    w["work_est"] = w["sets_manual"].fillna(0) * w["reps_manual"].fillna(0) * w["weight_for_calc"]
    
    # Aggregate
    agg = w.groupby(["week_start", "exercise_type"], as_index=False).agg(
        sessions=("date", "nunique"),
        total_sets=("sets_manual", "sum"),
        total_reps=("reps_manual", "sum"),
        total_work=("work_est", "sum"),
    )
    
    # Pivot
    features = {}
    for metric in ["sessions", "total_sets", "total_reps", "total_work"]:
        pivot = agg.pivot(index="week_start", columns="exercise_type", values=metric)
        pivot.columns = [f"{metric}_{col}" for col in pivot.columns]
        features[metric] = pivot
    
    feat_df = pd.concat(features.values(), axis=1).reset_index().fillna(0)
    
    # Totals
    set_cols = [c for c in feat_df.columns if c.startswith("total_sets_")]
    work_cols = [c for c in feat_df.columns if c.startswith("total_work_")]
    rep_cols = [c for c in feat_df.columns if c.startswith("total_reps_")]
    
    feat_df["total_sets_all"] = feat_df[set_cols].sum(axis=1)
    feat_df["total_reps_all"] = feat_df[rep_cols].sum(axis=1)
    feat_df["total_work_all"] = feat_df[work_cols].sum(axis=1)
    
    # Percentages
    for exercise_type in ["strength", "skill", "accessory", "mobility"]:
        col = f"total_work_{exercise_type}"
        if col in feat_df.columns:
            feat_df[f"pct_work_{exercise_type}"] = (
                feat_df[col] / feat_df["total_work_all"].replace(0, 1) * 100
            ).round(1)
    
    return feat_df


def main():
    # Header
    st.title("🏋️ Fitness Progress Dashboard")
    st.markdown("Track your training volume, exercise mix, and skill progress over time.")
    
    # Load data
    features, workouts, skills = load_data()
    
    if features is None:
        st.stop()
    
    # Sidebar filters
    st.sidebar.header("📊 Filters")
    
    # Date range filter
    min_date = features["week_start"].min().date()
    max_date = features["week_start"].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        features_filtered = features[
            (features["week_start"].dt.date >= start_date) & 
            (features["week_start"].dt.date <= end_date)
        ]
    else:
        features_filtered = features
    
    # ========== KEY METRICS ==========
    st.header("📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_weeks = len(features_filtered)
        st.metric("Weeks Tracked", total_weeks)
    
    with col2:
        avg_sets = features_filtered["total_sets_all"].mean()
        st.metric("Avg Sets/Week", f"{avg_sets:.0f}")
    
    with col3:
        avg_reps = features_filtered["total_reps_all"].mean()
        st.metric("Avg Reps/Week", f"{avg_reps:.0f}")
    
    with col4:
        total_work = features_filtered["total_work_all"].sum()
        st.metric("Total Work Volume", f"{total_work:,.0f}")
    
    # ========== TRAINING VOLUME OVER TIME ==========
    st.header("📊 Training Volume Over Time")
    
    # Create tabs for different views
    tab1, tab2, tab3 = st.tabs(["📈 Volume Trend", "🥧 Training Mix", "📋 Weekly Breakdown"])
    
    with tab1:
        # Stacked area chart of volume by exercise type
        fig = go.Figure()
        
        colors = {
            "strength": "#e74c3c",
            "skill": "#9b59b6", 
            "accessory": "#3498db",
            "mobility": "#2ecc71"
        }
        
        for exercise_type in ["strength", "skill", "accessory", "mobility"]:
            col_name = f"total_sets_{exercise_type}"
            if col_name in features_filtered.columns:
                fig.add_trace(go.Scatter(
                    x=features_filtered["week_start"],
                    y=features_filtered[col_name],
                    name=exercise_type.title(),
                    stackgroup='one',
                    fillcolor=colors.get(exercise_type, "#95a5a6"),
                    line=dict(color=colors.get(exercise_type, "#95a5a6"))
                ))
        
        fig.update_layout(
            title="Weekly Sets by Exercise Type",
            xaxis_title="Week",
            yaxis_title="Total Sets",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # Pie chart of training mix
        col1, col2 = st.columns([1, 1])
        
        with col1:
            avg_mix = {
                "Strength": features_filtered.get("pct_work_strength", pd.Series([0])).mean(),
                "Skill": features_filtered.get("pct_work_skill", pd.Series([0])).mean(),
                "Accessory": features_filtered.get("pct_work_accessory", pd.Series([0])).mean(),
                "Mobility": features_filtered.get("pct_work_mobility", pd.Series([0])).mean(),
            }
            
            fig_pie = px.pie(
                values=list(avg_mix.values()),
                names=list(avg_mix.keys()),
                color_discrete_sequence=["#e74c3c", "#9b59b6", "#3498db", "#2ecc71"],
                title="Average Training Mix (% of Work)"
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.subheader("Training Mix Breakdown")
            for exercise_type, pct in avg_mix.items():
                color = colors.get(exercise_type.lower(), "#95a5a6")
                st.markdown(f"""
                <div style="margin-bottom: 10px;">
                    <span style="color: {color}; font-weight: bold;">{exercise_type}</span>: {pct:.1f}%
                    <div style="background-color: #ddd; border-radius: 5px; height: 20px; width: 100%;">
                        <div style="background-color: {color}; width: {pct}%; height: 100%; border-radius: 5px;"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            # Recommendations
            st.markdown("---")
            st.subheader("💡 Recommendations")
            
            if avg_mix.get("Skill", 0) < 10:
                st.warning(f"⚠️ Skill work is only {avg_mix.get('Skill', 0):.1f}% — consider increasing to 15-20% for faster skill progress")
            
            if avg_mix.get("Mobility", 0) < 5:
                st.info(f"ℹ️ Mobility work is low ({avg_mix.get('Mobility', 0):.1f}%) — may help with skill positions")
            
            if avg_mix.get("Strength", 0) > 80:
                st.info(f"ℹ️ Strength dominates at {avg_mix.get('Strength', 0):.1f}% — consider rebalancing some volume to skill practice")
    
    with tab3:
        # Weekly data table
        display_cols = ["week_start", "total_sets_all", "total_reps_all", "total_work_all"]
        for t in ["strength", "skill", "accessory", "mobility"]:
            col = f"pct_work_{t}"
            if col in features_filtered.columns:
                display_cols.append(col)
        
        display_df = features_filtered[display_cols].copy()
        display_df["week_start"] = display_df["week_start"].dt.strftime("%Y-%m-%d")
        display_df.columns = [c.replace("_", " ").title() for c in display_df.columns]
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    
    # ========== SKILL PROGRESS ==========
    if skills is not None and len(skills) > 0:
        st.header("🎯 Skill Progress")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Line chart of skill progress
            fig_skills = px.line(
                skills,
                x="date",
                y="hold_seconds",
                color="skill",
                markers=True,
                title="Skill Hold Duration Over Time",
                color_discrete_sequence=["#9b59b6", "#e74c3c", "#3498db"]
            )
            
            fig_skills.update_layout(
                xaxis_title="Date",
                yaxis_title="Hold Duration (seconds)",
                hovermode="x unified",
                height=400
            )
            
            # Add annotations for each point
            for _, row in skills.iterrows():
                fig_skills.add_annotation(
                    x=row["date"],
                    y=row["hold_seconds"],
                    text=f"{row['hold_seconds']:.0f}s",
                    showarrow=False,
                    yshift=15,
                    font=dict(size=10)
                )
            
            st.plotly_chart(fig_skills, use_container_width=True)
        
        with col2:
            st.subheader("Progress Summary")
            
            for skill_name in skills["skill"].unique():
                skill_data = skills[skills["skill"] == skill_name].sort_values("date")
                
                if len(skill_data) >= 2:
                    first = skill_data.iloc[0]["hold_seconds"]
                    last = skill_data.iloc[-1]["hold_seconds"]
                    change = last - first
                    
                    delta_color = "normal" if change >= 0 else "inverse"
                    st.metric(
                        label=skill_name,
                        value=f"{last:.0f} sec",
                        delta=f"{change:+.0f} sec",
                        delta_color=delta_color
                    )
                else:
                    st.metric(
                        label=skill_name,
                        value=f"{skill_data.iloc[0]['hold_seconds']:.0f} sec"
                    )
            
            st.markdown("---")
            st.caption("💡 Add more skill check-ins to track progress over time")
    
    # ========== EXERCISE BREAKDOWN ==========
    if workouts is not None and len(workouts) > 0:
        st.header("🏃 Exercise Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Top exercises by frequency
            exercise_counts = workouts["exercise"].value_counts().head(15)
            
            fig_exercises = px.bar(
                x=exercise_counts.values,
                y=exercise_counts.index,
                orientation='h',
                title="Most Frequent Exercises",
                labels={"x": "Count", "y": "Exercise"},
                color=exercise_counts.values,
                color_continuous_scale="Blues"
            )
            fig_exercises.update_layout(
                height=500,
                showlegend=False,
                yaxis={'categoryorder': 'total ascending'}
            )
            st.plotly_chart(fig_exercises, use_container_width=True)
        
        with col2:
            # Exercises by type
            if "exercise_type" in workouts.columns:
                type_counts = workouts["exercise_type"].value_counts()
                
                fig_types = px.bar(
                    x=type_counts.index,
                    y=type_counts.values,
                    title="Exercises by Type",
                    labels={"x": "Type", "y": "Count"},
                    color=type_counts.index,
                    color_discrete_map={
                        "strength": "#e74c3c",
                        "skill": "#9b59b6",
                        "accessory": "#3498db",
                        "mobility": "#2ecc71"
                    }
                )
                fig_types.update_layout(showlegend=False, height=500)
                st.plotly_chart(fig_types, use_container_width=True)
    
    # ========== FOOTER ==========
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>📊 Data last updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M") + """</p>
        <p>Built with Streamlit | Data from Azure Fit Platform</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

