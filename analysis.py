import pandas as pd
from scipy.stats import mannwhitneyu


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
