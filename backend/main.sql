CREATE DATABASE maindb;
Use maindb;

create table table_messages
(
    id            INTEGER
        primary key auto_increment,
    message_id    BIGINT,
    chat_id       BIGINT,
    user_id       BIGINT,
    message_text  TEXT,
    chat_username TEXT,
    username      TEXT,
    date          INTEGER,
    type          TEXT
);

create table table_replies
(
    id                      BIGINT
        primary key auto_increment,
    message_id              BIGINT,
    chat_id                 BIGINT,
    user_id                 BIGINT,
    message_text            TEXT,
    chat_username           TEXT,
    username                TEXT,
    date                    INTEGER,
    replied_to_user_id      BIGINT,
    replied_to_message_text TEXT,
    replied_to_message_id   BIGINT,
    replied_to_message_date TEXT,
    post_id                 integer references table_messages (id)
);

create table table_users
(
    id              BIGINT
        primary key auto_increment,
    chat_id         BIGINT,
    chat_username   TEXT,
    user_id         BIGINT,
    username        TEXT,
    user_first_name TEXT,
    user_last_name  TEXT
);

create table table_users_private
(
    id              BIGINT
        primary key auto_increment,
    user_id         BIGINT,
    password        TEXT,
    username        TEXT,
    user_first_name TEXT,
    user_last_name  TEXT,
    date            BIGINT,
    is_admin        BOOL
);

SELECT *
FROM table_replies
JOIN table_users_private ON table_replies.user_id = table_users_private.user_id
WHERE table_replies.post_id = 1266
ORDER BY table_users_private.is_admin DESC;