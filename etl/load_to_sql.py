"""
Load cleaned workout and skill data to SQL database.
Uses flat tables that mirror the Excel sheets for fast iteration.
"""

import pandas as pd
from sqlalchemy import create_engine, text
from pathlib import Path
from read_and_clean_excel import load_workouts, load_skills
from validate import run_all_validations


def create_tables_sqlite(engine):
    """Create tables for SQLite (local testing)."""
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS workout_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                exercise TEXT NOT NULL,
                exercise_type TEXT,
                sets_manual INTEGER,
                reps_manual INTEGER,
                weight REAL,
                weight_unit TEXT,
                notes TEXT,
                is_bodyweight INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS skill_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                skill TEXT NOT NULL,
                progression TEXT,
                achieved INTEGER,
                hold_seconds REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
    print("✓ Tables created/verified")


def create_tables_mssql(engine):
    """Create tables for Azure SQL / SQL Server."""
    with engine.begin() as conn:
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='workout_log' AND xtype='U')
            CREATE TABLE workout_log (
                id INT IDENTITY(1,1) PRIMARY KEY,
                date DATE NOT NULL,
                exercise NVARCHAR(200) NOT NULL,
                exercise_type NVARCHAR(50),
                sets_manual INT,
                reps_manual INT,
                weight FLOAT,
                weight_unit NVARCHAR(50),
                notes NVARCHAR(MAX),
                is_bodyweight BIT,
                created_at DATETIME DEFAULT GETDATE()
            )
        """))
        
        conn.execute(text("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='skill_progress' AND xtype='U')
            CREATE TABLE skill_progress (
                id INT IDENTITY(1,1) PRIMARY KEY,
                date DATE NOT NULL,
                skill NVARCHAR(100) NOT NULL,
                progression NVARCHAR(100),
                achieved BIT,
                hold_seconds FLOAT,
                notes NVARCHAR(MAX),
                created_at DATETIME DEFAULT GETDATE()
            )
        """))
    print("✓ Tables created/verified")


def clear_tables(engine):
    """Clear existing data (useful for re-loading)."""
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM workout_log"))
        conn.execute(text("DELETE FROM skill_progress"))
    print("✓ Cleared existing data")


def load_to_sql(df_workouts: pd.DataFrame, df_skills: pd.DataFrame, engine):
    """Load DataFrames to SQL tables."""
    with engine.begin() as conn:
        # Load workouts
        df_workouts.to_sql("workout_log", conn, if_exists="append", index=False)
        print(f"✓ Loaded {len(df_workouts)} rows to workout_log")
        
        # Load skills
        if len(df_skills) > 0:
            df_skills.to_sql("skill_progress", conn, if_exists="append", index=False)
            print(f"✓ Loaded {len(df_skills)} rows to skill_progress")


def verify_load(engine):
    """Quick verification of loaded data."""
    with engine.connect() as conn:
        workout_count = conn.execute(text("SELECT COUNT(*) FROM workout_log")).scalar()
        skill_count = conn.execute(text("SELECT COUNT(*) FROM skill_progress")).scalar()
        
        print(f"\n=== Database Counts ===")
        print(f"workout_log: {workout_count} rows")
        print(f"skill_progress: {skill_count} rows")
        
        # Show sample data
        print("\n=== Sample Workout Data ===")
        result = conn.execute(text(
            "SELECT date, exercise, exercise_type, sets_manual, reps_manual, weight "
            "FROM workout_log LIMIT 5"
        ))
        for row in result:
            print(row)
        
        print("\n=== Sample Skill Data ===")
        result = conn.execute(text(
            "SELECT date, skill, progression, achieved, hold_seconds "
            "FROM skill_progress LIMIT 5"
        ))
        for row in result:
            print(row)


if __name__ == "__main__":
    # ===========================================
    # CONFIGURE YOUR CONNECTION STRING
    # ===========================================
    
    # Option 1: Local SQLite (for testing)
    SQL_CONN = "sqlite:///data_samples/fitness.db"
    USE_MSSQL = False
    
    # Option 2: Azure SQL (uncomment and configure when ready)
    # SQL_CONN = "mssql+pyodbc://username:password@server.database.windows.net/dbname?driver=ODBC+Driver+18+for+SQL+Server"
    # USE_MSSQL = True
    
    # ===========================================
    
    # Load and validate data
    excel_path = Path(__file__).parent.parent / "data_samples" / "workout_entry_template.xlsx"
    
    print("=== Loading Data ===")
    workouts = load_workouts(excel_path)
    skills = load_skills(excel_path)
    
    print("\n=== Validating Data ===")
    if not run_all_validations(workouts, skills):
        print("\n⚠️  Validation failed — fix errors before loading to DB")
        exit(1)
    
    # Connect to database
    print("\n=== Connecting to Database ===")
    engine = create_engine(SQL_CONN)
    
    # Create tables
    if USE_MSSQL:
        create_tables_mssql(engine)
    else:
        create_tables_sqlite(engine)
    
    # Clear and reload (set to False if you want to append)
    FRESH_LOAD = True
    if FRESH_LOAD:
        clear_tables(engine)
    
    # Load data
    print("\n=== Loading to Database ===")
    load_to_sql(workouts, skills, engine)
    
    # Verify
    verify_load(engine)
    
    print("\n✅ Step 3 Complete — Data loaded to SQL!")

