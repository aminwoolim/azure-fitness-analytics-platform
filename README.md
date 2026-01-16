# Azure Fit Platform 🏋️

A fitness analytics platform that transforms workout logs into insights. Track your training volume, monitor skill progression, and get ML-powered recommendations. See it all through a beautiful interactive dashboard.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red)
![License](https://img.shields.io/badge/License-MIT-green)

## ✨ Current Features

### 📊 Interactive Dashboard
- **Training Volume Visualization** — Stacked area charts showing weekly sets by exercise type
- **Training Mix Analysis** — Donut charts and progress bars breaking down your strength/skill/accessory/mobility balance
- **Recent Workout Cards** — At-a-glance view of your latest training sessions
- **Personal Record Celebrations** — Animated banners when you hit new PRs

### 🎯 Skill Progress Tracking
- Monitor hold times for calisthenics skills (Planche, Front Lever, Back Lever)
- Track progression over time with interactive line charts
- Get milestone notifications when you achieve significant improvements

### 🔄 ETL Pipeline
- Parse workout data from Excel templates
- Clean and validate entries
- Build weekly aggregated features
- Store in SQLite locally or Azure SQL in the cloud

## Coming Soon...

### 🤖 ML-Powered Insights
- **Feature Importance Analysis** — Understand which training factors correlate with skill gains
- **Linear Regression & Random Forest Models** — Identify what's helping (or hurting) your progress
- **Actionable Recommendations** — Get personalized suggestions to optimize your training mix

## 🏗️ Project Structure

```
azure-fit-platform/
├── dashboard/
│   └── app.py              # Streamlit dashboard application
├── etl/
│   ├── read_and_clean_excel.py
│   ├── parse_workout_text.py
│   ├── validate.py
│   └── load_to_sql.py
├── features/
│   └── build_weekly_features.py
├── models/
│   └── train_skill_predictor.py
├── infrastructure/
│   └── sql_schema.sql
├── data_samples/
│   ├── fitness.db          # Local SQLite database
│   ├── weekly_features.csv
│   └── workout_entry_template.xlsx
├── notebooks/
│   ├── 00_parse_test.ipynb
│   └── 01_explore_workouts.ipynb
└── requirements.txt
```

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/azure-fit-platform.git
   cd azure-fit-platform
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Dashboard

```bash
cd dashboard
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

### Using Azure SQL (Optional)

To connect to Azure SQL instead of local SQLite, set these environment variables or add them to `.streamlit/secrets.toml`:

```toml
AZURE_SQL_SERVER = "your-server.database.windows.net"
AZURE_SQL_DB = "fitness_db"
AZURE_SQL_USER = "your-username"
AZURE_SQL_PASS = "your-password"
```

## 📈 Dashboard Preview

The dashboard provides:

| Section | Description |
|---------|-------------|
| **Key Metrics** | Weeks tracked, average sets/week, total volume |
| **Recent Workouts** | Card view of last 7 training days |
| **Volume Trend** | Stacked area chart by exercise type |
| **Training Mix** | Pie chart + progress bars for workout distribution |
| **Skill Progress** | Line chart tracking hold durations over time |
| **Exercise Analysis** | Bar charts of most frequent exercises |


## 📝 Adding Your Data

1. Fill out `data_samples/workout_entry_template.xlsx` with your workouts
2. Run the ETL pipeline:
   ```bash
   python etl/read_and_clean_excel.py
   python features/build_weekly_features.py
   ```
3. Refresh the dashboard to see your data

## 🛠️ Tech Stack

- **Frontend**: Streamlit with custom CSS animations
- **Visualization**: Plotly (interactive charts)
- **Database**: SQLite (local) / Azure SQL (cloud)
- **ML**: scikit-learn (Linear Regression, Ridge, Random Forest)
- **Data Processing**: pandas, numpy

## 📄 License

This project is licensed under the MIT License.

---

<p align="center">
  Built with ❤️ for fitness enthusiasts who love data
</p>
