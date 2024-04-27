from sqlalchemy import Column, Integer, String, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

month_names = ["января", "февраля", "марта", "апреля", "мая", "июня",
               "июля", "августа", "сентября", "октября", "ноября", "декабря"]

Base = declarative_base()


class Reply_Insert(BaseModel):
    message_text: str
    username: str
    post_id: int
    chat_id: int


class Reply(Base):
    __tablename__ = 'table_replies'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_text = Column(Text)
    username = Column(String)
    date = Column(Integer)
    post_id = Column(Integer)
    chat_id = Column(Integer)


class Message(Base):
    __tablename__ = 'table_messages'

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(Integer)
    chat_id = Column(Integer)
    user_id = Column(Integer)
    message_text = Column(Text)
    chat_username = Column(String)
    username = Column(String)
    date = Column(Integer)


class User(Base):
    __tablename__ = 'table_users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(Integer)
    chat_username = Column(String)
    user_id = Column(Integer)
    username = Column(String)
    user_first_name = Column(String)
    user_last_name = Column(String)
    is_admin = Column(Boolean)


class PrivateUser(Base):
    __tablename__ = 'table_users_private'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    password = Column(String)
    username = Column(String)
    user_first_name = Column(String)
    user_last_name = Column(String)
    date = Column(Integer)
    is_admin = Column(Boolean)