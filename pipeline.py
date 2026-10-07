from pathlib import Path
import sqlite3

import pandas as pd

from analysis import (
    baseline_male_responder_b_cells, compare_responses,
    load_baseline_analysis, load_response_cohort,
)

ROOT = Path(__file__).resolve().parent


def main():
    output = ROOT / "results"
    output.mkdir(exist_ok=True)
    with sqlite3.connect(f"{(ROOT / 'teiko.db').as_uri()}?mode=ro", uri=True) as connection:
        frequencies = pd.read_sql_query(
            "SELECT * FROM population_frequencies ORDER BY sample, population", connection
        )
        comparisons = compare_responses(load_response_cohort(connection))
        baseline, summaries = load_baseline_analysis(connection)
        samples, mean = baseline_male_responder_b_cells(connection)

    frequencies.to_csv(output / "population_frequencies.csv", index=False)
    comparisons.to_csv(output / "response_comparisons.csv", index=False)
    baseline.to_csv(output / "baseline_samples.csv", index=False)
    for category, summary in summaries.items():
        summary.to_csv(output / f"baseline_by_{category}.csv", index=False)
    pd.DataFrame([{"samples": samples, "mean_b_cell_count": mean}]).to_csv(
        output / "baseline_male_responder_b_cells.csv", index=False
    )
    print(f"Exported analysis tables to {output.name}/")
    print(f"Mean B-cell count for baseline melanoma male responders: {mean:.2f}" if mean is not None
          else "No samples match the B-cell query.")


if __name__ == "__main__":
    main()
