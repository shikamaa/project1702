INSERT INTO tasks (
    task_name, 
    task_description, 
    test_cases, 
    hidden_test_cases, 
    memory_limit, 
    time_limit, 
    status
) VALUES (
    'Hello World',
    'Write a program that prints exactly "Hello, World!" to the console.',
    '[{"input": null, "output": "Hello, World!"}]',
    NULL,
    32,
    200,
    true
);

INSERT INTO tasks (
    task_name,
    task_description,
    test_cases,
    hidden_test_cases,
    memory_limit,
    time_limit,
    status
) VALUES (
    'A + B Problem',
    'Given two integers A and B. Print their sum',
    '[
        {"input": {"a": 1, "b": 2}, "output": 3},
        {"input": {"a": 0, "b": 0}, "output": 0},
        {"input": {"a": -1, "b": 1}, "output": 0},
        {"input": {"a": 100, "b": 200}, "output": 300},
        {"input": {"a": -50, "b": -50}, "output": -100},
        {"input": {"a": 999, "b": 1}, "output": 1000},
        {"input": {"a": -999, "b": 999}, "output": 0},
        {"input": {"a": 10, "b": -10}, "output": 0},
        {"input": {"a": 42, "b": 58}, "output": 100},
        {"input": {"a": -42, "b": -58}, "output": -100},
        {"input": {"a": 500, "b": 500}, "output": 1000},
        {"input": {"a": 1, "b": -1}, "output": 0},
        {"input": {"a": 7, "b": 3}, "output": 10},
        {"input": {"a": -7, "b": -3}, "output": -10},
        {"input": {"a": 123, "b": 456}, "output": 579},
        {"input": {"a": -123, "b": 456}, "output": 333},
        {"input": {"a": 123, "b": -456}, "output": -333},
        {"input": {"a": -123, "b": -456}, "output": -579},
        {"input": {"a": 0, "b": 1}, "output": 1},
        {"input": {"a": 1, "b": 0}, "output": 1}
    ]',
    '[
        {"input": {"a": 1000, "b": 2000}, "output": 3000},
        {"input": {"a": -1000, "b": -2000}, "output": -3000},
        {"input": {"a": 9999, "b": 1}, "output": 10000},
        {"input": {"a": -9999, "b": -1}, "output": -10000},
        {"input": {"a": 12345, "b": 67890}, "output": 80235},
        {"input": {"a": -12345, "b": 67890}, "output": 55545},
        {"input": {"a": 12345, "b": -67890}, "output": -55545},
        {"input": {"a": -12345, "b": -67890}, "output": -80235},
        {"input": {"a": 0, "b": 100000}, "output": 100000},
        {"input": {"a": -100000, "b": 0}, "output": -100000},
        {"input": {"a": 50000, "b": 50000}, "output": 100000},
        {"input": {"a": -50000, "b": 50000}, "output": 0},
        {"input": {"a": 11111, "b": 22222}, "output": 33333},
        {"input": {"a": -11111, "b": -22222}, "output": -33333},
        {"input": {"a": 99999, "b": -99999}, "output": 0},
        {"input": {"a": 1, "b": 99999}, "output": 100000},
        {"input": {"a": -1, "b": -99999}, "output": -100000},
        {"input": {"a": 33333, "b": 66667}, "output": 100000},
        {"input": {"a": -33333, "b": -66667}, "output": -100000},
        {"input": {"a": 2147483, "b": -2147483}, "output": 0}
    ]',
    256,
    2,
    true
);