UPDATE user_table SET user_role = 'TEACHER' WHERE username = 'rod';
UPDATE user_table SET user_role = 'ADMIN' WHERE username = 'adm';

ALTER TABLE user_table
ADD COLUMN reg_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE submission
ALTER COLUMN error_message SET DEFAULT 'None';

UPDATE submission SET error_message = 'None' WHERE error_message IS NULL;

ALTER TABLE submission
ADD COLUMN comment TEXT;

ALTER TABLE task
ADD COLUMN status BOOLEAN;

ALTER TABLE task 
ALTER COLUMN status SET DEFAULT 'false';

UPDATE task
SET status = 'true';


INSERT INTO task (task_name, task_description, test_cases, memory_limit, time_limit) 
VALUES (
    '1702',
    'Write a C program that prints "1702!" to the screen.',
    '[
        {"input": "", "output": "1702!"}
    ]'::jsonb,
    128,
    2
);


INSERT INTO task (
    task_name, 
    task_description, 
    test_cases, 
    hidden_test_cases, 
    memory_limit, 
    time_limit, 
    status
) VALUES (
    'Heavy Modulo Sum',
    'Calculate the sum of (i % 3) for all integers i from 1 to N. \nConstraint: N <= 2*10^9.',
    '[{"input": "3", "output": "3"}, {"input": "5", "output": "6"}, {"input": "10", "output": "10"}]'::jsonb,
    '[{"input": "1", "output": "1"}, {"input": "1500000000", "output": "1500000000"}, {"input": "2000000000", "output": "1999999999"}]'::jsonb,
    128,
    2,
    true
);