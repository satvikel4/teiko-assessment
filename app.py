from pathlib import Path
import sqlite3

import altair as alt
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

st.divider()
st.header("Treatment response comparison")
st.caption("Melanoma · miraclib · PBMC samples")
try:
    from analysis import compare_responses, load_response_cohort
except ModuleNotFoundError:
    st.error("Install the analysis dependencies with: pip install -r requirements.txt")
    st.stop()

with sqlite3.connect(f"{DB_PATH.as_uri()}?mode=ro", uri=True) as connection:
    cohort = load_response_cohort(connection)
if cohort.empty:
    st.info("No samples meet the response comparison criteria.")
    st.stop()

try:
    results = compare_responses(cohort)
except ValueError as error:
    st.error(str(error))
    st.stop()

day = st.selectbox("Days from treatment start", sorted(cohort.day.unique()),
                   format_func=lambda value: "0 (baseline)" if value == 0 else str(value))
day_cohort = cohort[cohort.day == day].copy()
day_results = results[results.day == day].drop(columns="day")
day_cohort["Response"] = day_cohort.response.map({"yes": "Responder", "no": "Non-responder"})
left, right = st.columns(2)
left.metric("Responders", day_cohort.loc[day_cohort.response == "yes", "subject_id"].nunique())
right.metric("Non-responders", day_cohort.loc[day_cohort.response == "no", "subject_id"].nunique())

plot_columns = st.columns(2)
for index, population in enumerate(populations):
    chart = alt.Chart(day_cohort[day_cohort.population == population]).mark_boxplot(extent=1.5).encode(
        x=alt.X("Response:N", sort=["Responder", "Non-responder"], title=None),
        y=alt.Y("percentage:Q", title="Relative frequency (%)", scale=alt.Scale(zero=False)),
        color=alt.Color("Response:N", legend=None),
    ).properties(title=population, height=260)
    with plot_columns[index % 2]:
        st.altair_chart(chart, width="stretch")
st.caption("Box: middle 50%; line: median; whiskers: 1.5 × interquartile range; dots: outliers. Each plot has its own vertical scale.")
st.write(
    "Two-sided Mann–Whitney U tests compare frequency distributions at each day. "
    "Bonferroni adjustment covers all populations and days together "
    f"({len(results)} tests); significance requires an adjusted p-value below 0.05. "
    "Each subject contributes once per population at each day; days are never pooled."
)
st.dataframe(day_results, hide_index=True, width="stretch", column_order=[
    "population", "significant", "adjusted_p_value", "p_value", "responders", "nonresponders",
    "responder_median_pct", "nonresponder_median_pct", "median_difference_pp",
], column_config={
    "responder_median_pct": st.column_config.NumberColumn(format="%.3f"),
    "nonresponder_median_pct": st.column_config.NumberColumn(format="%.3f"),
    "median_difference_pp": st.column_config.NumberColumn(format="%.3f"),
    "p_value": st.column_config.NumberColumn(format="%.3e"),
    "adjusted_p_value": st.column_config.NumberColumn(format="%.3e"),
})
significant = day_results.loc[day_results.significant, "population"].tolist()
st.write("Significant populations: " + (", ".join(significant) if significant else "None") + ".")
st.subheader("Overall conclusion across all three days")
st.write(
    "Among melanoma patients receiving miraclib with PBMC samples, none of the five cell "
    "populations showed a statistically significant difference between responders and "
    "nonresponders at days 0, 7, or 14. Each comparison included 331 responders and "
    "325 nonresponders. We used two-sided Mann–Whitney U tests with Bonferroni correction "
    "across 15 comparisons and an adjusted significance threshold of 0.05. The smallest "
    "adjusted p-value was 0.216 for B cells at day 14. These results do not provide "
    "sufficient evidence of a difference; they do not establish that the groups are equivalent."
)
st.caption(
    "Baseline associations are candidates for predicting response. Later measurements may reflect treatment effects. "
    "These comparisons without covariate adjustment do not establish causation or predictive performance; "
    "project, age, and sex may confound results, and cell percentages share a common total."
)
st.download_button("Download all response comparisons", results.to_csv(index=False).encode("utf-8"),
                   file_name="response_comparisons.csv", mime="text/csv")
