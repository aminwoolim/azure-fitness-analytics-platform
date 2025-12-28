"""
Fitness Progress Dashboard
Interactive Streamlit app for tracking workout progress and skill development.
Enhanced with animations and modern styling.
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

# Enhanced CSS with animations
st.markdown("""
<style>
    /* ===== ANIMATIONS ===== */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.4); }
        70% { box-shadow: 0 0 0 15px rgba(102, 126, 234, 0); }
        100% { box-shadow: 0 0 0 0 rgba(102, 126, 234, 0); }
    }
    
    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 5px rgba(102, 126, 234, 0.5), 0 0 10px rgba(102, 126, 234, 0.3); }
        50% { box-shadow: 0 0 20px rgba(102, 126, 234, 0.8), 0 0 30px rgba(102, 126, 234, 0.5); }
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-30px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes scaleIn {
        from {
            opacity: 0;
            transform: scale(0.8);
        }
        to {
            opacity: 1;
            transform: scale(1);
        }
    }
    
    @keyframes gradientMove {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* ===== METRIC CARDS ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1a1f2e 0%, #2d3748 100%);
        padding: 20px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        animation: fadeInUp 0.6s ease-out forwards;
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.3);
        border-color: rgba(102, 126, 234, 0.5);
    }
    
    [data-testid="stMetricLabel"] {
        color: #a0aec0 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        background: linear-gradient(90deg, #667eea, #764ba2, #667eea);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientMove 3s ease infinite;
    }
    
    [data-testid="stMetricDelta"] {
        font-weight: 600 !important;
    }
    
    [data-testid="stMetricDelta"] svg {
        display: inline-block;
    }
    
    /* ===== HEADERS ===== */
    h1 {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: fadeInUp 0.8s ease-out;
        font-size: 2.5rem !important;
    }
    
    h2 {
        color: #e2e8f0 !important;
        animation: slideIn 0.6s ease-out;
        border-left: 4px solid #667eea;
        padding-left: 15px;
        margin-top: 2rem !important;
    }
    
    h3 {
        color: #cbd5e0 !important;
    }
    
    /* ===== SIDEBAR ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #0d1117 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] [data-testid="stMarkdown"] {
        animation: fadeInUp 0.5s ease-out;
    }
    
    /* ===== TABS ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(26, 31, 46, 0.5);
        padding: 10px;
        border-radius: 12px;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: rgba(102, 126, 234, 0.2);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    }
    
    /* ===== PROGRESS BARS ===== */
    .progress-container {
        margin-bottom: 15px;
        animation: slideIn 0.5s ease-out;
    }
    
    .progress-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 5px;
        font-weight: 600;
    }
    
    .progress-bar-bg {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        height: 24px;
        width: 100%;
        overflow: hidden;
        position: relative;
    }
    
    .progress-bar-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 1s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .progress-bar-fill::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(
            90deg,
            transparent,
            rgba(255, 255, 255, 0.3),
            transparent
        );
        animation: shimmer 2s infinite;
        background-size: 200% 100%;
    }
    
    /* ===== CELEBRATION BANNER ===== */
    .celebration-banner {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 50%, #ffd700 100%);
        background-size: 200% 200%;
        animation: gradientMove 3s ease infinite;
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        margin: 20px 0;
        box-shadow: 0 8px 32px rgba(240, 147, 251, 0.3);
    }
    
    .celebration-banner h3 {
        color: white !important;
        margin: 0;
        font-size: 1.5rem;
    }
    
    .celebration-banner p {
        color: rgba(255, 255, 255, 0.9);
        margin: 10px 0 0 0;
    }
    
    /* ===== STAT CARD ===== */
    .stat-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #2d3748 100%);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
        animation: scaleIn 0.5s ease-out;
    }
    
    .stat-card:hover {
        transform: scale(1.02);
        border-color: rgba(102, 126, 234, 0.5);
        box-shadow: 0 8px 32px rgba(102, 126, 234, 0.2);
    }
    
    .stat-value {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .stat-label {
        color: #a0aec0;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 5px;
    }
    
    /* ===== DATAFRAME ===== */
    .stDataFrame {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* ===== PLOTLY CHARTS ===== */
    .js-plotly-plot {
        animation: scaleIn 0.8s ease-out;
    }
    
    /* ===== FOOTER ===== */
    .footer {
        text-align: center;
        padding: 30px;
        color: #666;
        animation: fadeInUp 0.8s ease-out;
    }
    
    .footer a {
        color: #667eea;
        text-decoration: none;
        transition: color 0.3s ease;
    }
    
    .footer a:hover {
        color: #764ba2;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=300)
def load_data():
    """Load data from Azure SQL, local SQLite, or CSV files."""
    import os
    
    azure_server = None
    azure_db = None
    azure_user = None
    azure_pass = None
    
    # Safely check for Streamlit secrets (won't error if no secrets file exists)
    try:
        if 'AZURE_SQL_SERVER' in st.secrets:
            azure_server = st.secrets.get("AZURE_SQL_SERVER")
            azure_db = st.secrets.get("AZURE_SQL_DB", "fitness_db")
            azure_user = st.secrets.get("AZURE_SQL_USER")
            azure_pass = st.secrets.get("AZURE_SQL_PASS")
    except Exception:
        pass  # No secrets file locally, that's fine
    
    # Also check environment variables if secrets not found
    if not azure_server and os.getenv("AZURE_SQL_SERVER"):
        azure_server = os.getenv("AZURE_SQL_SERVER")
        azure_db = os.getenv("AZURE_SQL_DB", "fitness_db")
        azure_user = os.getenv("AZURE_SQL_USER")
        azure_pass = os.getenv("AZURE_SQL_PASS")
    
    if azure_server:
        try:
            from sqlalchemy import create_engine
            from urllib.parse import quote_plus
            
            encoded_user = quote_plus(azure_user) if azure_user else ""
            encoded_pass = quote_plus(azure_pass) if azure_pass else ""
            
            conn_str = f"mssql+pyodbc://{encoded_user}:{encoded_pass}@{azure_server}/{azure_db}?driver=ODBC+Driver+18+for+SQL+Server"
            engine = create_engine(conn_str)
            
            workouts = pd.read_sql("SELECT * FROM workout_log", engine)
            skills = pd.read_sql("SELECT * FROM skill_progress", engine)
            workouts["date"] = pd.to_datetime(workouts["date"])
            skills["date"] = pd.to_datetime(skills["date"])
            
            features = build_features_from_workouts(workouts)
            return features, workouts, skills
        except Exception as e:
            st.warning(f"Could not connect to Azure SQL: {e}. Falling back to local files.")
    
    possible_paths = [
        Path("data_samples"),
        Path("../data_samples"),
        Path(__file__).parent.parent / "data_samples",
    ]
    
    data_path = None
    for p in possible_paths:
        if (p / "weekly_features.csv").exists():
            data_path = p
            break
    
    if data_path is None:
        st.error("Could not find data files. Please run the pipeline first.")
        return None, None, None
    
    features = pd.read_csv(data_path / "weekly_features.csv")
    features["week_start"] = pd.to_datetime(features["week_start"])
    
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
    """Build weekly features from workout data."""
    w = workouts.copy()
    w["week_start"] = pd.to_datetime(w["date"]).dt.to_period("W").apply(lambda r: r.start_time)
    w["exercise_type"] = w["exercise_type"].fillna("unknown").replace("", "unknown")
    
    w["weight_for_calc"] = w["weight"].fillna(0)
    w.loc[w["weight_for_calc"] == 0, "weight_for_calc"] = 1
    w["work_est"] = w["sets_manual"].fillna(0) * w["reps_manual"].fillna(0) * w["weight_for_calc"]
    
    agg = w.groupby(["week_start", "exercise_type"], as_index=False).agg(
        sessions=("date", "nunique"),
        total_sets=("sets_manual", "sum"),
        total_reps=("reps_manual", "sum"),
        total_work=("work_est", "sum"),
    )
    
    features = {}
    for metric in ["sessions", "total_sets", "total_reps", "total_work"]:
        pivot = agg.pivot(index="week_start", columns="exercise_type", values=metric)
        pivot.columns = [f"{metric}_{col}" for col in pivot.columns]
        features[metric] = pivot
    
    feat_df = pd.concat(features.values(), axis=1).reset_index().fillna(0)
    
    set_cols = [c for c in feat_df.columns if c.startswith("total_sets_")]
    work_cols = [c for c in feat_df.columns if c.startswith("total_work_")]
    rep_cols = [c for c in feat_df.columns if c.startswith("total_reps_")]
    
    feat_df["total_sets_all"] = feat_df[set_cols].sum(axis=1)
    feat_df["total_reps_all"] = feat_df[rep_cols].sum(axis=1)
    feat_df["total_work_all"] = feat_df[work_cols].sum(axis=1)
    
    for exercise_type in ["strength", "skill", "accessory", "mobility"]:
        col = f"total_work_{exercise_type}"
        if col in feat_df.columns:
            feat_df[f"pct_work_{exercise_type}"] = (
                feat_df[col] / feat_df["total_work_all"].replace(0, 1) * 100
            ).round(1)
    
    return feat_df


def render_progress_bar(label: str, value: float, color: str, max_value: float = 100):
    """Render an animated progress bar."""
    percentage = min(value / max_value * 100, 100)
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-label">
            <span style="color: {color};">{label}</span>
            <span style="color: #a0aec0;">{value:.1f}%</span>
        </div>
        <div class="progress-bar-bg">
            <div class="progress-bar-fill" style="width: {percentage}%; background: linear-gradient(90deg, {color}, {color}dd);"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def check_milestones(skills: pd.DataFrame) -> list:
    """Check for skill milestones/PRs."""
    milestones = []
    
    if skills is None or len(skills) == 0:
        return milestones
    
    for skill_name in skills["skill"].unique():
        skill_data = skills[skills["skill"] == skill_name].sort_values("date")
        
        if len(skill_data) >= 2:
            current = skill_data.iloc[-1]["hold_seconds"]
            previous = skill_data.iloc[-2]["hold_seconds"]
            first = skill_data.iloc[0]["hold_seconds"]
            
            # Check for new PR
            if current >= skill_data["hold_seconds"].max():
                if current > previous:
                    milestones.append({
                        "type": "pr",
                        "skill": skill_name,
                        "value": current,
                        "improvement": current - previous
                    })
            
            # Check for significant improvement (>50% from start)
            if current > first * 1.5:
                milestones.append({
                    "type": "milestone",
                    "skill": skill_name,
                    "value": current,
                    "improvement_pct": ((current - first) / first) * 100
                })
    
    return milestones


def main():
    # Header with animation
    st.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h1 style="font-size: 3rem; margin-bottom: 10px;">🏋️ Fitness Progress Dashboard</h1>
        <p style="color: #a0aec0; font-size: 1.1rem; animation: fadeInUp 1s ease-out;">
            Track your training volume, exercise mix, and skill progress over time
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    features, workouts, skills = load_data()
    
    if features is None:
        st.stop()
    
    # Check for milestones
    milestones = check_milestones(skills)
    
    # Show celebration banner if there are PRs
    pr_milestones = [m for m in milestones if m["type"] == "pr"]
    if pr_milestones:
        for m in pr_milestones:
            st.markdown(f"""
            <div class="celebration-banner">
                <h3>🎉 New Personal Record!</h3>
                <p><strong>{m['skill']}</strong>: {m['value']:.0f} seconds (+{m['improvement']:.0f}s improvement!)</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.markdown("""
    <div style="text-align: center; padding: 20px 0;">
        <h2 style="color: #667eea; border: none; padding: 0;">📊 Filters</h2>
    </div>
    """, unsafe_allow_html=True)
    
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
    
    # Sidebar stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    <div style="text-align: center;">
        <p style="color: #a0aec0; font-size: 0.9rem;">QUICK STATS</p>
    </div>
    """, unsafe_allow_html=True)
    
    total_workouts = len(workouts) if workouts is not None else 0
    st.sidebar.metric("Total Exercises Logged", f"{total_workouts:,}")
    
    if workouts is not None:
        unique_exercises = workouts["exercise"].nunique()
        st.sidebar.metric("Unique Exercises", unique_exercises)
    
    # ===== KEY METRICS =====
    st.header("📈 Key Metrics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_weeks = len(features_filtered)
        st.metric("Weeks Tracked", total_weeks)
    
    with col2:
        avg_sets = features_filtered["total_sets_all"].mean()
        # Calculate trend
        if len(features_filtered) >= 2:
            recent_avg = features_filtered["total_sets_all"].tail(4).mean()
            older_avg = features_filtered["total_sets_all"].head(4).mean()
            delta = recent_avg - older_avg
            st.metric("Avg Sets/Week", f"{avg_sets:.0f}", f"{delta:+.0f}")
        else:
            st.metric("Avg Sets/Week", f"{avg_sets:.0f}")
    
    with col3:
        avg_reps = features_filtered["total_reps_all"].mean()
        st.metric("Avg Reps/Week", f"{avg_reps:.0f}")
    
    with col4:
        total_work = features_filtered["total_work_all"].sum()
        st.metric("Total Work Volume", f"{total_work:,.0f}")
    
    # ===== TRAINING VOLUME =====
    st.header("📊 Training Volume Over Time")
    
    tab1, tab2, tab3 = st.tabs(["📈 Volume Trend", "🎯 Training Mix", "📋 Weekly Breakdown"])
    
    colors = {
        "strength": "#e74c3c",
        "skill": "#9b59b6", 
        "accessory": "#3498db",
        "mobility": "#2ecc71"
    }
    
    with tab1:
        fig = go.Figure()
        
        for exercise_type in ["mobility", "accessory", "skill", "strength"]:
            col_name = f"total_sets_{exercise_type}"
            if col_name in features_filtered.columns:
                fig.add_trace(go.Scatter(
                    x=features_filtered["week_start"],
                    y=features_filtered[col_name],
                    name=exercise_type.title(),
                    stackgroup='one',
                    fillcolor=colors.get(exercise_type, "#95a5a6"),
                    line=dict(color=colors.get(exercise_type, "#95a5a6"), width=0),
                    hovertemplate=f"<b>{exercise_type.title()}</b><br>Sets: %{{y}}<extra></extra>"
                ))
        
        fig.update_layout(
            title=dict(text="Weekly Sets by Exercise Type", font=dict(size=20)),
            xaxis_title="Week",
            yaxis_title="Total Sets",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
            height=450,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#a0aec0'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True),
            yaxis=dict(gridcolor='rgba(255,255,255,0.1)', showgrid=True),
        )
        
        # Add animation
        fig.update_traces(
            selector=dict(type='scatter'),
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            avg_mix = {
                "Strength": features_filtered.get("pct_work_strength", pd.Series([0])).mean(),
                "Skill": features_filtered.get("pct_work_skill", pd.Series([0])).mean(),
                "Accessory": features_filtered.get("pct_work_accessory", pd.Series([0])).mean(),
                "Mobility": features_filtered.get("pct_work_mobility", pd.Series([0])).mean(),
            }
            
            # Donut chart
            fig_pie = go.Figure(data=[go.Pie(
                labels=list(avg_mix.keys()),
                values=list(avg_mix.values()),
                hole=0.6,
                marker_colors=["#e74c3c", "#9b59b6", "#3498db", "#2ecc71"],
                textinfo='percent',
                textfont_size=14,
                hovertemplate="<b>%{label}</b><br>%{percent}<extra></extra>"
            )])
            
            fig_pie.update_layout(
                title=dict(text="Training Mix Distribution", font=dict(size=18)),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a0aec0'),
                annotations=[dict(
                    text='Training<br>Mix',
                    x=0.5, y=0.5,
                    font_size=16,
                    font_color='#a0aec0',
                    showarrow=False
                )]
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            st.markdown("### Training Breakdown")
            st.markdown("<br>", unsafe_allow_html=True)
            
            for exercise_type, pct in avg_mix.items():
                color = colors.get(exercise_type.lower(), "#95a5a6")
                render_progress_bar(exercise_type, pct, color)
            
            st.markdown("---")
            st.markdown("### 💡 Recommendations")
            
            if avg_mix.get("Skill", 0) < 10:
                st.warning(f"⚠️ Skill work is only **{avg_mix.get('Skill', 0):.1f}%** — consider increasing to 15-20%")
            
            if avg_mix.get("Mobility", 0) < 5:
                st.info(f"ℹ️ Mobility is low (**{avg_mix.get('Mobility', 0):.1f}%**) — may help skill positions")
            
            if avg_mix.get("Strength", 0) > 80:
                st.info(f"ℹ️ Strength dominates at **{avg_mix.get('Strength', 0):.1f}%**")
    
    with tab3:
        display_cols = ["week_start", "total_sets_all", "total_reps_all", "total_work_all"]
        for t in ["strength", "skill", "accessory", "mobility"]:
            col = f"pct_work_{t}"
            if col in features_filtered.columns:
                display_cols.append(col)
        
        display_df = features_filtered[display_cols].copy()
        display_df["week_start"] = display_df["week_start"].dt.strftime("%Y-%m-%d")
        display_df.columns = [c.replace("_", " ").title() for c in display_df.columns]
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Week Start": st.column_config.TextColumn("Week"),
                "Total Sets All": st.column_config.NumberColumn("Sets", format="%d"),
                "Total Reps All": st.column_config.NumberColumn("Reps", format="%d"),
                "Total Work All": st.column_config.NumberColumn("Volume", format="%,.0f"),
            }
        )
    
    # ===== SKILL PROGRESS =====
    if skills is not None and len(skills) > 0:
        st.header("🎯 Skill Progress")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig_skills = go.Figure()
            
            skill_colors = {"Planche": "#9b59b6", "Back Lever": "#e74c3c", "Front Lever": "#3498db"}
            
            for skill_name in skills["skill"].unique():
                skill_data = skills[skills["skill"] == skill_name].sort_values("date")
                color = skill_colors.get(skill_name, "#667eea")
                
                fig_skills.add_trace(go.Scatter(
                    x=skill_data["date"],
                    y=skill_data["hold_seconds"],
                    name=skill_name,
                    mode='lines+markers+text',
                    line=dict(color=color, width=3),
                    marker=dict(size=12, symbol='circle'),
                    text=[f"{v:.0f}s" for v in skill_data["hold_seconds"]],
                    textposition="top center",
                    textfont=dict(size=11),
                    hovertemplate=f"<b>{skill_name}</b><br>Date: %{{x}}<br>Hold: %{{y}}s<extra></extra>"
                ))
            
            fig_skills.update_layout(
                title=dict(text="Skill Hold Duration Over Time", font=dict(size=20)),
                xaxis_title="Date",
                yaxis_title="Hold Duration (seconds)",
                hovermode="x unified",
                height=400,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a0aec0'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
            )
            
            st.plotly_chart(fig_skills, use_container_width=True)
        
        with col2:
            st.markdown("### Progress Summary")
            
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
            st.caption("💡 Add more skill check-ins to track progress")
    
    # ===== EXERCISE ANALYSIS =====
    if workouts is not None and len(workouts) > 0:
        st.header("🏃 Exercise Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            exercise_counts = workouts["exercise"].value_counts().head(12)
            
            fig_exercises = go.Figure(go.Bar(
                x=exercise_counts.values,
                y=exercise_counts.index,
                orientation='h',
                marker=dict(
                    color=exercise_counts.values,
                    colorscale='Blues',
                    line=dict(width=0)
                ),
                hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>"
            ))
            
            fig_exercises.update_layout(
                title=dict(text="Most Frequent Exercises", font=dict(size=18)),
                xaxis_title="Count",
                yaxis_title="",
                height=450,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#a0aec0'),
                yaxis=dict(categoryorder='total ascending'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                showlegend=False,
            )
            
            st.plotly_chart(fig_exercises, use_container_width=True)
        
        with col2:
            if "exercise_type" in workouts.columns:
                # Filter out empty/unknown types for cleaner display
                type_counts = workouts[workouts["exercise_type"].isin(["strength", "skill", "accessory", "mobility"])]["exercise_type"].value_counts()
                
                fig_types = go.Figure(go.Bar(
                    x=type_counts.index,
                    y=type_counts.values,
                    marker_color=[colors.get(t, "#95a5a6") for t in type_counts.index],
                    hovertemplate="<b>%{x}</b><br>Count: %{y}<extra></extra>"
                ))
                
                fig_types.update_layout(
                    title=dict(text="Exercises by Type", font=dict(size=18)),
                    xaxis_title="Type",
                    yaxis_title="Count",
                    height=450,
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#a0aec0'),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.1)'),
                    showlegend=False,
                )
                
                st.plotly_chart(fig_types, use_container_width=True)
    
    # ===== FOOTER =====
    st.markdown("---")
    st.markdown(f"""
    <div class="footer">
        <p>📊 Data last updated: <strong>{datetime.now().strftime("%Y-%m-%d %H:%M")}</strong></p>
        <p>Built with ❤️ using Streamlit | Azure Fit Platform</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
