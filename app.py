from pathlib import Path
import sqlite3

import pandas as pd
import streamlit as st

DB_PATH = Path(__file__).resolve().parent / "teiko.db"

st.set_page_config(page_title="Teiko cell analysis", layout="wide")
st.title("Cell population frequencies")
st.caption("Each percentage is calculated from the total count across the five measured populations.")

if not DB_PATH.exists():
    st.error("Database not found. Run python load_data.py before starting the dashboard.")
    st.stop()

try:
    with sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True) as connection:
        frequencies = pd.read_sql_query(
            "SELECT sample, total_count, population, count, percentage "
            "FROM population_frequencies ORDER BY sample, population",
            connection,
        )
except (sqlite3.Error, pd.errors.DatabaseError):
    st.error("Could not read the frequency view. Run python load_data.py to rebuild the database.")
    st.stop()

sample_filter = st.text_input("Sample ID contains", placeholder="e.g. sample00000")
populations = sorted(frequencies["population"].unique())
selected_populations = st.multiselect("Populations", populations, default=populations)

filtered = frequencies[
    frequencies["sample"].str.contains(sample_filter, case=False, regex=False)
    & frequencies["population"].isin(selected_populations)
]

left, right = st.columns(2)
left.metric("Samples shown", filtered["sample"].nunique())
right.metric("Population rows", len(filtered))

if filtered.empty:
    st.info("No rows match the selected filters.")

st.dataframe(
    filtered,
    hide_index=True,
    width="stretch",
    column_config={
        "total_count": st.column_config.NumberColumn("total_count", format="%d"),
        "count": st.column_config.NumberColumn("count", format="%d"),
        "percentage": st.column_config.NumberColumn("percentage", format="%.2f%%"),
    },
)
st.download_button(
    "Download filtered CSV",
    filtered.to_csv(index=False).encode("utf-8"),
    file_name="population_frequencies.csv",
    mime="text/csv",
)
