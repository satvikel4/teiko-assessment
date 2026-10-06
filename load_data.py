import csv
import os
from pathlib import Path
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parent
CSV_PATH = ROOT / "cell-count.csv"
DB_PATH = ROOT / "teiko.db"
POPULATIONS = ("b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte")
SUBJECT_COLUMNS = ("project", "condition", "age", "sex", "treatment", "response")
REQUIRED_COLUMNS = {"subject", "sample", "sample_type", "time_from_treatment_start",
                    *SUBJECT_COLUMNS, *POPULATIONS}


def nonnegative_integer(value, column, line):
    if not value or not value.isascii() or not value.isdigit():
        raise ValueError(f"CSV line {line}: {column} must be a nonnegative integer")
    return int(value)


def read_data():
    projects, subjects, samples, counts = set(), {}, [], []
    sample_ids = set()
    with CSV_PATH.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or set(reader.fieldnames) != REQUIRED_COLUMNS:
            raise ValueError("CSV columns do not match the expected schema")
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSV line {line}: malformed row")
            row = {key: value.strip() for key, value in row.items()}
            for column in REQUIRED_COLUMNS - {"response"}:
                if not row[column]:
                    raise ValueError(f"CSV line {line}: missing {column}")
            if row["sex"] not in ("M", "F") or row["sample_type"] not in ("PBMC", "WB"):
                raise ValueError(f"CSV line {line}: invalid sex or sample type")
            if row["response"] not in ("", "yes", "no"):
                raise ValueError(f"CSV line {line}: invalid response")
            age = nonnegative_integer(row["age"], "age", line)
            time = nonnegative_integer(row["time_from_treatment_start"],
                                       "time_from_treatment_start", line)
            subject = (row["subject"], row["project"], row["condition"], age,
                       row["sex"], row["treatment"], row["response"] or None)
            previous = subjects.get(row["subject"])
            if previous is not None and previous != subject:
                raise ValueError(f"CSV line {line}: inconsistent metadata for {row['subject']}")
            subjects[row["subject"]] = subject
            projects.add(row["project"])
            if row["sample"] in sample_ids:
                raise ValueError(f"CSV line {line}: duplicate sample {row['sample']}")
            sample_ids.add(row["sample"])
            samples.append((row["sample"], row["subject"], row["sample_type"], time))
            population_counts = [nonnegative_integer(row[p], p, line) for p in POPULATIONS]
            if sum(population_counts) == 0:
                raise ValueError(f"CSV line {line}: sample has zero total cells")
            counts.extend((row["sample"], p, n) for p, n in zip(POPULATIONS, population_counts))
    if not samples:
        raise ValueError("CSV contains no samples")
    return projects, subjects, samples, counts


def main():
    projects, subjects, samples, counts = read_data()
    # Build separately so failed imports preserve any existing database.
    descriptor, temporary_path = tempfile.mkstemp(prefix=".teiko-", suffix=".db", dir=ROOT)
    os.close(descriptor)
    try:
        connection = sqlite3.connect(temporary_path)
        try:
            connection.executescript((ROOT / "schema.sql").read_text())
            with connection:
                connection.executemany("INSERT INTO projects VALUES (?)", [(p,) for p in sorted(projects)])
                connection.executemany("INSERT INTO subjects VALUES (?, ?, ?, ?, ?, ?, ?)", subjects.values())
                connection.executemany("INSERT INTO samples VALUES (?, ?, ?, ?)", samples)
                connection.executemany("INSERT INTO cell_counts VALUES (?, ?, ?)", counts)
                if connection.execute("PRAGMA foreign_key_check").fetchall():
                    raise ValueError("Database foreign-key validation failed")
        finally:
            connection.close()
        os.replace(temporary_path, DB_PATH)
    finally:
        Path(temporary_path).unlink(missing_ok=True)
    print(f"Created {DB_PATH.name}: {len(projects):,} projects, {len(subjects):,} subjects, "
          f"{len(samples):,} samples, {len(counts):,} cell counts")


if __name__ == "__main__":
    main()
