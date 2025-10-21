CREATE TABLE IF NOT EXISTS users (
    user_id bigserial PRIMARY KEY,
    username varchar(25) not null unique,
    first_name text not null,
    last_name text not null,
    password_hash text not null,
    role integer default 0
);
/*
CREATE TABLE IF NOT EXISTS tasks (
    task_id bigserial PRIMARY KEY,
    task_name varchar(50) not null unique
);
*/