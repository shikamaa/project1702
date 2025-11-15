INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Hello World',
    'Write a C program that prints "Hello, World!" to the screen.',
    '[
        {"input": "", "output": "Hello, World!"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Sum of Two Numbers',
    'Write a program that reads two integers and prints their sum.',
    '[
        {"input": "5 3", "output": "8"},
        {"input": "10 20", "output": "30"},
        {"input": "-5 5", "output": "0"},
        {"input": "100 200", "output": "300"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Even or Odd',
    'Write a program that reads an integer and prints "Even" if the number is even, or "Odd" if it is odd.',
    '[
        {"input": "4", "output": "Even"},
        {"input": "7", "output": "Odd"},
        {"input": "0", "output": "Even"},
        {"input": "-3", "output": "Odd"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Maximum of Three Numbers',
    'Write a program that reads three integers and prints the largest one.',
    '[
        {"input": "5 3 8", "output": "8"},
        {"input": "10 10 5", "output": "10"},
        {"input": "-1 -5 -3", "output": "-1"},
        {"input": "100 200 150", "output": "200"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Factorial',
    'Write a program that calculates the factorial of a number n (n!). It is guaranteed that 0 ≤ n ≤ 12.',
    '[
        {"input": "5", "output": "120"},
        {"input": "0", "output": "1"},
        {"input": "3", "output": "6"},
        {"input": "10", "output": "3628800"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Prime Number Check',
    'Write a program that checks whether a number is prime. Print "Prime" or "Not Prime".',
    '[
        {"input": "7", "output": "Prime"},
        {"input": "4", "output": "Not Prime"},
        {"input": "1", "output": "Not Prime"},
        {"input": "2", "output": "Prime"},
        {"input": "17", "output": "Prime"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Reverse Number',
    'Write a program that reverses the digits of an integer. For example, 123 becomes 321.',
    '[
        {"input": "123", "output": "321"},
        {"input": "500", "output": "5"},
        {"input": "1", "output": "1"},
        {"input": "9876", "output": "6789"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Palindrome Check',
    'Write a program that checks whether a number is a palindrome. Print "Yes" or "No".',
    '[
        {"input": "121", "output": "Yes"},
        {"input": "123", "output": "No"},
        {"input": "1", "output": "Yes"},
        {"input": "12321", "output": "Yes"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Sum of Digits',
    'Write a program that calculates the sum of the digits of an integer.',
    '[
        {"input": "123", "output": "6"},
        {"input": "999", "output": "27"},
        {"input": "1", "output": "1"},
        {"input": "5050", "output": "10"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Fibonacci Number',
    'Write a program that prints the n-th Fibonacci number (0-indexed). F(0)=0, F(1)=1.',
    '[
        {"input": "0", "output": "0"},
        {"input": "1", "output": "1"},
        {"input": "5", "output": "5"},
        {"input": "10", "output": "55"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Greatest Common Divisor',
    'Write a program that finds the greatest common divisor (GCD) of two numbers.',
    '[
        {"input": "12 8", "output": "4"},
        {"input": "17 5", "output": "1"},
        {"input": "100 50", "output": "50"},
        {"input": "21 14", "output": "7"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Power of Number',
    'Write a program that calculates x raised to the power of n (x^n). Use integers only.',
    '[
        {"input": "2 3", "output": "8"},
        {"input": "5 0", "output": "1"},
        {"input": "3 4", "output": "81"},
        {"input": "10 2", "output": "100"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Array Sum',
    'Write a program that reads n integers and prints their sum. First line contains n, second line contains n integers.',
    '[
        {"input": "3\n1 2 3", "output": "6"},
        {"input": "5\n10 20 30 40 50", "output": "150"},
        {"input": "1\n100", "output": "100"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Array Maximum',
    'Write a program that reads n integers and prints the maximum value. First line contains n, second line contains n integers.',
    '[
        {"input": "4\n3 7 2 9", "output": "9"},
        {"input": "5\n-1 -5 -3 -2 -4", "output": "-1"},
        {"input": "3\n100 200 150", "output": "200"}
    ]'::jsonb
);

INSERT INTO task (task_name, task_description, test_cases) 
VALUES (
    'Count Vowels',
    'Write a program that counts the number of vowels (a, e, i, o, u) in a string. Input is a single line string.',
    '[
        {"input": "hello", "output": "2"},
        {"input": "programming", "output": "3"},
        {"input": "aeiou", "output": "5"},
        {"input": "xyz", "output": "0"}
    ]'::jsonb
);