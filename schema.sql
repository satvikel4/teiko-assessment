PRAGMA foreign_keys = ON;

CREATE TABLE projects (
    project_id TEXT PRIMARY KEY NOT NULL
);

CREATE TABLE subjects (
    subject_id TEXT PRIMARY KEY NOT NULL,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    condition TEXT NOT NULL,
    age INTEGER NOT NULL CHECK (age >= 0),
    sex TEXT NOT NULL CHECK (sex IN ('M', 'F')),
    treatment TEXT NOT NULL,
    response TEXT CHECK (response IN ('yes', 'no'))
);

CREATE TABLE samples (
    sample_id TEXT PRIMARY KEY NOT NULL,
    subject_id TEXT NOT NULL REFERENCES subjects(subject_id),
    sample_type TEXT NOT NULL CHECK (sample_type IN ('PBMC', 'WB')),
    time_from_treatment_start INTEGER NOT NULL CHECK (time_from_treatment_start >= 0)
);

CREATE TABLE cell_counts (
    sample_id TEXT NOT NULL REFERENCES samples(sample_id),
    population TEXT NOT NULL CHECK (
        population IN ('b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte')
    ),
    count INTEGER NOT NULL CHECK (count >= 0),
    PRIMARY KEY (sample_id, population)
);

CREATE INDEX idx_subjects_project ON subjects(project_id);
CREATE INDEX idx_samples_subject ON samples(subject_id);
CREATE INDEX idx_subjects_cohort ON subjects(condition, treatment, response);
CREATE INDEX idx_samples_cohort ON samples(sample_type, time_from_treatment_start);

CREATE VIEW population_frequencies AS
WITH sample_totals AS (
    SELECT sample_id, SUM(count) AS total_count
    FROM cell_counts
    GROUP BY sample_id
)
SELECT
    c.sample_id AS sample,
    t.total_count,
    c.population,
    c.count,
    100.0 * c.count / NULLIF(t.total_count, 0) AS percentage
FROM cell_counts AS c
JOIN sample_totals AS t ON t.sample_id = c.sample_id;
