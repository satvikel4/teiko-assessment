import pandas as pd
from scipy.stats import mannwhitneyu


BASELINE_QUERY = """
    SELECT s.sample_id AS sample, u.subject_id AS subject, u.project_id AS project,
           u.response, u.sex, u.age, u.condition, u.treatment,
           s.sample_type, s.time_from_treatment_start
    FROM samples AS s
    JOIN subjects AS u ON u.subject_id = s.subject_id
    WHERE u.condition = 'melanoma' AND u.treatment = 'miraclib'
      AND s.sample_type = 'PBMC' AND s.time_from_treatment_start = 0
"""


def load_baseline_analysis(connection):
    samples = pd.read_sql_query(BASELINE_QUERY + " ORDER BY project, sample", connection)
    summaries = {}
    for category, count, label in [
        ("project", "COUNT(*)", "samples"),
        ("response", "COUNT(DISTINCT subject)", "subjects"),
        ("sex", "COUNT(DISTINCT subject)", "subjects"),
    ]:
        summaries[category] = pd.read_sql_query(
            f"WITH baseline AS ({BASELINE_QUERY}) "
            f"SELECT {category}, {count} AS {label} FROM baseline "
            f"GROUP BY {category} ORDER BY {category}",
            connection,
        )
    return samples, summaries


def baseline_male_responder_b_cells(connection):
    return connection.execute(
        """
        SELECT COUNT(*), AVG(c.count)
        FROM cell_counts AS c
        JOIN samples AS s ON s.sample_id = c.sample_id
        JOIN subjects AS u ON u.subject_id = s.subject_id
        WHERE c.population = 'b_cell' AND u.condition = 'melanoma'
          AND u.sex = 'M' AND u.response = 'yes'
          AND s.time_from_treatment_start = 0
        """
    ).fetchone()


def load_response_cohort(connection):
    return pd.read_sql_query(
        """
        SELECT f.*, s.subject_id, s.time_from_treatment_start AS day, u.response
        FROM population_frequencies AS f
        JOIN samples AS s ON s.sample_id = f.sample
        JOIN subjects AS u ON u.subject_id = s.subject_id
        WHERE u.condition = 'melanoma' AND u.treatment = 'miraclib'
          AND s.sample_type = 'PBMC' AND u.response IN ('yes', 'no')
        ORDER BY day, f.population, s.subject_id
        """,
        connection,
    )


def compare_responses(cohort):
    if cohort.duplicated(["subject_id", "day", "population"]).any():
        raise ValueError("Expected one measurement per subject, day, and population.")

    results = []
    for (day, population), group in cohort.groupby(["day", "population"]):
        responders = group.loc[group.response == "yes", "percentage"]
        nonresponders = group.loc[group.response == "no", "percentage"]
        if responders.empty or nonresponders.empty:
            raise ValueError("Each comparison requires responders and non-responders.")
        test = mannwhitneyu(
            responders, nonresponders, alternative="two-sided", method="asymptotic"
        )
        results.append({
            "day": day,
            "population": population,
            "responders": len(responders),
            "nonresponders": len(nonresponders),
            "responder_median_pct": responders.median(),
            "nonresponder_median_pct": nonresponders.median(),
            "median_difference_pp": responders.median() - nonresponders.median(),
            "p_value": test.pvalue,
        })

    results = pd.DataFrame(results)
    if not results.empty:
        results["adjusted_p_value"] = (results.p_value * len(results)).clip(upper=1)
        results["significant"] = results.adjusted_p_value < 0.05
    return results
