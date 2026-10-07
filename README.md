# Teiko assessment

SQLite data loading and a Streamlit dashboard for cell population frequencies, treatment response comparisons, and baseline subsets.

## Run in GitHub Codespaces

Create a Codespace from this repository's **Code → Codespaces** menu. From the repository root, run:

```bash
make setup
make pipeline
make dashboard
```

Requires Python 3.11+ and Make. Setup creates `.venv` and installs dependencies. Pipeline rebuilds `teiko.db` from `cell-count.csv` and exports all analysis tables to `results/`. Dashboard starts Streamlit on port 8501 and reads that database.

**Dashboard:** [Open locally](http://localhost:8501/). In Codespaces, open the **Ports** tab and select **Open in Browser** for port **8501**; the forwarded URL is specific to your Codespace. Keep the dashboard command running. No separately hosted dashboard is provided.

The same commands work locally. If Python is named differently, use `make setup PYTHON=python`. The required loader also runs directly with `python load_data.py` when Python is available under that name. After editing imported Python modules, restart the dashboard with Ctrl+C followed by `make dashboard` if Streamlit retains an older module.

## Data and analysis

- **Part 1:** `schema.sql` defines projects, subjects, samples, and cell counts. Foreign keys link the tables; each sample/population pair is unique. `load_data.py` validates the CSV and replaces the database only after a successful load.
- **Part 2:** The `population_frequencies` view sums the five populations per sample. Each population's percentage is `100 × count / total_count`. The dashboard displays the required five-column table with sample and population filters and a CSV download.
- **Part 3:** Comparisons include melanoma patients receiving miraclib with PBMC samples and response `yes` or `no`. Each population has a responder/nonresponder boxplot. Two-sided Mann–Whitney U tests compare distributions separately at days 0, 7, and 14, avoiding pooling repeated measurements from the same patient. The asymptotic calculation includes tie and continuity corrections. Bonferroni adjustment covers all 15 tests; significance requires adjusted p < 0.05. The table reports group sizes, medians, median differences in percentage points, raw p-values, and adjusted p-values.
- **Part 4:** SQL queries identify melanoma, miraclib, PBMC samples at day 0. Project totals count samples; response and sex totals count distinct subjects. The matching sample list is downloadable. The separate B-cell question includes all treatments and sample types and averages raw counts for baseline melanoma male responders.

## Results for the supplied CSV

The database contains 10,500 samples from 3,500 subjects and 52,500 population measurements.

Each Part 3 comparison includes 331 responders and 325 nonresponders. No population differs significantly after adjustment. The smallest adjusted p-value is 0.216 for B cells at day 14. These results do not establish equivalence, causation, or predictive performance. Baseline is the relevant starting point for predicting response; later measurements may reflect treatment effects. Project, age, and sex are not adjusted for, and the five percentages share a common denominator.

The Part 4 baseline subset contains 656 samples from 656 subjects:

| Summary | Count |
| --- | ---: |
| prj1 samples | 384 |
| prj3 samples | 272 |
| Responders | 331 |
| Nonresponders | 325 |
| Male subjects | 344 |
| Female subjects | 312 |

The separate form answer is **10206.15** B cells, averaged across **485** baseline melanoma male responder samples of all treatment and sample types.

`results/` includes population frequencies, response comparisons, baseline samples, three baseline summary tables, and the B-cell mean. Generated databases, results, and virtual environments are excluded from Git. Rerun `make pipeline` to reproduce them.
