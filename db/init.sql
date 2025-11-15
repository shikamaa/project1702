CREATE TABLE IF NOT EXISTS "user_table" (
    user_id BIGSERIAL PRIMARY KEY,
    username VARCHAR(30) NOT NULL UNIQUE,
    first_name VARCHAR(20) NOT NULL,
    last_name VARCHAR(30) NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS "task" (
    task_id BIGSERIAL PRIMARY KEY,
    task_name VARCHAR(200) NOT NULL UNIQUE,
    task_description TEXT,
    test_cases JSONB
);

CREATE TABLE IF NOT EXISTS "submission" (
    submission_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES "user_table"(user_id) ON DELETE CASCADE,
    task_id BIGINT NOT NULL REFERENCES task(task_id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    passed_tests INTEGER DEFAULT 0,
    total_tests INTEGER DEFAULT 0,
    error_message TEXT,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_submission_user ON submission(user_id);
CREATE INDEX idx_submission_task ON submission(task_id);
CREATE INDEX idx_submission_user_task ON submission(user_id, task_id);
CREATE INDEX idx_submission_time ON submission(submitted_at DESC);
CREATE INDEX idx_submission_status ON submission(status);
