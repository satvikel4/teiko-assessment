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
