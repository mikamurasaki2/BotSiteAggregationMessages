# CREATE DATABASE maindb;
Use maindb;
drop table table_messages;
drop table table_replies;
drop table table_users_private;
drop table table_users;

create table table_messages
(
    id            int auto_increment
        primary key,
    message_id    bigint null,
    chat_id       bigint null,
    user_id       bigint null,
    message_text  text   null,
    chat_username text   null,
    username      text   null,
    date          int    null,
    question_type          text   null,
    is_admin_answer tinyint(1) null
);

create table table_replies
(
    id                      int auto_increment
        primary key,
    message_id              bigint null,
    chat_id                 bigint null,
    user_id                 bigint null,
    message_text            text   null,
    chat_username           text   null,
    username                text   null,
    date                    int    null,
    replied_to_user_id      bigint null,
    replied_to_message_text text   null,
    replied_to_message_id   bigint null,
    replied_to_message_date text   null,
    post_id                 bigint null
);

create table table_users
(
    id              int auto_increment
        primary key,
    chat_id         bigint     null,
    chat_username   text       null,
    user_id         bigint     null,
    username        text       null,
    user_first_name text       null,
    user_last_name  text       null,
    is_admin        tinyint(1) null
);

create table table_users_private
(
    id              int auto_increment
        primary key,
    user_id         bigint     null,
    password        text       null,
    username        text       null,
    user_first_name text       null,
    user_last_name  text       null,
    date            bigint     null,
    is_admin        tinyint(1) null
);

INSERT INTO maindb.table_users_private (id, user_id, password, username,date, is_admin) VALUES (20, 1087706654, '12345', 'marsvest', 1713784856, 1);
INSERT INTO maindb.table_users_private (id, user_id, password, username, date, is_admin) VALUES (21, 428185681, '8888', 'meganame', 1819148, 0);
INSERT INTO maindb.table_users_private (id, user_id, password, username, date, is_admin) VALUES (22, 1, 'admin', 'admin', null, 1);
INSERT INTO maindb.table_messages (id, message_id, chat_id, user_id, message_text, chat_username, username, date, type) VALUES (1, 1266, -4181092157, 1087706654, '123', 'Чат', 'mars_vest', 1713785630, 'Общее');
INSERT INTO maindb.table_messages (id, message_id, chat_id, user_id, message_text, chat_username, username, date, type) VALUES (2, 1306, -4181092151, 1087706654, 'мой vopros', 'kfvgjdsq xfnbr ^>', 'mars_vest', 1713786815, 'Сервер');
INSERT INTO maindb.table_messages (id, message_id, chat_id, user_id, message_text, chat_username, username, date, type) VALUES (3, 1306, -4181092151, 1087706654, 'мой vopros', 'kfvgjdsq xfnbr ^>', 'mars_vest', 17137868, 'Сервер');
INSERT INTO maindb.table_replies (id, message_id, chat_id, user_id, message_text, chat_username, username, date, replied_to_user_id, replied_to_message_text, replied_to_message_id, replied_to_message_date, post_id) VALUES (1, 1266, -4181092157, 1087706654, 'ответ ответ', 'Чат', 'mars_vest', 1713785639, 1087706654, '123', 1264, '1713785630', 1266);
INSERT INTO maindb.table_replies (id, message_id, chat_id, user_id, message_text, chat_username, username, date, replied_to_user_id, replied_to_message_text, replied_to_message_id, replied_to_message_date, post_id) VALUES (2, 1308, -4181092157, 1087706654, 'ответ на вопрос1', 'Чат', 'mars_vest', 1713786821, 1087706654, 'мой вопрос1', 1306, '1713786815', 1306);
INSERT INTO maindb.table_replies (id, message_id, chat_id, user_id, message_text, chat_username, username, date, replied_to_user_id, replied_to_message_text, replied_to_message_id, replied_to_message_date, post_id) VALUES (3, 1266, 4181092157, 428185681, 'estsss', 'Чат', '8888', 1713786821, 1087706654, 'мой вопрос1', 1264, '1713785630', 1266);
INSERT INTO maindb.table_replies (id, message_id, chat_id, user_id, message_text, chat_username, username, date, replied_to_user_id, replied_to_message_text, replied_to_message_id, replied_to_message_date, post_id) VALUES (4, 1266, -4181092157, 428185681, 'estsssestsssestsss', 'Чат', '8888', 1713785639, 1087706654, 'мой вопрос1', 1264, '1713785630', 1266);
INSERT INTO maindb.table_replies (id, message_id, chat_id, user_id, message_text, chat_username, username, date, replied_to_user_id, replied_to_message_text, replied_to_message_id, replied_to_message_date, post_id) VALUES (5, 1266, -4181092157, 1, 'ответ на вопрос1', 'Чат', 'admin', 1713786821, 1087706654, 'мой вопрос1', 1264, '1713785630', 1266);
INSERT INTO maindb.table_users (id, chat_id, chat_username, user_id, username, user_first_name, user_last_name, is_admin) VALUES (1, -4181092157, 'Чат', 1087706654, 'mars_vest', 'Артём', null, 0);
INSERT INTO maindb.table_users (id, chat_id, chat_username, user_id, username, user_first_name, user_last_name, is_admin) VALUES (2, -4181092157, 'Чат', 1027898442, 'MursusMur', 'SadaTu', null, 0);

SELECT tup.*, tu.user_first_name, tu.user_last_name
FROM table_users_private as tup
LEFT JOIN table_users as tu ON tup.user_id = tu.user_id;