"""
Utility script to load normalized JSON hackathon datasets into Pandas DataFrames.
"""

import json
import sys
from pathlib import Path
from typing import Optional

# Automatically resolve root repository directory in sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import pandas as pd
from hackathon_scraper.config import NORMALIZED_OUTPUT_DIR

# Configure pandas options for clean terminal output
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 1000)
pd.set_option("display.max_colwidth", 40)


def get_upcoming_dataframe(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Loads upcoming valid hackathon records into a normalized Pandas DataFrame."""
    target = filepath or (NORMALIZED_OUTPUT_DIR / "upcoming.json")
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.json_normalize(data)


def get_all_dataframe(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Loads all normalized hackathon records into a normalized Pandas DataFrame."""
    target = filepath or (NORMALIZED_OUTPUT_DIR / "all.json")
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.json_normalize(data)


def export_dataframes_to_csv() -> None:
    """Exports upcoming and all dataframes to CSV files."""
    df_upcoming = get_upcoming_dataframe()
    df_all = get_all_dataframe()

    upcoming_csv = NORMALIZED_OUTPUT_DIR / "upcoming_dataframe.csv"
    all_csv = NORMALIZED_OUTPUT_DIR / "all_dataframe.csv"

    df_upcoming.to_csv(upcoming_csv, index=False)
    df_all.to_csv(all_csv, index=False)

    print(f"Exported Upcoming DataFrame ({len(df_upcoming)} rows) to: {upcoming_csv}")
    print(f"Exported All DataFrame ({len(df_all)} rows) to: {all_csv}")


if __name__ == "__main__":
    df_upcoming = get_upcoming_dataframe()
    
    print("\n==================== UPCOMING HACKATHONS DATAFRAME ====================")
    print(f"Total Rows: {len(df_upcoming)} | Total Columns: {len(df_upcoming.columns)}\n")
    
    display_cols = [
        "title", "source_site", "event_type", "start_date", "end_date",
        "registration_deadline", "location", "city", "college", "team_size_min", "team_size_max", "mode"
    ]
    avail_cols = [c for c in display_cols if c in df_upcoming.columns]
    
    print(df_upcoming[avail_cols].to_string(index=False))
    print("\n=======================================================================\n")
