"""
FitTrack - Fitness Progress Dashboard
Redesigned with sidebar navigation and compact views to match Figma mockup.
"""

import streamlit as st
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="FitTrack",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== STYLES ====================
st.markdown("""
<style>
    /* ===== GLOBAL ===== */
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 1200px;
    }
    
    /* ===== SIDEBAR STYLING ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #0d1117 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    [data-testid="stSidebar"] .stRadio > label {
        display: none;
    }
    
    [data-testid="stSidebar"] .stRadio > div {
        gap: 0.25rem;
    }
    
    [data-testid="stSidebar"] .stRadio > div > label {
        background: transparent;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 2px 0;
        cursor: pointer;
        transition: all 0.2s ease;
        border: none;
    }
    
    [data-testid="stSidebar"] .stRadio > div > label:hover {
        background: rgba(16, 185, 129, 0.1);
    }
    
    [data-testid="stSidebar"] .stRadio > div > label[data-checked="true"] {
        background: rgba(16, 185, 129, 0.15);
        border-left: 3px solid #10b981;
    }
    
    /* ===== BRAND LOGO ===== */
    .brand-container {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 20px 16px;
        margin-bottom: 20px;
    }
    
    .brand-logo {
        width: 40px;
        height: 40px;
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }
    
    .brand-name {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f3f4f6;
    }
    
    /* ===== NAV ITEMS ===== */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 12px 16px;
        border-radius: 8px;
        color: #9ca3af;
        text-decoration: none;
        transition: all 0.2s ease;
        cursor: pointer;
        margin: 2px 0;
    }
    
    .nav-item:hover {
        background: rgba(16, 185, 129, 0.1);
        color: #f3f4f6;
    }
    
    .nav-item.active {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border-left: 3px solid #10b981;
    }
    
    .nav-icon {
        font-size: 1.1rem;
        width: 24px;
        text-align: center;
    }
    
    /* ===== USER PROFILE ===== */
    .user-profile {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 16px;
        border-top: 1px solid rgba(255, 255, 255, 0.1);
        margin-top: auto;
        position: absolute;
        bottom: 20px;
        left: 0;
        right: 0;
    }
    
    .user-avatar {
        width: 36px;
        height: 36px;
        background: #374151;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
    }
    
    .user-info {
        flex: 1;
    }
    
    .user-name {
        color: #f3f4f6;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .user-plan {
        color: #6b7280;
        font-size: 0.75rem;
    }
    
    /* ===== METRIC CARDS ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        padding: 20px;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    [data-testid="stMetricLabel"] {
        color: #9ca3af !important;
        font-size: 0.8rem !important;
    }
    
    [data-testid="stMetricValue"] {
        color: #f3f4f6 !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricDelta"] {
        color: #10b981 !important;
    }
    
    /* ===== HEADERS ===== */
    .welcome-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #f3f4f6;
        margin-bottom: 0.25rem;
    }
    
    .welcome-subtitle {
        color: #9ca3af;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    
    h2 {
        color: #f3f4f6 !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        margin-bottom: 1rem !important;
    }
    
    /* ===== ACTIVITY CARD ===== */
    .activity-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        display: flex;
        align-items: center;
        gap: 12px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    .activity-card:hover {
        border-color: rgba(16, 185, 129, 0.3);
    }
    
    .activity-icon {
        width: 40px;
        height: 40px;
        background: rgba(16, 185, 129, 0.1);
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    .activity-info {
        flex: 1;
    }
    
    .activity-name {
        color: #f3f4f6;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .activity-date {
        color: #6b7280;
        font-size: 0.75rem;
    }
    
    .activity-arrow {
        color: #6b7280;
    }
    
    /* ===== WORKOUT HISTORY CARD ===== */
    .workout-card {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .workout-header {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 16px;
    }
    
    .workout-title {
        color: #f3f4f6;
        font-weight: 700;
        font-size: 1.1rem;
    }
    
    .workout-meta {
        color: #6b7280;
        font-size: 0.8rem;
    }
    
    .workout-volume {
        text-align: right;
    }
    
    .workout-volume-value {
        color: #10b981;
        font-weight: 700;
        font-size: 1.2rem;
    }
    
    .workout-volume-label {
        color: #6b7280;
        font-size: 0.7rem;
        text-transform: uppercase;
    }
    
    .exercise-row {
        display: flex;
        justify-content: space-between;
        padding: 8px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        color: #9ca3af;
        font-size: 0.85rem;
    }
    
    .exercise-row:last-child {
        border-bottom: none;
    }
    
    /* ===== LOG WORKOUT FORM ===== */
    .form-section {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border-radius: 12px;
        padding: 24px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .exercise-entry {
        background: rgba(0, 0, 0, 0.2);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
    }
    
    .exercise-number {
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        width: 28px;
        height: 28px;
        border-radius: 6px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-size: 0.8rem;
        font-weight: 600;
        margin-bottom: 12px;
    }
    
    /* ===== GREEN BUTTON ===== */
    .stButton > button {
        background: linear-gradient(135deg, #10b981 0%, #059669 100%);
        color: white;
        border: none;
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        width: 100%;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        border: none;
    }
    
    /* ===== COMING SOON ===== */
    .coming-soon {
        text-align: center;
        padding: 80px 20px;
        color: #6b7280;
    }
    
    .coming-soon-icon {
        font-size: 3rem;
        margin-bottom: 16px;
        opacity: 0.5;
    }
    
    .coming-soon-text {
        font-size: 1.2rem;
        font-weight: 600;
        color: #9ca3af;
    }
    
    /* ===== SECTION BOX ===== */
    .section-box {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
        border-radius: 12px;
        padding: 20px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        height: 100%;
    }
    
    .section-title {
        color: #f3f4f6;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 16px;
    }
    
    /* ===== PROGRESS BARS ===== */
    .progress-container {
        margin-bottom: 12px;
    }
    
    .progress-label {
        display: flex;
        justify-content: space-between;
        margin-bottom: 4px;
        font-size: 0.85rem;
    }
    
    .progress-bar-bg {
        background-color: rgba(255, 255, 255, 0.1);
        border-radius: 6px;
        height: 8px;
        width: 100%;
        overflow: hidden;
    }
    
    .progress-bar-fill {
        height: 100%;
        border-radius: 6px;
        transition: width 0.5s ease-out;
    }
    
    /* ===== EXPANDER STYLING ===== */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #1f2937 0%, #111827 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 12px !important;
        color: #f3f4f6 !important;
        font-size: 0.95rem !important;
        padding: 16px 20px !important;
    }
    
    .streamlit-expanderHeader:hover {
        border-color: rgba(16, 185, 129, 0.3) !important;
    }
    
    .streamlit-expanderContent {
        background: linear-gradient(135deg, #1a1f2e 0%, #0f1419 100%) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-top: none !important;
        border-radius: 0 0 12px 12px !important;
        padding: 16px 20px !important;
    }
    
    /* Style the expander arrow */
    .streamlit-expanderHeader svg {
        color: #10b981 !important;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ==================== DATA LOADING ====================
@st.cache_data(ttl=300)
def load_data():
    """Load data from Azure SQL, local SQLite, or CSV files."""
    import os
    
    azure_server = None
    azure_db = None
    azure_user = None
    azure_pass = None
    
    try:
        if 'AZURE_SQL_SERVER' in st.secrets:
            azure_server = st.secrets.get("AZURE_SQL_SERVER")
            azure_db = st.secrets.get("AZURE_SQL_DB", "fitness_db")
            azure_user = st.secrets.get("AZURE_SQL_USER")
            azure_pass = st.secrets.get("AZURE_SQL_PASS")
    except Exception:
        pass
    
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


# ==================== PAGE RENDERERS ====================

def render_dashboard(features, workouts, skills):
    """Render the compact dashboard view."""
    # Header row with welcome and Log Workout button
    col_header, col_btn = st.columns([3, 1])
    
    with col_header:
        st.markdown('<p class="welcome-header">Welcome back, Alex</p>', unsafe_allow_html=True)
        st.markdown('<p class="welcome-subtitle">Here\'s your fitness overview for this week.</p>', unsafe_allow_html=True)
    
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("➕ Log Workout", use_container_width=True):
            st.session_state.current_page = "Log Workout"
            st.rerun()
    
    # Key metrics row (3 cards like Figma)
    col1, col2, col3 = st.columns(3)
    
    # Calculate metrics
    if workouts is not None and len(workouts) > 0:
        last_30_days = datetime.now() - timedelta(days=30)
        recent_workouts = workouts[workouts["date"] >= last_30_days]
        workout_count = recent_workouts["date"].dt.date.nunique()
        
        # Calculate trend
        last_60_days = datetime.now() - timedelta(days=60)
        prev_workouts = workouts[(workouts["date"] >= last_60_days) & (workouts["date"] < last_30_days)]
        prev_count = prev_workouts["date"].dt.date.nunique()
        if prev_count > 0:
            workout_delta = f"+{int((workout_count - prev_count) / prev_count * 100)}%"
        else:
            workout_delta = "+12%"
    else:
        workout_count = 3
        workout_delta = "+12%"
    
    total_minutes = len(features) * 45 if features is not None else 155
    total_volume = features["total_work_all"].sum() if features is not None else 28500
    
    with col1:
        st.metric("Total Workouts", workout_count, workout_delta)
        st.caption("In the last 30 days")
    
    with col2:
        st.metric("Active Minutes", total_minutes, "+5%")
        st.caption("Total time spent training")
    
    with col3:
        volume_display = f"{total_volume/1000:.1f}k" if total_volume >= 1000 else f"{total_volume:.0f}"
        st.metric("Volume Lifted", volume_display, "+8%")
        st.caption("Total lbs moved")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Two-column layout: Chart left, Activity right
    col_chart, col_activity = st.columns([2, 1])
    
    with col_chart:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">Volume Progression</p>', unsafe_allow_html=True)
        
        if features is not None and len(features) > 0:
            # Create compact line chart
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=features["week_start"],
                y=features["total_work_all"],
                mode='lines',
                fill='tozeroy',
                line=dict(color='#10b981', width=2),
                fillcolor='rgba(16, 185, 129, 0.1)',
                hovertemplate="Volume: %{y:,.0f}<extra></extra>"
            ))
            
            fig.update_layout(
                height=250,
                margin=dict(l=0, r=0, t=10, b=0),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#9ca3af'),
                xaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.05)',
                    tickformat='%a',
                    showline=False,
                ),
                yaxis=dict(
                    showgrid=True,
                    gridcolor='rgba(255,255,255,0.05)',
                    tickformat='.0f',
                    showline=False,
                ),
                showlegend=False,
                hovermode='x unified',
            )
            
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        else:
            st.info("No data available yet")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col_activity:
        st.markdown('<div class="section-box">', unsafe_allow_html=True)
        st.markdown('<p class="section-title">Recent Activity</p>', unsafe_allow_html=True)
        
        if workouts is not None and len(workouts) > 0:
            recent = workouts.sort_values("date", ascending=False)
            unique_dates = recent["date"].dt.date.unique()[:3]
            
            for date in unique_dates:
                day_workouts = recent[recent["date"].dt.date == date]
                workout_name = get_workout_name(day_workouts)
                
                st.markdown(f"""
                <div class="activity-card">
                    <div class="activity-icon">💪</div>
                    <div class="activity-info">
                        <div class="activity-name">{workout_name}</div>
                        <div class="activity-date">{pd.Timestamp(date).strftime('%m/%d/%Y')}</div>
                    </div>
                    <div class="activity-arrow">›</div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("View All History", use_container_width=True, key="view_history"):
                st.session_state.current_page = "History"
                st.rerun()
        else:
            st.info("No recent workouts")
        
        st.markdown('</div>', unsafe_allow_html=True)


def get_workout_name(day_workouts):
    """Generate a workout name based on exercises."""
    if day_workouts is None or len(day_workouts) == 0:
        return "Workout"
    
    exercises = day_workouts["exercise"].str.lower()
    
    # Detect workout type
    if any(exercises.str.contains("squat|leg|lunge|calf", na=False)):
        return "Leg Day"
    elif any(exercises.str.contains("bench|chest|push|shoulder|press", na=False)):
        return "Upper Body Power"
    elif any(exercises.str.contains("pull|row|lat|back|deadlift", na=False)):
        return "Pull Day"
    elif any(exercises.str.contains("planche|lever|skill|hold", na=False)):
        return "Skill Practice"
    else:
        return "Full Body Intensity"


def render_log_workout():
    """Render the Log Workout form (placeholder)."""
    st.markdown('<p class="welcome-header">Log Workout</p>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Workout Name", placeholder="e.g. Pull Day")
    
    with col2:
        st.number_input("Duration (mins)", min_value=0, value=45)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Exercises section
    col_label, col_btn = st.columns([2, 1])
    with col_label:
        st.markdown("**Exercises**")
    with col_btn:
        st.markdown('<p style="color: #10b981; text-align: right; cursor: pointer;">+ Add Exercise</p>', unsafe_allow_html=True)
    
    # Exercise entry
    st.markdown("""
    <div class="exercise-entry">
        <div class="exercise-number">#1</div>
    </div>
    """, unsafe_allow_html=True)
    
    col_ex, col_s, col_r, col_w = st.columns([3, 1, 1, 1])
    
    with col_ex:
        st.text_input("Exercise Name", placeholder="Exercise Name", label_visibility="collapsed")
    with col_s:
        st.number_input("S", min_value=0, value=0, label_visibility="collapsed", key="sets")
    with col_r:
        st.number_input("R", min_value=0, value=0, label_visibility="collapsed", key="reps")
    with col_w:
        st.number_input("W", min_value=0, value=0, label_visibility="collapsed", key="weight")
    
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if st.button("Complete Workout", use_container_width=True):
        st.info("🚧 Workout logging coming soon! This is a preview of the interface.")


def render_history(workouts):
    """Render the Workout History page with collapsible cards."""
    st.markdown('<p class="welcome-header">Workout History</p>', unsafe_allow_html=True)
    
    if workouts is None or len(workouts) == 0:
        st.info("No workout history available yet.")
        return
    
    # Date filter
    min_date = workouts["date"].min().date()
    max_date = workouts["date"].max().date()
    
    col_filter1, col_filter2, col_filter3 = st.columns([1, 1, 1])
    
    with col_filter1:
        start_date = st.date_input(
            "From",
            value=max_date - timedelta(days=30),
            min_value=min_date,
            max_value=max_date,
            key="history_start_date"
        )
    
    with col_filter2:
        end_date = st.date_input(
            "To",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key="history_end_date"
        )
    
    with col_filter3:
        st.markdown("<br>", unsafe_allow_html=True)
        # Quick filter buttons
        quick_filter = st.selectbox(
            "Quick select",
            ["Custom", "Last 7 days", "Last 30 days", "Last 90 days", "All time"],
            label_visibility="collapsed"
        )
        
        if quick_filter == "Last 7 days":
            start_date = max_date - timedelta(days=7)
            end_date = max_date
        elif quick_filter == "Last 30 days":
            start_date = max_date - timedelta(days=30)
            end_date = max_date
        elif quick_filter == "Last 90 days":
            start_date = max_date - timedelta(days=90)
            end_date = max_date
        elif quick_filter == "All time":
            start_date = min_date
            end_date = max_date
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter workouts by date range
    filtered_workouts = workouts[
        (workouts["date"].dt.date >= start_date) & 
        (workouts["date"].dt.date <= end_date)
    ]
    
    recent = filtered_workouts.sort_values("date", ascending=False)
    unique_dates = recent["date"].dt.date.unique()
    
    # Show count
    st.markdown(f'<p style="color: #6b7280; font-size: 0.85rem; margin-bottom: 16px;">Showing {len(unique_dates)} workout days</p>', unsafe_allow_html=True)
    
    for i, date in enumerate(unique_dates):
        day_workouts = recent[recent["date"].dt.date == date].copy()
        workout_name = get_workout_name(day_workouts)
        duration = len(day_workouts) * 5  # Estimate
        
        # Calculate volume
        day_workouts["vol"] = day_workouts["sets_manual"].fillna(0) * day_workouts["reps_manual"].fillna(0) * day_workouts["weight"].fillna(0)
        total_volume = day_workouts["vol"].sum()
        
        # Create expander label with workout summary
        expander_label = f"**{workout_name}** · {pd.Timestamp(date).strftime('%m/%d/%Y')} · {duration} min · **{total_volume:,.0f} lbs**"
        
        with st.expander(expander_label, expanded=False):
            # Exercise list inside expander
            st.markdown('<div style="padding: 8px 0;">', unsafe_allow_html=True)
            
            for _, row in day_workouts.iterrows():
                sets = int(row["sets_manual"]) if pd.notna(row["sets_manual"]) else 0
                reps = int(row["reps_manual"]) if pd.notna(row["reps_manual"]) else 0
                weight = int(row["weight"]) if pd.notna(row["weight"]) else 0
                weight_unit = row.get("weight_unit", "lbs") if pd.notna(row.get("weight_unit")) else "lbs"
                
                # Format weight display - if weight is 0, only show the unit (or nothing if unit is "lbs")
                if weight > 0:
                    weight_display = f"@ {weight}{weight_unit}"
                elif weight_unit and weight_unit.lower() not in ["lbs", "lb", "kg", ""]:
                    # For bodyweight, bands, etc. - show just the unit
                    weight_display = f"@ {weight_unit}"
                else:
                    weight_display = ""
                
                st.markdown(f"""
                <div class="exercise-row">
                    <span style="color: #f3f4f6;">{row['exercise']}</span>
                    <span style="color: #10b981; font-weight: 500;">{sets} x {reps} {weight_display}</span>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Summary footer
            total_sets = day_workouts["sets_manual"].sum()
            total_reps = day_workouts["reps_manual"].sum()
            st.markdown(f"""
            <div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.1); color: #6b7280; font-size: 0.8rem;">
                Total: {len(day_workouts)} exercises · {int(total_sets)} sets · {int(total_reps)} reps
            </div>
            """, unsafe_allow_html=True)


def render_statistics(features, workouts, skills):
    """Render the Statistics page with all charts."""
    st.markdown('<p class="welcome-header">Statistics</p>', unsafe_allow_html=True)
    st.markdown('<p class="welcome-subtitle">Detailed analytics and training insights</p>', unsafe_allow_html=True)
    
    if features is None:
        st.info("No data available for statistics.")
        return
    
    colors = {
        "strength": "#e74c3c",
        "skill": "#9b59b6", 
        "accessory": "#3498db",
        "mobility": "#2ecc71"
    }
    
    # Volume Trend
    st.markdown("### 📈 Training Volume Over Time")
    
    fig = go.Figure()
    
    for exercise_type in ["mobility", "accessory", "skill", "strength"]:
        col_name = f"total_sets_{exercise_type}"
        if col_name in features.columns:
            fig.add_trace(go.Scatter(
                x=features["week_start"],
                y=features[col_name],
                name=exercise_type.title(),
                stackgroup='one',
                fillcolor=colors.get(exercise_type, "#95a5a6"),
                line=dict(color=colors.get(exercise_type, "#95a5a6"), width=0),
            ))
    
    fig.update_layout(
        height=350,
        margin=dict(l=0, r=0, t=10, b=0),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#9ca3af'),
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Training Mix
    st.markdown("### 🎯 Training Mix")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        avg_mix = {
            "Strength": features.get("pct_work_strength", pd.Series([0])).mean(),
            "Skill": features.get("pct_work_skill", pd.Series([0])).mean(),
            "Accessory": features.get("pct_work_accessory", pd.Series([0])).mean(),
            "Mobility": features.get("pct_work_mobility", pd.Series([0])).mean(),
        }
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=list(avg_mix.keys()),
            values=list(avg_mix.values()),
            hole=0.6,
            marker_colors=["#e74c3c", "#9b59b6", "#3498db", "#2ecc71"],
            textinfo='percent',
        )])
        
        fig_pie.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#9ca3af'),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        st.markdown("**Training Breakdown**")
        st.markdown("<br>", unsafe_allow_html=True)
        
        for exercise_type, pct in avg_mix.items():
            color = colors.get(exercise_type.lower(), "#95a5a6")
            percentage = min(pct, 100)
            
            st.markdown(f"""
            <div class="progress-container">
                <div class="progress-label">
                    <span style="color: {color};">{exercise_type}</span>
                    <span style="color: #9ca3af;">{pct:.1f}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: {percentage}%; background: {color};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    # Skill Progress
    if skills is not None and len(skills) > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🎯 Skill Progress")
        
        fig_skills = go.Figure()
        
        skill_colors = {"Planche": "#9b59b6", "Back Lever": "#e74c3c", "Front Lever": "#3498db"}
        
        for skill_name in skills["skill"].unique():
            skill_data = skills[skills["skill"] == skill_name].sort_values("date")
            color = skill_colors.get(skill_name, "#10b981")
            
            fig_skills.add_trace(go.Scatter(
                x=skill_data["date"],
                y=skill_data["hold_seconds"],
                name=skill_name,
                mode='lines+markers',
                line=dict(color=color, width=2),
                marker=dict(size=8),
            ))
        
        fig_skills.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#9ca3af'),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title="Hold (seconds)"),
        )
        
        st.plotly_chart(fig_skills, use_container_width=True)
    
    # Exercise Analysis
    if workouts is not None and len(workouts) > 0:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 🏃 Exercise Analysis")
        
        exercise_counts = workouts["exercise"].value_counts().head(10)
        
        fig_exercises = go.Figure(go.Bar(
            x=exercise_counts.values,
            y=exercise_counts.index,
            orientation='h',
            marker=dict(color='#10b981'),
        ))
        
        fig_exercises.update_layout(
            height=350,
            margin=dict(l=0, r=0, t=10, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#9ca3af'),
            yaxis=dict(categoryorder='total ascending'),
            xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
        )
        
        st.plotly_chart(fig_exercises, use_container_width=True)


def render_settings():
    """Render the Settings page (placeholder)."""
    st.markdown('<p class="welcome-header">Settings</p>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="coming-soon">
        <div class="coming-soon-icon">⚙️</div>
        <div class="coming-soon-text">Settings Coming Soon</div>
        <p style="color: #6b7280; margin-top: 8px;">Configure your profile, preferences, and data export options.</p>
    </div>
    """, unsafe_allow_html=True)


# ==================== MAIN ====================

def main():
    # Load data
    features, workouts, skills = load_data()
    
    # Initialize session state
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    # Sidebar
    with st.sidebar:
        # Brand logo
        st.markdown("""
        <div class="brand-container">
            <div class="brand-logo">📈</div>
            <div class="brand-name">FitTrack</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation
        pages = {
            "🏠  Dashboard": "Dashboard",
            "➕  Log Workout": "Log Workout",
            "📅  History": "History",
            "📊  Statistics": "Statistics",
            "⚙️  Settings": "Settings",
        }
        
        selected = st.radio(
            "Navigation",
            list(pages.keys()),
            index=list(pages.values()).index(st.session_state.current_page),
            label_visibility="collapsed"
        )
        
        st.session_state.current_page = pages[selected]
        
        # Spacer
        st.markdown("<br>" * 10, unsafe_allow_html=True)
        
        # User profile at bottom
        st.markdown("""
        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 16px; margin-top: auto;">
            <div style="display: flex; align-items: center; gap: 12px;">
                <div style="width: 36px; height: 36px; background: #374151; border-radius: 50%; display: flex; align-items: center; justify-content: center;">👤</div>
                <div>
                    <div style="color: #f3f4f6; font-weight: 600; font-size: 0.9rem;">Alex Doe</div>
                    <div style="color: #6b7280; font-size: 0.75rem;">Free Plan</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Render current page
    if st.session_state.current_page == "Dashboard":
        render_dashboard(features, workouts, skills)
    elif st.session_state.current_page == "Log Workout":
        render_log_workout()
    elif st.session_state.current_page == "History":
        render_history(workouts)
    elif st.session_state.current_page == "Statistics":
        render_statistics(features, workouts, skills)
    elif st.session_state.current_page == "Settings":
        render_settings()


if __name__ == "__main__":
    main()
